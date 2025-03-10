 import asyncio
import logging
import os
import psutil
import platform
from datetime import datetime
from typing import List
from dotenv import load_dotenv

from ..models.metric import Metric
from .system_collector.base import collect_system_data

logger = logging.getLogger('homelab_bot')

load_dotenv()
DOMAIN = os.getenv('DOMAIN')

async def collect_all() -> List[Metric]:
    """Converts system data into Metric objects"""
    logger.info("Collecting system metrics...")
    
    # Get raw data from your existing collector
    data = await collect_system_data()
    
    # Convert to metrics
    metrics = []
    
    # CPU metrics
    metrics.append(Metric(
        name="cpu_usage",
        value=data['cpu'],
        unit="percent",
        metadata={"type": "system", "component": "cpu"}
    ))
    
    # Memory metrics
    memory = data['memory']
    metrics.append(Metric(
        name="memory_used",
        value=memory.used,
        unit="bytes",
        metadata={"type": "system", "component": "memory"}
    ))
    metrics.append(Metric(
        name="memory_total",
        value=memory.total,
        unit="bytes",
        metadata={"type": "system", "component": "memory"}
    ))
    metrics.append(Metric(
        name="memory_percent",
        value=memory.percent,
        unit="percent",
        metadata={"type": "system", "component": "memory"}
    ))
    
    # Swap metrics
    swap = data['swap']
    metrics.append(Metric(
        name="swap_used",
        value=swap.used,
        unit="bytes",
        metadata={"type": "system", "component": "memory"}
    ))
    metrics.append(Metric(
        name="swap_total",
        value=swap.total,
        unit="bytes",
        metadata={"type": "system", "component": "memory"}
    ))
    
    # Disk metrics
    disk = data['disk']
    metrics.append(Metric(
        name="disk_percent",
        value=disk.percent,
        unit="percent",
        metadata={"type": "system", "component": "storage", "path": "/"}
    ))
    
    # Other metrics
    if data['public_ip'] != "N/A":
        metrics.append(Metric(
            name="public_ip",
            value=data['public_ip'],
            metadata={"type": "system", "component": "network"}
        ))
    
    if data['uptime'] != "N/A":
        metrics.append(Metric(
            name="uptime_text",
            value=data['uptime'],
            metadata={"type": "system", "component": "os"}
        ))
    
    if data['cpu_temp'] != "N/A":
        metrics.append(Metric(
            name="cpu_temperature",
            value=data['cpu_temp'],
            unit="celsius",
            metadata={"type": "system", "component": "cpu"}
        ))
    
    # Process disk details if available
    if isinstance(data['disk_details'], dict):
        for path, details in data['disk_details'].items():
            metrics.append(Metric(
                name="disk_used",
                value=details.get("used", 0),
                unit="bytes",
                metadata={"type": "system", "component": "storage", "path": path}
            ))
            metrics.append(Metric(
                name="disk_total", 
                value=details.get("total", 0),
                unit="bytes",
                metadata={"type": "system", "component": "storage", "path": path}
            ))
    
    logger.info(f"Collected {len(metrics)} system metrics")
    return metrics
