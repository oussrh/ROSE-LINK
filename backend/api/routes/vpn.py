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

import logging
from typing import Any, Optional, Union

from fastapi import APIRouter, Body, Depends, File, HTTPException, Request, UploadFile

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
from api.routes.auth import get_limiter

logger = logging.getLogger("rose-link.api.vpn")

router = APIRouter()
limiter = get_limiter()


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
async def list_profiles(
    authenticated: bool = Depends(require_auth),
) -> dict[str, list]:
    """
    List all available VPN profiles.

    Requires authentication.

    Returns:
        List of VPN profiles with their activation status
    """
    profiles = VPNService.list_profiles()
    return {"profiles": [{"name": p.name, "active": p.active} for p in profiles]}


def _is_valid_vpn_filename(filename: Optional[str]) -> bool:
    """
    Check if filename could be a VPN config file (WireGuard or OpenVPN).

    Accepts:
    - .conf files (e.g., vpn.conf)
    - .txt files (e.g., vpn.txt)
    - .conf.txt files (e.g., vpn.conf.txt)
    - .ovpn files (e.g., vpn.ovpn) - OpenVPN
    - .wg files (e.g., vpn.wg) - WireGuard
    - .ini files (e.g., vpn.ini)
    - Files without extension (e.g., vpn-config)

    Args:
        filename: The filename to check

    Returns:
        True if the file could be a VPN config
    """
    if not filename:
        return False

    # Accept common extensions for VPN configs
    lower_name = filename.lower()
    if lower_name.endswith(('.conf', '.txt', '.conf.txt', '.ovpn', '.wg', '.ini')):
        return True

    # Accept files without extension (no dot in the base name after last /)
    base_name = filename.rsplit('/', 1)[-1].rsplit('\\', 1)[-1]
    if '.' not in base_name:
        return True

    return False


def _normalize_profile_name(filename: str) -> str:
    """
    Normalize filename to a clean profile name.

    Removes extensions like .conf, .txt, .conf.txt, .ovpn, .wg, .ini

    Args:
        filename: Original filename

    Returns:
        Clean profile name
    """
    name = filename.rsplit('/', 1)[-1].rsplit('\\', 1)[-1]

    # Remove known extensions in order (longest first)
    for ext in ['.conf.txt', '.conf', '.txt', '.ovpn', '.wg', '.ini']:
        if name.lower().endswith(ext):
            name = name[:-len(ext)]
            break

    return name


@router.post("/upload")
@limiter.limit("10/minute")
async def upload_profile(
    request: Request,
    file: UploadFile = File(...),
    authenticated: bool = Depends(require_auth),
) -> dict[str, str]:
    """
    Upload a new VPN profile without activating it.

    Requires authentication.

    Args:
        file: WireGuard config file (.conf, .txt, .conf.txt, or no extension)

    Returns:
        Upload status with saved filename

    Raises:
        HTTPException 400: If file is invalid
        HTTPException 500: If upload fails
    """
    if not _is_valid_vpn_filename(file.filename):
        raise HTTPException(
            status_code=400,
            detail="Please upload a VPN configuration file"
        )

    try:
        content = await file.read()
        # Normalize the filename before passing to service
        normalized_name = _normalize_profile_name(file.filename or "vpn") + ".conf"
        safe_name = VPNService.upload_profile(normalized_name, content)
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
@limiter.limit("10/minute")
async def import_profile(
    request: Request,
    file: UploadFile = File(...),
    authenticated: bool = Depends(require_auth),
) -> dict[str, str]:
    """
    Import and immediately activate a VPN profile.

    Requires authentication.

    Args:
        file: WireGuard config file (.conf, .txt, .conf.txt, or no extension)

    Returns:
        Import and activation status

    Raises:
        HTTPException 400: If file is invalid
        HTTPException 500: If import fails
    """
    if not _is_valid_vpn_filename(file.filename):
        raise HTTPException(
            status_code=400,
            detail="Please upload a VPN configuration file"
        )

    try:
        content = await file.read()
        # Normalize the filename before passing to service
        normalized_name = _normalize_profile_name(file.filename or "vpn") + ".conf"
        profile_name = VPNService.import_profile(normalized_name, content)
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
@limiter.limit("10/minute")
async def activate_profile(
    request: Request,
    profile: VPNProfile = Body(...),
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
@limiter.limit("10/minute")
async def start_vpn(
    request: Request,
    authenticated: bool = Depends(require_auth),
) -> dict[str, str]:
    """
    Start the VPN connection.

    Requires authentication.

    Returns:
        Start status

    Raises:
        HTTPException 400: If no profile is configured
        HTTPException 500: If start fails
    """
    logger.info("VPN start requested")

    try:
        VPNService.start()
        return {"status": "started"}

    except VPNConnectionError as e:
        logger.error(f"VPN start failed: {e}")
        # Return 400 if no profile configured, 500 for other errors
        status_code = 400 if "No VPN profile" in str(e) else 500
        raise HTTPException(status_code=status_code, detail=str(e))


@router.post("/stop")
@limiter.limit("10/minute")
async def stop_vpn(
    request: Request,
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
@limiter.limit("10/minute")
async def restart_vpn(
    request: Request,
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
