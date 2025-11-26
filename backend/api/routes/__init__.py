"""
API Routes Package
==================

Contains all API endpoint modules organized by domain.

Author: ROSE Link Team
License: MIT
"""

from . import (
    auth,
    wifi,
    vpn,
    hotspot,
    system,
    health,
    websocket,
    backup,
    metrics,
    speedtest,
    ssl,
    adguard,
    clients,
    qos,
    setup,
)

__all__ = [
    "auth",
    "wifi",
    "vpn",
    "hotspot",
    "system",
    "health",
    "websocket",
    "backup",
    "metrics",
    "speedtest",
    "ssl",
    "adguard",
    "clients",
    "qos",
    "setup",
]
