"""
Hotspot API Routes
==================

Endpoints for WiFi hotspot (access point) management.

Endpoints:
- GET /api/hotspot/status: Get hotspot status
- GET /api/hotspot/clients: Get connected clients
- POST /api/hotspot/apply: Apply new configuration
- POST /api/hotspot/restart: Restart hotspot services

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Request

from models import HotspotConfig
from services.hotspot_service import HotspotService
from services.interface_service import InterfaceService
from exceptions import HotspotConfigurationError, ValidationError
from api.dependencies import require_auth
from api.routes.auth import get_limiter

logger = logging.getLogger("rose-link.api.hotspot")

router = APIRouter()
limiter = get_limiter()


@router.get("/status")
async def get_status() -> dict[str, Any]:
    """
    Get current hotspot status.

    Returns:
        Hotspot status including SSID, channel, frequency, and connected clients
    """
    status = HotspotService.get_status()
    return status.to_dict()


@router.get("/clients")
async def get_clients(
    authenticated: bool = Depends(require_auth),
) -> dict[str, Any]:
    """
    Get list of connected clients to the hotspot.

    Requires authentication.

    Returns:
        List of connected clients with MAC address, signal strength,
        IP address, hostname, and traffic statistics
    """
    logger.info("Getting connected clients list")

    clients = HotspotService.get_clients()

    return {
        "clients": [c.to_dict() for c in clients],
        "count": len(clients),
    }


@router.post("/apply")
@limiter.limit("5/minute")
async def apply_config(
    request: Request,
    config: HotspotConfig = Body(...),
    authenticated: bool = Depends(require_auth),
) -> dict[str, Any]:
    """
    Apply new hotspot configuration.

    Requires authentication.
    Supports both 2.4GHz and 5GHz bands with automatic channel validation.

    Args:
        config: New hotspot configuration

    Returns:
        Applied configuration status

    Raises:
        HTTPException 400: If configuration is invalid
        HTTPException 500: If configuration fails
    """
    try:
        HotspotService.apply_config(config)

        # Get the interface name for response
        interfaces = InterfaceService.get_interfaces()

        logger.info(f"Hotspot configuration applied: SSID={config.ssid}")
        return {
            "status": "applied",
            "config": config.model_dump(),
            "interface": interfaces.wifi_ap,
        }

    except (ValidationError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    except HotspotConfigurationError as e:
        logger.error(f"Hotspot configuration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        logger.error(f"Hotspot configuration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Apply failed: {str(e)}")


@router.post("/restart")
@limiter.limit("5/minute")
async def restart_hotspot(
    request: Request,
    authenticated: bool = Depends(require_auth),
) -> dict[str, str]:
    """
    Restart the hotspot services (hostapd and dnsmasq).

    Requires authentication.

    Returns:
        Restart status

    Raises:
        HTTPException 500: If restart fails
    """
    logger.info("Hotspot restart requested")

    try:
        HotspotService.restart()
        return {"status": "restarted"}

    except HotspotConfigurationError as e:
        logger.error(f"Hotspot restart failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
