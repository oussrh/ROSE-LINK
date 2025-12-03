"""
WebSocket Routes
================

Real-time WebSocket endpoints for live status updates.

Endpoints:
- WS /ws - Main WebSocket endpoint for real-time updates
- GET /ws/status - WebSocket connection status

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import logging
from typing import Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.websocket import manager

logger = logging.getLogger("rose-link.ws-routes")

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    Main WebSocket endpoint for real-time status updates.

    Clients connecting to this endpoint will receive:
    - Periodic status updates (WAN, VPN, Hotspot)
    - Event notifications (connection changes, errors)

    Message format (sent to clients):
    {
        "type": "status" | "event" | "error",
        "data": { ... },
        "timestamp": "ISO8601 timestamp"
    }

    Clients can send messages:
    {
        "action": "subscribe" | "unsubscribe" | "ping",
        "topic": "status" | "events" | "all"
    }
    """
    await manager.connect(websocket)

    try:
        # Send initial status immediately upon connection
        from services.wan_service import WANService
        from services.vpn_service import VPNService
        from services.hotspot_service import HotspotService

        initial_status = {
            "type": "status",
            "data": {
                "wan": WANService.get_status().to_dict(),
                "vpn": VPNService.get_status().to_dict(),
                "ap": HotspotService.get_status().to_dict(),
            },
        }
        await manager.send_personal(websocket, initial_status)

        # Keep connection alive and handle incoming messages
        while True:
            try:
                data = await websocket.receive_json()
                await _handle_client_message(websocket, data)
            except WebSocketDisconnect:
                break

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await manager.disconnect(websocket)


async def _handle_client_message(websocket: WebSocket, data: Dict[str, Any]) -> None:
    """
    Handle incoming messages from WebSocket clients.

    Args:
        websocket: The client WebSocket connection
        data: Parsed JSON message from client
    """
    action = data.get("action")

    if action == "ping":
        # Respond to ping with pong
        await manager.send_personal(websocket, {
            "type": "pong",
            "data": {},
        })

    elif action == "get_status":
        # Send current status on demand
        from services.wan_service import WANService
        from services.vpn_service import VPNService
        from services.hotspot_service import HotspotService

        await manager.send_personal(websocket, {
            "type": "status",
            "data": {
                "wan": WANService.get_status().to_dict(),
                "vpn": VPNService.get_status().to_dict(),
                "ap": HotspotService.get_status().to_dict(),
            },
        })

    elif action == "get_bandwidth":
        # Send bandwidth statistics
        from services.bandwidth_service import BandwidthService

        await manager.send_personal(websocket, {
            "type": "bandwidth",
            "data": BandwidthService.get_stats(),
        })

    else:
        # Unknown action
        await manager.send_personal(websocket, {
            "type": "error",
            "data": {"message": f"Unknown action: {action}"},
        })


@router.get("/ws/status")
async def websocket_status() -> Dict[str, Any]:
    """
    Get WebSocket service status.

    Returns:
        WebSocket connection statistics
    """
    return {
        "active_connections": manager.connection_count,
        "broadcast_running": manager._running,
    }
