from app.shared.interface.logging.api import get_bot_logger
logger = get_bot_logger()
from app.bot.infrastructure.config.constants.channel_constants import GameServerChannelConfig

class GameServerChannelService:
    def __init__(self, channel_setup_service):
        self.channel_setup = channel_setup_service
        
    async def setup_minecraft_channels(self, server_id: str, server_name: str) -> bool:
        """Sets up channels for a Minecraft server"""
        logger.info(f"Setting up channels for Minecraft server {server_id} ({server_name})")
        
        config = GameServerChannelConfig.get_minecraft_config(server_id, server_name)
        await self.channel_setup.register_gameserver_channels(server_id, config)
        return True