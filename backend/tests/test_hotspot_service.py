"""
Hotspot Service Tests
=====================

Unit tests for the WiFi hotspot service.

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from models import HotspotStatus, HotspotClient, HotspotConfig
from services.hotspot_service import HotspotService
from tests.conftest import MockCommandExecutor


class TestHotspotServiceGetStatus:
    """Tests for HotspotService.get_status()."""

    def test_get_status_returns_inactive_when_hostapd_not_running(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should return inactive status when hostapd is not running."""
        mock_executor.set_response("systemctl is-active hostapd", return_code=1)
        mock_executor.set_response("ip -j addr show", return_code=0, stdout="[]")

        status = HotspotService.get_status()

        assert status.active is False

    def test_get_status_returns_active_when_hostapd_running(
        self, mock_executor: MockCommandExecutor, temp_dir: Path
    ) -> None:
        """Should return active status when hostapd is running."""
        mock_executor.set_response("systemctl is-active hostapd", return_code=0, stdout="active\n")
        mock_executor.set_response("ip -j addr show", return_code=0, stdout="[]")
        mock_executor.set_response("sudo iw dev", return_code=1, stdout="")

        # Create a mock hostapd.conf
        hostapd_conf = temp_dir / "hostapd.conf"
        hostapd_conf.write_text("ssid=TestNetwork\nchannel=6\nhw_mode=g\n")

        with patch("services.hotspot_service.Paths") as mock_paths:
            mock_paths.HOSTAPD_CONF = hostapd_conf

            status = HotspotService.get_status()

        assert status.active is True

    def test_get_status_parses_ssid_from_config(
        self, mock_executor: MockCommandExecutor, temp_dir: Path
    ) -> None:
        """Should parse SSID from hostapd configuration."""
        mock_executor.set_response("systemctl is-active hostapd", return_code=0, stdout="active\n")
        mock_executor.set_response("ip -j addr show", return_code=0, stdout="[]")
        mock_executor.set_response("sudo iw dev", return_code=1, stdout="")

        hostapd_conf = temp_dir / "hostapd.conf"
        hostapd_conf.write_text("ssid=MyHotspot\nchannel=11\nhw_mode=g\n")

        with patch("services.hotspot_service.Paths") as mock_paths:
            mock_paths.HOSTAPD_CONF = hostapd_conf

            status = HotspotService.get_status()

        assert status.ssid == "MyHotspot"

    def test_get_status_parses_channel_from_config(
        self, mock_executor: MockCommandExecutor, temp_dir: Path
    ) -> None:
        """Should parse channel from hostapd configuration."""
        mock_executor.set_response("systemctl is-active hostapd", return_code=0, stdout="active\n")
        mock_executor.set_response("ip -j addr show", return_code=0, stdout="[]")
        mock_executor.set_response("sudo iw dev", return_code=1, stdout="")

        hostapd_conf = temp_dir / "hostapd.conf"
        hostapd_conf.write_text("ssid=TestNet\nchannel=11\nhw_mode=g\n")

        with patch("services.hotspot_service.Paths") as mock_paths:
            mock_paths.HOSTAPD_CONF = hostapd_conf

            status = HotspotService.get_status()

        assert status.channel == 11

    def test_get_status_detects_5ghz_mode(
        self, mock_executor: MockCommandExecutor, temp_dir: Path
    ) -> None:
        """Should detect 5GHz mode from hw_mode=a."""
        mock_executor.set_response("systemctl is-active hostapd", return_code=0, stdout="active\n")
        mock_executor.set_response("ip -j addr show", return_code=0, stdout="[]")
        mock_executor.set_response("sudo iw dev", return_code=1, stdout="")

        hostapd_conf = temp_dir / "hostapd.conf"
        hostapd_conf.write_text("ssid=5GHz-Net\nchannel=36\nhw_mode=a\n")

        with patch("services.hotspot_service.Paths") as mock_paths:
            mock_paths.HOSTAPD_CONF = hostapd_conf

            status = HotspotService.get_status()

        assert status.hw_mode == "a"
        assert status.frequency == "5GHz"


class TestHotspotServiceParseStationDump:
    """Tests for station dump parsing."""

    def test_parse_station_dump_empty_output(self) -> None:
        """Should return empty list for empty output."""
        clients = HotspotService._parse_station_dump("")

        assert clients == []

    def test_parse_station_dump_single_client(self) -> None:
        """Should parse single client."""
        output = """Station aa:bb:cc:dd:ee:ff (on wlan0)
	inactive time:	1234 ms
	rx bytes:	12345
	tx bytes:	67890
	signal:		-45 dBm"""

        clients = HotspotService._parse_station_dump(output)

        assert len(clients) == 1
        assert clients[0].mac == "aa:bb:cc:dd:ee:ff"
        assert clients[0].signal == "-45 dBm"
        assert clients[0].rx_bytes == 12345
        assert clients[0].tx_bytes == 67890

    def test_parse_station_dump_multiple_clients(self) -> None:
        """Should parse multiple clients."""
        output = """Station 11:22:33:44:55:66 (on wlan0)
	signal:		-30 dBm
Station aa:bb:cc:dd:ee:ff (on wlan0)
	signal:		-50 dBm"""

        clients = HotspotService._parse_station_dump(output)

        assert len(clients) == 2
        assert clients[0].mac == "11:22:33:44:55:66"
        assert clients[1].mac == "aa:bb:cc:dd:ee:ff"


class TestHotspotServiceEnrichWithDhcpInfo:
    """Tests for DHCP lease enrichment."""

    def test_enrich_with_dhcp_info_no_leases_file(self, temp_dir: Path) -> None:
        """Should handle missing leases file gracefully."""
        clients = [HotspotClient(mac="aa:bb:cc:dd:ee:ff")]

        with patch("services.hotspot_service.Paths") as mock_paths:
            mock_paths.DNSMASQ_LEASES = temp_dir / "nonexistent"

            HotspotService._enrich_with_dhcp_info(clients)

        # Should not raise, client unchanged
        assert clients[0].ip is None

    def test_enrich_with_dhcp_info_matches_mac(self, temp_dir: Path) -> None:
        """Should match and enrich client by MAC address."""
        leases_file = temp_dir / "dnsmasq.leases"
        leases_file.write_text("1234567890 aa:bb:cc:dd:ee:ff 192.168.50.100 TestDevice *\n")

        clients = [HotspotClient(mac="aa:bb:cc:dd:ee:ff")]

        with patch("services.hotspot_service.Paths") as mock_paths:
            mock_paths.DNSMASQ_LEASES = leases_file

            HotspotService._enrich_with_dhcp_info(clients)

        assert clients[0].ip == "192.168.50.100"
        assert clients[0].hostname == "TestDevice"


class TestHotspotServiceGenerateConfig:
    """Tests for hostapd config generation."""

    def test_generate_hostapd_config_2ghz(self) -> None:
        """Should generate valid 2.4GHz configuration."""
        config = HotspotService._generate_hostapd_config(
            interface="wlan0",
            ssid="TestNet",
            password="securepass123",
            country="US",
            channel=6,
            band="2.4GHz",
            wpa3=False,
        )

        assert "interface=wlan0" in config
        assert "ssid=TestNet" in config
        assert "hw_mode=g" in config
        assert "channel=6" in config
        assert "country_code=US" in config
        assert "wpa_passphrase=securepass123" in config

    def test_generate_hostapd_config_5ghz(self) -> None:
        """Should generate valid 5GHz configuration."""
        config = HotspotService._generate_hostapd_config(
            interface="wlan0",
            ssid="FastNet",
            password="securepass123",
            country="US",
            channel=36,
            band="5GHz",
            wpa3=False,
        )

        assert "hw_mode=a" in config
        assert "channel=36" in config
        assert "ieee80211ac=1" in config

    def test_generate_hostapd_config_wpa3(self) -> None:
        """Should include WPA3 configuration when enabled."""
        config = HotspotService._generate_hostapd_config(
            interface="wlan0",
            ssid="SecureNet",
            password="securepass123",
            country="US",
            channel=6,
            band="2.4GHz",
            wpa3=True,
        )

        assert "SAE" in config
        assert "ieee80211w=1" in config


class TestHotspotServiceIsActive:
    """Tests for is_active() quick check."""

    def test_is_active_returns_true_when_running(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should return True when hostapd is active."""
        mock_executor.set_response("systemctl is-active hostapd", return_code=0, stdout="active\n")

        result = HotspotService.is_active()

        assert result is True

    def test_is_active_returns_false_when_not_running(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should return False when hostapd is not active."""
        mock_executor.set_response("systemctl is-active hostapd", return_code=3, stdout="inactive\n")

        result = HotspotService.is_active()

        assert result is False
