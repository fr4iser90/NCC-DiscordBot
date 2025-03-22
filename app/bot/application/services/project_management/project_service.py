import logging
from typing import List, Optional, Dict
import discord
from app.shared.infrastructure.database.service import DatabaseService
from app.shared.infrastructure.repositories.project_repository_impl import ProjectRepository
from app.shared.infrastructure.database.models.project.project import Project

logger = logging.getLogger("homelab.bot")

class ProjectService:
    """Service for managing projects"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.project_repository = ProjectRepository(db_service)
    
    async def create_project(self, name: str, description: str, guild_id: str, owner_id: str, due_date=None) -> Optional[Project]:
        """Create a new project"""
        try:
            project = Project(
                name=name,
                description=description,
                guild_id=guild_id,
                owner_id=owner_id,
                due_date=due_date,
                status="active"
            )
            
            return await self.project_repository.create_project(project)
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            return None
    
    async def get_projects_for_guild(self, guild_id: str) -> List[Project]:
        """Get all projects for a guild"""
        try:
            return await self.project_repository.get_projects_by_guild(guild_id)
        except Exception as e:
            logger.error(f"Error getting projects for guild {guild_id}: {e}")
            return []
    
    async def get_project(self, project_id: int) -> Optional[Project]:
        """Get a project by ID"""
        try:
            return await self.project_repository.get_project(project_id)
        except Exception as e:
            logger.error(f"Error getting project {project_id}: {e}")
            return None
    
    async def update_project(self, project_id: int, **updates) -> bool:
        """Update a project"""
        try:
            return await self.project_repository.update_project(project_id, **updates)
        except Exception as e:
            logger.error(f"Error updating project {project_id}: {e}")
            return False
    
    async def delete_project(self, project_id: int) -> bool:
        """Delete a project"""
        try:
            return await self.project_repository.delete_project(project_id)
        except Exception as e:
            logger.error(f"Error deleting project {project_id}: {e}")
            return False
    
    async def add_member(self, project_id: int, user_id: str) -> bool:
        """Add a member to a project"""
        try:
            return await self.project_repository.add_project_member(project_id, user_id)
        except Exception as e:
            logger.error(f"Error adding member {user_id} to project {project_id}: {e}")
            return False 