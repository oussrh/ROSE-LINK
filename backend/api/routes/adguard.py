"""
AdGuard Home API Routes
=======================

Endpoints for AdGuard Home DNS ad-blocking management.

Endpoints:
- GET /api/adguard/status: Get AdGuard Home status and stats
- POST /api/adguard/enable: Enable DNS protection
- POST /api/adguard/disable: Disable DNS protection
- POST /api/adguard/filtering/enable: Enable DNS filtering
- POST /api/adguard/filtering/disable: Disable DNS filtering
- GET /api/adguard/stats: Get blocking statistics
- POST /api/adguard/stats/reset: Reset statistics
- GET /api/adguard/querylog: Get DNS query log
- POST /api/adguard/start: Start AdGuard service
- POST /api/adguard/stop: Stop AdGuard service
- POST /api/adguard/restart: Restart AdGuard service

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from services.adguard_service import AdGuardService
from api.dependencies import require_auth

logger = logging.getLogger("rose-link.api.adguard")

router = APIRouter(prefix="/adguard")


@router.get("/status")
async def get_status() -> dict[str, Any]:
    """
    Get AdGuard Home status and statistics.

    Returns:
        Status including installation state, protection status, and stats
    """
    status = await AdGuardService.get_status()
    return status.to_dict()


@router.post("/enable")
async def enable_protection(
    authenticated: bool = Depends(require_auth),
) -> dict[str, str]:
    """
    Enable AdGuard Home DNS protection.

    Requires authentication.

    Returns:
        Operation status

    Raises:
        HTTPException 500: If operation fails
    """
    logger.info("Enable AdGuard protection requested")

    if not AdGuardService.is_installed():
        raise HTTPException(
            status_code=503,
            detail="AdGuard Home is not installed"
        )

    success = await AdGuardService.enable_protection()
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to enable AdGuard protection"
        )

    return {"status": "enabled"}


@router.post("/disable")
async def disable_protection(
    authenticated: bool = Depends(require_auth),
) -> dict[str, str]:
    """
    Disable AdGuard Home DNS protection.

    Requires authentication.

    Returns:
        Operation status

    Raises:
        HTTPException 500: If operation fails
    """
    logger.info("Disable AdGuard protection requested")

    if not AdGuardService.is_installed():
        raise HTTPException(
            status_code=503,
            detail="AdGuard Home is not installed"
        )

    success = await AdGuardService.disable_protection()
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to disable AdGuard protection"
        )

    return {"status": "disabled"}


@router.post("/filtering/enable")
async def enable_filtering(
    authenticated: bool = Depends(require_auth),
) -> dict[str, str]:
    """
    Enable AdGuard Home DNS filtering.

    Requires authentication.

    Returns:
        Operation status

    Raises:
        HTTPException 500: If operation fails
    """
    logger.info("Enable AdGuard filtering requested")

    if not AdGuardService.is_installed():
        raise HTTPException(
            status_code=503,
            detail="AdGuard Home is not installed"
        )

    success = await AdGuardService.enable_filtering()
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to enable AdGuard filtering"
        )

    return {"status": "enabled"}


@router.post("/filtering/disable")
async def disable_filtering(
    authenticated: bool = Depends(require_auth),
) -> dict[str, str]:
    """
    Disable AdGuard Home DNS filtering.

    Requires authentication.

    Returns:
        Operation status

    Raises:
        HTTPException 500: If operation fails
    """
    logger.info("Disable AdGuard filtering requested")

    if not AdGuardService.is_installed():
        raise HTTPException(
            status_code=503,
            detail="AdGuard Home is not installed"
        )

    success = await AdGuardService.disable_filtering()
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to disable AdGuard filtering"
        )

    return {"status": "disabled"}


@router.get("/stats")
async def get_stats() -> dict[str, Any]:
    """
    Get AdGuard Home blocking statistics.

    Returns:
        Blocking statistics including queries, blocked count, etc.
    """
    if not AdGuardService.is_installed():
        raise HTTPException(
            status_code=503,
            detail="AdGuard Home is not installed"
        )

    stats = await AdGuardService.get_stats()
    if stats is None:
        raise HTTPException(
            status_code=503,
            detail="AdGuard Home is not running or stats unavailable"
        )

    return stats.to_dict()


@router.post("/stats/reset")
async def reset_stats(
    authenticated: bool = Depends(require_auth),
) -> dict[str, str]:
    """
    Reset AdGuard Home statistics.

    Requires authentication.

    Returns:
        Operation status

    Raises:
        HTTPException 500: If operation fails
    """
    logger.info("Reset AdGuard stats requested")

    if not AdGuardService.is_installed():
        raise HTTPException(
            status_code=503,
            detail="AdGuard Home is not installed"
        )

    success = await AdGuardService.reset_stats()
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to reset AdGuard statistics"
        )

    return {"status": "reset"}


@router.get("/querylog")
async def get_query_log(
    limit: int = Query(default=100, ge=1, le=1000),
) -> dict[str, Any]:
    """
    Get recent DNS query log entries.

    Args:
        limit: Maximum number of entries to return (1-1000)

    Returns:
        List of query log entries
    """
    if not AdGuardService.is_installed():
        raise HTTPException(
            status_code=503,
            detail="AdGuard Home is not installed"
        )

    queries = await AdGuardService.get_query_log(limit=limit)
    return {"queries": queries, "count": len(queries)}


@router.post("/start")
async def start_service(
    authenticated: bool = Depends(require_auth),
) -> dict[str, str]:
    """
    Start AdGuard Home service.

    Requires authentication.

    Returns:
        Operation status

    Raises:
        HTTPException 500: If operation fails
    """
    logger.info("Start AdGuard service requested")

    if not AdGuardService.is_installed():
        raise HTTPException(
            status_code=503,
            detail="AdGuard Home is not installed"
        )

    success = AdGuardService.start()
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to start AdGuard Home service"
        )

    return {"status": "started"}


@router.post("/stop")
async def stop_service(
    authenticated: bool = Depends(require_auth),
) -> dict[str, str]:
    """
    Stop AdGuard Home service.

    Requires authentication.

    Returns:
        Operation status

    Raises:
        HTTPException 500: If operation fails
    """
    logger.info("Stop AdGuard service requested")

    success = AdGuardService.stop()
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to stop AdGuard Home service"
        )

    return {"status": "stopped"}


@router.post("/restart")
async def restart_service(
    authenticated: bool = Depends(require_auth),
) -> dict[str, str]:
    """
    Restart AdGuard Home service.

    Requires authentication.

    Returns:
        Operation status

    Raises:
        HTTPException 500: If operation fails
    """
    logger.info("Restart AdGuard service requested")

    if not AdGuardService.is_installed():
        raise HTTPException(
            status_code=503,
            detail="AdGuard Home is not installed"
        )

    success = AdGuardService.restart()
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to restart AdGuard Home service"
        )

    return {"status": "restarted"}
