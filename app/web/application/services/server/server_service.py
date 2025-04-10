"""
Service responsible for server selection logic within the web application.
"""
from fastapi import Request, HTTPException, status
from app.shared.infrastructure.models.auth import AppUserEntity
# Import necessary DB models and session management
from app.shared.infrastructure.models.discord import GuildEntity, DiscordGuildUserEntity
from app.shared.infrastructure.database.session.context import session_context # Or use the factory approach if preferred
from app.shared.interface.logging.api import get_web_logger
from sqlalchemy import select
from sqlalchemy.orm import selectinload # To potentially load relationships if needed by ServerInfo
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = get_web_logger()

class ServerService:
    """Handles logic related to server selection and session management for servers."""

    def __init__(self):
        """Initialize ServerService."""
        logger.info("ServerService initialized.")
        # In a real application, repositories should be injected here
        # For now, we use the session context directly

    async def get_available_servers(self, user: AppUserEntity) -> List[GuildEntity]: # Return type is now List[GuildEntity]
        """Get list of servers the user has access to (approved status)."""
        logger.debug(f"Fetching available servers for user: {user.id}")
        
        servers: List[GuildEntity] = []
        try:
            async with session_context() as session:
                if user.is_owner:
                    # Owners see all approved servers
                    stmt = (
                        select(GuildEntity)
                        .where(GuildEntity.access_status == 'approved')
                        # Optionally load relationships if needed for ServerInfo conversion
                        # .options(selectinload(GuildEntity.some_relationship))
                        .order_by(GuildEntity.name)
                    )
                    result = await session.execute(stmt)
                    servers = result.scalars().all()
                    logger.info(f"Owner {user.id} has access to {len(servers)} approved servers.")
                else:
                    # Non-owners: Find guilds they are associated with AND are approved
                    # We need to join AppUser -> DiscordGuildUserEntity -> GuildEntity
                    stmt = (
                        select(GuildEntity)
                        .join(DiscordGuildUserEntity, DiscordGuildUserEntity.guild_id == GuildEntity.guild_id)
                        .where(DiscordGuildUserEntity.user_id == user.id)
                        .where(GuildEntity.access_status == 'approved')
                        # Optionally load relationships
                        .order_by(GuildEntity.name)
                        # Use distinct() to avoid duplicates if a user has multiple roles in one guild (rare)
                        .distinct()
                    )
                    result = await session.execute(stmt)
                    servers = result.scalars().all()
                    logger.info(f"User {user.id} has access to {len(servers)} approved servers they are members of.")
            
            # --- DEBUG LOGGING --- 
            logger.debug(f"Returning {len(servers)} servers from ServerService.get_available_servers.")
            for i, s in enumerate(servers):
                # Log type and relevant attributes to check before Pydantic conversion
                logger.debug(f"  Server {i}: Type={type(s)}, ID={getattr(s, 'guild_id', 'N/A')}, Name={getattr(s, 'name', 'N/A')}, Status={getattr(s, 'access_status', 'N/A')}, Icon={getattr(s, 'icon_url', 'N/A')}, Members={getattr(s, 'member_count', 'N/A')}") 
            # --- END DEBUG LOGGING ---

            # The list of GuildEntity objects will be automatically converted 
            # by FastAPI using the ServerInfo response_model with orm_mode=True.
            return servers
            
        except Exception as e:
            logger.exception(f"Error fetching available servers for user {user.id}: {e}", exc_info=e)
            # Let the controller/global handler deal with the exception
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve server list")

    async def get_all_manageable_servers(self, user: AppUserEntity) -> List[GuildEntity]:
        """Get all servers relevant for owner management (all statuses)."""
        logger.debug(f"Fetching all manageable servers for owner: {user.id}")
        if not user.is_owner:
            logger.warning(f"Non-owner {user.id} attempted to fetch all manageable servers.")
            # Return empty list or raise 403 - raising is probably better
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owners can view all manageable servers.")

        servers: List[GuildEntity] = []
        try:
            async with session_context() as session:
                # Owners see all servers, ordered by name
                stmt = (
                    select(GuildEntity)
                    # Optionally load relationships needed for display later
                    # .options(selectinload(GuildEntity.config), selectinload(GuildEntity.user_roles))
                    .order_by(GuildEntity.name)
                )
                result = await session.execute(stmt)
                servers = result.scalars().all()
                logger.info(f"Owner {user.id} fetching {len(servers)} total servers for management.")
            return servers
        except Exception as e:
            logger.exception(f"Error fetching all manageable servers for owner {user.id}: {e}", exc_info=e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve manageable server list")

    async def get_current_server(self, request: Request, user: AppUserEntity) -> Optional[GuildEntity]: # Return type can also be GuildEntity
        """Get the currently selected server from the user's session."""
        selected_guild_data = request.session.get('selected_guild')
        if not selected_guild_data or 'guild_id' not in selected_guild_data:
            logger.debug(f"No server selected in session for user {user.id}")
            return None

        guild_id = selected_guild_data['guild_id']
        logger.debug(f"Fetching current server {guild_id} from DB for user {user.id}")
        try:
             async with session_context() as session:
                # Fetch the full GuildEntity to ensure data consistency
                stmt = select(GuildEntity).where(GuildEntity.guild_id == guild_id)
                result = await session.execute(stmt)
                guild = result.scalar_one_or_none()
                if not guild:
                     logger.warning(f"Server {guild_id} from session not found in DB.")
                     # Clear invalid session data?
                     request.session.pop('selected_guild', None)
                     return None
                return guild # Return the ORM object
        except Exception as e:
            logger.exception(f"Error fetching current server {guild_id} for user {user.id}: {e}", exc_info=e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve current server")

    async def select_server(self, request: Request, guild_id: str, user: AppUserEntity) -> GuildEntity: # Return GuildEntity
        """Select a server and store its basic info in the session."""
        logger.info(f"User {user.id} attempting to select server: {guild_id}")
        
        try:
            async with session_context() as session:
                # Verify user has access AND server is approved
                stmt = (
                    select(GuildEntity)
                    .join(DiscordGuildUserEntity, DiscordGuildUserEntity.guild_id == GuildEntity.guild_id, isouter=not user.is_owner) # Outer join only if not owner
                    .where(GuildEntity.guild_id == guild_id)
                    .where(GuildEntity.access_status == 'approved')
                )
                # If user is not owner, add condition to check their membership
                if not user.is_owner:
                    stmt = stmt.where(DiscordGuildUserEntity.user_id == user.id)
                
                result = await session.execute(stmt.limit(1))
                server = result.scalar_one_or_none()
                
                if not server:
                    logger.warning(f"User {user.id} denied access to select server {guild_id} (not found, not approved, or no access).")
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this server")

                # Store essential info in session
                selected_data = {
                    "guild_id": server.guild_id,
                    "name": server.name,
                    "icon_url": str(server.icon_url) if server.icon_url else None # Ensure icon_url is string or None for session
                }
                request.session['selected_guild'] = selected_data
                logger.info(f"Stored selected server in session for user {user.id}: {selected_data}")
                
                # Return the full GuildEntity object
                return server 
                
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.exception(f"Error selecting server {guild_id} for user {user.id}: {e}", exc_info=e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server selection failed")

    async def update_guild_access_status(self, guild_id: str, new_status: str, reviewed_by_user_id: int) -> GuildEntity:
        """Updates the access status of a specific guild."""
        logger.info(f"Attempting to update server {guild_id} status to {new_status} by user {reviewed_by_user_id}")
        
        valid_statuses = ['pending', 'approved', 'rejected', 'blocked', 'suspended']
        if new_status.lower() not in valid_statuses:
            logger.error(f"Invalid status '{new_status}' provided for server {guild_id}.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status: {new_status}")

        try:
            async with session_context() as session:
                stmt = select(GuildEntity).where(GuildEntity.guild_id == guild_id)
                result = await session.execute(stmt)
                guild = result.scalar_one_or_none()
                
                if not guild:
                    logger.warning(f"Attempted to update status for non-existent server {guild_id}")
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
                
                guild.access_status = new_status.lower()
                guild.access_reviewed_at = datetime.utcnow() # Use UTC time
                guild.access_reviewed_by = str(reviewed_by_user_id) # Store user ID as string
                
                # Optionally add a note based on status change?
                # guild.access_notes = f"Status set to {new_status} by user {reviewed_by_user_id}"
                
                await session.commit()
                await session.refresh(guild) # Refresh to get updated data
                
                logger.info(f"Successfully updated server {guild_id} status to {new_status}")
                return guild
                
        except HTTPException as http_exc:
            raise http_exc # Re-raise specific HTTP errors
        except Exception as e:
            logger.exception(f"Database error updating server {guild_id} status: {e}", exc_info=e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error during status update")

    # --- Placeholder for potential helper --- 
    # async def check_user_guild_access(self, user_id: int, guild_id: str) -> bool:
    #     """Check if user has approved access to the guild."""
    #     # Logic using DiscordGuildUserRepository and/or GuildRepository
    #     return True # Placeholder
