"""
System API Routes
=================

Endpoints for system information, monitoring, and settings.

Endpoints:
- GET /api/system/info: Get system information
- GET /api/system/interfaces: Get network interface details
- GET /api/system/logs: Get service logs
- POST /api/system/reboot: Reboot the system
- GET /api/system/version: Check for updates
- POST /api/system/update: Trigger system update
- GET /api/settings/vpn: Get VPN watchdog settings
- POST /api/settings/vpn: Update VPN watchdog settings

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
from typing import Any

import aiohttp
from fastapi import APIRouter, Body, Depends, HTTPException, Request, BackgroundTasks

from config import Services, APP_VERSION
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
# Version & Updates
# =============================================================================

GITHUB_VERSION_URL = "https://raw.githubusercontent.com/oussrh/ROSE-LINK/main/VERSION"
UPDATE_SCRIPT_URL = "https://raw.githubusercontent.com/oussrh/ROSE-LINK/main/update.sh"

# Track update status
_update_status = {"status": "idle", "message": "", "progress": 0}


async def fetch_latest_version() -> str | None:
    """Fetch the latest version from GitHub."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(GITHUB_VERSION_URL, timeout=10) as response:
                if response.status == 200:
                    version = await response.text()
                    return version.strip()
    except Exception as e:
        logger.error(f"Failed to fetch latest version: {e}")
    return None


def compare_versions(current: str, latest: str) -> bool:
    """Compare version strings. Returns True if latest > current."""
    try:
        current_parts = [int(x) for x in current.split(".")]
        latest_parts = [int(x) for x in latest.split(".")]
        return latest_parts > current_parts
    except (ValueError, AttributeError):
        return False


@router.get("/version")
async def check_version() -> dict[str, Any]:
    """
    Check current version and if updates are available.

    Returns:
        Current version, latest version, and update availability
    """
    current_version = APP_VERSION
    latest_version = await fetch_latest_version()

    if latest_version is None:
        return {
            "current_version": current_version,
            "latest_version": None,
            "update_available": False,
            "error": "Could not fetch latest version"
        }

    update_available = compare_versions(current_version, latest_version)

    return {
        "current_version": current_version,
        "latest_version": latest_version,
        "update_available": update_available,
    }


def run_update_script():
    """Run the update script in background."""
    import tempfile
    import os

    global _update_status
    temp_script = None
    try:
        _update_status = {"status": "downloading", "message": "Downloading update...", "progress": 10}

        # Create secure temporary file (not in /tmp with predictable name)
        fd, temp_script = tempfile.mkstemp(suffix=".sh", prefix="rose-update-")
        os.close(fd)

        # Download the update script to secure temp file
        result = subprocess.run(
            ["curl", "-fsSL", UPDATE_SCRIPT_URL, "-o", temp_script],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            _update_status = {"status": "error", "message": "Failed to download update script", "progress": 0}
            return

        _update_status = {"status": "updating", "message": "Installing update...", "progress": 30}

        # Make executable (file already has restrictive permissions from mkstemp)
        os.chmod(temp_script, 0o700)

        # Run update script with -y flag (non-interactive)
        result = subprocess.run(
            [temp_script, "-y"],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode == 0:
            _update_status = {"status": "complete", "message": "Update complete! Restarting services...", "progress": 100}
            # Services will be restarted by the update script
        else:
            _update_status = {"status": "error", "message": f"Update failed: {result.stderr[:200]}", "progress": 0}
            logger.error(f"Update script failed: {result.stderr}")

    except subprocess.TimeoutExpired:
        _update_status = {"status": "error", "message": "Update timed out", "progress": 0}
    except Exception as e:
        _update_status = {"status": "error", "message": str(e), "progress": 0}
        logger.error(f"Update error: {e}")
    finally:
        # Clean up temporary file
        if temp_script and os.path.exists(temp_script):
            try:
                os.unlink(temp_script)
            except OSError:
                pass


@router.post("/update")
@limiter.limit("1/minute")
async def trigger_update(
    request: Request,
    background_tasks: BackgroundTasks,
    authenticated: bool = Depends(require_auth),
) -> dict[str, str]:
    """
    Trigger a system update.

    Requires authentication. The update runs in the background.

    Returns:
        Update initiation status
    """
    global _update_status

    # Check if update is already running
    if _update_status["status"] in ["downloading", "updating"]:
        return {"status": "already_running", "message": "Update already in progress"}

    # Reset status and start update
    _update_status = {"status": "starting", "message": "Starting update...", "progress": 0}

    # Run update in background
    background_tasks.add_task(run_update_script)

    logger.info("System update triggered")
    return {"status": "started", "message": "Update started"}


@router.get("/update/status")
async def get_update_status() -> dict[str, Any]:
    """
    Get the current update status.

    Returns:
        Current update status, message, and progress percentage
    """
    return _update_status


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
    settings: VPNSettings = Body(...),
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
