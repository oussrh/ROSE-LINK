"""
VPN API Routes
==============

Endpoints for WireGuard VPN management.

Endpoints:
- GET /api/vpn/status: Get VPN connection status
- GET /api/vpn/profiles: List available profiles
- POST /api/vpn/upload: Upload a new profile
- POST /api/vpn/import: Import and activate a profile
- POST /api/vpn/activate: Activate an existing profile
- DELETE /api/vpn/profiles/{name}: Delete a profile
- POST /api/vpn/start: Start VPN
- POST /api/vpn/stop: Stop VPN
- POST /api/vpn/restart: Restart VPN

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from config import Limits
from models import VPNProfile, VPNSettings
from services.vpn_service import VPNService
from exceptions import (
    VPNProfileNotFoundError,
    VPNProfileActiveError,
    VPNConnectionError,
    InvalidWireGuardConfigError,
    FileTooLargeError,
    ValidationError,
)
from utils.validators import validate_ping_host
from api.dependencies import require_auth

logger = logging.getLogger("rose-link.api.vpn")

router = APIRouter()


@router.get("/status")
async def get_status() -> dict[str, Any]:
    """
    Get current VPN connection status.

    Returns:
        VPN status including connection state, endpoint, and transfer stats
    """
    status = VPNService.get_status()
    return status.to_dict()


@router.get("/profiles")
async def list_profiles() -> dict[str, list]:
    """
    List all available VPN profiles.

    Returns:
        List of VPN profiles with their activation status
    """
    profiles = VPNService.list_profiles()
    return {"profiles": [{"name": p.name, "active": p.active} for p in profiles]}


@router.post("/upload")
async def upload_profile(
    file: UploadFile = File(...),
    authenticated: bool = Depends(require_auth),
) -> dict[str, str]:
    """
    Upload a new VPN profile without activating it.

    Requires authentication.

    Args:
        file: WireGuard .conf file

    Returns:
        Upload status with saved filename

    Raises:
        HTTPException 400: If file is invalid
        HTTPException 500: If upload fails
    """
    if not file.filename or not file.filename.endswith(".conf"):
        raise HTTPException(status_code=400, detail="File must be a .conf file")

    try:
        content = await file.read()
        safe_name = VPNService.upload_profile(file.filename, content)
        return {"status": "uploaded", "name": safe_name}

    except FileTooLargeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except InvalidWireGuardConfigError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"VPN profile upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/import")
async def import_profile(
    file: UploadFile = File(...),
    authenticated: bool = Depends(require_auth),
) -> dict[str, str]:
    """
    Import and immediately activate a VPN profile.

    Requires authentication.

    Args:
        file: WireGuard .conf file

    Returns:
        Import and activation status

    Raises:
        HTTPException 400: If file is invalid
        HTTPException 500: If import fails
    """
    if not file.filename or not file.filename.endswith(".conf"):
        raise HTTPException(status_code=400, detail="File must be a .conf file")

    try:
        content = await file.read()
        profile_name = VPNService.import_profile(file.filename, content)
        return {"status": "imported", "name": profile_name}

    except FileTooLargeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except InvalidWireGuardConfigError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"VPN profile import failed: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/activate")
async def activate_profile(
    profile: VPNProfile,
    authenticated: bool = Depends(require_auth),
) -> dict[str, str]:
    """
    Activate an existing VPN profile.

    Requires authentication.

    Args:
        profile: Profile name to activate

    Returns:
        Activation status

    Raises:
        HTTPException 404: If profile not found
        HTTPException 500: If activation fails
    """
    try:
        VPNService.activate_profile(profile.name)
        return {"status": "activated", "name": profile.name}

    except VPNProfileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        logger.error(f"VPN profile activation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Activation failed: {str(e)}")


@router.delete("/profiles/{profile_name}")
async def delete_profile(
    profile_name: str,
    authenticated: bool = Depends(require_auth),
) -> dict[str, str]:
    """
    Delete a VPN profile.

    Requires authentication.
    Cannot delete the currently active profile.

    Args:
        profile_name: Name of the profile to delete (without .conf)

    Returns:
        Deletion status

    Raises:
        HTTPException 400: If trying to delete active profile
        HTTPException 404: If profile not found
        HTTPException 500: If deletion fails
    """
    try:
        VPNService.delete_profile(profile_name)
        return {"status": "deleted", "name": profile_name}

    except VPNProfileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except VPNProfileActiveError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"VPN profile deletion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@router.post("/start")
async def start_vpn(
    authenticated: bool = Depends(require_auth),
) -> dict[str, str]:
    """
    Start the VPN connection.

    Requires authentication.

    Returns:
        Start status

    Raises:
        HTTPException 500: If start fails
    """
    logger.info("VPN start requested")

    try:
        VPNService.start()
        return {"status": "started"}

    except VPNConnectionError as e:
        logger.error(f"VPN start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_vpn(
    authenticated: bool = Depends(require_auth),
) -> dict[str, str]:
    """
    Stop the VPN connection.

    Requires authentication.

    Returns:
        Stop status

    Raises:
        HTTPException 500: If stop fails
    """
    logger.info("VPN stop requested")

    try:
        VPNService.stop()
        return {"status": "stopped"}

    except VPNConnectionError as e:
        logger.error(f"VPN stop failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restart")
async def restart_vpn(
    authenticated: bool = Depends(require_auth),
) -> dict[str, str]:
    """
    Restart the VPN connection.

    Requires authentication.

    Returns:
        Restart status

    Raises:
        HTTPException 500: If restart fails
    """
    logger.info("VPN restart requested")

    try:
        VPNService.restart()
        return {"status": "restarted"}

    except VPNConnectionError as e:
        logger.error(f"VPN restart failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
