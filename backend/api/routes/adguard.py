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
from typing import Any, Union

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, Response

from services.adguard_service import AdGuardService
from api.dependencies import require_auth

logger = logging.getLogger("rose-link.api.adguard")

router = APIRouter(prefix="/adguard")


def _render_not_installed_html() -> str:
    """Render HTML for AdGuard not installed status."""
    return '''
    <div class="bg-gray-700/50 rounded-lg p-4 text-center">
        <div class="text-yellow-400 mb-2">
            <i data-lucide="alert-triangle" class="w-8 h-8 mx-auto"></i>
        </div>
        <p class="text-gray-300 font-medium">AdGuard Home not installed</p>
        <p class="text-gray-500 text-sm mt-1">Run: sudo rose-adguard install</p>
    </div>
    '''


def _render_unavailable_html(message: str) -> str:
    """Render HTML for unavailable AdGuard stats."""
    return f'''
    <div class="grid grid-cols-3 gap-2 sm:gap-4">
        <div class="bg-gray-700 rounded-lg p-3 text-center col-span-3">
            <p class="text-gray-400 text-sm">{message}</p>
        </div>
    </div>
    '''


@router.get("/status", response_model=None)
async def get_status(request: Request) -> Union[dict[str, Any], Response]:
    """
    Get AdGuard Home status and statistics.

    Returns:
        Status including installation state, protection status, and stats
    """
    is_htmx = request.headers.get("HX-Request") == "true"

    try:
        status = await AdGuardService.get_status()
        return status.to_dict()
    except Exception as e:
        logger.error(f"Error getting AdGuard status: {e}")
        if is_htmx:
            return HTMLResponse(
                content=_render_not_installed_html(),
                status_code=200,
            )
        # Return a graceful response instead of 500
        return {
            "installed": False,
            "running": False,
            "protection_enabled": False,
            "filtering_enabled": False,
            "version": "",
            "dns_addresses": [],
            "stats": None
        }


@router.post("/enable", response_model=None)
async def enable_protection(
    request: Request,
    authenticated: bool = Depends(require_auth),
) -> Union[dict[str, Any], Response]:
    """
    Enable AdGuard Home DNS protection.

    Requires authentication.

    Returns:
        Operation status or error message
    """
    logger.info("Enable AdGuard protection requested")
    is_htmx = request.headers.get("HX-Request") == "true"

    if not AdGuardService.is_installed():
        if is_htmx:
            return HTMLResponse(
                content='<div class="text-yellow-500 text-sm p-2">AdGuard Home is not installed</div>',
                status_code=200,
            )
        return {"status": "error", "detail": "AdGuard Home is not installed"}

    try:
        success = await AdGuardService.enable_protection()
        if not success:
            if is_htmx:
                return HTMLResponse(
                    content='<div class="text-red-500 text-sm p-2">Failed to enable protection</div>',
                    status_code=200,
                )
            return {"status": "error", "detail": "Failed to enable AdGuard protection"}

        return {"status": "enabled"}
    except Exception as e:
        logger.error(f"Error enabling AdGuard protection: {e}")
        if is_htmx:
            return HTMLResponse(
                content='<div class="text-red-500 text-sm p-2">Error enabling protection</div>',
                status_code=200,
            )
        return {"status": "error", "detail": str(e)}


@router.post("/disable", response_model=None)
async def disable_protection(
    request: Request,
    authenticated: bool = Depends(require_auth),
) -> Union[dict[str, Any], Response]:
    """
    Disable AdGuard Home DNS protection.

    Requires authentication.

    Returns:
        Operation status or error message
    """
    logger.info("Disable AdGuard protection requested")
    is_htmx = request.headers.get("HX-Request") == "true"

    if not AdGuardService.is_installed():
        if is_htmx:
            return HTMLResponse(
                content='<div class="text-yellow-500 text-sm p-2">AdGuard Home is not installed</div>',
                status_code=200,
            )
        return {"status": "error", "detail": "AdGuard Home is not installed"}

    try:
        success = await AdGuardService.disable_protection()
        if not success:
            if is_htmx:
                return HTMLResponse(
                    content='<div class="text-red-500 text-sm p-2">Failed to disable protection</div>',
                    status_code=200,
                )
            return {"status": "error", "detail": "Failed to disable AdGuard protection"}

        return {"status": "disabled"}
    except Exception as e:
        logger.error(f"Error disabling AdGuard protection: {e}")
        if is_htmx:
            return HTMLResponse(
                content='<div class="text-red-500 text-sm p-2">Error disabling protection</div>',
                status_code=200,
            )
        return {"status": "error", "detail": str(e)}


@router.post("/filtering/enable", response_model=None)
async def enable_filtering(
    request: Request,
    authenticated: bool = Depends(require_auth),
) -> Union[dict[str, Any], Response]:
    """
    Enable AdGuard Home DNS filtering.

    Requires authentication.

    Returns:
        Operation status or error message
    """
    logger.info("Enable AdGuard filtering requested")
    is_htmx = request.headers.get("HX-Request") == "true"

    if not AdGuardService.is_installed():
        if is_htmx:
            return HTMLResponse(
                content='<div class="text-yellow-500 text-sm p-2">AdGuard Home is not installed</div>',
                status_code=200,
            )
        return {"status": "error", "detail": "AdGuard Home is not installed"}

    try:
        success = await AdGuardService.enable_filtering()
        if not success:
            if is_htmx:
                return HTMLResponse(
                    content='<div class="text-red-500 text-sm p-2">Failed to enable filtering</div>',
                    status_code=200,
                )
            return {"status": "error", "detail": "Failed to enable AdGuard filtering"}

        return {"status": "enabled"}
    except Exception as e:
        logger.error(f"Error enabling AdGuard filtering: {e}")
        if is_htmx:
            return HTMLResponse(
                content='<div class="text-red-500 text-sm p-2">Error enabling filtering</div>',
                status_code=200,
            )
        return {"status": "error", "detail": str(e)}


@router.post("/filtering/disable", response_model=None)
async def disable_filtering(
    request: Request,
    authenticated: bool = Depends(require_auth),
) -> Union[dict[str, Any], Response]:
    """
    Disable AdGuard Home DNS filtering.

    Requires authentication.

    Returns:
        Operation status or error message
    """
    logger.info("Disable AdGuard filtering requested")
    is_htmx = request.headers.get("HX-Request") == "true"

    if not AdGuardService.is_installed():
        if is_htmx:
            return HTMLResponse(
                content='<div class="text-yellow-500 text-sm p-2">AdGuard Home is not installed</div>',
                status_code=200,
            )
        return {"status": "error", "detail": "AdGuard Home is not installed"}

    try:
        success = await AdGuardService.disable_filtering()
        if not success:
            if is_htmx:
                return HTMLResponse(
                    content='<div class="text-red-500 text-sm p-2">Failed to disable filtering</div>',
                    status_code=200,
                )
            return {"status": "error", "detail": "Failed to disable AdGuard filtering"}

        return {"status": "disabled"}
    except Exception as e:
        logger.error(f"Error disabling AdGuard filtering: {e}")
        if is_htmx:
            return HTMLResponse(
                content='<div class="text-red-500 text-sm p-2">Error disabling filtering</div>',
                status_code=200,
            )
        return {"status": "error", "detail": str(e)}


@router.get("/stats", response_model=None)
async def get_stats(request: Request) -> Union[dict[str, Any], Response]:
    """
    Get AdGuard Home blocking statistics.

    Returns:
        Blocking statistics including queries, blocked count, etc.
        For HTMX requests, returns HTML content when unavailable.
    """
    is_htmx = request.headers.get("HX-Request") == "true"

    if not AdGuardService.is_installed():
        if is_htmx:
            return HTMLResponse(
                content=_render_unavailable_html("AdGuard Home is not installed"),
                status_code=200,
            )
        return {"status": "error", "detail": "AdGuard Home is not installed"}

    try:
        stats = await AdGuardService.get_stats()
        if stats is None:
            if is_htmx:
                return HTMLResponse(
                    content=_render_unavailable_html("AdGuard Home is not running"),
                    status_code=200,
                )
            return {"status": "error", "detail": "AdGuard Home is not running or stats unavailable"}

        return stats.to_dict()
    except Exception as e:
        logger.error(f"Error getting AdGuard stats: {e}")
        if is_htmx:
            return HTMLResponse(
                content=_render_unavailable_html("Error getting statistics"),
                status_code=200,
            )
        return {"status": "error", "detail": str(e)}


@router.post("/stats/reset", response_model=None)
async def reset_stats(
    request: Request,
    authenticated: bool = Depends(require_auth),
) -> Union[dict[str, Any], Response]:
    """
    Reset AdGuard Home statistics.

    Requires authentication.

    Returns:
        Operation status or error message
    """
    logger.info("Reset AdGuard stats requested")
    is_htmx = request.headers.get("HX-Request") == "true"

    if not AdGuardService.is_installed():
        if is_htmx:
            return HTMLResponse(
                content='<div class="text-yellow-400 text-sm">AdGuard Home is not installed</div>',
                status_code=200,
            )
        return {"status": "error", "detail": "AdGuard Home is not installed"}

    try:
        success = await AdGuardService.reset_stats()
        if not success:
            if is_htmx:
                return HTMLResponse(
                    content='<div class="text-red-500 text-sm">Failed to reset statistics</div>',
                    status_code=200,
                )
            return {"status": "error", "detail": "Failed to reset AdGuard statistics"}

        return {"status": "reset"}
    except Exception as e:
        logger.error(f"Error resetting AdGuard stats: {e}")
        if is_htmx:
            return HTMLResponse(
                content='<div class="text-red-500 text-sm">Error resetting statistics</div>',
                status_code=200,
            )
        return {"status": "error", "detail": str(e)}


@router.get("/querylog", response_model=None)
async def get_query_log(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000),
) -> Union[dict[str, Any], Response]:
    """
    Get recent DNS query log entries.

    Args:
        limit: Maximum number of entries to return (1-1000)

    Returns:
        List of query log entries
    """
    is_htmx = request.headers.get("HX-Request") == "true"

    if not AdGuardService.is_installed():
        if is_htmx:
            return HTMLResponse(
                content='<div class="text-gray-400 text-sm p-4 text-center">AdGuard Home is not installed</div>',
                status_code=200,
            )
        return {"status": "error", "detail": "AdGuard Home is not installed"}

    try:
        queries = await AdGuardService.get_query_log(limit=limit)
        return {"queries": queries, "count": len(queries)}
    except Exception as e:
        logger.error(f"Error getting AdGuard query log: {e}")
        if is_htmx:
            return HTMLResponse(
                content='<div class="text-gray-400 text-sm p-4 text-center">Error getting query log</div>',
                status_code=200,
            )
        return {"status": "error", "detail": str(e)}


@router.post("/start", response_model=None)
async def start_service(
    request: Request,
    authenticated: bool = Depends(require_auth),
) -> Union[dict[str, Any], Response]:
    """
    Start AdGuard Home service.

    Requires authentication.

    Returns:
        Operation status or error message
    """
    logger.info("Start AdGuard service requested")
    is_htmx = request.headers.get("HX-Request") == "true"

    if not AdGuardService.is_installed():
        if is_htmx:
            return HTMLResponse(
                content='<div class="text-yellow-500 text-sm p-2">AdGuard Home is not installed</div>',
                status_code=200,
            )
        return {"status": "error", "detail": "AdGuard Home is not installed"}

    try:
        success = AdGuardService.start()
        if not success:
            if is_htmx:
                return HTMLResponse(
                    content='<div class="text-red-500 text-sm p-2">Failed to start service</div>',
                    status_code=200,
                )
            return {"status": "error", "detail": "Failed to start AdGuard Home service"}

        return {"status": "started"}
    except Exception as e:
        logger.error(f"Error starting AdGuard service: {e}")
        if is_htmx:
            return HTMLResponse(
                content='<div class="text-red-500 text-sm p-2">Error starting service</div>',
                status_code=200,
            )
        return {"status": "error", "detail": str(e)}


@router.post("/stop", response_model=None)
async def stop_service(
    request: Request,
    authenticated: bool = Depends(require_auth),
) -> Union[dict[str, Any], Response]:
    """
    Stop AdGuard Home service.

    Requires authentication.

    Returns:
        Operation status or error message
    """
    logger.info("Stop AdGuard service requested")
    is_htmx = request.headers.get("HX-Request") == "true"

    try:
        success = AdGuardService.stop()
        if not success:
            if is_htmx:
                return HTMLResponse(
                    content='<div class="text-red-500 text-sm p-2">Failed to stop service</div>',
                    status_code=200,
                )
            return {"status": "error", "detail": "Failed to stop AdGuard Home service"}

        return {"status": "stopped"}
    except Exception as e:
        logger.error(f"Error stopping AdGuard service: {e}")
        if is_htmx:
            return HTMLResponse(
                content='<div class="text-red-500 text-sm p-2">Error stopping service</div>',
                status_code=200,
            )
        return {"status": "error", "detail": str(e)}


@router.post("/restart", response_model=None)
async def restart_service(
    request: Request,
    authenticated: bool = Depends(require_auth),
) -> Union[dict[str, Any], Response]:
    """
    Restart AdGuard Home service.

    Requires authentication.

    Returns:
        Operation status or error message
    """
    logger.info("Restart AdGuard service requested")
    is_htmx = request.headers.get("HX-Request") == "true"

    if not AdGuardService.is_installed():
        if is_htmx:
            return HTMLResponse(
                content='<div class="text-yellow-500 text-sm p-2">AdGuard Home is not installed</div>',
                status_code=200,
            )
        return {"status": "error", "detail": "AdGuard Home is not installed"}

    try:
        success = AdGuardService.restart()
        if not success:
            if is_htmx:
                return HTMLResponse(
                    content='<div class="text-red-500 text-sm p-2">Failed to restart service</div>',
                    status_code=200,
                )
            return {"status": "error", "detail": "Failed to restart AdGuard Home service"}

        return {"status": "restarted"}
    except Exception as e:
        logger.error(f"Error restarting AdGuard service: {e}")
        if is_htmx:
            return HTMLResponse(
                content='<div class="text-red-500 text-sm p-2">Error restarting service</div>',
                status_code=200,
            )
        return {"status": "error", "detail": str(e)}
