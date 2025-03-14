# app/shared/infrastructure/config/env_manager.py
import os
import logging
from typing import Dict, Any, Optional

class EnvManager:
    """
    Simple environment variable manager for HomeLab Discord Bot
    
    Features:
    - Direct loading of environment variables
    - Optional defaults for missing variables
    """
    
    def __init__(self, 
                 defaults: Optional[Dict[str, str]] = None,
                 log_values: bool = True):
        
        self.logger = logging.getLogger("homelab.env_manager")
        self.defaults = defaults or {}
        self.log_values = log_values
        self.config = {}
    
    def configure(self) -> Dict[str, str]:
        """Load environment variables into configuration dictionary"""
        try:
            # Read environment variables directly
            self._load_from_env()
            
            # Apply defaults for missing values if specified
            self._apply_defaults()
            
            return self.config
            
        except Exception as e:
            self.logger.error(f"Error loading environment variables: {e}")
            return {}
    
    def _load_from_env(self) -> None:
        """Load all environment variables"""
        for key, value in os.environ.items():
            self.config[key] = value
            
            # Log loaded values (but hide sensitive values)
            if self.log_values:
                if any(sensitive in key.lower() for sensitive in ['password', 'token', 'secret', 'key']):
                    self.logger.debug(f"Loaded {key}=[HIDDEN]")
                else:
                    self.logger.debug(f"Loaded {key}={value}")
    
    def _apply_defaults(self) -> None:
        """Apply default values for missing environment variables"""
        for key, value in self.defaults.items():
            if key not in self.config:
                self.config[key] = value
                self.logger.debug(f"Using default for {key}: {value}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value with optional default"""
        return self.config.get(key, default)
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get a boolean configuration value"""
        value = self.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', 'yes', '1', 'y')
        return bool(value)
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get an integer configuration value"""
        value = self.get(key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def get_list(self, key: str, default: list = None, separator: str = ',') -> list:
        """Get a list configuration value (comma-separated by default)"""
        default = default or []
        value = self.get(key)
        if not value:
            return default
        return [item.strip() for item in value.split(separator)]