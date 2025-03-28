from abc import ABC, abstractmethod
from typing import List, Optional
from app.shared.domain.models.discord.category_model import CategoryModel, CategoryTemplate

class CategoryRepository(ABC):
    """Interface for Category repository operations"""
    
    @abstractmethod
    def get_all_categories(self) -> List[CategoryModel]:
        """Get all categories from the database"""
        pass
    
    @abstractmethod
    def get_category_by_id(self, category_id: int) -> Optional[CategoryModel]:
        """Get a category by its database ID"""
        pass
    
    @abstractmethod
    def get_category_by_discord_id(self, discord_id: int) -> Optional[CategoryModel]:
        """Get a category by its Discord ID"""
        pass
    
    @abstractmethod
    def get_category_by_name(self, name: str) -> Optional[CategoryModel]:
        """Get a category by its name"""
        pass
    
    @abstractmethod
    def save_category(self, category: CategoryModel) -> CategoryModel:
        """Save a category to the database (create or update)"""
        pass
    
    @abstractmethod
    def update_discord_id(self, category_id: int, discord_id: int) -> bool:
        """Update the Discord ID of a category after it's created in Discord"""
        pass
    
    @abstractmethod
    def update_category_status(self, category_id: int, is_created: bool) -> bool:
        """Update the creation status of a category"""
        pass
    
    @abstractmethod
    def delete_category(self, category_id: int) -> bool:
        """Delete a category from the database"""
        pass
    
    @abstractmethod
    def create_from_template(self, template: CategoryTemplate) -> CategoryModel:
        """Create a new category from a template"""
        pass
    
    @abstractmethod
    def get_enabled_categories(self) -> List[CategoryModel]:
        """Get all enabled categories"""
        pass 