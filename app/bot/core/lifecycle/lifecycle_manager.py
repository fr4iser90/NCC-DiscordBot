from infrastructure.discord.command_sync_service import CommandSyncService
import asyncio
import os
import logging

logger = logging.getLogger(__name__)

class BotLifecycleManager:
    def __init__(self, bot):
        self.bot = bot
        self.services = []
        self.tasks = []
        self.commands = []
        self.ready_event = asyncio.Event()
        self.command_sync_service = None
        self.pending_commands = []  # Track commands during registration
        self.channel_setup = None
        
    async def _initialize_service(self, service):
        """Initialize a service"""
        try:
            logger.info(f"Initializing service: {service['name']}")
            service_instance = await service['setup'](self.bot)
            # Speichere den Service im Bot für späteren Zugriff
            setattr(self.bot, f"{service['name'].lower().replace(' ', '_')}_service", service_instance)
            logger.info(f"Service initialized: {service['name']}")
        except Exception as e:
            logger.error(f"Failed to initialize service {service['name']}: {e}")
            raise

    async def _start_task(self, task):
        """Start a background task"""
        try:
            logger.info(f"Starting task: {task['name']}")
            asyncio.create_task(task['func'](self.bot, *task['args']))
            logger.info(f"Task started: {task['name']}")
        except Exception as e:
            logger.error(f"Failed to start task {task['name']}: {e}")
            raise

    async def add_service(self, service):
        """Add and initialize a service"""
        self.services.append(service)
        await self._initialize_service(service)
        
    async def add_task(self, task):
        """Add and start a task"""
        self.tasks.append(task)
        await self._start_task(task)

    async def add_command(self, command):
        """Add and register a command"""
        try:
            logger.info(f"Registering command: {command['name']}")
            self.bot.add_cog(command['cog'])
            self.commands.append(command)
            self.pending_commands.extend(command['cog'].application_commands)
            logger.info(f"Command registered: {command['name']}")
        except Exception as e:
            logger.error(f"Failed to register command {command['name']}: {e}")
            raise

    async def register_command(self, cog):
        """Track commands during registration (compatibility with old code)"""
        self.pending_commands.extend(cog.application_commands)
        self.bot.add_cog(cog)

    async def wait_until_ready(self, timeout=30):
        """Wait for all components to be ready"""
        try:
            await asyncio.wait_for(self.ready_event.wait(), timeout=timeout)
            logger.info("All components are ready")
        except asyncio.TimeoutError:
            logger.warning("Timeout waiting for components")

    async def shutdown(self):
        """Gracefully shutdown all components"""
        logger.info("Starting shutdown sequence")
        
        # Shutdown tasks
        for task in self.tasks:
            try:
                logger.debug(f"Stopping task: {task['name']}")
                # Add task cleanup logic here
            except Exception as e:
                logger.error(f"Error stopping task {task['name']}: {e}")

        # Shutdown services
        for service in reversed(self.services):
            try:
                logger.debug(f"Stopping service: {service['name']}")
                # Add service cleanup logic here
            except Exception as e:
                logger.error(f"Error stopping service {service['name']}: {e}")

    async def setup_command_sync(self, enable_guild_sync=True, enable_global_sync=True, timeout=60):
        """Set up the command synchronization service"""
        try:
            logger.info("Setting up command sync service")
            self.command_sync_service = CommandSyncService(
                self.bot, 
                enable_guild_sync=enable_guild_sync,
                enable_global_sync=enable_global_sync
            )
            await self.command_sync_service.initialize()
            logger.info("Command sync service initialized")
            return self.command_sync_service
        except Exception as e:
            logger.error(f"Failed to set up command sync service: {e}")
            raise
    
    async def sync_commands(self, timeout=60):
        """Synchronize commands with Discord"""
        if not self.command_sync_service:
            logger.warning("Command sync service not initialized, setting up now")
            await self.setup_command_sync()
            
        try:
            logger.info("Starting command synchronization")
            sync_time = await self.command_sync_service.sync_all()
            logger.info(f"Command synchronization completed in {sync_time:.2f} seconds")
            return sync_time
        except Exception as e:
            logger.error(f"Command synchronization failed: {e}")
            return None
            
    async def verify_commands(self):
        """Verify commands are properly registered"""
        if not self.command_sync_service:
            logger.warning("Command sync service not initialized, setting up now")
            await self.setup_command_sync()
            
        try:
            registered = await self.command_sync_service.verify_commands()
            return len(registered) > 0
        except Exception as e:
            logger.error(f"Command verification failed: {e}")
            return False

    async def sync_commands_background(self):
        """Start command synchronization in background"""
        if not self.command_sync_service:
            logger.warning("Command sync service not initialized, setting up now")
            await self.setup_command_sync()
            
        try:
            logger.info("Starting background command synchronization")
            await self.command_sync_service.start_background_sync()
            return True
        except Exception as e:
            logger.error(f"Background command synchronization failed: {e}")
            return False

    async def initialize(self, critical_services=None, module_services=None, tasks=None, channel_setup=None, dashboards=None):
        """Initialize all components"""
        try:
            logger.info("Starting initialization sequence")
            
            # Warte bis der Bot bereit ist
            if not self.bot.is_ready():
                logger.info("Waiting for bot to be ready...")
                await self.bot.wait_until_ready()
                
            # Initialize channel setup FIRST
            if channel_setup:
                logger.info("Initializing channel setup...")
                self.channel_setup = await channel_setup['setup'](self.bot)
                # WICHTIG: Erst Mappings erstellen, dann Channels
                await self.channel_setup.initialize()  # Erstellt Mappings
                await self.channel_setup.setup()      # Erstellt Channels und setzt IDs
            
            # Initialize critical services first
            if critical_services:
                for service in critical_services:
                    await self._initialize_service(service)
            
            # Initialize module services BEFORE dashboards
            if module_services:
                for service in module_services:
                    await self._initialize_service(service)
                    
            # Initialize dashboards AFTER services
            if dashboards:
                logger.info("Initializing dashboards...")
                await dashboards['setup'](self.bot)
            
            # Start background tasks
            if tasks:
                for task in tasks:
                    await self._start_task(task)
                    
            logger.info("Initialization sequence completed")
            self.ready_event.set()
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            raise