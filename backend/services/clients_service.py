"""
Connected Clients Service
=========================

Manages connected hotspot clients with persistent tracking,
device information, and management features.

Features:
- Real-time client list from hostapd
- Persistent client history
- Device type detection via MAC OUI
- Client blocking/unblocking
- Custom device naming

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from config import Paths
from utils.command_runner import run_command

logger = logging.getLogger("rose-link.clients")

# Client data storage
CLIENTS_DATA_FILE = Paths.ROSE_LINK_DIR / "data" / "clients.json"
BLOCKED_CLIENTS_FILE = Paths.ROSE_LINK_DIR / "data" / "blocked_clients.txt"

# MAC OUI database for device type detection (simplified)
MAC_OUI_DATABASE = {
    "00:1A:79": ("Apple", "iPhone/iPad"),
    "00:03:93": ("Apple", "Mac"),
    "00:1E:C2": ("Apple", "Mac"),
    "00:25:00": ("Apple", "Mac"),
    "3C:22:FB": ("Apple", "iPhone/iPad"),
    "F0:18:98": ("Apple", "iPhone/iPad"),
    "64:A2:F9": ("Apple", "iPhone/iPad"),
    "AC:DE:48": ("Apple", "iPhone/iPad"),
    "00:1A:2B": ("Samsung", "Android"),
    "00:26:37": ("Samsung", "Android"),
    "94:35:0A": ("Samsung", "Android"),
    "BC:44:86": ("Samsung", "Android"),
    "E4:7C:F9": ("Samsung", "Android"),
    "00:17:C4": ("Google", "Android"),
    "00:1A:11": ("Google", "Android"),
    "3C:5A:B4": ("Google", "Android"),
    "98:D2:93": ("Google", "Android"),
    "00:15:5D": ("Microsoft", "Windows"),
    "00:50:F2": ("Microsoft", "Windows"),
    "28:18:78": ("Microsoft", "Windows"),
    "B8:27:EB": ("Raspberry Pi", "Linux"),
    "DC:A6:32": ("Raspberry Pi", "Linux"),
    "E4:5F:01": ("Raspberry Pi", "Linux"),
    "00:1A:A0": ("Dell", "PC"),
    "14:FE:B5": ("Dell", "PC"),
    "00:1E:68": ("HP", "PC"),
    "00:21:5A": ("HP", "PC"),
    "00:1C:C0": ("Intel", "PC"),
    "3C:97:0E": ("Intel", "PC"),
    "00:E0:4C": ("Realtek", "PC"),
    "52:54:00": ("QEMU", "Virtual"),
}


@dataclass
class ClientInfo:
    """Information about a connected or historical client."""

    mac: str
    ip: Optional[str] = None
    hostname: Optional[str] = None
    custom_name: Optional[str] = None
    signal: str = "N/A"
    rx_bytes: int = 0
    tx_bytes: int = 0
    inactive_time: Optional[str] = None
    connected: bool = False
    blocked: bool = False
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    total_rx_bytes: int = 0
    total_tx_bytes: int = 0
    manufacturer: Optional[str] = None
    device_type: Optional[str] = None
    connection_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "mac": self.mac,
            "ip": self.ip,
            "hostname": self.hostname,
            "custom_name": self.custom_name,
            "display_name": self.custom_name or self.hostname or self.mac,
            "signal": self.signal,
            "rx_bytes": self.rx_bytes,
            "tx_bytes": self.tx_bytes,
            "inactive_time": self.inactive_time,
            "connected": self.connected,
            "blocked": self.blocked,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "total_rx_bytes": self.total_rx_bytes,
            "total_tx_bytes": self.total_tx_bytes,
            "manufacturer": self.manufacturer,
            "device_type": self.device_type,
            "connection_count": self.connection_count,
        }


class ClientsService:
    """
    Service for managing connected hotspot clients.

    Provides real-time client monitoring, historical tracking,
    and client management (block/unblock, naming).
    """

    @classmethod
    def get_connected_clients(cls) -> list[ClientInfo]:
        """
        Get list of currently connected clients.

        Combines data from hostapd_cli and dnsmasq leases.

        Returns:
            List of currently connected ClientInfo objects
        """
        clients = []

        # Get raw client data from hostapd
        ret, out, _ = run_command("hostapd_cli all_sta", timeout=10)
        if ret != 0:
            logger.debug("Failed to get client list from hostapd")
            return clients

        # Parse hostapd output
        current_mac = None
        current_client = None

        for line in out.splitlines():
            line = line.strip()

            # MAC address line
            mac_match = re.match(r'^([0-9a-fA-F:]{17})$', line)
            if mac_match:
                if current_client:
                    clients.append(current_client)

                mac = mac_match.group(1).upper()
                current_mac = mac
                current_client = ClientInfo(
                    mac=mac,
                    connected=True,
                )
                cls._detect_device_type(current_client)
                continue

            if current_client and "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                if key == "signal":
                    current_client.signal = f"{value} dBm"
                elif key == "rx_bytes":
                    current_client.rx_bytes = int(value)
                elif key == "tx_bytes":
                    current_client.tx_bytes = int(value)
                elif key == "inactive_msec":
                    ms = int(value)
                    current_client.inactive_time = f"{ms // 1000}s"

        # Add the last client
        if current_client:
            clients.append(current_client)

        # Enrich with IP/hostname from dnsmasq leases
        leases = cls._get_dnsmasq_leases()
        blocked_macs = cls._get_blocked_macs()

        for client in clients:
            if client.mac in leases:
                client.ip = leases[client.mac].get("ip")
                client.hostname = leases[client.mac].get("hostname")

            client.blocked = client.mac in blocked_macs

        # Update historical data
        cls._update_client_history(clients)

        return clients

    @classmethod
    def get_all_clients(cls) -> list[ClientInfo]:
        """
        Get all clients (connected and historical).

        Returns:
            List of all ClientInfo objects, sorted by last seen
        """
        # Load historical data
        history = cls._load_client_history()

        # Get currently connected clients
        connected = cls.get_connected_clients()
        connected_macs = {c.mac for c in connected}

        # Merge with history
        all_clients = list(connected)

        for mac, data in history.items():
            if mac not in connected_macs:
                client = cls._history_to_client(mac, data)
                all_clients.append(client)

        # Sort by connected status, then last seen
        all_clients.sort(
            key=lambda c: (
                not c.connected,  # Connected first
                c.last_seen or "",  # Then by last seen
            ),
            reverse=False
        )

        return all_clients

    @classmethod
    def get_client(cls, mac: str) -> Optional[ClientInfo]:
        """
        Get information about a specific client.

        Args:
            mac: Client MAC address

        Returns:
            ClientInfo or None if not found
        """
        mac = mac.upper()

        # Check connected clients first
        connected = cls.get_connected_clients()
        for client in connected:
            if client.mac == mac:
                return client

        # Check history
        history = cls._load_client_history()
        if mac in history:
            return cls._history_to_client(mac, history[mac])

        return None

    @classmethod
    def update_client(
        cls,
        mac: str,
        custom_name: Optional[str] = None,
    ) -> bool:
        """
        Update client information (e.g., custom name).

        Args:
            mac: Client MAC address
            custom_name: Custom display name for the device

        Returns:
            True if successful
        """
        mac = mac.upper()
        history = cls._load_client_history()

        if mac not in history:
            history[mac] = {"custom_name": custom_name}
        else:
            if custom_name is not None:
                history[mac]["custom_name"] = custom_name

        cls._save_client_history(history)
        logger.info(f"Updated client {mac}: name={custom_name}")
        return True

    @classmethod
    def block_client(cls, mac: str) -> bool:
        """
        Block a client from connecting.

        Uses hostapd_cli to deauthenticate and iptables for MAC filtering.

        Args:
            mac: Client MAC address to block

        Returns:
            True if successful
        """
        mac = mac.upper()

        # Add to blocked list
        blocked = cls._get_blocked_macs()
        if mac not in blocked:
            blocked.add(mac)
            cls._save_blocked_macs(blocked)

        # Add iptables rule to block
        run_command(
            f"sudo iptables -I FORWARD -m mac --mac-source {mac} -j DROP",
            timeout=10
        )

        # Deauthenticate if currently connected
        run_command(f"hostapd_cli deauthenticate {mac}", timeout=10)

        logger.info(f"Blocked client: {mac}")
        return True

    @classmethod
    def unblock_client(cls, mac: str) -> bool:
        """
        Unblock a previously blocked client.

        Args:
            mac: Client MAC address to unblock

        Returns:
            True if successful
        """
        mac = mac.upper()

        # Remove from blocked list
        blocked = cls._get_blocked_macs()
        if mac in blocked:
            blocked.discard(mac)
            cls._save_blocked_macs(blocked)

        # Remove iptables rule
        run_command(
            f"sudo iptables -D FORWARD -m mac --mac-source {mac} -j DROP",
            timeout=10
        )

        logger.info(f"Unblocked client: {mac}")
        return True

    @classmethod
    def kick_client(cls, mac: str) -> bool:
        """
        Disconnect a client without blocking.

        Args:
            mac: Client MAC address to disconnect

        Returns:
            True if successful
        """
        mac = mac.upper()

        ret, _, _ = run_command(f"hostapd_cli deauthenticate {mac}", timeout=10)
        if ret == 0:
            logger.info(f"Kicked client: {mac}")
            return True
        else:
            logger.warning(f"Failed to kick client: {mac}")
            return False

    @classmethod
    def _get_dnsmasq_leases(cls) -> dict[str, dict]:
        """
        Get IP/hostname mappings from dnsmasq leases.

        Returns:
            Dict mapping MAC addresses to IP/hostname
        """
        leases = {}

        if not Paths.DNSMASQ_LEASES.exists():
            return leases

        try:
            with open(Paths.DNSMASQ_LEASES, "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        # Format: timestamp mac ip hostname client_id
                        mac = parts[1].upper()
                        ip = parts[2]
                        hostname = parts[3] if parts[3] != "*" else None

                        leases[mac] = {"ip": ip, "hostname": hostname}

        except Exception as e:
            logger.debug(f"Error reading dnsmasq leases: {e}")

        return leases

    @classmethod
    def _detect_device_type(cls, client: ClientInfo) -> None:
        """
        Detect device manufacturer and type from MAC OUI.

        Args:
            client: ClientInfo to update
        """
        if not client.mac:
            return

        # Get OUI prefix (first 3 octets)
        oui = client.mac[:8].upper()

        if oui in MAC_OUI_DATABASE:
            manufacturer, device_type = MAC_OUI_DATABASE[oui]
            client.manufacturer = manufacturer
            client.device_type = device_type

    @classmethod
    def _get_blocked_macs(cls) -> set[str]:
        """Load set of blocked MAC addresses."""
        blocked = set()

        if BLOCKED_CLIENTS_FILE.exists():
            try:
                with open(BLOCKED_CLIENTS_FILE, "r") as f:
                    for line in f:
                        mac = line.strip().upper()
                        if mac:
                            blocked.add(mac)
            except Exception as e:
                logger.debug(f"Error reading blocked clients: {e}")

        return blocked

    @classmethod
    def _save_blocked_macs(cls, blocked: set[str]) -> None:
        """Save set of blocked MAC addresses."""
        try:
            BLOCKED_CLIENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(BLOCKED_CLIENTS_FILE, "w") as f:
                for mac in sorted(blocked):
                    f.write(f"{mac}\n")
        except Exception as e:
            logger.error(f"Error saving blocked clients: {e}")

    @classmethod
    def _load_client_history(cls) -> dict:
        """Load client history from JSON file."""
        if not CLIENTS_DATA_FILE.exists():
            return {}

        try:
            with open(CLIENTS_DATA_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.debug(f"Error loading client history: {e}")
            return {}

    @classmethod
    def _save_client_history(cls, history: dict) -> None:
        """Save client history to JSON file."""
        try:
            CLIENTS_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CLIENTS_DATA_FILE, "w") as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving client history: {e}")

    @classmethod
    def _update_client_history(cls, connected: list[ClientInfo]) -> None:
        """
        Update historical data with connected clients.

        Args:
            connected: List of currently connected clients
        """
        history = cls._load_client_history()
        now = datetime.now().isoformat()

        for client in connected:
            mac = client.mac

            if mac not in history:
                history[mac] = {
                    "first_seen": now,
                    "connection_count": 0,
                    "total_rx_bytes": 0,
                    "total_tx_bytes": 0,
                }

            history[mac]["last_seen"] = now
            history[mac]["connection_count"] = history[mac].get("connection_count", 0) + 1

            # Update totals
            if client.rx_bytes > 0:
                history[mac]["total_rx_bytes"] = (
                    history[mac].get("total_rx_bytes", 0) + client.rx_bytes
                )
            if client.tx_bytes > 0:
                history[mac]["total_tx_bytes"] = (
                    history[mac].get("total_tx_bytes", 0) + client.tx_bytes
                )

            # Store other info
            if client.hostname:
                history[mac]["hostname"] = client.hostname
            if client.ip:
                history[mac]["ip"] = client.ip
            if client.manufacturer:
                history[mac]["manufacturer"] = client.manufacturer
            if client.device_type:
                history[mac]["device_type"] = client.device_type

            # Update client with historical data
            client.first_seen = history[mac].get("first_seen")
            client.last_seen = now
            client.total_rx_bytes = history[mac].get("total_rx_bytes", 0)
            client.total_tx_bytes = history[mac].get("total_tx_bytes", 0)
            client.connection_count = history[mac].get("connection_count", 0)
            client.custom_name = history[mac].get("custom_name")

        cls._save_client_history(history)

    @classmethod
    def _history_to_client(cls, mac: str, data: dict) -> ClientInfo:
        """
        Convert historical data to ClientInfo.

        Args:
            mac: Client MAC address
            data: Historical data dictionary

        Returns:
            ClientInfo with historical data
        """
        client = ClientInfo(
            mac=mac,
            hostname=data.get("hostname"),
            custom_name=data.get("custom_name"),
            ip=data.get("ip"),
            connected=False,
            blocked=mac in cls._get_blocked_macs(),
            first_seen=data.get("first_seen"),
            last_seen=data.get("last_seen"),
            total_rx_bytes=data.get("total_rx_bytes", 0),
            total_tx_bytes=data.get("total_tx_bytes", 0),
            manufacturer=data.get("manufacturer"),
            device_type=data.get("device_type"),
            connection_count=data.get("connection_count", 0),
        )
        cls._detect_device_type(client)
        return client

    @classmethod
    def get_client_count(cls) -> dict[str, int]:
        """
        Get client count statistics.

        Returns:
            Dict with connected, blocked, and total counts
        """
        connected = cls.get_connected_clients()
        history = cls._load_client_history()
        blocked = cls._get_blocked_macs()

        return {
            "connected": len(connected),
            "blocked": len(blocked),
            "total_known": len(history),
        }
