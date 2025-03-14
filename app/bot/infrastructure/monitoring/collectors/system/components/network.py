import aiohttp
import psutil
import logging
from app.bot.infrastructure.config.feature_flags import OFFLINE_MODE

logger = logging.getLogger('homelab_bot')

async def fetch_public_ip():
    """Gets the public IP address asynchronously."""
    if OFFLINE_MODE:
        return "127.0.0.1 (Offline Mode)"
        
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("https://api.ipify.org?format=json") as resp:
                data = await resp.json()
                return data.get("ip", "N/A")
        except Exception as e:
            logger.error(f"Error fetching public IP: {e}")
            return "N/A"

async def get_network_stats():
    """Ermittelt Netzwerkstatistiken."""
    try:
        net_io = psutil.net_io_counters(pernic=True)
        main_interface = max(net_io.items(), key=lambda x: x[1].bytes_sent + x[1].bytes_recv)[0]
        
        admin_text = "Netzwerkschnittstellen:\n"
        for interface, stats in net_io.items():
            sent_mb = stats.bytes_sent / (1024 * 1024)
            recv_mb = stats.bytes_recv / (1024 * 1024)
            admin_text += f"{interface}: ↑ {sent_mb:.2f} MB | ↓ {recv_mb:.2f} MB\n"
        
        main_stats = net_io[main_interface]
        sent_mb = main_stats.bytes_sent / (1024 * 1024)
        recv_mb = main_stats.bytes_recv / (1024 * 1024)
        public_text = f"↑ {sent_mb:.2f} MB | ↓ {recv_mb:.2f} MB"
        
        # Dictionary mit allen Infos zurückgeben
        return {
            "main_interface": main_interface,
            "interfaces": net_io,
            "admin_text": admin_text,
            "public_text": public_text,
            "net_upload": sent_mb,
            "net_download": recv_mb
        }
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Netzwerkstatistiken: {e}")
        return {}