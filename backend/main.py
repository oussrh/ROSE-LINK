#!/usr/bin/env python3
"""
ROSE Link - Backend API
=======================

A modern FastAPI-based REST API for managing a VPN router on Raspberry Pi.
Supports Raspberry Pi 3, 4, 5, and Zero 2W.

Features:
- WiFi WAN management (scan, connect, disconnect)
- WireGuard VPN management (profiles, start/stop/restart)
- WiFi Hotspot configuration (SSID, password, channel, WPA3)
- System monitoring (CPU, RAM, disk, temperature)
- VPN watchdog settings

Architecture:
This module is the application entry point. Business logic is organized in:
- config.py: Centralized configuration constants
- models.py: Pydantic models and dataclasses
- exceptions.py: Custom exception hierarchy
- services/: Business logic services
- api/routes/: API endpoint handlers
- utils/: Helper functions (validators, sanitizers, commands)

Author: ROSE Link Team
License: MIT
Version: 0.2.1
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import (
    APP_NAME,
    APP_VERSION,
    APP_DESCRIPTION,
    Paths,
    Security,
    Server,
)
from api import api_router
from services.auth_service import AuthService

# =============================================================================
# Logging Configuration
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("rose-link")

# =============================================================================
# Application Setup
# =============================================================================

app = FastAPI(
    title=f"{APP_NAME} API",
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# =============================================================================
# Middleware Configuration
# =============================================================================

# CORS - Restricted to local network only (security)
app.add_middleware(
    CORSMiddleware,
    allow_origins=Security.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=Security.ALLOWED_METHODS,
    allow_headers=Security.ALLOWED_HEADERS,
)

# =============================================================================
# Route Registration
# =============================================================================

# Mount API routes under /api prefix
app.include_router(api_router, prefix="/api")


# Health check endpoint (at root API level)
@app.get("/api/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """
    Health check endpoint for monitoring.

    Returns:
        Status information for the ROSE Link service
    """
    return {
        "status": "ok",
        "service": APP_NAME,
        "version": APP_VERSION,
    }


# Combined status endpoint (at root API level for backward compatibility)
@app.get("/api/status", tags=["Status"])
async def get_status() -> dict:
    """
    Get overall system status including WAN, VPN, and hotspot.

    Returns:
        Combined status of all major components
    """
    from services.wan_service import WANService
    from services.vpn_service import VPNService
    from services.hotspot_service import HotspotService

    return {
        "wan": WANService.get_status().to_dict(),
        "vpn": VPNService.get_status().to_dict(),
        "ap": HotspotService.get_status().to_dict(),
    }


# =============================================================================
# Static Files
# =============================================================================

# Serve web UI - must be last to not override API routes
app.mount("/", StaticFiles(directory=str(Paths.WEB_DIR), html=True), name="static")

# =============================================================================
# Initialization
# =============================================================================

# Ensure required directories exist
Paths.WG_PROFILES_DIR.mkdir(parents=True, exist_ok=True)

# Initialize API key on startup
_api_key = AuthService.get_or_create_api_key()
logger.info(f"API key available at {Paths.API_KEY_FILE}")

# =============================================================================
# Application Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=Server.HOST,
        port=Server.PORT,
        log_level=Server.LOG_LEVEL,
        access_log=True,
    )
