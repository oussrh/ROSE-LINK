"""
WAN Service Tests
=================

Unit tests for the WAN service with mocked command execution.

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from tests.conftest import MockCommandExecutor


class TestWANServiceEthernet:
    """Tests for Ethernet status checking."""

    def test_get_ethernet_status_connected(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """_get_ethernet_status should detect connected state."""
        mock_executor.set_response(
            "ip addr show eth0",
            return_code=0,
            stdout="""2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500
    link/ether 00:11:22:33:44:55 brd ff:ff:ff:ff:ff:ff
    inet 192.168.1.100/24 brd 192.168.1.255 scope global eth0
""",
        )

        # Mock InterfaceService to return eth0
        with patch("services.wan_service.InterfaceService") as mock_iface:
            mock_interfaces = MagicMock()
            mock_interfaces.ethernet = "eth0"
            mock_interfaces.wifi_wan = ""
            mock_iface.get_interfaces.return_value = mock_interfaces

            from services.wan_service import WANService

            status = WANService._get_ethernet_status("eth0")

            assert status.connected is True
            assert "192.168.1.100" in status.ip

    def test_get_ethernet_status_disconnected(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """_get_ethernet_status should detect disconnected state."""
        mock_executor.set_response(
            "ip addr show eth0",
            return_code=0,
            stdout="""2: eth0: <BROADCAST,MULTICAST> mtu 1500
    link/ether 00:11:22:33:44:55 brd ff:ff:ff:ff:ff:ff
""",
        )

        from services.wan_service import WANService

        status = WANService._get_ethernet_status("eth0")

        assert status.connected is False


class TestWANServiceWifi:
    """Tests for WiFi status checking."""

    def test_get_wifi_status_connected(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """_get_wifi_status should detect connected state."""
        mock_executor.set_response(
            "nmcli -t -f DEVICE,STATE,CONNECTION device",
            return_code=0,
            stdout="wlan1:connected:MyNetwork\n",
        )
        mock_executor.set_response(
            "ip addr show wlan1",
            return_code=0,
            stdout="inet 192.168.1.50/24",
        )

        from services.wan_service import WANService

        status = WANService._get_wifi_status("wlan1")

        assert status.connected is True
        assert status.ssid == "MyNetwork"

    def test_get_wifi_status_disconnected(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """_get_wifi_status should detect disconnected state."""
        mock_executor.set_response(
            "nmcli -t -f DEVICE,STATE,CONNECTION device",
            return_code=0,
            stdout="wlan1:disconnected:\n",
        )

        from services.wan_service import WANService

        status = WANService._get_wifi_status("wlan1")

        assert status.connected is False


class TestWANServiceScan:
    """Tests for WiFi scanning."""

    def test_scan_networks_parses_results(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """scan_networks should parse nmcli output correctly."""
        mock_executor.set_response(
            "sudo nmcli -t -f SSID,SIGNAL,SECURITY device wifi list",
            return_code=0,
            stdout="""NetworkA:90:WPA2
NetworkB:75:WPA3
NetworkC:50:Open
""",
        )

        from services.wan_service import WANService

        networks = WANService.scan_networks()

        assert len(networks) == 3
        # Should be sorted by signal strength
        assert networks[0].ssid == "NetworkA"
        assert networks[0].signal == 90
        assert networks[1].ssid == "NetworkB"
        assert networks[2].ssid == "NetworkC"

    def test_scan_networks_deduplicates(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """scan_networks should remove duplicate SSIDs."""
        mock_executor.set_response(
            "sudo nmcli -t -f SSID,SIGNAL,SECURITY device wifi list",
            return_code=0,
            stdout="""DuplicateNetwork:90:WPA2
DuplicateNetwork:85:WPA2
UniqueNetwork:70:WPA3
""",
        )

        from services.wan_service import WANService

        networks = WANService.scan_networks()

        ssids = [n.ssid for n in networks]
        assert ssids.count("DuplicateNetwork") == 1
        assert len(networks) == 2

    def test_scan_networks_raises_on_failure(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """scan_networks should raise WifiScanError on failure."""
        mock_executor.set_response(
            "sudo nmcli -t -f SSID,SIGNAL,SECURITY device wifi list",
            return_code=1,
            stderr="Error: NetworkManager is not running",
        )

        from services.wan_service import WANService
        from exceptions import WifiScanError

        with pytest.raises(WifiScanError):
            WANService.scan_networks()


class TestWANServiceConnect:
    """Tests for WiFi connection."""

    def test_connect_wifi_success(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """connect_wifi should succeed when nmcli succeeds."""
        mock_executor.set_response(
            "sudo nmcli device wifi connect TestNetwork password secret123",
            return_code=0,
            stdout="Device 'wlan1' successfully activated.\n",
        )

        from services.wan_service import WANService

        result = WANService.connect_wifi("TestNetwork", "secret123")

        assert result is True

    def test_connect_wifi_failure(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """connect_wifi should raise WifiConnectionError on failure."""
        mock_executor.set_response(
            "sudo nmcli device wifi connect TestNetwork password wrongpass",
            return_code=1,
            stderr="Error: Connection activation failed",
        )

        from services.wan_service import WANService
        from exceptions import WifiConnectionError

        with pytest.raises(WifiConnectionError) as exc_info:
            WANService.connect_wifi("TestNetwork", "wrongpass")

        assert "TestNetwork" in str(exc_info.value) or exc_info.value.details.get("ssid") == "TestNetwork"


class TestWANServiceDisconnect:
    """Tests for WiFi disconnection."""

    def test_disconnect_wifi_success(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """disconnect_wifi should succeed when nmcli succeeds."""
        mock_executor.set_response(
            "sudo nmcli device disconnect wlan1",
            return_code=0,
            stdout="Device 'wlan1' successfully disconnected.\n",
        )

        with patch("services.wan_service.InterfaceService") as mock_iface:
            mock_interfaces = MagicMock()
            mock_interfaces.wifi_wan = "wlan1"
            mock_iface.get_interfaces.return_value = mock_interfaces

            from services.wan_service import WANService

            result = WANService.disconnect_wifi()

            assert result is True

    def test_disconnect_wifi_failure(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """disconnect_wifi should raise WifiConnectionError on failure."""
        mock_executor.set_response(
            "sudo nmcli device disconnect wlan1",
            return_code=1,
            stderr="Error: Device is not connected",
        )

        with patch("services.wan_service.InterfaceService") as mock_iface:
            mock_interfaces = MagicMock()
            mock_interfaces.wifi_wan = "wlan1"
            mock_iface.get_interfaces.return_value = mock_interfaces

            from services.wan_service import WANService
            from exceptions import WifiConnectionError

            with pytest.raises(WifiConnectionError):
                WANService.disconnect_wifi()


class TestWANServiceHelpers:
    """Tests for WAN service helper methods."""

    def test_is_connected_with_ethernet(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """is_connected should return True when Ethernet is connected."""
        mock_executor.set_response(
            "ip addr show eth0",
            return_code=0,
            stdout="inet 192.168.1.100/24",
        )
        mock_executor.set_response(
            "nmcli -t -f DEVICE,STATE,CONNECTION device",
            return_code=0,
            stdout="wlan1:disconnected:\n",
        )

        with patch("services.wan_service.InterfaceService") as mock_iface:
            mock_interfaces = MagicMock()
            mock_interfaces.ethernet = "eth0"
            mock_interfaces.wifi_wan = "wlan1"
            mock_iface.get_interfaces.return_value = mock_interfaces

            from services.wan_service import WANService

            result = WANService.is_connected()

            assert result is True

    def test_is_connected_with_wifi(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """is_connected should return True when WiFi is connected."""
        mock_executor.set_response(
            "ip addr show eth0",
            return_code=0,
            stdout="",  # No IP
        )
        mock_executor.set_response(
            "nmcli -t -f DEVICE,STATE,CONNECTION device",
            return_code=0,
            stdout="wlan1:connected:MyNetwork\n",
        )
        mock_executor.set_response(
            "ip addr show wlan1",
            return_code=0,
            stdout="inet 10.0.0.50/24",
        )

        with patch("services.wan_service.InterfaceService") as mock_iface:
            mock_interfaces = MagicMock()
            mock_interfaces.ethernet = "eth0"
            mock_interfaces.wifi_wan = "wlan1"
            mock_iface.get_interfaces.return_value = mock_interfaces

            from services.wan_service import WANService

            result = WANService.is_connected()

            assert result is True

    def test_is_connected_nothing_connected(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """is_connected should return False when nothing is connected."""
        mock_executor.set_response("ip addr show eth0", return_code=0, stdout="")
        mock_executor.set_response(
            "nmcli -t -f DEVICE,STATE,CONNECTION device",
            return_code=0,
            stdout="wlan1:disconnected:\n",
        )

        with patch("services.wan_service.InterfaceService") as mock_iface:
            mock_interfaces = MagicMock()
            mock_interfaces.ethernet = "eth0"
            mock_interfaces.wifi_wan = "wlan1"
            mock_iface.get_interfaces.return_value = mock_interfaces

            from services.wan_service import WANService

            result = WANService.is_connected()

            assert result is False
