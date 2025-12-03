"""
Interface Service Tests
=======================

Unit tests for the network interface service.

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from services.interface_service import (
    InterfaceService,
    get_interface_config,
    detect_ap_interface,
)
from models import NetworkInterfaces


class TestInterfaceServiceGetInterfaces:
    """Tests for get_interfaces method."""

    def test_returns_network_interfaces_object(self, temp_dir: Path) -> None:
        """Should return NetworkInterfaces dataclass."""
        sys_net = temp_dir / "sys" / "class" / "net"
        sys_net.mkdir(parents=True)

        with patch("services.interface_service.Paths") as mock_paths:
            mock_paths.INTERFACES_CONF = temp_dir / "nonexistent.conf"
            mock_paths.SYS_NET = sys_net

            InterfaceService.clear_cache()
            result = InterfaceService.get_interfaces()

        assert isinstance(result, NetworkInterfaces)

    def test_uses_cache_by_default(self, temp_dir: Path) -> None:
        """Should use cached value on subsequent calls."""
        cached = NetworkInterfaces(
            ethernet="cached_eth",
            wifi_ap="cached_ap",
            wifi_wan="cached_wan",
        )
        InterfaceService._cache = cached

        result = InterfaceService.get_interfaces(use_cache=True)

        assert result.ethernet == "cached_eth"

        # Clean up
        InterfaceService.clear_cache()

    def test_bypasses_cache_when_requested(self, temp_dir: Path) -> None:
        """Should bypass cache when use_cache=False."""
        sys_net = temp_dir / "sys" / "class" / "net"
        sys_net.mkdir(parents=True)
        (sys_net / "eth0").mkdir()

        # Set stale cache
        InterfaceService._cache = NetworkInterfaces(ethernet="stale")

        with patch("services.interface_service.Paths") as mock_paths:
            mock_paths.INTERFACES_CONF = temp_dir / "nonexistent.conf"
            mock_paths.SYS_NET = sys_net

            result = InterfaceService.get_interfaces(use_cache=False)

        assert result.ethernet == "eth0"

        # Clean up
        InterfaceService.clear_cache()


class TestInterfaceServiceLoadFromConfig:
    """Tests for _load_from_config method."""

    def test_loads_from_config_file(self, temp_dir: Path) -> None:
        """Should load interface names from config file."""
        config_file = temp_dir / "interfaces.conf"
        config_file.write_text("""
ETH_INTERFACE=eth0
WIFI_WAN_INTERFACE=wlan1
WIFI_AP_INTERFACE=wlan0
""")

        with patch("services.interface_service.Paths") as mock_paths:
            mock_paths.INTERFACES_CONF = config_file

            result = InterfaceService._load_from_config()

        assert result is not None
        assert result.ethernet == "eth0"
        assert result.wifi_wan == "wlan1"
        assert result.wifi_ap == "wlan0"

    def test_handles_quoted_values(self, temp_dir: Path) -> None:
        """Should handle quoted values in config."""
        config_file = temp_dir / "interfaces.conf"
        config_file.write_text('ETH_INTERFACE="eth0"')

        with patch("services.interface_service.Paths") as mock_paths:
            mock_paths.INTERFACES_CONF = config_file

            result = InterfaceService._load_from_config()

        assert result is not None
        assert result.ethernet == "eth0"

    def test_skips_comments(self, temp_dir: Path) -> None:
        """Should skip comment lines."""
        config_file = temp_dir / "interfaces.conf"
        config_file.write_text("""
# This is a comment
ETH_INTERFACE=eth0
# Another comment
WIFI_AP_INTERFACE=wlan0
""")

        with patch("services.interface_service.Paths") as mock_paths:
            mock_paths.INTERFACES_CONF = config_file

            result = InterfaceService._load_from_config()

        assert result is not None
        assert result.ethernet == "eth0"

    def test_returns_none_when_no_config(self, temp_dir: Path) -> None:
        """Should return None when config file doesn't exist."""
        with patch("services.interface_service.Paths") as mock_paths:
            mock_paths.INTERFACES_CONF = temp_dir / "nonexistent.conf"

            result = InterfaceService._load_from_config()

        assert result is None

    def test_handles_empty_values(self, temp_dir: Path) -> None:
        """Should skip empty values in config."""
        config_file = temp_dir / "interfaces.conf"
        config_file.write_text("""
ETH_INTERFACE=eth0
WIFI_WAN_INTERFACE=
""")

        with patch("services.interface_service.Paths") as mock_paths:
            mock_paths.INTERFACES_CONF = config_file

            result = InterfaceService._load_from_config()

        assert result is not None
        assert result.ethernet == "eth0"
        # wifi_wan should be default since value was empty


class TestInterfaceServiceAutoDetect:
    """Tests for _auto_detect method."""

    def test_detects_eth0(self, temp_dir: Path) -> None:
        """Should detect eth0 interface."""
        sys_net = temp_dir / "sys" / "class" / "net"
        sys_net.mkdir(parents=True)
        (sys_net / "eth0").mkdir()

        with patch("services.interface_service.Paths") as mock_paths:
            mock_paths.SYS_NET = sys_net

            with patch("services.interface_service.Network") as mock_network:
                mock_network.ALT_ETH_INTERFACES = ("eth0", "end0")

                result = InterfaceService._auto_detect()

        assert result.ethernet == "eth0"

    def test_detects_end0_for_pi5(self, temp_dir: Path) -> None:
        """Should detect end0 interface for Pi 5."""
        sys_net = temp_dir / "sys" / "class" / "net"
        sys_net.mkdir(parents=True)
        (sys_net / "end0").mkdir()

        with patch("services.interface_service.Paths") as mock_paths:
            mock_paths.SYS_NET = sys_net

            with patch("services.interface_service.Network") as mock_network:
                mock_network.ALT_ETH_INTERFACES = ("eth0", "end0")

                result = InterfaceService._auto_detect()

        assert result.ethernet == "end0"

    def test_detects_wifi_interfaces(self, temp_dir: Path) -> None:
        """Should detect WiFi interfaces."""
        sys_net = temp_dir / "sys" / "class" / "net"
        sys_net.mkdir(parents=True)
        (sys_net / "wlan0").mkdir()
        (sys_net / "wlan0" / "wireless").mkdir()

        with patch("services.interface_service.Paths") as mock_paths:
            mock_paths.SYS_NET = sys_net

            with patch("services.interface_service.Network") as mock_network:
                mock_network.ALT_ETH_INTERFACES = ()

                result = InterfaceService._auto_detect()

        assert result.wifi_ap == "wlan0"
        assert result.wifi_wan == "wlan0"

    def test_detects_multiple_wifi_interfaces(self, temp_dir: Path) -> None:
        """Should detect multiple WiFi interfaces."""
        sys_net = temp_dir / "sys" / "class" / "net"
        sys_net.mkdir(parents=True)
        (sys_net / "wlan0").mkdir()
        (sys_net / "wlan0" / "wireless").mkdir()
        (sys_net / "wlan1").mkdir()
        (sys_net / "wlan1" / "wireless").mkdir()

        with patch("services.interface_service.Paths") as mock_paths:
            mock_paths.SYS_NET = sys_net

            with patch("services.interface_service.Network") as mock_network:
                mock_network.ALT_ETH_INTERFACES = ()

                result = InterfaceService._auto_detect()

        # First interface for AP, second for WAN
        assert result.wifi_ap == "wlan0"
        assert result.wifi_wan == "wlan1"


class TestInterfaceServiceClearCache:
    """Tests for clear_cache method."""

    def test_clears_cache(self) -> None:
        """Should clear the cache."""
        InterfaceService._cache = NetworkInterfaces(ethernet="test")

        InterfaceService.clear_cache()

        assert InterfaceService._cache is None


class TestInterfaceServiceInterfaceExists:
    """Tests for _interface_exists method."""

    def test_returns_true_for_existing_interface(self, temp_dir: Path) -> None:
        """Should return True for existing interface."""
        sys_net = temp_dir / "sys" / "class" / "net"
        (sys_net / "eth0").mkdir(parents=True)

        with patch("services.interface_service.Paths") as mock_paths:
            mock_paths.SYS_NET = sys_net

            result = InterfaceService._interface_exists("eth0")

        assert result is True

    def test_returns_false_for_missing_interface(self, temp_dir: Path) -> None:
        """Should return False for missing interface."""
        sys_net = temp_dir / "sys" / "class" / "net"
        sys_net.mkdir(parents=True)

        with patch("services.interface_service.Paths") as mock_paths:
            mock_paths.SYS_NET = sys_net

            result = InterfaceService._interface_exists("eth99")

        assert result is False


class TestInterfaceServiceDetectWifiInterfaces:
    """Tests for _detect_wifi_interfaces method."""

    def test_detects_wifi_interfaces(self, temp_dir: Path) -> None:
        """Should detect all wireless interfaces."""
        sys_net = temp_dir / "sys" / "class" / "net"
        sys_net.mkdir(parents=True)

        # Create wlan0 with wireless subdir
        (sys_net / "wlan0").mkdir()
        (sys_net / "wlan0" / "wireless").mkdir()

        # Create eth0 without wireless subdir
        (sys_net / "eth0").mkdir()

        with patch("services.interface_service.Paths") as mock_paths:
            mock_paths.SYS_NET = sys_net

            result = InterfaceService._detect_wifi_interfaces()

        assert "wlan0" in result
        assert "eth0" not in result

    def test_returns_empty_list_when_no_wifi(self, temp_dir: Path) -> None:
        """Should return empty list when no WiFi interfaces."""
        sys_net = temp_dir / "sys" / "class" / "net"
        sys_net.mkdir(parents=True)
        (sys_net / "eth0").mkdir()

        with patch("services.interface_service.Paths") as mock_paths:
            mock_paths.SYS_NET = sys_net

            result = InterfaceService._detect_wifi_interfaces()

        assert result == []


class TestInterfaceServiceIsInterfaceUp:
    """Tests for is_interface_up method."""

    def test_returns_true_when_up(self, temp_dir: Path) -> None:
        """Should return True when interface is up."""
        sys_net = temp_dir / "sys" / "class" / "net"
        (sys_net / "eth0").mkdir(parents=True)
        (sys_net / "eth0" / "operstate").write_text("up")

        with patch("services.interface_service.Paths") as mock_paths:
            mock_paths.SYS_NET = sys_net

            result = InterfaceService.is_interface_up("eth0")

        assert result is True

    def test_returns_true_for_unknown_state(self, temp_dir: Path) -> None:
        """Should return True for 'unknown' state."""
        sys_net = temp_dir / "sys" / "class" / "net"
        (sys_net / "eth0").mkdir(parents=True)
        (sys_net / "eth0" / "operstate").write_text("unknown")

        with patch("services.interface_service.Paths") as mock_paths:
            mock_paths.SYS_NET = sys_net

            result = InterfaceService.is_interface_up("eth0")

        assert result is True

    def test_returns_false_when_down(self, temp_dir: Path) -> None:
        """Should return False when interface is down."""
        sys_net = temp_dir / "sys" / "class" / "net"
        (sys_net / "eth0").mkdir(parents=True)
        (sys_net / "eth0" / "operstate").write_text("down")

        with patch("services.interface_service.Paths") as mock_paths:
            mock_paths.SYS_NET = sys_net

            result = InterfaceService.is_interface_up("eth0")

        assert result is False

    def test_returns_false_when_interface_missing(self, temp_dir: Path) -> None:
        """Should return False when interface doesn't exist."""
        sys_net = temp_dir / "sys" / "class" / "net"
        sys_net.mkdir(parents=True)

        with patch("services.interface_service.Paths") as mock_paths:
            mock_paths.SYS_NET = sys_net

            result = InterfaceService.is_interface_up("eth99")

        assert result is False


class TestGetInterfaceConfig:
    """Tests for get_interface_config convenience function."""

    def test_returns_dictionary(self, temp_dir: Path) -> None:
        """Should return dictionary with interface config."""
        sys_net = temp_dir / "sys" / "class" / "net"
        sys_net.mkdir(parents=True)
        (sys_net / "eth0").mkdir()

        with patch("services.interface_service.Paths") as mock_paths:
            mock_paths.INTERFACES_CONF = temp_dir / "nonexistent.conf"
            mock_paths.SYS_NET = sys_net

            with patch("services.interface_service.Network") as mock_network:
                mock_network.ALT_ETH_INTERFACES = ("eth0",)

                InterfaceService.clear_cache()
                result = get_interface_config()

        assert isinstance(result, dict)
        assert "eth" in result
        assert "wifi_wan" in result
        assert "wifi_ap" in result


class TestDetectApInterface:
    """Tests for detect_ap_interface convenience function."""

    def test_returns_ap_interface(self, temp_dir: Path) -> None:
        """Should return AP interface name."""
        sys_net = temp_dir / "sys" / "class" / "net"
        sys_net.mkdir(parents=True)
        (sys_net / "wlan0").mkdir()
        (sys_net / "wlan0" / "wireless").mkdir()

        with patch("services.interface_service.Paths") as mock_paths:
            mock_paths.INTERFACES_CONF = temp_dir / "nonexistent.conf"
            mock_paths.SYS_NET = sys_net

            with patch("services.interface_service.Network") as mock_network:
                mock_network.ALT_ETH_INTERFACES = ()

                InterfaceService.clear_cache()
                result = detect_ap_interface()

        assert result == "wlan0"

    def test_returns_none_when_no_ap_interface(self, temp_dir: Path) -> None:
        """Should return None when no AP interface found."""
        sys_net = temp_dir / "sys" / "class" / "net"
        sys_net.mkdir(parents=True)

        with patch("services.interface_service.Paths") as mock_paths:
            mock_paths.INTERFACES_CONF = temp_dir / "nonexistent.conf"
            mock_paths.SYS_NET = sys_net

            with patch("services.interface_service.Network") as mock_network:
                mock_network.ALT_ETH_INTERFACES = ()

                InterfaceService.clear_cache()
                result = detect_ap_interface()

        assert result is None
