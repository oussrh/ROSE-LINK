"""
VPN Services Package
====================

Unified VPN management supporting multiple VPN providers.

Currently supported:
- WireGuard (.conf files)
- OpenVPN (.ovpn files)

Usage:
    from services.vpn import VPNManager, VPNType

    # Get status from all providers
    status = VPNManager.get_combined_status()

    # List all profiles
    profiles = VPNManager.list_all_profiles()

    # Upload a profile (auto-detects type)
    VPNManager.upload_profile("my-vpn.ovpn", content)

    # Use specific provider
    wg = VPNManager.get_provider(VPNType.WIREGUARD)
    wg.start()

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from .base import VPNProvider, VPNType, VPNConnectionStatus, VPNTransferStats, VPNProfileInfo
from .wireguard import WireGuardProvider
from .openvpn import OpenVPNProvider

logger = logging.getLogger("rose-link.vpn")

__all__ = [
    "VPNManager",
    "VPNProvider",
    "VPNType",
    "VPNConnectionStatus",
    "VPNTransferStats",
    "VPNProfileInfo",
    "WireGuardProvider",
    "OpenVPNProvider",
]


class VPNManager:
    """
    Unified VPN manager that handles multiple VPN providers.

    Provides a single interface for managing both WireGuard and OpenVPN
    connections and profiles.
    """

    # Provider instances (lazy-loaded singletons)
    _wireguard: Optional[WireGuardProvider] = None
    _openvpn: Optional[OpenVPNProvider] = None

    @classmethod
    def get_provider(cls, vpn_type: VPNType) -> VPNProvider:
        """
        Get a VPN provider instance by type.

        Args:
            vpn_type: The type of VPN provider to get

        Returns:
            VPN provider instance

        Raises:
            ValueError: If unknown VPN type
        """
        if vpn_type == VPNType.WIREGUARD:
            if cls._wireguard is None:
                cls._wireguard = WireGuardProvider()
            return cls._wireguard
        elif vpn_type == VPNType.OPENVPN:
            if cls._openvpn is None:
                cls._openvpn = OpenVPNProvider()
            return cls._openvpn
        else:
            raise ValueError(f"Unknown VPN type: {vpn_type}")

    @classmethod
    def detect_vpn_type(cls, filename: str) -> VPNType:
        """
        Detect VPN type from filename extension.

        Args:
            filename: Name of the config file

        Returns:
            VPNType based on extension

        Raises:
            ValueError: If extension not recognized
        """
        filename_lower = filename.lower()

        if filename_lower.endswith(".conf"):
            return VPNType.WIREGUARD
        elif filename_lower.endswith(".ovpn"):
            return VPNType.OPENVPN
        else:
            raise ValueError(
                f"Unknown VPN config file type: {filename}. "
                "Use .conf for WireGuard or .ovpn for OpenVPN."
            )

    @classmethod
    def get_combined_status(cls) -> dict[str, Any]:
        """
        Get combined status from all VPN providers.

        Returns:
            Dictionary with status from each provider
        """
        wireguard = cls.get_provider(VPNType.WIREGUARD)
        openvpn = cls.get_provider(VPNType.OPENVPN)

        wg_status = wireguard.get_status()
        ovpn_status = openvpn.get_status()

        # Determine which VPN is currently active
        active_vpn = None
        active_status = None

        if wg_status.active:
            active_vpn = VPNType.WIREGUARD
            active_status = wg_status
        elif ovpn_status.active:
            active_vpn = VPNType.OPENVPN
            active_status = ovpn_status

        return {
            "active": active_vpn.value if active_vpn else None,
            "wireguard": wg_status.to_dict(),
            "openvpn": ovpn_status.to_dict(),
            "current": active_status.to_dict() if active_status else None,
        }

    @classmethod
    def get_active_status(cls) -> VPNConnectionStatus:
        """
        Get status of the currently active VPN.

        Returns:
            VPNConnectionStatus of active VPN, or inactive status if none
        """
        wireguard = cls.get_provider(VPNType.WIREGUARD)
        wg_status = wireguard.get_status()

        if wg_status.active:
            return wg_status

        openvpn = cls.get_provider(VPNType.OPENVPN)
        ovpn_status = openvpn.get_status()

        if ovpn_status.active:
            return ovpn_status

        # Return inactive WireGuard status as default
        return VPNConnectionStatus(vpn_type=VPNType.WIREGUARD)

    @classmethod
    def list_all_profiles(cls) -> list[VPNProfileInfo]:
        """
        List all VPN profiles from all providers.

        Returns:
            Combined list of all VPN profiles
        """
        profiles = []

        wireguard = cls.get_provider(VPNType.WIREGUARD)
        profiles.extend(wireguard.list_profiles())

        openvpn = cls.get_provider(VPNType.OPENVPN)
        profiles.extend(openvpn.list_profiles())

        return profiles

    @classmethod
    def upload_profile(cls, filename: str, content: bytes) -> tuple[str, VPNType]:
        """
        Upload a VPN profile, auto-detecting the type.

        Args:
            filename: Original filename
            content: File content as bytes

        Returns:
            Tuple of (saved_filename, vpn_type)
        """
        vpn_type = cls.detect_vpn_type(filename)
        provider = cls.get_provider(vpn_type)

        saved_name = provider.upload_profile(filename, content)
        return saved_name, vpn_type

    @classmethod
    def import_profile(cls, filename: str, content: bytes) -> tuple[str, VPNType]:
        """
        Import and activate a VPN profile, auto-detecting the type.

        Args:
            filename: Original filename
            content: File content as bytes

        Returns:
            Tuple of (profile_name, vpn_type)
        """
        vpn_type = cls.detect_vpn_type(filename)
        provider = cls.get_provider(vpn_type)

        profile_name = provider.import_profile(filename, content)
        return profile_name, vpn_type

    @classmethod
    def activate_profile(cls, name: str, vpn_type: VPNType) -> bool:
        """
        Activate a specific VPN profile.

        Args:
            name: Profile name
            vpn_type: Type of VPN

        Returns:
            True if successful
        """
        # Stop any other VPN first
        cls.stop_all()

        provider = cls.get_provider(vpn_type)
        return provider.activate_profile(name)

    @classmethod
    def delete_profile(cls, name: str, vpn_type: VPNType) -> bool:
        """
        Delete a VPN profile.

        Args:
            name: Profile name
            vpn_type: Type of VPN

        Returns:
            True if successful
        """
        provider = cls.get_provider(vpn_type)
        return provider.delete_profile(name)

    @classmethod
    def start(cls, vpn_type: Optional[VPNType] = None) -> bool:
        """
        Start a VPN connection.

        If vpn_type is None, starts WireGuard by default.

        Args:
            vpn_type: Type of VPN to start

        Returns:
            True if successful
        """
        if vpn_type is None:
            vpn_type = VPNType.WIREGUARD

        # Stop other VPN first
        if vpn_type == VPNType.WIREGUARD:
            cls.get_provider(VPNType.OPENVPN).stop()
        else:
            cls.get_provider(VPNType.WIREGUARD).stop()

        provider = cls.get_provider(vpn_type)
        return provider.start()

    @classmethod
    def stop(cls, vpn_type: Optional[VPNType] = None) -> bool:
        """
        Stop a VPN connection.

        If vpn_type is None, stops all VPNs.

        Args:
            vpn_type: Type of VPN to stop, or None for all

        Returns:
            True if successful
        """
        if vpn_type is None:
            return cls.stop_all()

        provider = cls.get_provider(vpn_type)
        return provider.stop()

    @classmethod
    def stop_all(cls) -> bool:
        """
        Stop all VPN connections.

        Returns:
            True if all stops successful
        """
        success = True

        try:
            cls.get_provider(VPNType.WIREGUARD).stop()
        except Exception as e:
            logger.debug(f"Error stopping WireGuard: {e}")
            success = False

        try:
            cls.get_provider(VPNType.OPENVPN).stop()
        except Exception as e:
            logger.debug(f"Error stopping OpenVPN: {e}")
            success = False

        return success

    @classmethod
    def restart(cls, vpn_type: VPNType) -> bool:
        """
        Restart a VPN connection.

        Args:
            vpn_type: Type of VPN to restart

        Returns:
            True if successful
        """
        provider = cls.get_provider(vpn_type)
        return provider.restart()

    @classmethod
    def is_any_active(cls) -> bool:
        """
        Check if any VPN is currently active.

        Returns:
            True if any VPN is connected
        """
        return (
            cls.get_provider(VPNType.WIREGUARD).is_active() or
            cls.get_provider(VPNType.OPENVPN).is_active()
        )

    @classmethod
    def get_active_type(cls) -> Optional[VPNType]:
        """
        Get the type of currently active VPN.

        Returns:
            VPNType of active VPN, or None if none active
        """
        if cls.get_provider(VPNType.WIREGUARD).is_active():
            return VPNType.WIREGUARD
        elif cls.get_provider(VPNType.OPENVPN).is_active():
            return VPNType.OPENVPN
        return None
