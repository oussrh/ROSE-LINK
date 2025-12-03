"""
Tests for Connected Clients Service
===================================

Unit tests for the connected clients management service.

Author: ROSE Link Team
License: MIT
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import os

from services.clients_service import (
    ClientsService,
    ClientInfo,
    CLIENTS_DATA_FILE,
    BLOCKED_CLIENTS_FILE,
    MAC_OUI_DATABASE,
)


class TestClientInfo:
    """Tests for ClientInfo dataclass."""

    def test_default_values(self):
        """Test default client values."""
        client = ClientInfo(mac="AA:BB:CC:DD:EE:FF")

        assert client.mac == "AA:BB:CC:DD:EE:FF"
        assert client.ip is None
        assert client.connected is False
        assert client.blocked is False

    def test_to_dict(self):
        """Test client serialization."""
        client = ClientInfo(
            mac="AA:BB:CC:DD:EE:FF",
            ip="192.168.50.10",
            hostname="my-device",
            custom_name="My Phone",
            connected=True,
            rx_bytes=1024,
            tx_bytes=2048,
        )

        result = client.to_dict()

        assert result["mac"] == "AA:BB:CC:DD:EE:FF"
        assert result["ip"] == "192.168.50.10"
        assert result["hostname"] == "my-device"
        assert result["custom_name"] == "My Phone"
        assert result["display_name"] == "My Phone"  # Prefers custom_name
        assert result["connected"] is True
        assert result["rx_bytes"] == 1024

    def test_display_name_fallback(self):
        """Test display name fallback order."""
        # Custom name takes priority
        client1 = ClientInfo(mac="AA:BB:CC:DD:EE:FF", hostname="device", custom_name="Custom")
        assert client1.to_dict()["display_name"] == "Custom"

        # Then hostname
        client2 = ClientInfo(mac="AA:BB:CC:DD:EE:FF", hostname="device")
        assert client2.to_dict()["display_name"] == "device"

        # Finally MAC address
        client3 = ClientInfo(mac="AA:BB:CC:DD:EE:FF")
        assert client3.to_dict()["display_name"] == "AA:BB:CC:DD:EE:FF"


class TestClientsService:
    """Tests for ClientsService class."""

    @pytest.fixture
    def temp_data_dir(self, tmp_path):
        """Create temporary data directory."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        return data_dir

    def test_detect_device_type_apple(self):
        """Test device type detection for Apple devices."""
        client = ClientInfo(mac="00:1A:79:11:22:33")
        ClientsService._detect_device_type(client)

        assert client.manufacturer == "Apple"
        assert client.device_type == "iPhone/iPad"

    def test_detect_device_type_samsung(self):
        """Test device type detection for Samsung devices."""
        client = ClientInfo(mac="00:1A:2B:11:22:33")
        ClientsService._detect_device_type(client)

        assert client.manufacturer == "Samsung"
        assert client.device_type == "Android"

    def test_detect_device_type_raspberry_pi(self):
        """Test device type detection for Raspberry Pi."""
        client = ClientInfo(mac="B8:27:EB:11:22:33")
        ClientsService._detect_device_type(client)

        assert client.manufacturer == "Raspberry Pi"
        assert client.device_type == "Linux"

    def test_detect_device_type_unknown(self):
        """Test device type detection for unknown manufacturer."""
        client = ClientInfo(mac="11:22:33:44:55:66")
        ClientsService._detect_device_type(client)

        assert client.manufacturer is None
        assert client.device_type is None

    def test_get_connected_clients_no_hostapd(self):
        """Test getting clients when hostapd not available."""
        with patch('services.clients_service.run_command') as mock_run:
            mock_run.return_value = (1, "", "error")

            clients = ClientsService.get_connected_clients()

            assert clients == []

    def test_get_connected_clients_with_data(self):
        """Test getting clients with hostapd output."""
        hostapd_output = """AA:BB:CC:DD:EE:FF
signal=-50
rx_bytes=1024
tx_bytes=2048
inactive_msec=1000
11:22:33:44:55:66
signal=-60
rx_bytes=512
tx_bytes=256
inactive_msec=500"""

        with patch('services.clients_service.run_command') as mock_run:
            mock_run.return_value = (0, hostapd_output, "")

            with patch.object(ClientsService, '_get_dnsmasq_leases', return_value={}):
                with patch.object(ClientsService, '_get_blocked_macs', return_value=set()):
                    with patch.object(ClientsService, '_update_client_history'):
                        clients = ClientsService.get_connected_clients()

                        assert len(clients) == 2
                        assert clients[0].mac == "AA:BB:CC:DD:EE:FF"
                        assert clients[0].signal == "-50 dBm"
                        assert clients[0].rx_bytes == 1024
                        assert clients[0].connected is True

    def test_get_blocked_macs_empty(self):
        """Test getting blocked MACs when file doesn't exist."""
        with patch('pathlib.Path.exists', return_value=False):
            blocked = ClientsService._get_blocked_macs()
            assert isinstance(blocked, set)

    def test_get_blocked_macs_with_data(self, tmp_path):
        """Test getting blocked MACs from file."""
        blocked_file = tmp_path / "blocked.txt"
        blocked_file.write_text("AA:BB:CC:DD:EE:FF\n11:22:33:44:55:66\n")

        with patch('services.clients_service.BLOCKED_CLIENTS_FILE', blocked_file):
            blocked = ClientsService._get_blocked_macs()

            assert "AA:BB:CC:DD:EE:FF" in blocked
            assert "11:22:33:44:55:66" in blocked

    def test_save_blocked_macs(self, tmp_path):
        """Test saving blocked MACs to file."""
        blocked_file = tmp_path / "blocked.txt"
        blocked = {"AA:BB:CC:DD:EE:FF", "11:22:33:44:55:66"}

        with patch('services.clients_service.BLOCKED_CLIENTS_FILE', blocked_file):
            ClientsService._save_blocked_macs(blocked)

            content = blocked_file.read_text()
            assert "AA:BB:CC:DD:EE:FF" in content
            assert "11:22:33:44:55:66" in content

    def test_block_client(self):
        """Test blocking a client."""
        with patch.object(ClientsService, '_get_blocked_macs', return_value=set()):
            with patch.object(ClientsService, '_save_blocked_macs'):
                with patch('services.clients_service.run_command', return_value=(0, "", "")):
                    result = ClientsService.block_client("AA:BB:CC:DD:EE:FF")
                    assert result is True

    def test_unblock_client(self):
        """Test unblocking a client."""
        with patch.object(ClientsService, '_get_blocked_macs', return_value={"AA:BB:CC:DD:EE:FF"}):
            with patch.object(ClientsService, '_save_blocked_macs'):
                with patch('services.clients_service.run_command', return_value=(0, "", "")):
                    result = ClientsService.unblock_client("AA:BB:CC:DD:EE:FF")
                    assert result is True

    def test_kick_client_success(self):
        """Test kicking a client successfully."""
        with patch('services.clients_service.run_command', return_value=(0, "", "")):
            result = ClientsService.kick_client("AA:BB:CC:DD:EE:FF")
            assert result is True

    def test_kick_client_failure(self):
        """Test kicking a client when it fails."""
        with patch('services.clients_service.run_command', return_value=(1, "", "error")):
            result = ClientsService.kick_client("AA:BB:CC:DD:EE:FF")
            assert result is False

    def test_update_client(self, tmp_path):
        """Test updating client information."""
        data_file = tmp_path / "clients.json"

        with patch('services.clients_service.CLIENTS_DATA_FILE', data_file):
            with patch.object(ClientsService, '_load_client_history', return_value={}):
                with patch.object(ClientsService, '_save_client_history') as mock_save:
                    result = ClientsService.update_client(
                        mac="AA:BB:CC:DD:EE:FF",
                        custom_name="My Device"
                    )

                    assert result is True
                    mock_save.assert_called_once()

    def test_get_client_count(self):
        """Test getting client count statistics."""
        with patch.object(ClientsService, 'get_connected_clients', return_value=[
            ClientInfo(mac="AA:BB:CC:DD:EE:FF"),
            ClientInfo(mac="11:22:33:44:55:66"),
        ]):
            with patch.object(ClientsService, '_load_client_history', return_value={
                "AA:BB:CC:DD:EE:FF": {},
                "11:22:33:44:55:66": {},
                "00:11:22:33:44:55": {},
            }):
                with patch.object(ClientsService, '_get_blocked_macs', return_value={"00:11:22:33:44:55"}):
                    counts = ClientsService.get_client_count()

                    assert counts["connected"] == 2
                    assert counts["blocked"] == 1
                    assert counts["total_known"] == 3

    def test_history_to_client(self):
        """Test converting historical data to ClientInfo."""
        history_data = {
            "hostname": "my-device",
            "custom_name": "Phone",
            "ip": "192.168.50.10",
            "first_seen": "2024-01-01T00:00:00",
            "last_seen": "2024-01-02T00:00:00",
            "total_rx_bytes": 1000000,
            "total_tx_bytes": 500000,
            "manufacturer": "Apple",
            "device_type": "iPhone/iPad",
            "connection_count": 5,
        }

        with patch.object(ClientsService, '_get_blocked_macs', return_value=set()):
            client = ClientsService._history_to_client("AA:BB:CC:DD:EE:FF", history_data)

            assert client.mac == "AA:BB:CC:DD:EE:FF"
            assert client.hostname == "my-device"
            assert client.custom_name == "Phone"
            assert client.connected is False
            assert client.total_rx_bytes == 1000000
            assert client.connection_count == 5
