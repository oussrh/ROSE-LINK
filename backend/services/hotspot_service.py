"""
Hotspot Service
===============

Handles WiFi Access Point (hotspot) configuration and monitoring.

Features:
- Configure hotspot SSID and password
- Support for 2.4GHz and 5GHz bands
- WPA2 and WPA3 security options
- Monitor connected clients
- Parse DHCP leases for client info

Technical Details:
- Uses hostapd for AP functionality
- Uses dnsmasq for DHCP/DNS
- Configuration written to /etc/hostapd/hostapd.conf

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional

from config import Paths, Network, Services
from models import (
    HotspotStatus,
    HotspotConfig,
    HotspotClient,
)
from exceptions import HotspotConfigurationError
from utils.command_runner import run_command, CommandRunner
from utils.validators import validate_ssid, validate_wpa_password, validate_country_code
from utils.sanitizers import escape_hostapd_value
from services.interface_service import InterfaceService

logger = logging.getLogger("rose-link.hotspot")


class HotspotService:
    """
    Service for WiFi hotspot management.

    This service handles hostapd configuration and monitoring
    of connected clients.
    """

    @classmethod
    def get_status(cls) -> HotspotStatus:
        """
        Get current hotspot status.

        Checks if hostapd is running and parses configuration
        to get current settings.

        Returns:
            HotspotStatus with current state and configuration
        """
        interfaces = InterfaceService.get_interfaces()
        status = HotspotStatus(interface=interfaces.wifi_ap)

        # Check if hostapd is running
        if not CommandRunner.is_service_active(Services.HOSTAPD):
            return status

        status.active = True

        # Parse configuration from hostapd.conf
        cls._parse_hostapd_config(status)

        # Count connected clients
        status.clients = cls._count_connected_clients(interfaces.wifi_ap)

        return status

    @classmethod
    def _parse_hostapd_config(cls, status: HotspotStatus) -> None:
        """
        Parse hostapd configuration file to populate status.

        Args:
            status: HotspotStatus to update with parsed values
        """
        if not Paths.HOSTAPD_CONF.exists():
            return

        try:
            with open(Paths.HOSTAPD_CONF, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()

                    if line.startswith("ssid="):
                        status.ssid = line.split("=", 1)[1].strip()

                    elif line.startswith("channel="):
                        try:
                            status.channel = int(line.split("=", 1)[1].strip())
                        except ValueError:
                            pass

                    elif line.startswith("hw_mode="):
                        hw_mode = line.split("=", 1)[1].strip()
                        status.hw_mode = hw_mode
                        # 'a' mode = 5GHz, 'g' mode = 2.4GHz
                        status.frequency = "5GHz" if hw_mode == "a" else "2.4GHz"

        except (IOError, OSError) as e:
            logger.warning(f"Error reading hostapd config: {e}")

    @classmethod
    def _count_connected_clients(cls, interface: str) -> int:
        """
        Count connected WiFi clients.

        Uses 'iw station dump' to get connected stations.

        Args:
            interface: AP interface name

        Returns:
            Number of connected clients
        """
        ret, out, _ = CommandRunner.get_station_dump(interface)

        if ret != 0:
            return 0

        # Count "Station" entries
        return out.count("Station ")

    @classmethod
    def get_clients(cls) -> list[HotspotClient]:
        """
        Get detailed list of connected clients.

        Parses 'iw station dump' output and enriches with
        DHCP lease information.

        Returns:
            List of HotspotClient with connection details
        """
        interface = InterfaceService.detect_ap_interface()

        if not interface:
            logger.warning("No AP interface detected")
            return []

        # Get station information
        ret, out, _ = CommandRunner.get_station_dump(interface)

        if ret != 0 or not out:
            return []

        # Parse station dump
        clients = cls._parse_station_dump(out)

        # Enrich with DHCP lease info
        cls._enrich_with_dhcp_info(clients)

        logger.info(f"Found {len(clients)} connected clients")
        return clients

    @classmethod
    def _parse_station_dump(cls, output: str) -> list[HotspotClient]:
        """
        Parse 'iw station dump' output.

        Example output:
            Station aa:bb:cc:dd:ee:ff (on wlan0)
                inactive time:  1234 ms
                rx bytes:       12345
                tx bytes:       67890
                signal:         -45 dBm

        Args:
            output: Raw output from iw station dump

        Returns:
            List of HotspotClient objects
        """
        clients = []
        current_client: Optional[HotspotClient] = None

        for line in output.split('\n'):
            line = line.strip()

            if line.startswith("Station "):
                # Save previous client
                if current_client:
                    clients.append(current_client)

                # Start new client
                parts = line.split()
                if len(parts) >= 2:
                    mac = parts[1]
                    current_client = HotspotClient(mac=mac)
                else:
                    current_client = None

            elif current_client and ":" in line:
                # Parse property lines
                key, _, value = line.partition(":")
                key = key.strip().lower().replace(" ", "_")
                value = value.strip()

                if key == "signal":
                    current_client.signal = value
                elif key == "rx_bytes":
                    try:
                        current_client.rx_bytes = int(value)
                    except ValueError:
                        pass
                elif key == "tx_bytes":
                    try:
                        current_client.tx_bytes = int(value)
                    except ValueError:
                        pass
                elif key == "inactive_time":
                    current_client.inactive_time = value

        # Don't forget the last client
        if current_client:
            clients.append(current_client)

        return clients

    @classmethod
    def _enrich_with_dhcp_info(cls, clients: list[HotspotClient]) -> None:
        """
        Add DHCP lease information to client list.

        Reads dnsmasq.leases to find IP and hostname for each MAC.

        Args:
            clients: List of clients to enrich (modified in place)
        """
        if not Paths.DNSMASQ_LEASES.exists():
            return

        try:
            with open(Paths.DNSMASQ_LEASES, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split()

                    if len(parts) < 4:
                        continue

                    # Format: timestamp mac ip hostname client-id
                    lease_mac = parts[1].lower()
                    lease_ip = parts[2]
                    lease_hostname = parts[3] if parts[3] != "*" else ""

                    # Find matching client
                    for client in clients:
                        if client.mac.lower() == lease_mac:
                            client.ip = lease_ip
                            client.hostname = lease_hostname
                            break

        except (IOError, OSError) as e:
            logger.debug(f"Could not read DHCP leases: {e}")

    @classmethod
    def apply_config(cls, config: HotspotConfig) -> bool:
        """
        Apply new hotspot configuration.

        Generates hostapd.conf with the new settings and
        restarts the relevant services.

        Args:
            config: New hotspot configuration

        Returns:
            True if successful

        Raises:
            HotspotConfigurationError: If configuration fails
        """
        try:
            # Validate and sanitize inputs
            safe_ssid = validate_ssid(config.ssid)
            safe_password = validate_wpa_password(config.password)
            safe_country = validate_country_code(config.country)

            # Get interface
            interfaces = InterfaceService.get_interfaces()
            ap_iface = interfaces.wifi_ap

            # Generate configuration
            hostapd_config = cls._generate_hostapd_config(
                interface=ap_iface,
                ssid=safe_ssid,
                password=safe_password,
                country=safe_country,
                channel=config.channel,
                band=config.band,
                wpa3=config.wpa3,
            )

            # Write configuration
            with open(Paths.HOSTAPD_CONF, "w", encoding="utf-8") as f:
                f.write(hostapd_config)

            # Restart services
            cls.restart()

            logger.info(f"Hotspot config applied: SSID={safe_ssid}, channel={config.channel}")
            return True

        except (IOError, OSError) as e:
            logger.error(f"Failed to apply hotspot config: {e}")
            raise HotspotConfigurationError(f"Failed to apply configuration: {e}")

    @classmethod
    def _generate_hostapd_config(
        cls,
        interface: str,
        ssid: str,
        password: str,
        country: str,
        channel: int,
        band: str,
        wpa3: bool,
    ) -> str:
        """
        Generate hostapd configuration file content.

        Args:
            interface: WiFi interface name
            ssid: Network SSID
            password: WPA password
            country: Country code
            channel: WiFi channel
            band: WiFi band ("2.4GHz" or "5GHz")
            wpa3: Enable WPA3 security

        Returns:
            Complete hostapd.conf content
        """
        # Escape values for safe config writing
        safe_ssid = escape_hostapd_value(ssid)
        safe_password = escape_hostapd_value(password)

        # Configure based on band
        if band == "5GHz":
            hw_mode = "a"

            # Validate 5GHz channel
            if channel not in Network.VALID_5GHZ_CHANNELS:
                channel = Network.DEFAULT_5GHZ_CHANNEL

            extra_config = """
# 802.11ac (WiFi 5) support
ieee80211ac=1
vht_oper_chwidth=1
vht_oper_centr_freq_seg0_idx=42
vht_capab=[MAX-MPDU-11454][SHORT-GI-80][TX-STBC-2BY1][RX-STBC-1]"""

        else:
            hw_mode = "g"

            # Validate 2.4GHz channel
            if channel < 1 or channel > 13:
                channel = Network.DEFAULT_2GHZ_CHANNEL

            extra_config = ""

        # WPA configuration
        if wpa3:
            wpa_config = """wpa=2
wpa_key_mgmt=SAE WPA-PSK
ieee80211w=1"""
        else:
            wpa_config = """wpa=2
wpa_key_mgmt=WPA-PSK"""

        return f"""# ROSE Link Hotspot Configuration
# Auto-generated via Web API
# Band: {band}

interface={interface}
driver=nl80211

# Network settings
ssid={safe_ssid}
hw_mode={hw_mode}
channel={channel}
country_code={country}

# 802.11n support
ieee80211n=1
wmm_enabled=1
{extra_config}

# Security
auth_algs=1
{wpa_config}
wpa_passphrase={safe_password}
rsn_pairwise=CCMP

# Logging
logger_syslog=-1
logger_syslog_level=2
"""

    @classmethod
    def restart(cls) -> bool:
        """
        Restart hotspot services.

        Restarts both hostapd and dnsmasq.

        Returns:
            True if successful

        Raises:
            HotspotConfigurationError: If restart fails
        """
        logger.info("Restarting hotspot services")

        hostapd_ok = CommandRunner.restart_service(Services.HOSTAPD)
        dnsmasq_ok = CommandRunner.restart_service(Services.DNSMASQ)

        if not (hostapd_ok and dnsmasq_ok):
            raise HotspotConfigurationError("Failed to restart hotspot services")

        return True

    @classmethod
    def is_active(cls) -> bool:
        """
        Quick check if hotspot is currently active.

        Returns:
            True if hostapd is running
        """
        return CommandRunner.is_service_active(Services.HOSTAPD)
