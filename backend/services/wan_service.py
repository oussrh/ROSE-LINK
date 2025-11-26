"""
WAN Connection Service
======================

Handles WAN (Wide Area Network) connectivity through both Ethernet
and WiFi interfaces.

Features:
- Monitor Ethernet connection status
- Scan for available WiFi networks
- Connect/disconnect WiFi WAN
- Track connection status and IP addresses

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from models import (
    WANStatus,
    EthernetStatus,
    WifiWanStatus,
    WifiNetwork,
)
from exceptions import WifiScanError, WifiConnectionError
from utils.command_runner import run_command, CommandRunner
from services.interface_service import InterfaceService

logger = logging.getLogger("rose-link.wan")


class WANService:
    """
    Service for managing WAN connections.

    This service handles both Ethernet and WiFi WAN connections,
    providing methods to check status, scan networks, and manage
    WiFi connections through NetworkManager.
    """

    @classmethod
    def get_status(cls) -> WANStatus:
        """
        Get WAN connection status for both Ethernet and WiFi.

        Returns:
            WANStatus containing ethernet and wifi status
        """
        interfaces = InterfaceService.get_interfaces()

        status = WANStatus(
            ethernet=cls._get_ethernet_status(interfaces.ethernet),
            wifi=cls._get_wifi_status(interfaces.wifi_wan),
        )

        return status

    @classmethod
    def _get_ethernet_status(cls, interface: str) -> EthernetStatus:
        """
        Get Ethernet connection status.

        Args:
            interface: Ethernet interface name (e.g., "eth0")

        Returns:
            EthernetStatus with connection info
        """
        status = EthernetStatus(interface=interface)

        if not interface:
            return status

        ret, out, _ = run_command(
            ["ip", "addr", "show", interface],
            check=False,
        )

        if ret == 0 and "inet " in out:
            status.connected = True

            # Extract IP address
            match = re.search(r"inet\s+(\S+)", out)
            if match:
                status.ip = match.group(1)

        return status

    @classmethod
    def _get_wifi_status(cls, interface: str) -> WifiWanStatus:
        """
        Get WiFi WAN connection status using NetworkManager.

        Args:
            interface: WiFi interface name (e.g., "wlan1")

        Returns:
            WifiWanStatus with connection info
        """
        status = WifiWanStatus(interface=interface)

        if not interface:
            return status

        # Get device state from NetworkManager
        ret, out, _ = run_command(
            ["nmcli", "-t", "-f", "DEVICE,STATE,CONNECTION", "device"],
            check=False,
        )

        if ret != 0:
            logger.warning("Failed to get WiFi status from NetworkManager")
            return status

        for line in out.splitlines():
            parts = line.split(":")
            if len(parts) >= 3:
                device, state, connection = parts[0], parts[1], parts[2]

                if device == interface and state == "connected":
                    status.connected = True
                    status.ssid = connection

                    # Get IP address
                    status.ip = CommandRunner.get_interface_ip(interface)
                    break

        return status

    @classmethod
    def scan_networks(cls) -> list[WifiNetwork]:
        """
        Scan for available WiFi networks.

        Uses NetworkManager (nmcli) to perform the scan.

        Returns:
            List of WifiNetwork objects sorted by signal strength

        Raises:
            WifiScanError: If scan fails
        """
        ret, out, err = CommandRunner.wifi_scan()

        if ret != 0:
            logger.error(f"WiFi scan failed: {err}")
            raise WifiScanError(f"Scan failed: {err}")

        networks = []
        seen_ssids: set[str] = set()

        for line in out.splitlines():
            parts = line.split(":")
            if len(parts) >= 3:
                ssid = parts[0].strip()

                # Skip empty SSIDs and duplicates
                if ssid and ssid not in seen_ssids:
                    seen_ssids.add(ssid)

                    # Parse signal strength
                    try:
                        signal = int(parts[1]) if parts[1].isdigit() else 0
                    except (ValueError, IndexError):
                        signal = 0

                    # Get security type
                    security = parts[2] if len(parts) > 2 else "Open"

                    networks.append(WifiNetwork(
                        ssid=ssid,
                        signal=signal,
                        security=security,
                    ))

        # Sort by signal strength (strongest first)
        networks.sort(key=lambda x: x.signal, reverse=True)

        logger.info(f"WiFi scan found {len(networks)} networks")
        return networks

    @classmethod
    def connect_wifi(cls, ssid: str, password: str) -> bool:
        """
        Connect to a WiFi network.

        Uses NetworkManager to establish the connection.

        Args:
            ssid: Network SSID
            password: Network password

        Returns:
            True if connection successful

        Raises:
            WifiConnectionError: If connection fails
        """
        logger.info(f"Connecting to WiFi: {ssid}")

        ret, out, err = CommandRunner.wifi_connect(ssid, password)

        if ret != 0:
            logger.error(f"WiFi connection failed: {err}")
            raise WifiConnectionError(
                f"Connection failed: {err}",
                ssid=ssid,
            )

        logger.info(f"WiFi connected successfully: {ssid}")
        return True

    @classmethod
    def disconnect_wifi(cls) -> bool:
        """
        Disconnect from WiFi WAN.

        Uses the configured WiFi WAN interface.

        Returns:
            True if disconnection successful

        Raises:
            WifiConnectionError: If disconnection fails
        """
        interfaces = InterfaceService.get_interfaces()
        interface = interfaces.wifi_wan

        logger.info(f"Disconnecting WiFi: {interface}")

        ret, out, err = CommandRunner.wifi_disconnect(interface)

        if ret != 0:
            logger.error(f"WiFi disconnect failed: {err}")
            raise WifiConnectionError(f"Disconnect failed: {err}")

        logger.info("WiFi disconnected successfully")
        return True

    @classmethod
    def get_current_ssid(cls) -> Optional[str]:
        """
        Get the SSID of the currently connected WiFi network.

        Returns:
            SSID string or None if not connected
        """
        status = cls.get_status()
        if status.wifi.connected:
            return status.wifi.ssid
        return None

    @classmethod
    def is_connected(cls) -> bool:
        """
        Check if any WAN connection is active.

        Returns:
            True if either Ethernet or WiFi is connected
        """
        status = cls.get_status()
        return status.ethernet.connected or status.wifi.connected
