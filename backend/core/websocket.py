"""
WebSocket Manager
=================

Manages WebSocket connections for real-time status updates.

This module provides:
- Connection management (add/remove clients)
- Broadcasting status updates to all connected clients
- Background task for periodic status updates

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Set, Optional, Dict, Any
from datetime import datetime

from fastapi import WebSocket

logger = logging.getLogger("rose-link.websocket")


class ConnectionManager:
    """
    Manages WebSocket connections and broadcasts messages.

    This class handles:
    - Tracking active WebSocket connections
    - Broadcasting messages to all connected clients
    - Graceful connection handling with proper cleanup
    """

    def __init__(self) -> None:
        """Initialize the connection manager."""
        self._connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self._broadcast_task: Optional[asyncio.Task] = None
        self._running = False

    @property
    def connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self._connections)

    async def connect(self, websocket: WebSocket) -> None:
        """
        Accept a new WebSocket connection.

        Args:
            websocket: The WebSocket connection to accept
        """
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
        logger.info(f"WebSocket connected. Active connections: {self.connection_count}")

    async def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection.

        Args:
            websocket: The WebSocket connection to remove
        """
        async with self._lock:
            self._connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Active connections: {self.connection_count}")

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """
        Broadcast a message to all connected clients.

        Args:
            message: Dictionary to send as JSON to all clients
        """
        if not self._connections:
            return

        # Add timestamp to message
        message["timestamp"] = datetime.utcnow().isoformat()

        # Send to all connections, handling disconnections
        disconnected: Set[WebSocket] = set()

        async with self._lock:
            for websocket in self._connections.copy():
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.debug(f"Failed to send to client: {e}")
                    disconnected.add(websocket)

            # Remove disconnected clients
            self._connections -= disconnected

        if disconnected:
            logger.info(f"Removed {len(disconnected)} disconnected clients")

    async def send_personal(self, websocket: WebSocket, message: Dict[str, Any]) -> bool:
        """
        Send a message to a specific client.

        Args:
            websocket: The target WebSocket connection
            message: Dictionary to send as JSON

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            message["timestamp"] = datetime.utcnow().isoformat()
            await websocket.send_json(message)
            return True
        except Exception as e:
            logger.debug(f"Failed to send personal message: {e}")
            return False

    async def start_broadcast_loop(self, interval: float = 2.0) -> None:
        """
        Start the background broadcast loop.

        This loop periodically broadcasts system status to all connected clients.

        Args:
            interval: Seconds between broadcasts (default: 2.0)
        """
        if self._running:
            logger.warning("Broadcast loop already running")
            return

        self._running = True
        logger.info(f"Starting WebSocket broadcast loop (interval: {interval}s)")

        while self._running:
            try:
                if self._connections:
                    status = await self._get_system_status()
                    await self.broadcast({
                        "type": "status",
                        "data": status,
                    })
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}")
                await asyncio.sleep(interval)

        logger.info("WebSocket broadcast loop stopped")

    def stop_broadcast_loop(self) -> None:
        """Stop the background broadcast loop."""
        self._running = False
        if self._broadcast_task:
            self._broadcast_task.cancel()
            self._broadcast_task = None

    async def _get_system_status(self) -> Dict[str, Any]:
        """
        Get current system status for broadcasting.

        Returns:
            Dictionary containing WAN, VPN, and AP status
        """
        # Import here to avoid circular imports
        from services.wan_service import WANService
        from services.vpn_service import VPNService
        from services.hotspot_service import HotspotService

        try:
            return {
                "wan": WANService.get_status().to_dict(),
                "vpn": VPNService.get_status().to_dict(),
                "ap": HotspotService.get_status().to_dict(),
            }
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                "error": str(e),
                "wan": {"active": False},
                "vpn": {"active": False},
                "ap": {"active": False},
            }

    async def close_all(self) -> None:
        """Close all WebSocket connections gracefully."""
        self.stop_broadcast_loop()

        async with self._lock:
            for websocket in self._connections.copy():
                try:
                    await websocket.close(code=1001, reason="Server shutdown")
                except Exception:
                    pass
            self._connections.clear()

        logger.info("All WebSocket connections closed")


# Global connection manager instance
manager = ConnectionManager()


async def get_manager() -> ConnectionManager:
    """
    Get the global connection manager instance.

    This is used as a dependency in FastAPI routes.

    Returns:
        The global ConnectionManager instance
    """
    return manager
