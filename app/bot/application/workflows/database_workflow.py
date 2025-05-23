import logging
import asyncio
from typing import Dict, Any, Optional
import nextcord  # Geändert von discord zu nextcord
from sqlalchemy import text  # Wichtig: text direkt importieren
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.application.workflows.base_workflow import BaseWorkflow, WorkflowStatus
from app.shared.infrastructure.database.core.connection import DatabaseConnection
from app.shared.interfaces.logging.api import get_bot_logger
from app.shared.infrastructure.database.session.context import session_context  # Add this import

logger = get_bot_logger()

class DatabaseWorkflow(BaseWorkflow):
    """Workflow for database operations"""
    
    def __init__(self, bot):
        super().__init__("database")
        self.bot = bot
        self.db_service = None
        
        # Database workflow doesn't require guild approval
        self.requires_guild_approval = False
    
    async def initialize(self) -> bool:
        """Initialize the database workflow globally"""
        logger.debug("[DatabaseWorkflow] Starting initialization...")
        try:
            # Important: Initialize the db_service without passing session
            from app.shared.infrastructure.database.service import DatabaseService
            self.db_service = DatabaseService()
            await self.db_service.initialize()
            
            # Mark as active for all guilds since database is global
            if hasattr(self, 'bot') and self.bot:
                for guild in self.bot.guilds:
                    self.guild_status[str(guild.id)] = WorkflowStatus.ACTIVE
            
            logger.debug("[DatabaseWorkflow] Initialized successfully.")
            return True
        except Exception as e:
            logger.error(f"[DatabaseWorkflow] Initialization failed: {e}", exc_info=True)
            return False
            
    async def initialize_for_guild(self, guild_id: str) -> bool:
        """Initialize workflow for a specific guild"""
        # Database is global, so just mark as active
        self.guild_status[guild_id] = WorkflowStatus.ACTIVE
        return True
    
    async def cleanup(self) -> None:
        """Cleanup database resources"""
        logger.info("[DatabaseWorkflow] Starting cleanup...")
        
        try:
            if self.db_service:
                await self.db_service.close()
                
            await super().cleanup()
            logger.info("[DatabaseWorkflow] Cleanup successful.")
            
        except Exception as e:
            logger.error(f"[DatabaseWorkflow] Error during cleanup: {e}", exc_info=True)
    
    def get_db_service(self):
        """Get the database service"""
        return self.db_service
        
    async def cleanup_guild(self, guild_id: str) -> None:
        """Cleanup resources for a specific guild"""
        # Database is global, so just remove status
        await super().cleanup_guild(guild_id)
