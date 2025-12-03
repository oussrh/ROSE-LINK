"""
VPN Service
===========

Handles WireGuard VPN profile management and connection control.

Features:
- Upload and store VPN profiles
- Activate/deactivate profiles via symlinks
- Start/stop/restart VPN connections
- Monitor VPN status and health
- Manage VPN watchdog settings

Profile Management:
- Profiles stored in /etc/wireguard/profiles/
- Active profile symlinked to /etc/wireguard/wg0.conf
- Systemd manages the wg-quick@wg0 service

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Optional

from config import Paths, Limits, Services
from models import (
    VPNStatus,
    TransferStats,
    VPNProfileInfo,
    VPNSettings,
)
from exceptions import (
    VPNProfileNotFoundError,
    VPNProfileActiveError,
    VPNConnectionError,
    InvalidWireGuardConfigError,
    FileTooLargeError,
)
from utils.command_runner import run_command, CommandRunner
from utils.sanitizers import sanitize_filename
from utils.validators import validate_wireguard_config

logger = logging.getLogger("rose-link.vpn")


class VPNService:
    """
    Service for WireGuard VPN management.

    This service handles all VPN-related operations including
    profile management and connection control.
    """

    @classmethod
    def get_status(cls) -> VPNStatus:
        """
        Get current VPN connection status.

        Parses output from 'wg show' command to extract:
        - Connection state
        - Endpoint address
        - Latest handshake time
        - Transfer statistics

        Returns:
            VPNStatus with connection details
        """
        status = VPNStatus()

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
                status.transfer = cls._parse_transfer_stats(line)

        return status

    @classmethod
    def _parse_transfer_stats(cls, line: str) -> TransferStats:
        """
        Parse transfer statistics from wg show output.

        Example line: "transfer: 1.23 MiB received, 456 KiB sent"

        Args:
            line: Transfer line from wg show output

        Returns:
            TransferStats with received and sent values
        """
        stats = TransferStats()

        try:
            # Extract the value after "transfer:"
            transfer = line.split(":", 1)[1].strip()
            parts = transfer.split(",")

            if len(parts) == 2:
                # Parse received (e.g., "1.23 MiB received")
                recv_parts = parts[0].strip().split()
                if len(recv_parts) >= 2:
                    stats.received = f"{recv_parts[0]} {recv_parts[1]}"

                # Parse sent (e.g., "456 KiB sent")
                sent_parts = parts[1].strip().split()
                if len(sent_parts) >= 2:
                    stats.sent = f"{sent_parts[0]} {sent_parts[1]}"

        except (IndexError, ValueError) as e:
            logger.debug(f"Error parsing transfer stats: {e}")

        return stats

    # =========================================================================
    # Profile Management
    # =========================================================================

    @classmethod
    def list_profiles(cls) -> list[VPNProfileInfo]:
        """
        List all available VPN profiles.

        Returns:
            List of VPNProfileInfo with name and active status
        """
        profiles = []

        if not Paths.WG_PROFILES_DIR.exists():
            return profiles

        # Get active profile path for comparison
        active_profile_path = cls._get_active_profile_path()

        for conf_file in Paths.WG_PROFILES_DIR.glob("*.conf"):
            is_active = False

            if active_profile_path:
                try:
                    is_active = conf_file.resolve() == active_profile_path
                except OSError:
                    pass

            profiles.append(VPNProfileInfo(
                name=conf_file.stem,
                active=is_active,
            ))

        return profiles

    @classmethod
    def _get_active_profile_path(cls) -> Optional[Path]:
        """
        Get the path of the currently active profile.

        Returns:
            Resolved path of active profile or None
        """
        if not Paths.WG_ACTIVE_CONF.exists():
            return None

        try:
            return Paths.WG_ACTIVE_CONF.resolve()
        except OSError:
            return None

    @classmethod
    def upload_profile(cls, filename: str, content: bytes) -> str:
        """
        Upload a new VPN profile without activating it.

        Args:
            filename: Original filename (will be sanitized)
            content: File content as bytes

        Returns:
            Sanitized filename of saved profile

        Raises:
            FileTooLargeError: If content exceeds size limit
            InvalidWireGuardConfigError: If config is invalid
            ValueError: If filename is invalid
        """
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
        validate_wireguard_config(content)

        # Save profile
        profile_path = Paths.WG_PROFILES_DIR / safe_filename
        cls._ensure_profiles_dir()

        with open(profile_path, "wb") as f:
            f.write(content)

        # Set secure permissions
        os.chmod(profile_path, 0o600)

        logger.info(f"VPN profile uploaded: {safe_filename}")
        return safe_filename

    @classmethod
    def import_profile(cls, filename: str, content: bytes) -> str:
        """
        Import and immediately activate a VPN profile.

        This is a convenience method that uploads the profile
        and then activates it.

        Args:
            filename: Original filename
            content: File content as bytes

        Returns:
            Profile name (without .conf)

        Raises:
            Same exceptions as upload_profile and activate_profile
        """
        # Upload the profile
        safe_filename = cls.upload_profile(filename, content)
        profile_name = safe_filename.replace('.conf', '')

        # Activate it
        cls.activate_profile(profile_name)

        logger.info(f"VPN profile imported and activated: {profile_name}")
        return profile_name

    @classmethod
    def activate_profile(cls, name: str) -> bool:
        """
        Activate a VPN profile.

        This stops any running VPN, updates the symlink to point
        to the new profile, and starts the VPN.

        Args:
            name: Profile name (without .conf extension)

        Returns:
            True if activation successful

        Raises:
            VPNProfileNotFoundError: If profile doesn't exist
        """
        # Sanitize and verify profile exists
        safe_name = sanitize_filename(name)
        if safe_name.endswith('.conf'):
            safe_name = safe_name[:-5]

        profile_path = Paths.WG_PROFILES_DIR / f"{safe_name}.conf"

        if not profile_path.exists():
            raise VPNProfileNotFoundError(safe_name)

        # Stop current VPN
        CommandRunner.wg_stop()

        # Update symlink
        cls._update_active_symlink(profile_path)

        # Start VPN with new profile
        CommandRunner.wg_start()

        logger.info(f"VPN profile activated: {safe_name}")
        return True

    @classmethod
    def delete_profile(cls, name: str) -> bool:
        """
        Delete a VPN profile.

        Cannot delete the currently active profile.

        Args:
            name: Profile name (without .conf extension)

        Returns:
            True if deletion successful

        Raises:
            VPNProfileNotFoundError: If profile doesn't exist
            VPNProfileActiveError: If trying to delete active profile
        """
        # Sanitize profile name
        safe_name = sanitize_filename(name)
        if safe_name.endswith('.conf'):
            safe_name = safe_name[:-5]

        profile_path = Paths.WG_PROFILES_DIR / f"{safe_name}.conf"

        if not profile_path.exists():
            raise VPNProfileNotFoundError(safe_name)

        # Check if this is the active profile
        active_path = cls._get_active_profile_path()
        if active_path:
            try:
                if profile_path.resolve() == active_path:
                    raise VPNProfileActiveError(safe_name)
            except OSError:
                pass

        # Delete the profile
        profile_path.unlink()

        logger.info(f"VPN profile deleted: {safe_name}")
        return True

    @classmethod
    def _update_active_symlink(cls, profile_path: Path) -> None:
        """
        Update the active profile symlink.

        Args:
            profile_path: Path to the profile to activate
        """
        # Remove existing symlink if present
        if Paths.WG_ACTIVE_CONF.exists() or Paths.WG_ACTIVE_CONF.is_symlink():
            Paths.WG_ACTIVE_CONF.unlink()

        # Create new symlink
        Paths.WG_ACTIVE_CONF.symlink_to(profile_path)

    @classmethod
    def _ensure_profiles_dir(cls) -> None:
        """Ensure the profiles directory exists."""
        Paths.WG_PROFILES_DIR.mkdir(parents=True, exist_ok=True)

    # =========================================================================
    # Connection Control
    # =========================================================================

    @classmethod
    def start(cls) -> bool:
        """
        Start the VPN connection.

        Returns:
            True if successful

        Raises:
            VPNConnectionError: If start fails or no profile is configured
        """
        logger.info("Starting VPN")

        # Check if a profile is configured
        if not Paths.WG_ACTIVE_CONF.exists():
            raise VPNConnectionError(
                "No VPN profile configured. Please import a WireGuard configuration file first.",
                operation="start"
            )

        if not CommandRunner.wg_start():
            raise VPNConnectionError("Failed to start VPN", operation="start")

        return True

    @classmethod
    def stop(cls) -> bool:
        """
        Stop the VPN connection.

        Returns:
            True if successful

        Raises:
            VPNConnectionError: If stop fails
        """
        logger.info("Stopping VPN")

        if not CommandRunner.wg_stop():
            raise VPNConnectionError("Failed to stop VPN", operation="stop")

        return True

    @classmethod
    def restart(cls) -> bool:
        """
        Restart the VPN connection.

        Returns:
            True if successful

        Raises:
            VPNConnectionError: If restart fails
        """
        logger.info("Restarting VPN")

        if not CommandRunner.wg_restart():
            raise VPNConnectionError("Failed to restart VPN", operation="restart")

        return True

    # =========================================================================
    # Watchdog Settings
    # =========================================================================

    @classmethod
    def get_settings(cls) -> VPNSettings:
        """
        Load VPN watchdog settings from configuration file.

        Returns:
            VPNSettings with ping_host and check_interval
        """
        settings = VPNSettings()

        if not Paths.VPN_SETTINGS_CONF.exists():
            return settings

        try:
            with open(Paths.VPN_SETTINGS_CONF, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()

                    if line.startswith("#") or "=" not in line:
                        continue

                    key, value = line.split("=", 1)
                    key = key.strip().lower()
                    value = value.strip().strip('"')

                    if key == "ping_host":
                        settings.ping_host = value
                    elif key == "check_interval":
                        try:
                            settings.check_interval = int(value)
                        except ValueError:
                            pass

        except (IOError, OSError) as e:
            logger.warning(f"Error reading VPN settings: {e}")

        return settings

    @classmethod
    def save_settings(cls, settings: VPNSettings) -> bool:
        """
        Save VPN watchdog settings to configuration file.

        Restarts the watchdog service to apply new settings.

        Args:
            settings: New VPN settings

        Returns:
            True if successful
        """
        try:
            config_content = f"""# ROSE Link VPN Watchdog Settings
# Auto-generated via Web API

# IP/Host to ping through VPN to verify connectivity
PING_HOST={settings.ping_host}

# Check interval in seconds (30-300)
CHECK_INTERVAL={settings.check_interval}
"""
            # Ensure directory exists
            Paths.VPN_SETTINGS_CONF.parent.mkdir(parents=True, exist_ok=True)

            with open(Paths.VPN_SETTINGS_CONF, "w", encoding="utf-8") as f:
                f.write(config_content)

            # Restart watchdog to apply settings
            CommandRunner.restart_service(Services.ROSE_WATCHDOG)

            logger.info(
                f"VPN settings saved: ping_host={settings.ping_host}, "
                f"interval={settings.check_interval}"
            )
            return True

        except (IOError, OSError) as e:
            logger.error(f"Failed to save VPN settings: {e}")
            return False

    @classmethod
    def is_active(cls) -> bool:
        """
        Quick check if VPN is currently active.

        Returns:
            True if VPN connection is up
        """
        return cls.get_status().active
