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
This module is the application entry point. It uses the application factory
pattern for better testability and separation of concerns:

- core/app_factory.py: Application creation and configuration
- core/lifespan.py: Startup/shutdown event handling
- core/middleware.py: CORS and security middleware
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

from config import Server
from core import create_app

# =============================================================================
# Logging Configuration
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

# =============================================================================
# Application Instance
# =============================================================================

# Create the application using the factory pattern
# This allows for easy testing with different configurations
app = create_app()


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
