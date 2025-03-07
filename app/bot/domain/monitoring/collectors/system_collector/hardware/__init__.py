from typing import Dict, Any
import logging
from .cpu import get_cpu_info
from .memory import get_memory_info
from .network import get_network_info
from .system import get_system_info
from .power import get_power_info
from .sensors import get_sensor_info

logger = logging.getLogger('homelab_bot')

async def get_hardware_info() -> Dict[str, Any]:
    """Sammelt alle Hardware-Informationen"""
    try:
        hardware_info = {}
        
        # Sammle Informationen von allen Modulen mit Logging
        try:
            cpu_info = await get_cpu_info()
            logger.debug(f"CPU Info erhalten: {cpu_info}")
            hardware_info.update(cpu_info)
        except Exception as e:
            logger.error(f"Fehler beim Sammeln der CPU-Info: {e}")

        try:
            memory_info = await get_memory_info()
            logger.debug(f"Memory Info erhalten: {memory_info}")
            hardware_info.update(memory_info)
        except Exception as e:
            logger.error(f"Fehler beim Sammeln der Memory-Info: {e}")

        try:
            network_info = await get_network_info()
            logger.debug(f"Network Info erhalten: {network_info}")
            hardware_info.update(network_info)
        except Exception as e:
            logger.error(f"Fehler beim Sammeln der Network-Info: {e}")

        try:
            system_info = await get_system_info()
            logger.debug(f"System Info erhalten: {system_info}")
            hardware_info.update(system_info)
        except Exception as e:
            logger.error(f"Fehler beim Sammeln der System-Info: {e}")

        try:
            power_info = await get_power_info()
            logger.debug(f"Power Info erhalten: {power_info}")
            hardware_info.update(power_info)
        except Exception as e:
            logger.error(f"Fehler beim Sammeln der Power-Info: {e}")

        try:
            sensor_info = await get_sensor_info()
            logger.debug(f"Sensor Info erhalten: {sensor_info}")
            hardware_info.update(sensor_info)
        except Exception as e:
            logger.error(f"Fehler beim Sammeln der Sensor-Info: {e}")

        logger.debug(f"Finale Hardware Info: {hardware_info}")
        return hardware_info

    except Exception as e:
        logger.error(f"Kritischer Fehler beim Sammeln der Hardware-Informationen: {e}")
        return {
            'cpu_model': "Nicht verfügbar",
            'cpu_cores': "N/A",
            'cpu_threads': "N/A",
            'ram_total': 0,
            'error': str(e)
        }