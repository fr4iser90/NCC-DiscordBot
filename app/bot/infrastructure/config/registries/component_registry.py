"""Registry for dashboard components."""
import logging
import json
from typing import Dict, Type, Any, Optional
from dataclasses import dataclass

from app.bot.application.interfaces.component_registry import ComponentRegistry as ComponentRegistryInterface
from app.bot.application.interfaces.bot import Bot as BotInterface
from app.bot.interfaces.dashboards.components.base_component import BaseComponent
from app.shared.infrastructure.database.session.context import session_context
from app.shared.infrastructure.repositories.dashboards import DashboardComponentDefinitionRepositoryImpl
from app.shared.infrastructure.models.dashboards import DashboardComponentDefinitionEntity

try:
    from app.shared.interfaces.logging.api import get_bot_logger
    logger = get_bot_logger()
except ImportError:
    logger = logging.getLogger("homelab.components")
    logger.warning("Could not import shared logger, using default logging.")

@dataclass
class ComponentDefinition:
    """Definition of a component that can be registered (for implementation class lookup)"""
    component_type: str
    component_class: Type[BaseComponent]
    description: str
    default_config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.default_config is None:
            self.default_config = {}

class ComponentRegistry(ComponentRegistryInterface):
    """Registry for dashboard UI components, loading definitions from DB."""
    
    def __init__(self):
        self._components: Dict[str, ComponentDefinition] = {}
        self._definitions_by_key: Dict[str, Dict[str, Any]] = {}
        self.bot = None
        self._db_definitions_loaded = False
        logger.debug("Component registry initialized")
        
    async def initialize(self, bot):
        """Loads component definitions from the database."""
        self.bot = bot
        if self._db_definitions_loaded:
             logger.debug("Database component definitions already loaded.")
             return True

        logger.debug("Loading component definitions from database...")
        loaded_count = 0
        try:
            async with session_context() as session:
                repo = DashboardComponentDefinitionRepositoryImpl(session)
                all_definitions = await repo.list_definitions()

                for definition_entity in all_definitions:
                    try:
                        definition_json_str = definition_entity.definition
                        if isinstance(definition_json_str, str):
                            definition_data = json.loads(definition_json_str)
                        elif isinstance(definition_json_str, dict):
                            definition_data = definition_json_str
                        else:
                             logger.warning(f"Skipping definition for key '{definition_entity.component_key}': Invalid format in DB - {type(definition_json_str)}")
                             continue

                        self._definitions_by_key[definition_entity.component_key] = {
                            "type": definition_entity.component_type,
                            "key": definition_entity.component_key,
                            "dashboard_type": definition_entity.dashboard_type,
                            "definition": definition_data
                        }
                        loaded_count += 1
                    except json.JSONDecodeError as json_err:
                         logger.error(f"Failed to parse JSON definition for component key '{definition_entity.component_key}': {json_err}")
                    except Exception as parse_err:
                         logger.error(f"Error processing definition for component key '{definition_entity.component_key}': {parse_err}", exc_info=True)

            self._db_definitions_loaded = True
            logger.debug(f"Successfully loaded {loaded_count} component definitions from database.")
            return True
        except Exception as e:
            logger.error(f"Failed to load component definitions from database: {e}", exc_info=True)
            return False

    def register_component(self, 
                         component_type, 
                         component_class,
                         description,
                         default_config = None):
        """
        Register a component's IMPLEMENTATION CLASS by its type.
        This is needed so the registry knows which Python class to instantiate for a given type.
        This should be called explicitly (e.g., in setup_hooks) for all BaseComponent subclasses.
        """
        if component_type in self._components:
            logger.warning(f"Component implementation class for type '{component_type}' already registered, overwriting.")
            
        self._components[component_type] = ComponentDefinition(
            component_type=component_type,
            component_class=component_class,
            description=description,
            default_config=default_config or {}
        )
        logger.debug(f"Registered component implementation class for type: {component_type} -> {component_class.__name__}")
    
    def get_component_class(self, component_type):
        """Get a component's implementation class by its type."""
        definition = self._components.get(component_type)
        if not definition:
            logger.error(f"Component implementation class for type '{component_type}' not found in registry. Ensure it was registered.")
            return None
        return definition.component_class

    def get_type_by_key(self, component_key):
        """Get the component type ('embed', 'button', etc.) by its unique key."""
        definition = self._definitions_by_key.get(component_key)
        if definition and 'type' in definition:
            return definition['type']
        logger.warning(f"Component type not found in loaded DB definitions for key: '{component_key}'")
        return None

    def get_definition_by_key(self, component_key):
        """Get the full definition dictionary loaded from the DB by its unique key."""
        definition = self._definitions_by_key.get(component_key)
        if not definition:
            logger.warning(f"Component definition not found in loaded DB definitions for key: '{component_key}'")
        return definition
    
    def get_all_component_types(self):
        """Get all registered component implementation types."""
        return list(self._components.keys())
    
    def has_component(self, component_type):
        """Check if a component implementation class is registered for a type."""
        return component_type in self._components 