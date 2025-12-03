"""
Health & Status Endpoints
=========================

Provides health check and system status endpoints for monitoring.

Endpoints:
- GET /health - Basic health check for load balancers/monitoring
- GET /status - Combined status of all major components

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

from fastapi import APIRouter

from config import APP_NAME, APP_VERSION

health_router = APIRouter()


@health_router.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """
    Health check endpoint for monitoring.

    This endpoint is designed for:
    - Load balancer health checks
    - Kubernetes liveness probes
    - Monitoring systems (Prometheus, etc.)

    Returns:
        Status information including:
        - status: "ok" if the service is running
        - service: The service name
        - version: The current version
    """
    return {
        "status": "ok",
        "service": APP_NAME,
        "version": APP_VERSION,
    }


@health_router.get("/status", tags=["Status"])
async def get_status() -> dict:
    """
    Get overall system status including WAN, VPN, and hotspot.

    This endpoint aggregates status from all major components
    for dashboard display and monitoring.

    Returns:
        Combined status of all major components:
        - wan: WiFi WAN connection status
        - vpn: VPN connection status
        - ap: WiFi hotspot status
    """
    # Import here to avoid circular imports and for lazy loading
    from services.wan_service import WANService
    from services.vpn_service import VPNService
    from services.hotspot_service import HotspotService

    return {
        "wan": WANService.get_status().to_dict(),
        "vpn": VPNService.get_status().to_dict(),
        "ap": HotspotService.get_status().to_dict(),
    }
