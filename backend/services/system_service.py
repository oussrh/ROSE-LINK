"""
System Service
==============

Handles system information gathering and monitoring.

Features:
- Raspberry Pi model detection
- Resource monitoring (CPU, RAM, disk, temperature)
- Network interface enumeration
- WiFi capability detection
- Service log retrieval
- System reboot

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Optional

from config import Paths, Services, Limits
from models import (
    SystemInfo,
    NetworkInterfaces,
    WiFiCapabilities,
    InterfaceInfo,
)
from utils.command_runner import run_command, CommandRunner
from utils.sanitizers import sanitize_service_name
from services.interface_service import InterfaceService

logger = logging.getLogger("rose-link.system")


class SystemService:
    """
    Service for system information and monitoring.

    This service provides comprehensive system information including
    hardware details, resource usage, and network configuration.
    """

    @classmethod
    def get_info(cls) -> SystemInfo:
        """
        Get comprehensive system information.

        Gathers information about:
        - Raspberry Pi model
        - System resources (RAM, disk)
        - Performance metrics (CPU temp, usage, uptime)
        - Software versions
        - Network interfaces
        - WiFi capabilities

        Returns:
            SystemInfo with all available system data
        """
        info = SystemInfo()

        # Gather information from various sources
        cls._get_model_info(info)
        cls._get_architecture(info)
        cls._get_software_versions(info)
        cls._get_memory_info(info)
        cls._get_disk_info(info)
        cls._get_cpu_info(info)
        cls._get_uptime(info)
        cls._get_interface_config(info)
        cls._get_wifi_capabilities(info)

        return info

    @classmethod
    def _get_model_info(cls, info: SystemInfo) -> None:
        """Get Raspberry Pi model information."""
        if not Paths.DEVICE_TREE_MODEL.exists():
            return

        try:
            model = Paths.DEVICE_TREE_MODEL.read_text().strip("\x00")
            info.model = model

            # Extract short model name
            if "Raspberry Pi 5" in model:
                info.model_short = "Pi 5"
            elif "Raspberry Pi 4" in model:
                info.model_short = "Pi 4"
            elif "Raspberry Pi 3" in model:
                info.model_short = "Pi 3"
            elif "Raspberry Pi Zero 2" in model:
                info.model_short = "Zero 2W"
            elif "Raspberry Pi" in model:
                info.model_short = "Pi"

        except (IOError, OSError) as e:
            logger.debug(f"Could not read model info: {e}")

    @classmethod
    def _get_architecture(cls, info: SystemInfo) -> None:
        """Get system architecture."""
        ret, out, _ = run_command(["uname", "-m"], check=False)
        if ret == 0:
            info.architecture = out.strip()

    @classmethod
    def _get_software_versions(cls, info: SystemInfo) -> None:
        """Get kernel and OS versions."""
        # Kernel version
        ret, out, _ = run_command(["uname", "-r"], check=False)
        if ret == 0:
            info.kernel_version = out.strip()

        # OS version
        if Paths.OS_RELEASE.exists():
            try:
                with open(Paths.OS_RELEASE, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("PRETTY_NAME="):
                            info.os_version = line.split("=", 1)[1].strip().strip('"')
                            break
            except (IOError, OSError):
                pass

    @classmethod
    def _get_memory_info(cls, info: SystemInfo) -> None:
        """Get RAM information."""
        ret, out, _ = run_command(["free", "-m"], check=False)
        if ret != 0:
            return

        for line in out.splitlines():
            if line.startswith("Mem:"):
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        info.ram_mb = int(parts[1])
                        info.ram_free_mb = int(parts[3])
                    except ValueError:
                        pass
                break

    @classmethod
    def _get_disk_info(cls, info: SystemInfo) -> None:
        """Get disk usage information."""
        ret, out, _ = run_command(["df", "-BG", "/"], check=False)
        if ret != 0:
            return

        lines = out.strip().split("\n")
        if len(lines) >= 2:
            parts = lines[1].split()
            if len(parts) >= 4:
                try:
                    info.disk_total_gb = int(parts[1].rstrip("G"))
                    info.disk_free_gb = int(parts[3].rstrip("G"))
                except ValueError:
                    pass

    @classmethod
    def _get_cpu_info(cls, info: SystemInfo) -> None:
        """Get CPU temperature and usage."""
        # Temperature
        if Paths.THERMAL_ZONE.exists():
            try:
                temp = int(Paths.THERMAL_ZONE.read_text().strip())
                info.cpu_temp_c = temp // 1000
            except (IOError, OSError, ValueError):
                pass

        # CPU usage (simple calculation)
        ret, out, _ = run_command(["grep", "cpu ", str(Paths.PROC_STAT)], check=False)
        if ret == 0:
            parts = out.split()
            if len(parts) >= 5:
                try:
                    idle = int(parts[4])
                    total = sum(int(x) for x in parts[1:])
                    if total > 0:
                        info.cpu_usage_percent = round(100 * (1 - idle / total), 1)
                except (ValueError, IndexError):
                    pass

    @classmethod
    def _get_uptime(cls, info: SystemInfo) -> None:
        """Get system uptime."""
        if Paths.PROC_UPTIME.exists():
            try:
                content = Paths.PROC_UPTIME.read_text()
                info.uptime_seconds = int(float(content.split()[0]))
            except (IOError, OSError, ValueError, IndexError):
                pass

    @classmethod
    def _get_interface_config(cls, info: SystemInfo) -> None:
        """Get configured network interfaces."""
        interfaces = InterfaceService.get_interfaces()
        info.interfaces = interfaces

    @classmethod
    def _get_wifi_capabilities(cls, info: SystemInfo) -> None:
        """Detect WiFi hardware capabilities."""
        ret, out, _ = run_command(["iw", "list"], check=False)
        if ret != 0:
            return

        caps = WiFiCapabilities()

        # Check for 5GHz support (look for 5xxx MHz frequencies)
        if re.search(r"5[0-9]{3} MHz", out):
            caps.supports_5ghz = True

        # Check for 802.11ac (VHT)
        if "VHT" in out:
            caps.supports_ac = True

        # Check for 802.11ax (HE)
        if "HE" in out:
            caps.supports_ax = True

        # Check for AP mode support
        if "* AP" in out:
            caps.ap_mode = True

        info.wifi_capabilities = caps

    # =========================================================================
    # Interface Enumeration
    # =========================================================================

    @classmethod
    def get_interfaces(cls) -> dict[str, list[InterfaceInfo]]:
        """
        Get detailed information about all network interfaces.

        Returns:
            Dictionary with 'ethernet', 'wifi', and 'vpn' lists
        """
        result: dict[str, list[InterfaceInfo]] = {
            "ethernet": [],
            "wifi": [],
            "vpn": [],
        }

        # Get interface information using JSON output
        ret, out, _ = run_command(["ip", "-j", "addr", "show"], check=False)
        if ret != 0:
            return result

        try:
            interfaces = json.loads(out)
        except json.JSONDecodeError:
            return result

        for iface in interfaces:
            info = cls._parse_interface_info(iface)

            if info is None:
                continue

            # Categorize by name prefix
            name = info.name
            if name.startswith(("eth", "end", "enp")):
                result["ethernet"].append(info)
            elif name.startswith(("wlan", "wlp")):
                # Add WiFi-specific info
                info.type = InterfaceService.get_interface_type(name)
                info.driver = InterfaceService.get_interface_driver(name)
                result["wifi"].append(info)
            elif name.startswith("wg"):
                result["vpn"].append(info)

        return result

    @classmethod
    def _parse_interface_info(cls, data: dict) -> Optional[InterfaceInfo]:
        """
        Parse interface information from ip JSON output.

        Args:
            data: Dictionary from 'ip -j addr show' output

        Returns:
            InterfaceInfo or None if parsing fails
        """
        name = data.get("ifname")
        if not name:
            return None

        info = InterfaceInfo(
            name=name,
            state=data.get("operstate", "unknown").lower(),
            mac=data.get("address", ""),
        )

        # Extract IPv4 addresses
        for addr_info in data.get("addr_info", []):
            if addr_info.get("family") == "inet":
                ip = addr_info.get("local")
                if ip:
                    info.ip_addresses.append(ip)

        return info

    # =========================================================================
    # Service Logs
    # =========================================================================

    @classmethod
    def get_logs(cls, service: str, lines: int = Limits.DEFAULT_LOG_LINES) -> str:
        """
        Get systemd journal logs for a service.

        Args:
            service: Service name (must be in allowed list)
            lines: Number of log lines to retrieve

        Returns:
            Log content as string

        Raises:
            ValueError: If service is not in allowed list
        """
        # Validate service name
        sanitize_service_name(service, Services.VALID_LOG_SERVICES)

        ret, out, _ = CommandRunner.get_journalctl_logs(service, lines)

        return out

    # =========================================================================
    # System Control
    # =========================================================================

    @classmethod
    def reboot(cls) -> bool:
        """
        Initiate system reboot.

        Returns:
            True if reboot command was issued
        """
        logger.info("System reboot requested")
        return CommandRunner.reboot()
