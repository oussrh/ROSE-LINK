"""
WireGuard VPN Provider
======================

WireGuard implementation of the VPN provider interface.

Features:
- Upload and store WireGuard profiles (.conf)
- Activate/deactivate profiles via symlinks
- Start/stop/restart VPN connections
- Monitor VPN status and health

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Optional

from config import Paths, Limits
from exceptions import (
    VPNProfileNotFoundError,
    VPNProfileActiveError,
    VPNConnectionError,
    InvalidWireGuardConfigError,
    FileTooLargeError,
)
from utils.command_runner import CommandRunner
from utils.sanitizers import sanitize_filename
from utils.validators import validate_wireguard_config

from .base import VPNProvider, VPNType, VPNConnectionStatus, VPNTransferStats, VPNProfileInfo

logger = logging.getLogger("rose-link.vpn.wireguard")


class WireGuardProvider(VPNProvider):
    """
    WireGuard VPN provider implementation.

    Manages WireGuard VPN profiles and connections using
    wg-quick and systemd services.
    """

    @property
    def vpn_type(self) -> VPNType:
        return VPNType.WIREGUARD

    @property
    def interface_name(self) -> str:
        return "wg0"

    @property
    def profiles_dir(self) -> Path:
        return Paths.WG_PROFILES_DIR

    @property
    def file_extension(self) -> str:
        return ".conf"

    def get_status(self) -> VPNConnectionStatus:
        """
        Get current WireGuard connection status.

        Parses output from 'wg show' command to extract:
        - Connection state
        - Endpoint address
        - Latest handshake time
        - Transfer statistics
        """
        status = VPNConnectionStatus(
            vpn_type=VPNType.WIREGUARD,
            interface=self.interface_name,
        )

        ret, out, _ = CommandRunner.wg_show()

        if ret != 0 or not out:
            return status

        status.active = True

        # Parse wg show output line by line
        for line in out.splitlines():
            line = line.strip()

            if line.startswith("endpoint:"):
                status.endpoint = line.split(":", 1)[1].strip()

            elif line.startswith("latest handshake:"):
                status.latest_handshake = line.split(":", 1)[1].strip()

            elif line.startswith("transfer:"):
                status.transfer = self._parse_transfer_stats(line)

        return status

    def _parse_transfer_stats(self, line: str) -> VPNTransferStats:
        """
        Parse transfer statistics from wg show output.

        Example line: "transfer: 1.23 MiB received, 456 KiB sent"
        """
        stats = VPNTransferStats()

        try:
            transfer = line.split(":", 1)[1].strip()
            parts = transfer.split(",")

            if len(parts) == 2:
                recv_parts = parts[0].strip().split()
                if len(recv_parts) >= 2:
                    stats.received = f"{recv_parts[0]} {recv_parts[1]}"
                    stats.received_bytes = self._parse_size_to_bytes(
                        recv_parts[0], recv_parts[1]
                    )

                sent_parts = parts[1].strip().split()
                if len(sent_parts) >= 2:
                    stats.sent = f"{sent_parts[0]} {sent_parts[1]}"
                    stats.sent_bytes = self._parse_size_to_bytes(
                        sent_parts[0], sent_parts[1]
                    )

        except (IndexError, ValueError) as e:
            logger.debug(f"Error parsing transfer stats: {e}")

        return stats

    def _parse_size_to_bytes(self, value: str, unit: str) -> int:
        """Convert size string to bytes."""
        try:
            num = float(value)
            unit = unit.lower()
            multipliers = {
                "b": 1,
                "kib": 1024,
                "mib": 1024 ** 2,
                "gib": 1024 ** 3,
                "tib": 1024 ** 4,
                "kb": 1000,
                "mb": 1000 ** 2,
                "gb": 1000 ** 3,
                "tb": 1000 ** 4,
            }
            return int(num * multipliers.get(unit, 1))
        except (ValueError, TypeError):
            return 0

    def list_profiles(self) -> list[VPNProfileInfo]:
        """List all available WireGuard profiles."""
        profiles = []

        if not self.profiles_dir.exists():
            return profiles

        active_profile_path = self._get_active_profile_path()

        for conf_file in self.profiles_dir.glob("*.conf"):
            is_active = False

            if active_profile_path:
                try:
                    is_active = conf_file.resolve() == active_profile_path
                except OSError:
                    pass

            profiles.append(VPNProfileInfo(
                name=conf_file.stem,
                vpn_type=VPNType.WIREGUARD,
                active=is_active,
                filename=conf_file.name,
            ))

        return profiles

    def _get_active_profile_path(self) -> Optional[Path]:
        """Get the path of the currently active profile."""
        if not Paths.WG_ACTIVE_CONF.exists():
            return None

        try:
            return Paths.WG_ACTIVE_CONF.resolve()
        except OSError:
            return None

    def upload_profile(self, filename: str, content: bytes) -> str:
        """Upload a new WireGuard profile without activating it."""
        # Check file size
        if len(content) > Limits.MAX_VPN_PROFILE_SIZE:
            raise FileTooLargeError(
                max_size=Limits.MAX_VPN_PROFILE_SIZE,
                actual_size=len(content),
            )

        # Sanitize filename
        safe_filename = sanitize_filename(filename)
        if not safe_filename.endswith('.conf'):
            safe_filename += '.conf'

        # Validate WireGuard config
        self.validate_config(content)

        # Save profile
        profile_path = self.profiles_dir / safe_filename
        self._ensure_profiles_dir()

        with open(profile_path, "wb") as f:
            f.write(content)

        # Set secure permissions
        os.chmod(profile_path, 0o600)

        logger.info(f"WireGuard profile uploaded: {safe_filename}")
        return safe_filename

    def import_profile(self, filename: str, content: bytes) -> str:
        """Import and immediately activate a WireGuard profile."""
        safe_filename = self.upload_profile(filename, content)
        profile_name = safe_filename.replace('.conf', '')

        self.activate_profile(profile_name)

        logger.info(f"WireGuard profile imported and activated: {profile_name}")
        return profile_name

    def activate_profile(self, name: str) -> bool:
        """Activate a WireGuard profile."""
        safe_name = sanitize_filename(name)
        if safe_name.endswith('.conf'):
            safe_name = safe_name[:-5]

        profile_path = self.profiles_dir / f"{safe_name}.conf"

        if not profile_path.exists():
            raise VPNProfileNotFoundError(safe_name)

        # Stop current VPN
        CommandRunner.wg_stop()

        # Update symlink
        self._update_active_symlink(profile_path)

        # Start VPN with new profile
        CommandRunner.wg_start()

        logger.info(f"WireGuard profile activated: {safe_name}")
        return True

    def delete_profile(self, name: str) -> bool:
        """Delete a WireGuard profile."""
        safe_name = sanitize_filename(name)
        if safe_name.endswith('.conf'):
            safe_name = safe_name[:-5]

        profile_path = self.profiles_dir / f"{safe_name}.conf"

        if not profile_path.exists():
            raise VPNProfileNotFoundError(safe_name)

        # Check if this is the active profile
        active_path = self._get_active_profile_path()
        if active_path:
            try:
                if profile_path.resolve() == active_path:
                    raise VPNProfileActiveError(safe_name)
            except OSError:
                pass

        profile_path.unlink()

        logger.info(f"WireGuard profile deleted: {safe_name}")
        return True

    def _update_active_symlink(self, profile_path: Path) -> None:
        """Update the active profile symlink."""
        if Paths.WG_ACTIVE_CONF.exists() or Paths.WG_ACTIVE_CONF.is_symlink():
            Paths.WG_ACTIVE_CONF.unlink()

        Paths.WG_ACTIVE_CONF.symlink_to(profile_path)

    def _ensure_profiles_dir(self) -> None:
        """Ensure the profiles directory exists."""
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def start(self) -> bool:
        """Start the WireGuard VPN connection."""
        logger.info("Starting WireGuard VPN")

        if not CommandRunner.wg_start():
            raise VPNConnectionError("Failed to start WireGuard VPN", operation="start")

        return True

    def stop(self) -> bool:
        """Stop the WireGuard VPN connection."""
        logger.info("Stopping WireGuard VPN")

        if not CommandRunner.wg_stop():
            raise VPNConnectionError("Failed to stop WireGuard VPN", operation="stop")

        return True

    def restart(self) -> bool:
        """Restart the WireGuard VPN connection."""
        logger.info("Restarting WireGuard VPN")

        if not CommandRunner.wg_restart():
            raise VPNConnectionError("Failed to restart WireGuard VPN", operation="restart")

        return True

    def is_active(self) -> bool:
        """Quick check if WireGuard VPN is currently active."""
        return self.get_status().active

    def validate_config(self, content: bytes) -> bool:
        """Validate a WireGuard configuration file."""
        validate_wireguard_config(content)
        return True
