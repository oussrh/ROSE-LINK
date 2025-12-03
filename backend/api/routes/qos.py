"""
QoS API Routes
==============

Endpoints for Quality of Service traffic prioritization.

Endpoints:
- GET /api/qos/status: Get QoS status and configuration
- POST /api/qos/enable: Enable QoS traffic prioritization
- POST /api/qos/disable: Disable QoS
- PUT /api/qos/config: Update QoS configuration

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, Field

from services.qos_service import QoSService
from api.dependencies import require_auth

logger = logging.getLogger("rose-link.api.qos")

router = APIRouter(prefix="/qos")


class QoSConfigUpdate(BaseModel):
    """Request model for QoS configuration update."""
    total_bandwidth_mbps: Optional[int] = Field(
        None,
        ge=1,
        le=1000,
        description="Total bandwidth in Mbps"
    )
    vpn_bandwidth_percent: Optional[int] = Field(
        None,
        ge=10,
        le=90,
        description="Percentage of bandwidth allocated to VPN traffic"
    )


@router.get("/status")
async def get_status() -> dict[str, Any]:
    """
    Get QoS status and configuration.

    Returns:
        QoS status including enabled state and configuration
    """
    status = QoSService.get_status()
    return status.to_dict()


@router.post("/enable")
async def enable_qos(
    authenticated: bool = Depends(require_auth),
) -> dict[str, str]:
    """
    Enable QoS traffic prioritization.

    Requires authentication.
    Applies traffic control rules to prioritize VPN traffic.

    Returns:
        Operation status

    Raises:
        HTTPException 500: If operation fails
    """
    logger.info("Enable QoS requested")

    success = QoSService.enable()
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to enable QoS. Check system logs for details."
        )

    return {"status": "enabled"}


@router.post("/disable")
async def disable_qos(
    authenticated: bool = Depends(require_auth),
) -> dict[str, str]:
    """
    Disable QoS traffic prioritization.

    Requires authentication.
    Removes all traffic control rules.

    Returns:
        Operation status

    Raises:
        HTTPException 500: If operation fails
    """
    logger.info("Disable QoS requested")

    success = QoSService.disable()
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to disable QoS"
        )

    return {"status": "disabled"}


@router.put("/config")
async def update_config(
    request: QoSConfigUpdate = Body(...),
    authenticated: bool = Depends(require_auth),
) -> dict[str, Any]:
    """
    Update QoS configuration.

    Requires authentication.
    If QoS is enabled, rules will be re-applied with new settings.

    Args:
        request: Configuration update data

    Returns:
        Updated configuration

    Raises:
        HTTPException 500: If update fails
    """
    logger.info(f"Update QoS config: bandwidth={request.total_bandwidth_mbps}, vpn_percent={request.vpn_bandwidth_percent}")

    success = QoSService.update_config(
        total_bandwidth_mbps=request.total_bandwidth_mbps,
        vpn_bandwidth_percent=request.vpn_bandwidth_percent,
    )

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to update QoS configuration"
        )

    status = QoSService.get_status()
    return {
        "status": "updated",
        "config": status.config.to_dict(),
    }
