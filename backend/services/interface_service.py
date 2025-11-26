"""
Network Interface Service
=========================

Handles network interface detection and configuration.

This service manages:
- Auto-detection of ethernet and WiFi interfaces
- Loading interface configuration from config file
- Caching interface information for performance

Raspberry Pi Interface Naming:
- Pi 3/4: eth0, wlan0 (built-in), wlan1 (USB adapter)
- Pi 5: end0 (ethernet), wlan0
- Zero 2W: wlan0 (built-in only)

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from config import Paths, Network
from models import NetworkInterfaces

logger = logging.getLogger("rose-link.interfaces")


class InterfaceService:
    """
    Service for network interface management.

    This class provides methods to detect and configure network interfaces
    on different Raspberry Pi models.

    The interface configuration can be either:
    1. Auto-detected from the system
    2. Loaded from a configuration file

    Attributes:
        _cache: Cached interface configuration
        _cache_time: When the cache was last updated
    """

    _cache: Optional[NetworkInterfaces] = None

    @classmethod
    def get_interfaces(cls, use_cache: bool = True) -> NetworkInterfaces:
        """
        Get configured network interface names.

        First attempts to load from config file, then falls back
        to auto-detection.

        Args:
            use_cache: Whether to use cached values (default: True)

        Returns:
            NetworkInterfaces dataclass with interface names
        """
        if use_cache and cls._cache is not None:
            return cls._cache

        # Try loading from config file
        interfaces = cls._load_from_config()

        # Fall back to auto-detection if config doesn't exist
        if interfaces is None:
            interfaces = cls._auto_detect()

        # Cache the result
        cls._cache = interfaces

        return interfaces

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the interface cache to force re-detection."""
        cls._cache = None
        logger.debug("Interface cache cleared")

    @classmethod
    def _load_from_config(cls) -> Optional[NetworkInterfaces]:
        """
        Load interface configuration from config file.

        The config file uses a simple key=value format:
            ETH_INTERFACE=eth0
            WIFI_WAN_INTERFACE=wlan1
            WIFI_AP_INTERFACE=wlan0

        Returns:
            NetworkInterfaces if config exists and is valid, None otherwise
        """
        if not Paths.INTERFACES_CONF.exists():
            logger.debug("Interface config file not found, will auto-detect")
            return None

        try:
            interfaces = NetworkInterfaces()

            with open(Paths.INTERFACES_CONF, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()

                    # Skip comments and empty lines
                    if line.startswith("#") or "=" not in line:
                        continue

                    key, value = line.split("=", 1)
                    key = key.strip().upper()
                    value = value.strip().strip('"')

                    if not value:
                        continue

                    if key == "ETH_INTERFACE":
                        interfaces.ethernet = value
                    elif key == "WIFI_WAN_INTERFACE":
                        interfaces.wifi_wan = value
                    elif key == "WIFI_AP_INTERFACE":
                        interfaces.wifi_ap = value

            logger.info(
                f"Loaded interfaces from config: eth={interfaces.ethernet}, "
                f"ap={interfaces.wifi_ap}, wan={interfaces.wifi_wan}"
            )
            return interfaces

        except (IOError, OSError, ValueError) as e:
            logger.warning(f"Error reading interface config: {e}")
            return None

    @classmethod
    def _auto_detect(cls) -> NetworkInterfaces:
        """
        Auto-detect network interfaces.

        Detection logic:
        1. Ethernet: Check for eth0, end0 (Pi 5), enp1s0
        2. WiFi: Find all wireless interfaces, use first for AP
                 and second (if exists) for WAN

        Returns:
            NetworkInterfaces with detected interface names
        """
        interfaces = NetworkInterfaces()

        # Detect Ethernet interface
        # Pi 5 uses 'end0' instead of 'eth0'
        for iface in Network.ALT_ETH_INTERFACES:
            if cls._interface_exists(iface):
                interfaces.ethernet = iface
                logger.debug(f"Detected ethernet interface: {iface}")
                break

        # Detect WiFi interfaces
        wifi_ifaces = cls._detect_wifi_interfaces()

        if wifi_ifaces:
            # Sort for consistent ordering
            wifi_ifaces.sort()

            # First WiFi interface is used for AP
            interfaces.wifi_ap = wifi_ifaces[0]

            # If second WiFi exists, use it for WAN
            # Otherwise, same interface handles both
            if len(wifi_ifaces) > 1:
                interfaces.wifi_wan = wifi_ifaces[1]
            else:
                interfaces.wifi_wan = wifi_ifaces[0]

            logger.debug(
                f"Detected WiFi interfaces: {wifi_ifaces}, "
                f"AP={interfaces.wifi_ap}, WAN={interfaces.wifi_wan}"
            )

        logger.info(
            f"Auto-detected interfaces: eth={interfaces.ethernet}, "
            f"ap={interfaces.wifi_ap}, wan={interfaces.wifi_wan}"
        )

        return interfaces

    @classmethod
    def _interface_exists(cls, interface: str) -> bool:
        """
        Check if a network interface exists.

        Args:
            interface: Interface name to check

        Returns:
            True if interface exists
        """
        return (Paths.SYS_NET / interface).exists()

    @classmethod
    def _detect_wifi_interfaces(cls) -> list[str]:
        """
        Detect all wireless interfaces on the system.

        An interface is considered wireless if it has a 'wireless'
        subdirectory in /sys/class/net/<interface>/.

        Returns:
            List of wireless interface names
        """
        wifi_ifaces = []

        try:
            for iface in os.listdir(Paths.SYS_NET):
                wireless_path = Paths.SYS_NET / iface / "wireless"
                if wireless_path.exists():
                    wifi_ifaces.append(iface)
        except OSError as e:
            logger.warning(f"Error scanning for WiFi interfaces: {e}")

        return wifi_ifaces

    @classmethod
    def get_interface_type(cls, interface: str) -> Optional[str]:
        """
        Determine if a WiFi interface is built-in or USB.

        Args:
            interface: WiFi interface name

        Returns:
            "builtin" for internal WiFi, "usb" for USB adapters, None if unknown
        """
        try:
            device_link = Paths.SYS_NET / interface / "device"
            if device_link.exists():
                device_path = os.readlink(device_link)

                # Built-in WiFi is usually on the SoC or MMC bus
                if "mmc" in device_path or "soc" in device_path:
                    return "builtin"
                elif "usb" in device_path:
                    return "usb"

        except OSError:
            pass

        return None

    @classmethod
    def get_interface_driver(cls, interface: str) -> Optional[str]:
        """
        Get the driver name for a network interface.

        Args:
            interface: Interface name

        Returns:
            Driver name or None if not found
        """
        try:
            driver_link = Paths.SYS_NET / interface / "device" / "driver"
            if driver_link.exists():
                driver_path = os.readlink(driver_link)
                return os.path.basename(driver_path)
        except OSError:
            pass

        return None

    @classmethod
    def is_interface_up(cls, interface: str) -> bool:
        """
        Check if a network interface is up.

        Args:
            interface: Interface name

        Returns:
            True if interface is up
        """
        try:
            operstate_file = Paths.SYS_NET / interface / "operstate"
            if operstate_file.exists():
                state = operstate_file.read_text().strip()
                return state in ("up", "unknown")  # 'unknown' often means up
        except (IOError, OSError):
            pass

        return False

    @classmethod
    def detect_ap_interface(cls) -> Optional[str]:
        """
        Detect the WiFi interface configured for AP mode.

        Returns:
            AP interface name or None
        """
        interfaces = cls.get_interfaces()
        if interfaces.wifi_ap and cls._interface_exists(interfaces.wifi_ap):
            return interfaces.wifi_ap
        return None


# Convenience function for backward compatibility
def get_interface_config() -> dict[str, str]:
    """
    Get interface configuration as a dictionary.

    This function maintains backward compatibility with code
    expecting a dictionary return type.

    Returns:
        Dictionary with 'eth', 'wifi_wan', and 'wifi_ap' keys
    """
    interfaces = InterfaceService.get_interfaces()
    return {
        "eth": interfaces.ethernet,
        "wifi_wan": interfaces.wifi_wan,
        "wifi_ap": interfaces.wifi_ap,
    }


def detect_ap_interface() -> Optional[str]:
    """
    Detect the WiFi interface configured for AP mode.

    Backward-compatible convenience function.

    Returns:
        AP interface name or None
    """
    return InterfaceService.detect_ap_interface()
