"""
WebSocket Tests
===============

Unit tests for the WebSocket connection manager.

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

import pytest

from core.websocket import ConnectionManager, manager, get_manager


class MockWebSocket:
    """Mock WebSocket for testing."""

    def __init__(self) -> None:
        self.accepted = False
        self.closed = False
        self.close_code = None
        self.close_reason = None
        self.sent_messages: list[Dict[str, Any]] = []

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, data: Dict[str, Any]) -> None:
        if self.closed:
            raise RuntimeError("Connection closed")
        self.sent_messages.append(data)

    async def close(self, code: int = 1000, reason: str = "") -> None:
        self.closed = True
        self.close_code = code
        self.close_reason = reason


class TestConnectionManager:
    """Tests for ConnectionManager class."""

    @pytest.fixture
    def manager(self) -> ConnectionManager:
        """Create a fresh ConnectionManager for each test."""
        return ConnectionManager()

    def test_init_creates_empty_connections(self, manager: ConnectionManager) -> None:
        """Should initialize with no connections."""
        assert manager.connection_count == 0

    def test_connection_count_property(self, manager: ConnectionManager) -> None:
        """Should return correct connection count."""
        assert manager.connection_count == 0


class TestConnectionManagerConnect:
    """Tests for connect method."""

    @pytest.fixture
    def manager(self) -> ConnectionManager:
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_accepts_websocket(self, manager: ConnectionManager) -> None:
        """Should accept the WebSocket connection."""
        ws = MockWebSocket()

        await manager.connect(ws)

        assert ws.accepted is True

    @pytest.mark.asyncio
    async def test_adds_to_connections(self, manager: ConnectionManager) -> None:
        """Should add WebSocket to connections set."""
        ws = MockWebSocket()

        await manager.connect(ws)

        assert manager.connection_count == 1

    @pytest.mark.asyncio
    async def test_multiple_connections(self, manager: ConnectionManager) -> None:
        """Should handle multiple connections."""
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()
        ws3 = MockWebSocket()

        await manager.connect(ws1)
        await manager.connect(ws2)
        await manager.connect(ws3)

        assert manager.connection_count == 3


class TestConnectionManagerDisconnect:
    """Tests for disconnect method."""

    @pytest.fixture
    def manager(self) -> ConnectionManager:
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_removes_from_connections(self, manager: ConnectionManager) -> None:
        """Should remove WebSocket from connections set."""
        ws = MockWebSocket()
        await manager.connect(ws)

        await manager.disconnect(ws)

        assert manager.connection_count == 0

    @pytest.mark.asyncio
    async def test_handles_unknown_websocket(
        self, manager: ConnectionManager
    ) -> None:
        """Should handle disconnecting unknown WebSocket gracefully."""
        ws = MockWebSocket()

        # Should not raise
        await manager.disconnect(ws)

        assert manager.connection_count == 0

    @pytest.mark.asyncio
    async def test_removes_only_specified_connection(
        self, manager: ConnectionManager
    ) -> None:
        """Should only remove specified connection."""
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()
        await manager.connect(ws1)
        await manager.connect(ws2)

        await manager.disconnect(ws1)

        assert manager.connection_count == 1


class TestConnectionManagerBroadcast:
    """Tests for broadcast method."""

    @pytest.fixture
    def manager(self) -> ConnectionManager:
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_broadcasts_to_all_connections(
        self, manager: ConnectionManager
    ) -> None:
        """Should send message to all connected clients."""
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()
        await manager.connect(ws1)
        await manager.connect(ws2)

        await manager.broadcast({"type": "test", "data": "hello"})

        assert len(ws1.sent_messages) == 1
        assert len(ws2.sent_messages) == 1
        assert ws1.sent_messages[0]["type"] == "test"

    @pytest.mark.asyncio
    async def test_adds_timestamp_to_message(
        self, manager: ConnectionManager
    ) -> None:
        """Should add timestamp to broadcast messages."""
        ws = MockWebSocket()
        await manager.connect(ws)

        await manager.broadcast({"type": "test"})

        assert "timestamp" in ws.sent_messages[0]

    @pytest.mark.asyncio
    async def test_handles_no_connections(
        self, manager: ConnectionManager
    ) -> None:
        """Should handle broadcast with no connections."""
        # Should not raise
        await manager.broadcast({"type": "test"})

    @pytest.mark.asyncio
    async def test_removes_failed_connections(
        self, manager: ConnectionManager
    ) -> None:
        """Should remove connections that fail to receive."""
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()
        await manager.connect(ws1)
        await manager.connect(ws2)

        # Make ws1 fail
        ws1.closed = True

        await manager.broadcast({"type": "test"})

        # ws1 should be removed
        assert manager.connection_count == 1
        # ws2 should have received the message
        assert len(ws2.sent_messages) == 1


class TestConnectionManagerSendPersonal:
    """Tests for send_personal method."""

    @pytest.fixture
    def manager(self) -> ConnectionManager:
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_sends_to_specific_client(
        self, manager: ConnectionManager
    ) -> None:
        """Should send message to specific client."""
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()
        await manager.connect(ws1)
        await manager.connect(ws2)

        result = await manager.send_personal(ws1, {"type": "personal"})

        assert result is True
        assert len(ws1.sent_messages) == 1
        assert len(ws2.sent_messages) == 0

    @pytest.mark.asyncio
    async def test_adds_timestamp(self, manager: ConnectionManager) -> None:
        """Should add timestamp to personal messages."""
        ws = MockWebSocket()
        await manager.connect(ws)

        await manager.send_personal(ws, {"type": "test"})

        assert "timestamp" in ws.sent_messages[0]

    @pytest.mark.asyncio
    async def test_returns_false_on_failure(
        self, manager: ConnectionManager
    ) -> None:
        """Should return False when send fails."""
        ws = MockWebSocket()
        ws.closed = True

        result = await manager.send_personal(ws, {"type": "test"})

        assert result is False


class TestConnectionManagerBroadcastLoop:
    """Tests for broadcast loop methods."""

    @pytest.fixture
    def manager(self) -> ConnectionManager:
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_start_sets_running_flag(
        self, manager: ConnectionManager
    ) -> None:
        """Should set running flag when started."""
        assert manager._running is False

        # Start the loop briefly
        task = asyncio.create_task(manager.start_broadcast_loop(interval=0.1))
        await asyncio.sleep(0.05)

        assert manager._running is True

        manager.stop_broadcast_loop()
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_stop_clears_running_flag(
        self, manager: ConnectionManager
    ) -> None:
        """Should clear running flag when stopped."""
        manager._running = True

        manager.stop_broadcast_loop()

        assert manager._running is False

    @pytest.mark.asyncio
    async def test_broadcasts_status_to_clients(
        self, manager: ConnectionManager
    ) -> None:
        """Should broadcast status messages to connected clients."""
        ws = MockWebSocket()
        await manager.connect(ws)

        # Mock the status fetching
        with patch.object(
            manager, "_get_system_status",
            new_callable=AsyncMock,
            return_value={"wan": {}, "vpn": {}, "ap": {}}
        ):
            task = asyncio.create_task(manager.start_broadcast_loop(interval=0.1))
            await asyncio.sleep(0.15)  # Wait for at least one broadcast
            manager.stop_broadcast_loop()
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Should have received at least one status message
        assert len(ws.sent_messages) >= 1
        assert ws.sent_messages[0]["type"] == "status"


class TestConnectionManagerGetSystemStatus:
    """Tests for _get_system_status method."""

    @pytest.fixture
    def manager(self) -> ConnectionManager:
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_returns_status_dict(self, manager: ConnectionManager) -> None:
        """Should return dictionary with wan, vpn, ap status."""
        mock_status = MagicMock()
        mock_status.to_dict.return_value = {"active": True}

        with patch("services.wan_service.WANService") as wan_mock:
            with patch("services.vpn_service.VPNService") as vpn_mock:
                with patch("services.hotspot_service.HotspotService") as ap_mock:
                    wan_mock.get_status.return_value = mock_status
                    vpn_mock.get_status.return_value = mock_status
                    ap_mock.get_status.return_value = mock_status

                    result = await manager._get_system_status()

        assert "wan" in result
        assert "vpn" in result
        assert "ap" in result

    @pytest.mark.asyncio
    async def test_handles_service_errors(
        self, manager: ConnectionManager
    ) -> None:
        """Should handle errors gracefully."""
        with patch("services.wan_service.WANService") as wan_mock:
            wan_mock.get_status.side_effect = Exception("Service error")

            result = await manager._get_system_status()

        assert "error" in result
        assert result["wan"]["active"] is False


class TestConnectionManagerCloseAll:
    """Tests for close_all method."""

    @pytest.fixture
    def manager(self) -> ConnectionManager:
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_closes_all_connections(
        self, manager: ConnectionManager
    ) -> None:
        """Should close all WebSocket connections."""
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()
        await manager.connect(ws1)
        await manager.connect(ws2)

        await manager.close_all()

        assert manager.connection_count == 0
        assert ws1.closed is True
        assert ws2.closed is True

    @pytest.mark.asyncio
    async def test_stops_broadcast_loop(
        self, manager: ConnectionManager
    ) -> None:
        """Should stop the broadcast loop."""
        manager._running = True

        await manager.close_all()

        assert manager._running is False

    @pytest.mark.asyncio
    async def test_uses_correct_close_code(
        self, manager: ConnectionManager
    ) -> None:
        """Should use 1001 close code for server shutdown."""
        ws = MockWebSocket()
        await manager.connect(ws)

        await manager.close_all()

        assert ws.close_code == 1001


class TestGetManager:
    """Tests for get_manager dependency."""

    @pytest.mark.asyncio
    async def test_returns_global_manager(self) -> None:
        """Should return the global manager instance."""
        result = await get_manager()

        assert result is manager

    @pytest.mark.asyncio
    async def test_returns_connection_manager(self) -> None:
        """Should return a ConnectionManager instance."""
        result = await get_manager()

        assert isinstance(result, ConnectionManager)
