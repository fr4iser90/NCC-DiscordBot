import os
import logging
import nextcord
from app.shared.logging import logger

class EnvConfig:
    """
    Environment configuration for the application.
    Handles loading and default values for environment variables.
    """
    
    def __init__(self):
        self.environment = None
        self.is_development = False
        self.is_production = False
        # Core security keys (will be loaded, not generated)
        self.JWT_SECRET_KEY = None
        self.AES_KEY = None
        self.ENCRYPTION_KEY = None
        # Other config values
        self.DISCORD_BOT_TOKEN = None
        self.guild_id = None
        # etc...
        
    def load(self):
        """Load all environment variables with smart defaults"""
        try:
            # Load basic environment settings
            self.environment = os.getenv('ENVIRONMENT', 'development').lower()
            self.is_development = self.environment == 'development'
            self.is_production = self.environment == 'production'
            
            # Load required application variables
            self.DISCORD_BOT_TOKEN = self._load_required_env_var('DISCORD_BOT_TOKEN')
            self.guild_id = self._load_int_env_var('DISCORD_SERVER')
            
            # Load the security keys from environment 
            # (should have been generated by SecurityBootstrapper)
            self.JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
            self.AES_KEY = os.getenv('AES_KEY')
            self.ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
            
            # Fill in optional defaults
            self._load_defaults()
            
            logger.info(f"Environment configuration loaded: {self.environment}")
            return self
            
        except Exception as e:
            logger.error(f"Failed to load environment configuration: {e}")
            raise
    
    def get_intents(self):
        """
        Return Discord intents for the bot based on environment settings.
        Used during bot initialization.
        """
        intents = nextcord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.presences = True
        
        # In development mode, we can enable all intents
        if self.is_development:
            logger.debug("Development mode: Enabling all intents")
            intents = nextcord.Intents.all()
            
        return intents
    
    def _load_defaults(self):
        """Apply default values to missing optional variables"""
        # Define default values for optional variables
        defaults = {
            "DOMAIN": "localhost",
            "TYPE": "Web,Game,File",
            "SESSION_DURATION_HOURS": "24",
            "RATE_LIMIT_WINDOW": "60",
            "RATE_LIMIT_MAX_ATTEMPTS": "5",
            "PUID": "1001",
            "PGID": "987",
        }
        
        # Apply defaults if variables aren't set
        for key, default_value in defaults.items():
            if not os.getenv(key):
                os.environ[key] = default_value
                logger.debug(f"Using default value for {key}: {default_value}")
    
    @staticmethod
    def _load_required_env_var(name):
        """Load a required environment variable"""
        value = os.getenv(name)
        if value is None:
            raise ValueError(f"Required environment variable '{name}' is not set")
        return value
        
    @staticmethod
    def _load_int_env_var(name, default=0):
        """Load an environment variable as an integer"""
        value = os.getenv(name)
        return int(value) if value else default
