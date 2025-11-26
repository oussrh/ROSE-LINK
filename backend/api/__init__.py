"""
ROSE Link API Package
=====================

This package contains the FastAPI routes organized by domain:
- auth: Authentication endpoints
- wifi: WiFi WAN management
- vpn: VPN profile and connection management
- hotspot: WiFi hotspot configuration
- system: System information and settings
- websocket: Real-time WebSocket updates
- backup: Configuration backup and restore
- metrics: Prometheus metrics endpoint
- speedtest: Internet speed testing
- ssl: SSL certificate management
- adguard: AdGuard Home DNS ad blocking
- clients: Connected clients management
- qos: Quality of Service traffic prioritization
- setup: First-time setup wizard

Each module contains related endpoints grouped together.
The main router aggregates all sub-routers.

Author: ROSE Link Team
License: MIT
"""

from fastapi import APIRouter

from api.routes import (
    auth,
    wifi,
    vpn,
    hotspot,
    system,
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

# Create the main API router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(wifi.router, prefix="/wifi", tags=["WiFi"])
api_router.include_router(vpn.router, prefix="/vpn", tags=["VPN"])
api_router.include_router(hotspot.router, prefix="/hotspot", tags=["Hotspot"])
api_router.include_router(system.router, prefix="/system", tags=["System"])
api_router.include_router(websocket.router, tags=["WebSocket"])
api_router.include_router(backup.router, tags=["Backup"])
api_router.include_router(metrics.router, tags=["Metrics"])
api_router.include_router(speedtest.router, tags=["SpeedTest"])
api_router.include_router(ssl.router, tags=["SSL"])
api_router.include_router(adguard.router, tags=["AdGuard"])
api_router.include_router(clients.router, tags=["Clients"])
api_router.include_router(qos.router, tags=["QoS"])
api_router.include_router(setup.router, tags=["Setup"])

__all__ = ["api_router"]
