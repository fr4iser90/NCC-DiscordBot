from cryptography.fernet import Fernet
from datetime import datetime, timedelta
import base64
import os
from app.shared.interface.logging.api import get_bot_logger
logger = get_bot_logger()
from app.shared.domain.repositories.auth.key_repository import KeyRepository
from app.shared.infrastructure.database.session.factory import get_session

class KeyManagementService:
    def __init__(self):
        self.current_key = None
        self.previous_key = None
        self.aes_key = None
        self.jwt_secret_key = None
        self.last_rotation = None
        self.rotation_interval = timedelta(days=30)
        self.session = None
        self.key_repository = None
    
    async def initialize(self):
        """Async initialization method that should be called after creation"""
        # Initialize the repository first
        await self.initialize_repository()
        
        # Then initialize the repository tables if needed
        if self.key_repository:
            await self.key_repository.initialize()
            
        # Then load keys
        await self._load_keys()
        
    async def initialize_repository(self):
        """Initialize the key repository with a database session"""
        try:
            self.session = await get_session()
            self.key_repository = KeyRepository(self.session)
            return True
        except Exception as e:
            logger.error(f"Failed to initialize key repository: {e}")
            return False
        
    async def _load_keys(self):
        """Load keys from database, generating if needed"""
        if not self.key_repository:
            logger.error("Key repository not initialized")
            return False
            
        try:
            # Get encryption keys
            keys = await self.key_repository.get_encryption_keys()
            
            # If no keys exist, generate initial keys
            if not keys or not keys.get('current_key'):
                logger.info("No encryption keys found in database. Generating initial keys.")
                self.current_key = Fernet.generate_key().decode()
                self.previous_key = None
                # Save the initial key
                await self.key_repository.save_encryption_keys(self.current_key, None)
            else:
                self.current_key = keys.get('current_key')
                self.previous_key = keys.get('previous_key')
                
            # Get AES key
            self.aes_key = await self.key_repository.get_aes_key()
            if not self.aes_key:
                logger.info("No AES key found in database. Generating initial key.")
                self.aes_key = base64.urlsafe_b64encode(os.urandom(32)).decode()
                # Save the initial key
                await self.key_repository.save_aes_key(self.aes_key)
                
            # Get JWT secret key
            self.jwt_secret_key = await self.key_repository.get_jwt_secret_key()
            if not self.jwt_secret_key:
                logger.info("No JWT secret key found in database. Generating initial key.")
                self.jwt_secret_key = base64.urlsafe_b64encode(os.urandom(24)).decode()
                # Save the initial key
                await self.key_repository.save_jwt_secret_key(self.jwt_secret_key)
                
            self.last_rotation = await self._get_last_rotation_time()
            return True
        except Exception as e:
            logger.error(f"Failed to load keys: {e}")
            return False
        
    async def _get_last_rotation_time(self):
        """Get timestamp of last key rotation from app.bot.database"""
        return await self.key_repository.get_last_rotation_time()
        
    async def needs_rotation(self):
        """Check if keys need rotation based on time interval"""
        if not self.last_rotation:
            return True
        return datetime.now() - self.last_rotation > self.rotation_interval
        
    async def rotate_keys(self):
        """Perform key rotation and store new keys in database"""
        self.previous_key = self.current_key
        self.current_key = Fernet.generate_key().decode()
        self.last_rotation = datetime.now()
        
        # Store keys in database ONLY
        await self.key_repository.save_encryption_keys(self.current_key, self.previous_key)
        await self.key_repository.save_rotation_timestamp(self.last_rotation)
        
        # Also rotate JWT secret key
        self.jwt_secret_key = base64.urlsafe_b64encode(os.urandom(24)).decode()
        await self.key_repository.save_jwt_secret_key(self.jwt_secret_key)
        
        # Log key rotation (without exposing keys)
        logger.info(f"Security keys have been rotated successfully at {self.last_rotation}")
        
    def get_current_key(self):
        """Get the current encryption key"""
        return self.current_key
        
    def get_previous_key(self):
        """Get the previous encryption key"""
        return self.previous_key
        
    def get_aes_key(self):
        """Get the AES key"""
        return self.aes_key
        
    async def get_jwt_secret_key(self):
        """Get the JWT secret key"""
        return self.jwt_secret_key 