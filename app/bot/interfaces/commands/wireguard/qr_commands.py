import os
import nextcord
from nextcord.ext import commands
from app.shared.interfaces.logging.api import get_bot_logger
logger = get_bot_logger()
from app.bot.interfaces.commands.decorators.auth import bot_owner_only, user_or_higher
from app.bot.interfaces.commands.wireguard.utils import get_user_config
import asyncio
import io
import qrcode

class WireguardQRCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_path = "/app/bot/database/wireguard"

    @nextcord.slash_command(name="wireguard_qr", description="Holt deinen eigenen Wireguard QR-Code")
    @user_or_higher()
    async def wireguard_qr(self, interaction: nextcord.Interaction):
        """Sendet dem Benutzer automatisch seinen WireGuard-QR-Code basierend auf dem Discord-Namen."""
        await interaction.response.defer(ephemeral=True)
        
        username = interaction.user.name  # Holt den Discord-Namen
        logger.debug(f"Executing wireguard_qr command for user: {username}")
        
        user_config = get_user_config(self.config_path, username)
        
        if user_config:
            user_dir = os.path.join(self.config_path, f"peer_{username}")
            qr_code_file = os.path.join(user_dir, f"peer_{username}.png")
            
            if os.path.exists(qr_code_file):
                logger.debug(f"Using existing QR code file: {qr_code_file}")
                # Datei senden
                try:
                    # Verschlüssele die Datei
                    encrypted_file_path = await self.bot.encryption.encrypt_file(qr_code_file)
                    
                    if encrypted_file_path:
                        with open(encrypted_file_path, 'rb') as file:
                            # Erstelle ein File-Objekt für Discord
                            discord_file = nextcord.File(file, filename=f"wireguard_config_{username}.enc")
                            # Sende die Datei als DM
                            try:
                                await interaction.user.send(
                                    content="🔒 Hier ist dein verschlüsselter Wireguard QR-Code. Verwende `/decrypt_file` um ihn zu entschlüsseln:",
                                    file=discord_file
                                )
                                await interaction.followup.send("✅ Verschlüsselter QR-Code wurde dir als private Nachricht gesendet!", ephemeral=True)
                            except nextcord.Forbidden:
                                await interaction.followup.send("❌ Ich konnte dir keine DM senden. Bitte aktiviere DMs von Servermitgliedern.", ephemeral=True)
                        
                        # Temporäre verschlüsselte Datei löschen
                        os.remove(encrypted_file_path)
                    else:
                        await interaction.followup.send("❌ Fehler bei der Verschlüsselung des QR-Codes.", ephemeral=True)
                except Exception as e:
                    logger.error(f"Error sending QR code file: {e}")
                    await interaction.followup.send("❌ Fehler beim Senden des QR-Codes.", ephemeral=True)
            else:
                logger.warning(f"QR code file not found for user {username} at path: {qr_code_file}")
                await interaction.followup.send("❌ QR-Code für deinen Benutzer nicht gefunden.", ephemeral=True)
        else:
            await interaction.followup.send("❌ Keine Wireguard-Konfiguration für deinen Benutzer gefunden.", ephemeral=True)

    @nextcord.slash_command(name="wireguard_get_user_qr", description="Holt den Wireguard QR-Code eines bestimmten Benutzers")
    @bot_owner_only()
    async def wireguard_get_user_qr(self, interaction: nextcord.Interaction, username: str):
        """Sendet die WireGuard-Config eines bestimmten Users als QR-Code."""
        await interaction.response.defer(ephemeral=True)
        
        logger.debug(f"Executing get_user_qr command for user: {username}")
        
        user_config = get_user_config(self.config_path, username)
        
        if user_config:
            user_dir = os.path.join(self.config_path, f"peer_{username}")
            qr_code_file = os.path.join(user_dir, f"peer_{username}.png")
            
            if os.path.exists(qr_code_file):
                logger.debug(f"Using existing QR code file: {qr_code_file}")
                # Datei senden
                try:
                    # Verschlüssele die Datei
                    encrypted_file_path = await self.bot.encryption.encrypt_file(qr_code_file)
                    
                    if encrypted_file_path:
                        with open(encrypted_file_path, 'rb') as file:
                            # Erstelle ein File-Objekt für Discord
                            discord_file = nextcord.File(file, filename=f"wireguard_config_{username}.enc")
                            # Sende die Datei als DM
                            try:
                                await interaction.user.send(
                                    content=f"🔒 Hier ist der verschlüsselte Wireguard QR-Code für Benutzer {username}. Verwende `/decrypt_file` um ihn zu entschlüsseln:",
                                    file=discord_file
                                )
                                await interaction.followup.send(f"✅ Verschlüsselter QR-Code für {username} wurde dir als private Nachricht gesendet!", ephemeral=True)
                            except nextcord.Forbidden:
                                await interaction.followup.send("❌ Ich konnte dir keine DM senden. Bitte aktiviere DMs von Servermitgliedern.", ephemeral=True)
                        
                        # Temporäre verschlüsselte Datei löschen
                        os.remove(encrypted_file_path)
                    else:
                        await interaction.followup.send("❌ Fehler bei der Verschlüsselung des QR-Codes.", ephemeral=True)
                except Exception as e:
                    logger.error(f"Error sending QR code file: {e}")
                    await interaction.followup.send("❌ Fehler beim Senden des QR-Codes.", ephemeral=True)
            else:
                logger.warning(f"QR code file not found for user {username} at path: {qr_code_file}")
                await interaction.followup.send(f"❌ QR-Code für Benutzer {username} nicht gefunden.", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ Keine Wireguard-Konfiguration für Benutzer {username} gefunden.", ephemeral=True)

async def setup(bot):
    # Warte bis encryption service verfügbar ist
    while not hasattr(bot, 'encryption'):
        await asyncio.sleep(1)
    await bot.add_cog(WireguardQRCommands(bot))