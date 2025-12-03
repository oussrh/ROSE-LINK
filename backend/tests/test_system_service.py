"""
System Service Tests
====================

Unit tests for the system information service.

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from models import SystemInfo, InterfaceInfo, WiFiCapabilities
from services.system_service import SystemService
from tests.conftest import MockCommandExecutor


class TestSystemServiceGetInfo:
    """Tests for SystemService.get_info()."""

    def test_get_info_returns_system_info(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should return a SystemInfo object."""
        mock_executor.set_response("uname -m", return_code=0, stdout="aarch64\n")
        mock_executor.set_response("uname -r", return_code=0, stdout="6.1.0-rpi\n")
        mock_executor.set_response("free -m", return_code=0, stdout="Mem: 8000 4000 4000 0 0 0\n")
        mock_executor.set_response("df -BG /", return_code=0, stdout="Filesystem 32G 16G 16G 50% /\n")
        mock_executor.set_response("iw list", return_code=1, stdout="")
        mock_executor.set_response("ip -j addr show", return_code=0, stdout="[]")
        mock_executor.set_response("grep cpu ", return_code=1, stdout="")

        info = SystemService.get_info()

        assert isinstance(info, SystemInfo)

    def test_get_info_includes_architecture(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should include system architecture."""
        mock_executor.set_response("uname -m", return_code=0, stdout="aarch64\n")
        mock_executor.set_response("uname -r", return_code=1, stdout="")
        mock_executor.set_response("free -m", return_code=1, stdout="")
        mock_executor.set_response("df -BG /", return_code=1, stdout="")
        mock_executor.set_response("iw list", return_code=1, stdout="")
        mock_executor.set_response("ip -j addr show", return_code=0, stdout="[]")
        mock_executor.set_response("grep cpu ", return_code=1, stdout="")

        info = SystemService.get_info()

        assert info.architecture == "aarch64"


class TestSystemServiceModelInfo:
    """Tests for Raspberry Pi model detection."""

    def test_get_model_info_pi5(self, temp_dir: Path) -> None:
        """Should detect Raspberry Pi 5."""
        model_file = temp_dir / "model"
        model_file.write_text("Raspberry Pi 5 Model B Rev 1.0\x00")

        info = SystemInfo()

        with patch("services.system_service.Paths") as mock_paths:
            mock_paths.DEVICE_TREE_MODEL = model_file

            SystemService._get_model_info(info)

        assert info.model_short == "Pi 5"
        assert "Raspberry Pi 5" in info.model

    def test_get_model_info_pi4(self, temp_dir: Path) -> None:
        """Should detect Raspberry Pi 4."""
        model_file = temp_dir / "model"
        model_file.write_text("Raspberry Pi 4 Model B Rev 1.4\x00")

        info = SystemInfo()

        with patch("services.system_service.Paths") as mock_paths:
            mock_paths.DEVICE_TREE_MODEL = model_file

            SystemService._get_model_info(info)

        assert info.model_short == "Pi 4"

    def test_get_model_info_zero2w(self, temp_dir: Path) -> None:
        """Should detect Raspberry Pi Zero 2 W."""
        model_file = temp_dir / "model"
        model_file.write_text("Raspberry Pi Zero 2 W Rev 1.0\x00")

        info = SystemInfo()

        with patch("services.system_service.Paths") as mock_paths:
            mock_paths.DEVICE_TREE_MODEL = model_file

            SystemService._get_model_info(info)

        assert info.model_short == "Zero 2W"

    def test_get_model_info_missing_file(self, temp_dir: Path) -> None:
        """Should handle missing model file gracefully."""
        info = SystemInfo()

        with patch("services.system_service.Paths") as mock_paths:
            mock_paths.DEVICE_TREE_MODEL = temp_dir / "nonexistent"

            SystemService._get_model_info(info)

        # Model keeps default value ('unknown') when file is missing
        assert info.model == "unknown"


class TestSystemServiceMemoryInfo:
    """Tests for memory information parsing."""

    def test_get_memory_info_parses_ram(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should parse RAM from free output."""
        mock_executor.set_response(
            "free -m",
            return_code=0,
            stdout="              total        used        free      shared  buff/cache   available\n"
                   "Mem:           7815        1234        4000         100        2581        6200\n"
                   "Swap:           100          50          50\n"
        )

        info = SystemInfo()
        SystemService._get_memory_info(info)

        assert info.ram_mb == 7815
        assert info.ram_free_mb == 4000

    def test_get_memory_info_handles_failure(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should handle command failure gracefully."""
        mock_executor.set_response("free -m", return_code=1, stdout="")

        info = SystemInfo()
        SystemService._get_memory_info(info)

        # ram_mb keeps default value (0) when command fails
        assert info.ram_mb == 0


class TestSystemServiceDiskInfo:
    """Tests for disk information parsing."""

    def test_get_disk_info_parses_df(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should parse disk info from df output."""
        mock_executor.set_response(
            "df -BG /",
            return_code=0,
            stdout="Filesystem     1G-blocks  Used Available Use% Mounted on\n"
                   "/dev/mmcblk0p2       29G    8G       19G  30% /\n"
        )

        info = SystemInfo()
        SystemService._get_disk_info(info)

        assert info.disk_total_gb == 29
        assert info.disk_free_gb == 19


class TestSystemServiceCpuInfo:
    """Tests for CPU information parsing."""

    def test_get_cpu_info_reads_temperature(
        self, mock_executor: MockCommandExecutor, temp_dir: Path
    ) -> None:
        """Should read CPU temperature from thermal zone."""
        thermal_file = temp_dir / "temp"
        thermal_file.write_text("45000")  # 45°C in millidegrees

        info = SystemInfo()

        with patch("services.system_service.Paths") as mock_paths:
            mock_paths.THERMAL_ZONE = thermal_file
            mock_paths.PROC_STAT = temp_dir / "stat"

            mock_executor.set_response("grep cpu ", return_code=1)

            SystemService._get_cpu_info(info)

        assert info.cpu_temp_c == 45


class TestSystemServiceUptime:
    """Tests for uptime parsing."""

    def test_get_uptime_parses_seconds(self, temp_dir: Path) -> None:
        """Should parse uptime from /proc/uptime."""
        uptime_file = temp_dir / "uptime"
        uptime_file.write_text("12345.67 23456.78")

        info = SystemInfo()

        with patch("services.system_service.Paths") as mock_paths:
            mock_paths.PROC_UPTIME = uptime_file

            SystemService._get_uptime(info)

        assert info.uptime_seconds == 12345


class TestSystemServiceWifiCapabilities:
    """Tests for WiFi capability detection."""

    def test_get_wifi_capabilities_detects_5ghz(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should detect 5GHz support."""
        mock_executor.set_response(
            "iw list",
            return_code=0,
            stdout="Frequencies:\n\t* 2412 MHz\n\t* 5180 MHz\n\t* 5200 MHz\n"
        )

        info = SystemInfo()
        SystemService._get_wifi_capabilities(info)

        assert info.wifi_capabilities.supports_5ghz is True

    def test_get_wifi_capabilities_detects_ac(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should detect 802.11ac (VHT) support."""
        mock_executor.set_response(
            "iw list",
            return_code=0,
            stdout="VHT Capabilities:\n\tMax MPDU length: 11454\n"
        )

        info = SystemInfo()
        SystemService._get_wifi_capabilities(info)

        assert info.wifi_capabilities.supports_ac is True

    def test_get_wifi_capabilities_detects_ap_mode(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should detect AP mode support."""
        mock_executor.set_response(
            "iw list",
            return_code=0,
            stdout="Supported interface modes:\n\t* IBSS\n\t* managed\n\t* AP\n"
        )

        info = SystemInfo()
        SystemService._get_wifi_capabilities(info)

        assert info.wifi_capabilities.ap_mode is True


class TestSystemServiceGetInterfaces:
    """Tests for interface enumeration."""

    def test_get_interfaces_categorizes_correctly(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should categorize interfaces by type."""
        interfaces_json = json.dumps([
            {"ifname": "eth0", "operstate": "UP", "address": "aa:bb:cc:dd:ee:ff", "addr_info": []},
            {"ifname": "wlan0", "operstate": "UP", "address": "11:22:33:44:55:66", "addr_info": []},
            {"ifname": "wg0", "operstate": "UNKNOWN", "address": "00:00:00:00:00:00", "addr_info": []},
        ])

        mock_executor.set_response("ip -j addr show", return_code=0, stdout=interfaces_json)

        result = SystemService.get_interfaces()

        assert len(result["ethernet"]) == 1
        assert len(result["wifi"]) == 1
        assert len(result["vpn"]) == 1
        assert result["ethernet"][0].name == "eth0"
        assert result["wifi"][0].name == "wlan0"
        assert result["vpn"][0].name == "wg0"

    def test_get_interfaces_parses_ip_addresses(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should parse IP addresses from interface info."""
        interfaces_json = json.dumps([
            {
                "ifname": "eth0",
                "operstate": "UP",
                "address": "aa:bb:cc:dd:ee:ff",
                "addr_info": [
                    {"family": "inet", "local": "192.168.1.100"},
                    {"family": "inet6", "local": "fe80::1"},
                ]
            }
        ])

        mock_executor.set_response("ip -j addr show", return_code=0, stdout=interfaces_json)

        result = SystemService.get_interfaces()

        assert "192.168.1.100" in result["ethernet"][0].ip_addresses

    def test_get_interfaces_handles_empty_output(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should handle empty interface list."""
        mock_executor.set_response("ip -j addr show", return_code=0, stdout="[]")

        result = SystemService.get_interfaces()

        assert result["ethernet"] == []
        assert result["wifi"] == []
        assert result["vpn"] == []


class TestSystemServiceGetLogs:
    """Tests for service log retrieval."""

    def test_get_logs_returns_log_content(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should return log content from journalctl."""
        expected_logs = "Nov 25 10:00:00 roselink hostapd[123]: Station connected\n"
        mock_executor.set_response("sudo journalctl", return_code=0, stdout=expected_logs)

        logs = SystemService.get_logs("hostapd", lines=50)

        assert "Station connected" in logs


class TestSystemServiceReboot:
    """Tests for system reboot."""

    def test_reboot_calls_reboot_command(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should call the reboot command."""
        mock_executor.set_response("sudo reboot", return_code=0)

        result = SystemService.reboot()

        # Check that reboot was called
        reboot_calls = [c for c in mock_executor.calls if "reboot" in " ".join(c[0])]
        assert len(reboot_calls) > 0
