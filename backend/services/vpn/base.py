"""
VPN Provider Base Class
=======================

Abstract base class defining the interface for VPN providers.
Both WireGuard and OpenVPN implementations inherit from this.

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class VPNType(str, Enum):
    """Supported VPN types."""
    WIREGUARD = "wireguard"
    OPENVPN = "openvpn"


@dataclass
class VPNTransferStats:
    """VPN transfer statistics."""

    received: str = "0 B"
    sent: str = "0 B"
    received_bytes: int = 0
    sent_bytes: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "received": self.received,
            "sent": self.sent,
            "received_bytes": self.received_bytes,
            "sent_bytes": self.sent_bytes,
        }


@dataclass
class VPNConnectionStatus:
    """Current VPN connection status."""

    active: bool = False
    vpn_type: VPNType = VPNType.WIREGUARD
    interface: str = ""
    endpoint: Optional[str] = None
    connected_since: Optional[str] = None
    latest_handshake: Optional[str] = None
    local_ip: Optional[str] = None
    transfer: VPNTransferStats = field(default_factory=VPNTransferStats)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "active": self.active,
            "vpn_type": self.vpn_type.value,
            "interface": self.interface,
            "endpoint": self.endpoint,
            "connected_since": self.connected_since,
            "latest_handshake": self.latest_handshake,
            "local_ip": self.local_ip,
            "transfer": self.transfer.to_dict(),
        }


@dataclass
class VPNProfileInfo:
    """Information about a VPN profile."""

    name: str
    vpn_type: VPNType
    active: bool = False
    filename: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "vpn_type": self.vpn_type.value,
            "active": self.active,
            "filename": self.filename,
        }


class VPNProvider(ABC):
    """
    Abstract base class for VPN providers.

    Defines the interface that all VPN implementations must follow.
    """

    @property
    @abstractmethod
    def vpn_type(self) -> VPNType:
        """Return the VPN type for this provider."""
        pass

    @property
    @abstractmethod
    def interface_name(self) -> str:
        """Return the network interface name used by this VPN."""
        pass

    @property
    @abstractmethod
    def profiles_dir(self) -> Path:
        """Return the directory where profiles are stored."""
        pass

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Return the file extension for config files."""
        pass

    @abstractmethod
    def get_status(self) -> VPNConnectionStatus:
        """
        Get current VPN connection status.

        Returns:
            VPNConnectionStatus with connection details
        """
        pass

    @abstractmethod
    def list_profiles(self) -> list[VPNProfileInfo]:
        """
        List all available VPN profiles.

        Returns:
            List of VPNProfileInfo objects
        """
        pass

    @abstractmethod
    def upload_profile(self, filename: str, content: bytes) -> str:
        """
        Upload a new VPN profile without activating it.

        Args:
            filename: Original filename
            content: File content as bytes

        Returns:
            Sanitized filename of saved profile

        Raises:
            FileTooLargeError: If content exceeds size limit
            ValidationError: If config is invalid
            ValueError: If filename is invalid
        """
        pass

    @abstractmethod
    def import_profile(self, filename: str, content: bytes) -> str:
        """
        Import and immediately activate a VPN profile.

        Args:
            filename: Original filename
            content: File content as bytes

        Returns:
            Profile name (without extension)
        """
        pass

    @abstractmethod
    def activate_profile(self, name: str) -> bool:
        """
        Activate a VPN profile.

        Args:
            name: Profile name (without extension)

        Returns:
            True if activation successful
        """
        pass

    @abstractmethod
    def delete_profile(self, name: str) -> bool:
        """
        Delete a VPN profile.

        Args:
            name: Profile name (without extension)

        Returns:
            True if deletion successful
        """
        pass

    @abstractmethod
    def start(self) -> bool:
        """
        Start the VPN connection.

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def stop(self) -> bool:
        """
        Stop the VPN connection.

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def restart(self) -> bool:
        """
        Restart the VPN connection.

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def is_active(self) -> bool:
        """
        Quick check if VPN is currently active.

        Returns:
            True if VPN connection is up
        """
        pass

    @abstractmethod
    def validate_config(self, content: bytes) -> bool:
        """
        Validate a VPN configuration file.

        Args:
            content: File content as bytes

        Returns:
            True if valid

        Raises:
            ValidationError: If config is invalid
        """
        pass
