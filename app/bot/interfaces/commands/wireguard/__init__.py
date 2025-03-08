from .config_commands import WireguardConfigCommands
from .qr_commands import WireguardQRCommands

async def setup(bot):
    """Setup function for the WireGuard commands"""
    try:
        # Check if wireguard service exists
        if not hasattr(bot, 'wireguard_service'):
            from application.services.wireguard.wireguard_service import setup as setup_service
            bot.wireguard_service = await setup_service(bot)
        
        # Initialize command interfaces
        config_commands = WireguardConfigCommands(bot, bot.wireguard_service)
        qr_commands = WireguardQRCommands(bot, bot.wireguard_service)
        
        # Add cogs to bot
        bot.add_cog(config_commands)
        bot.add_cog(qr_commands)
        
        logger.info("WireGuard commands initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize WireGuard commands: {e}")
        raise

__all__ = ["WireguardConfigCommands", "WireguardQRCommands", "setup"]