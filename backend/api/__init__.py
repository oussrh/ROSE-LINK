"""
ROSE Link API Package
=====================

This package contains the FastAPI routes organized by domain:
- auth: Authentication endpoints
- wifi: WiFi WAN management
- vpn: VPN profile and connection management
- hotspot: WiFi hotspot configuration
- system: System information and settings

Each module contains related endpoints grouped together.
The main router aggregates all sub-routers.

Author: ROSE Link Team
License: MIT
"""

from fastapi import APIRouter

from api.routes import auth, wifi, vpn, hotspot, system

# Create the main API router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(wifi.router, prefix="/wifi", tags=["WiFi"])
api_router.include_router(vpn.router, prefix="/vpn", tags=["VPN"])
api_router.include_router(hotspot.router, prefix="/hotspot", tags=["Hotspot"])
api_router.include_router(system.router, prefix="/system", tags=["System"])

__all__ = ["api_router"]
