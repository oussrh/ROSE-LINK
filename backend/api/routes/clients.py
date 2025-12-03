"""
Connected Clients API Routes
============================

Endpoints for managing connected hotspot clients.

Endpoints:
- GET /api/clients: List all clients (connected + historical)
- GET /api/clients/connected: List currently connected clients
- GET /api/clients/count: Get client count statistics
- GET /api/clients/{mac}: Get specific client info
- PUT /api/clients/{mac}: Update client (name, etc.)
- POST /api/clients/{mac}/block: Block a client
- POST /api/clients/{mac}/unblock: Unblock a client
- POST /api/clients/{mac}/kick: Disconnect a client

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import logging
import re
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Body
from pydantic import BaseModel, Field

from services.clients_service import ClientsService
from api.dependencies import require_auth

logger = logging.getLogger("rose-link.api.clients")

router = APIRouter(prefix="/clients")


class ClientUpdateRequest(BaseModel):
    """Request model for updating client info."""
    custom_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="Custom display name for the device"
    )


def validate_mac(mac: str) -> str:
    """Validate and normalize MAC address."""
    mac = mac.upper().strip()
    if not re.match(r'^([0-9A-F]{2}:){5}[0-9A-F]{2}$', mac):
        raise HTTPException(
            status_code=400,
            detail="Invalid MAC address format. Use XX:XX:XX:XX:XX:XX"
        )
    return mac


@router.get("")
async def list_all_clients() -> dict[str, Any]:
    """
    List all clients (connected and historical).

    Returns:
        List of all known clients with their status
    """
    clients = ClientsService.get_all_clients()
    return {
        "clients": [c.to_dict() for c in clients],
        "count": len(clients),
    }


@router.get("/connected")
async def list_connected_clients() -> dict[str, Any]:
    """
    List currently connected clients.

    Returns:
        List of currently connected clients
    """
    clients = ClientsService.get_connected_clients()
    return {
        "clients": [c.to_dict() for c in clients],
        "count": len(clients),
    }


@router.get("/count")
async def get_client_count() -> dict[str, int]:
    """
    Get client count statistics.

    Returns:
        Connected, blocked, and total known client counts
    """
    return ClientsService.get_client_count()


@router.get("/{mac}")
async def get_client(
    mac: str = Path(..., description="Client MAC address")
) -> dict[str, Any]:
    """
    Get information about a specific client.

    Args:
        mac: Client MAC address

    Returns:
        Client information

    Raises:
        HTTPException 404: If client not found
    """
    mac = validate_mac(mac)

    client = ClientsService.get_client(mac)
    if client is None:
        raise HTTPException(
            status_code=404,
            detail=f"Client not found: {mac}"
        )

    return client.to_dict()


@router.put("/{mac}")
async def update_client(
    mac: str = Path(..., description="Client MAC address"),
    request: ClientUpdateRequest = Body(...),
    authenticated: bool = Depends(require_auth),
) -> dict[str, str]:
    """
    Update client information (e.g., custom name).

    Requires authentication.

    Args:
        mac: Client MAC address
        request: Update data

    Returns:
        Update status

    Raises:
        HTTPException 500: If update fails
    """
    mac = validate_mac(mac)

    logger.info(f"Update client {mac}: name={request.custom_name}")

    success = ClientsService.update_client(
        mac=mac,
        custom_name=request.custom_name,
    )

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to update client"
        )

    return {"status": "updated", "mac": mac}


@router.post("/{mac}/block")
async def block_client(
    mac: str = Path(..., description="Client MAC address"),
    authenticated: bool = Depends(require_auth),
) -> dict[str, str]:
    """
    Block a client from connecting.

    Requires authentication.
    Disconnects the client if currently connected and prevents reconnection.

    Args:
        mac: Client MAC address

    Returns:
        Block status

    Raises:
        HTTPException 500: If block fails
    """
    mac = validate_mac(mac)

    logger.info(f"Block client requested: {mac}")

    success = ClientsService.block_client(mac)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to block client"
        )

    return {"status": "blocked", "mac": mac}


@router.post("/{mac}/unblock")
async def unblock_client(
    mac: str = Path(..., description="Client MAC address"),
    authenticated: bool = Depends(require_auth),
) -> dict[str, str]:
    """
    Unblock a previously blocked client.

    Requires authentication.

    Args:
        mac: Client MAC address

    Returns:
        Unblock status

    Raises:
        HTTPException 500: If unblock fails
    """
    mac = validate_mac(mac)

    logger.info(f"Unblock client requested: {mac}")

    success = ClientsService.unblock_client(mac)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to unblock client"
        )

    return {"status": "unblocked", "mac": mac}


@router.post("/{mac}/kick")
async def kick_client(
    mac: str = Path(..., description="Client MAC address"),
    authenticated: bool = Depends(require_auth),
) -> dict[str, str]:
    """
    Disconnect a client without blocking.

    Requires authentication.
    The client may reconnect automatically.

    Args:
        mac: Client MAC address

    Returns:
        Kick status

    Raises:
        HTTPException 500: If kick fails
    """
    mac = validate_mac(mac)

    logger.info(f"Kick client requested: {mac}")

    success = ClientsService.kick_client(mac)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to disconnect client"
        )

    return {"status": "disconnected", "mac": mac}
