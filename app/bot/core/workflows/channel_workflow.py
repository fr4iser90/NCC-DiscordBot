import logging
import nextcord
import asyncio
from typing import Dict, Optional, List
from sqlalchemy import text
import traceback

from app.bot.core.workflows.base_workflow import BaseWorkflow, WorkflowStatus
from app.bot.core.workflows.category_workflow import CategoryWorkflow
from app.bot.core.workflows.database_workflow import DatabaseWorkflow
from app.shared.interface.logging.api import get_bot_logger
from app.shared.infrastructure.database.api import get_session
from app.shared.infrastructure.database.session.context import session_context
from app.shared.domain.repositories.discord import ChannelRepository
from app.shared.domain.repositories.discord import GuildConfigRepository
from app.shared.infrastructure.repositories.discord import ChannelRepositoryImpl
from app.bot.application.services.channel.channel_setup_service import ChannelSetupService


logger = get_bot_logger()

class ChannelWorkflow(BaseWorkflow):
    """Workflow for channel setup and management"""
    
    def __init__(self, category_workflow: CategoryWorkflow, database_workflow: DatabaseWorkflow):
        super().__init__("channel")
        self.category_workflow = category_workflow
        self.database_workflow = database_workflow
        self.channel_repository = None
        self.channel_setup_service = None
        
        # Define dependencies
        self.add_dependency("category")
        self.add_dependency("database")
        
        # Channels require guild approval
        self.requires_guild_approval = True
    
    async def initialize(self) -> bool:
        """Initialize the channel workflow globally"""
        try:
            logger.info("Initializing channel workflow")
            
            # Get database service from the database workflow
            db_service = self.database_workflow.get_db_service()
            if not db_service:
                logger.error("Database service not available, cannot initialize channel workflow")
                return False
            
            # Get category setup service from the category workflow
            category_service = self.category_workflow.get_category_setup_service()
            if not category_service:
                logger.error("Category service not available, cannot initialize channel workflow")
                return False
            
            # Get category repository from the category workflow
            category_repository = self.category_workflow.get_category_repository()
            if not category_repository:
                logger.error("Category repository not available, cannot initialize channel workflow")
                return False
            
            # Create repository and builder
            from app.bot.application.services.channel.channel_builder import ChannelBuilder
            
            self.channel_repository = ChannelRepositoryImpl(db_service)
            
            # Pass both repositories to the channel builder
            channel_builder = ChannelBuilder(self.channel_repository, category_repository)
            
            # Create the channel setup service with all required dependencies
            self.channel_setup_service = ChannelSetupService(
                self.channel_repository,
                channel_builder,
                category_service
            )
            
            # Initialize using direct SQL query to avoid ORM mismatches
            logger.info("Initializing channel setup service")
            
            async with session_context() as session:
                # Check if channels exist
                count_result = await session.execute(text("SELECT COUNT(*) FROM discord_channels"))
                channel_count = count_result.scalar()
                logger.info(f"Found {channel_count} channels")
                
                # Initialize with simplified approach similar to category workflow
                self.channel_setup_service.channels_cache = {}
                
                # Use direct SQL with only columns that actually exist in the database
                channels_query = text("""
                    SELECT id, name, description, category_id, type, position, 
                           permission_level, is_enabled, is_created, nsfw, 
                           slowmode_delay, topic, metadata_json
                    FROM discord_channels
                """)
                channels_result = await session.execute(channels_query)
                
                for row in channels_result:
                    # Unpack the row data
                    (id, name, description, category_id, channel_type, position, 
                     permission_level, is_enabled, is_created, nsfw, 
                     slowmode_delay, topic, metadata_json) = row
                    
                    # Create a channel dictionary for cache
                    channel = {
                        "id": id,
                        "name": name,
                        "description": description,
                        "category_id": category_id,
                        "type": channel_type,
                        "position": position,
                        "permission_level": permission_level,
                        "is_enabled": is_enabled,
                        "is_created": is_created,
                        "nsfw": nsfw,
                        "slowmode_delay": slowmode_delay,
                        "topic": topic,
                        "metadata": metadata_json,
                        # Provide default values for expected properties that don't exist in DB
                        "discord_id": None,
                        "category_discord_id": None,
                        "thread_config": None
                    }
                    self.channel_setup_service.channels_cache[name] = channel
                    
                logger.info(f"Loaded {len(self.channel_setup_service.channels_cache)} channels into cache")
                
            return True
            
        except Exception as e:
            logger.error(f"Channel workflow initialization failed: {e}")
            traceback.print_exc()
            return False
            
    async def initialize_for_guild(self, guild_id: str) -> bool:
        """Initialize workflow for a specific guild"""
        try:
            # Update status to initializing
            self.guild_status[guild_id] = WorkflowStatus.INITIALIZING
            
            # Get the guild
            if not hasattr(self, 'bot') or not self.bot:
                logger.error("Bot instance not available")
                self.guild_status[guild_id] = WorkflowStatus.FAILED
                return False
                
            guild = self.bot.get_guild(int(guild_id))
            if not guild:
                logger.error(f"Could not find guild {guild_id}")
                self.guild_status[guild_id] = WorkflowStatus.FAILED
                return False
                
            # Check if channels are enabled for this guild
            async with session_context() as session:
                guild_config_repo = GuildConfigRepository(session)
                config = await guild_config_repo.get_by_guild_id(str(guild.id))
                
                if not config or not config.enable_channels:
                    logger.info(f"Channels are disabled for guild {guild_id}")
                    self.guild_status[guild_id] = WorkflowStatus.DISABLED
                    return True
            
            # Set up channels
            channels = await self.setup_channels(guild)
            if not channels:
                logger.error(f"Failed to set up channels for guild {guild_id}")
                self.guild_status[guild_id] = WorkflowStatus.FAILED
                return False
                
            # Sync with Discord
            await self.sync_with_discord(guild)
            
            # Mark as active
            self.guild_status[guild_id] = WorkflowStatus.ACTIVE
            return True
            
        except Exception as e:
            logger.error(f"Error initializing channel workflow for guild {guild_id}: {e}")
            self.guild_status[guild_id] = WorkflowStatus.FAILED
            return False
    
    async def cleanup(self) -> None:
        """Cleanup all resources"""
        logger.info("Cleaning up channel workflow")
        await super().cleanup()
        
        # Clear channel cache
        if self.channel_setup_service:
            self.channel_setup_service.channels_cache.clear()
        
    async def setup_channels(self, guild: nextcord.Guild) -> Dict[str, nextcord.TextChannel]:
        """Set up all channels for the guild"""
        if not self.channel_setup_service:
            logger.error("Channel setup service not initialized")
            return {}
            
        # Check if this workflow is enabled for this guild
        async with session_context() as session:
            # Use the implementation class instead of the abstract base class
            from app.shared.infrastructure.repositories.discord.guild_config_repository_impl import GuildConfigRepositoryImpl
            guild_config_repo = GuildConfigRepositoryImpl(session)
            config = await guild_config_repo.get_by_guild_id(str(guild.id))
            
            if not config or not config.enable_channels:
                logger.info(f"Channel workflow is disabled for guild: {guild.name}")
                return {}
        
        logger.info(f"Setting up channels for guild: {guild.name}")
        return await self.channel_setup_service.setup_channels(guild)
    
    async def sync_with_discord(self, guild: nextcord.Guild) -> None:
        """Sync channels with existing Discord channels"""
        if not self.channel_setup_service:
            logger.error("Channel setup service not initialized")
            return
            
        logger.info(f"Syncing channels with Discord for guild: {guild.name}")
        await self.channel_setup_service.sync_with_discord(guild)

    def get_channel_repository(self):
        """Get the channel repository"""
        return self.channel_repository
    
    def get_channel_setup_service(self):
        """Get the channel setup service"""
        return self.channel_setup_service
        
    async def cleanup_guild(self, guild_id: str) -> None:
        """Cleanup resources for a specific guild"""
        logger.info(f"Cleaning up channel workflow for guild {guild_id}")
        await super().cleanup_guild(guild_id)
        
        # Clear any cached data for this guild
        if self.channel_setup_service and hasattr(self.channel_setup_service, 'channels_cache'):
            # Remove any guild-specific channels from cache
            self.channel_setup_service.channels_cache = {
                name: data for name, data in self.channel_setup_service.channels_cache.items()
                if not data.get('guild_id') or data.get('guild_id') != guild_id
            }
