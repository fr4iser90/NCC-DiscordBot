from typing import Dict, List, Any, Optional, Callable
import asyncio
from app.shared.infrastructure.encryption.key_management_service import KeyManagementService
from app.web.domain.auth.services.web_authentication_service import WebAuthenticationService
from app.shared.interface.logging.api import get_bot_logger

logger = get_bot_logger()

class WebLifecycleManager:
    """Manages the lifecycle of web components, following bot pattern"""
    
    def __init__(self):
        self.state = "initializing"
        self.shutdown_hooks = []
        self.startup_hooks = []
        self.components = {}
        self.services_initialized = False

        # Register core services
        self._register_core_services()

    def _register_core_services(self):
        """Register core services that should be available"""
        try:
            # Create and register key service
            key_service = KeyManagementService()
            self.register_component('key_service', key_service)

            # Create and register auth service
            auth_service = WebAuthenticationService(key_service)
            self.register_component('auth_service', auth_service)

            logger.info("Core services registered successfully")
        except Exception as e:
            logger.error(f"Failed to register core services: {e}")
            raise

    def register_shutdown_hook(self, hook: Callable):
        """Register a function to be called during shutdown"""
        self.shutdown_hooks.append(hook)
        logger.debug(f"Registered shutdown hook: {hook.__name__}")
    
    def register_startup_hook(self, hook: Callable):
        """Register a function to be called during startup"""
        self.startup_hooks.append(hook)
        logger.debug(f"Registered startup hook: {hook.__name__}")
    
    async def on_startup(self):
        """Execute all registered startup hooks and initialize services"""
        logger.info("Executing startup hooks")
        self.state = "starting"
        
        # Initialize registered services
        for name, service in self.components.items():
            if hasattr(service, 'initialize'):
                try:
                    await service.initialize()
                    logger.info(f"Initialized service: {name}")
                except Exception as e:
                    logger.error(f"Failed to initialize service {name}: {e}")
                    raise
        
        # Execute startup hooks
        for hook in self.startup_hooks:
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook()
                else:
                    hook()
            except Exception as e:
                logger.error(f"Error in startup hook {hook.__name__}: {e}")
                raise
        
        self.state = "running"
        self.services_initialized = True
        logger.info("Startup complete")
    
    async def on_shutdown(self):
        """Execute all registered shutdown hooks"""
        logger.info("Executing shutdown hooks")
        self.state = "shutting_down"
        
        for hook in self.shutdown_hooks:
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook()
                else:
                    hook()
            except Exception as e:
                logger.error(f"Error in shutdown hook {hook.__name__}: {e}")
        
        self.state = "shutdown"
        logger.info("Shutdown complete")
    
    def register_component(self, name: str, component: Any):
        """Register a component with the lifecycle manager"""
        self.components[name] = component
        logger.debug(f"Registered component: {name}")
    
    def get_component(self, name: str) -> Optional[Any]:
        """Get a registered component by name"""
        return self.components.get(name)
    
    def get_state(self) -> str:
        """Get the current lifecycle state"""
        return self.state