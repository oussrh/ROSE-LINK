"""
WiFi WAN API Routes
===================

Endpoints for WiFi WAN connection management.

Endpoints:
- POST /api/wifi/scan: Scan for available networks
- POST /api/wifi/connect: Connect to a WiFi network
- POST /api/wifi/disconnect: Disconnect from WiFi

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from models import WifiConnectRequest
from services.wan_service import WANService
from exceptions import WifiScanError, WifiConnectionError
from api.dependencies import require_auth
from api.routes.auth import get_limiter

logger = logging.getLogger("rose-link.api.wifi")

router = APIRouter()
limiter = get_limiter()


@router.post("/scan")
@limiter.limit("10/minute")
async def scan_networks(
    request: Request,
    authenticated: bool = Depends(require_auth),
) -> dict[str, list]:
    """
    Scan for available WiFi networks.

    Requires authentication.
    Uses NetworkManager to scan for nearby networks.

    Returns:
        List of networks with SSID, signal strength, and security type

    Raises:
        HTTPException 500: If scan fails
    """
    try:
        networks = WANService.scan_networks()
        return {"networks": [n.model_dump() for n in networks]}

    except WifiScanError as e:
        logger.error(f"WiFi scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connect")
@limiter.limit("5/minute")
async def connect_wifi(
    request: Request,
    wifi_request: WifiConnectRequest,
    authenticated: bool = Depends(require_auth),
) -> dict[str, str]:
    """
    Connect to a WiFi network as WAN.

    Requires authentication.

    Args:
        request: WiFi connection credentials (SSID and password)

    Returns:
        Connection status with SSID

    Raises:
        HTTPException 500: If connection fails
    """
    logger.info(f"WiFi connection requested: SSID={wifi_request.ssid}")

    try:
        WANService.connect_wifi(wifi_request.ssid, wifi_request.password)
        return {"status": "connected", "ssid": wifi_request.ssid}

    except WifiConnectionError as e:
        logger.error(f"WiFi connection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/disconnect")
@limiter.limit("10/minute")
async def disconnect_wifi(
    request: Request,
    authenticated: bool = Depends(require_auth),
) -> dict[str, str]:
    """
    Disconnect from WiFi WAN.

    Requires authentication.
    Uses the configured WiFi WAN interface.

    Returns:
        Disconnection status

    Raises:
        HTTPException 500: If disconnection fails
    """
    logger.info("WiFi disconnect requested")

    try:
        WANService.disconnect_wifi()
        return {"status": "disconnected"}

    except WifiConnectionError as e:
        logger.error(f"WiFi disconnect failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
