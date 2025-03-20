"""Security bootstrapper for generating and managing security keys."""
import logging
import base64
import os
import traceback
from cryptography.fernet import Fernet
from sqlalchemy.exc import SQLAlchemyError
from app.shared.infrastructure.database.session.context import session_context
from app.shared.infrastructure.database.repositories.key_repository_impl import KeyRepository

logger = logging.getLogger("homelab.bot")

class SecurityBootstrapper:
    """Handles security initialization and key bootstrapping"""
    
    KEY_TYPES = ["AES_KEY", "ENCRYPTION_KEY", "JWT_SECRET_KEY"]
    
    def __init__(self, auto_db_key_management=True):
        self.auto_db_key_management = auto_db_key_management
        self.key_repository = None
        self.initialized = False
        self.keys = {}  # Store keys in memory instead of environment variables
        
    async def initialize(self):
        """Initialize security bootstrapper with database support"""
        if self.initialized:
            logger.debug("Security bootstrapper already initialized")
            return True
            
        try:
            # Generate in-memory keys first (not in environment variables)
            self._generate_memory_keys()
            
            if self.auto_db_key_management:
                # Try to load keys from database
                try:
                    async with session_context() as session:  # Use context manager
                        self.key_repository = KeyRepository(session)
                        await self._load_keys_from_database()
                        logger.info("Security keys loaded from database successfully")
                except Exception as e:
                    logger.error(f"Failed to load keys from database: {str(e)}")
                    logger.error(traceback.format_exc())
                    # Continue with in-memory keys as fallback
                    logger.warning("Using in-memory keys as fallback for security")
            
            self.initialized = True
            return True
        except Exception as e:
            logger.error(f"Security bootstrapper initialization failed: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def _generate_memory_keys(self):
        """Generate all required security keys in memory (not in environment variables)."""
        for key_type in self.KEY_TYPES:
            # Generate a new key
            if key_type in ["AES_KEY", "ENCRYPTION_KEY"]:
                new_key = Fernet.generate_key().decode('utf-8')
            else:  # JWT_SECRET_KEY
                new_key = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8')
            
            # Store the key in memory
            self.keys[key_type] = new_key
            
            # Log the generation (hide part of the key)
            visible_part = new_key[:5] + "..." if len(new_key) > 5 else new_key
            logger.info(f"Generated {key_type} in memory: {visible_part}")
    
    async def _load_keys_from_database(self):
        """Load security keys from database."""
        for key_type in self.KEY_TYPES:
            try:
                # Try to get the key from database
                key_value = await self.key_repository.get_key(key_type)
                
                if key_value:
                    # Key exists in database, use it
                    self.keys[key_type] = key_value
                    logger.info(f"Loaded {key_type} from database")
                else:
                    # Key doesn't exist in database, store the current one
                    current_key = self.keys.get(key_type)
                    if current_key:
                        # Store the current key in database
                        await self.key_repository.store_key(key_type, current_key)
                        logger.info(f"Stored {key_type} in database")
            except Exception as e:
                logger.error(f"Error processing {key_type}: {str(e)}")
                # Continue with next key
    
    def get_key(self, key_type):
        """Get a security key by type."""
        if key_type not in self.KEY_TYPES:
            raise ValueError(f"Unknown key type: {key_type}")
        
        return self.keys.get(key_type)
