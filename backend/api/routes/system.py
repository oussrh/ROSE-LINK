"""
System API Routes
=================

Endpoints for system information, monitoring, and settings.

Endpoints:
- GET /api/system/info: Get system information
- GET /api/system/interfaces: Get network interface details
- GET /api/system/logs: Get service logs
- POST /api/system/reboot: Reboot the system
- GET /api/settings/vpn: Get VPN watchdog settings
- POST /api/settings/vpn: Update VPN watchdog settings

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from config import Services
from models import VPNSettings
from services.system_service import SystemService
from services.vpn_service import VPNService
from services.wan_service import WANService
from exceptions import ValidationError
from utils.validators import validate_ping_host
from api.dependencies import require_auth
from api.routes.auth import get_limiter

logger = logging.getLogger("rose-link.api.system")

router = APIRouter()
limiter = get_limiter()


# =============================================================================
# System Information
# =============================================================================

@router.get("/info")
async def get_system_info() -> dict[str, Any]:
    """
    Get comprehensive Raspberry Pi system information.

    Returns:
        System info including model, RAM, disk, CPU, interfaces, and WiFi capabilities
    """
    info = SystemService.get_info()
    return info.to_dict()


@router.get("/interfaces")
async def get_interfaces() -> dict[str, list]:
    """
    Get detailed network interface information.

    Returns:
        Lists of ethernet, wifi, and vpn interfaces with their status
    """
    interfaces = SystemService.get_interfaces()
    return {
        category: [iface.to_dict() for iface in ifaces]
        for category, ifaces in interfaces.items()
    }


@router.get("/logs")
async def get_logs(
    service: str = "rose-backend",
    authenticated: bool = Depends(require_auth),
) -> dict[str, str]:
    """
    Get system logs for a specific service.

    Requires authentication.

    Args:
        service: Service name (rose-backend, rose-watchdog, hostapd, dnsmasq, wg-quick@wg0)

    Returns:
        Recent log entries for the specified service

    Raises:
        HTTPException 400: If service name is invalid
    """
    try:
        logs = SystemService.get_logs(service)
        return {"service": service, "logs": logs}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reboot")
@limiter.limit("2/minute")
async def reboot_system(
    request: Request,
    authenticated: bool = Depends(require_auth),
) -> dict[str, str]:
    """
    Reboot the Raspberry Pi.

    Requires authentication.

    Returns:
        Reboot confirmation status
    """
    logger.info("System reboot requested")
    SystemService.reboot()
    return {"status": "rebooting"}


# =============================================================================
# Overall Status
# =============================================================================

@router.get("/status")
async def get_overall_status() -> dict[str, Any]:
    """
    Get overall system status including WAN, VPN, and hotspot.

    This is a convenience endpoint that combines status from all
    major components.

    Returns:
        Combined status of all major components
    """
    from ...services.hotspot_service import HotspotService

    return {
        "wan": WANService.get_status().to_dict(),
        "vpn": VPNService.get_status().to_dict(),
        "ap": HotspotService.get_status().to_dict(),
    }


# =============================================================================
# VPN Settings
# =============================================================================

@router.get("/settings/vpn")
async def get_vpn_settings(
    authenticated: bool = Depends(require_auth),
) -> dict[str, Any]:
    """
    Get current VPN watchdog settings.

    Requires authentication.

    Returns:
        Current ping_host and check_interval values
    """
    settings = VPNService.get_settings()
    return settings.model_dump()


@router.post("/settings/vpn")
@limiter.limit("10/minute")
async def update_vpn_settings(
    request: Request,
    settings: VPNSettings,
    authenticated: bool = Depends(require_auth),
) -> dict[str, Any]:
    """
    Update VPN watchdog settings.

    Requires authentication.

    Args:
        settings: New VPN watchdog configuration

    Returns:
        Confirmation with saved settings

    Raises:
        HTTPException 400: If settings are invalid
        HTTPException 500: If save fails
    """
    # Validate ping host
    try:
        safe_ping_host = validate_ping_host(settings.ping_host)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Create validated settings
    validated_settings = VPNSettings(
        ping_host=safe_ping_host,
        check_interval=settings.check_interval,
    )

    if VPNService.save_settings(validated_settings):
        logger.info(
            f"VPN settings updated: ping_host={safe_ping_host}, "
            f"interval={settings.check_interval}"
        )
        return {"status": "saved", "settings": validated_settings.model_dump()}
    else:
        logger.error("Failed to save VPN settings")
        raise HTTPException(status_code=500, detail="Failed to save settings")
