from app.bot.application.services.channel.channel_setup_service import ChannelSetupService
from .game_server_channels import setup_minecraft_channels
from app.shared.interface.logging.api import get_bot_logger
logger = get_bot_logger()

async def setup_discord_channels(bot):
    """Setup function for Discord channels"""
    try:
        # 1. Erst Datenbank initialisieren
        logger.info("Database tables created")
        
        # 2. Dann Channel Setup Service erstellen
        if not hasattr(bot, 'channel_setup'):
            logger.info("Creating new ChannelSetupService")
            bot.channel_setup = ChannelSetupService(bot)
        
        # 3. Service initialisieren wenn Bot ready
        if bot.is_ready():
            await bot.channel_setup.initialize()
            
        logger.info("Discord channel setup service registered")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing Discord channel setup: {e}")
        return False
