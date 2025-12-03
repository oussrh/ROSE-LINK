"""
OpenVPN VPN Provider
====================

OpenVPN implementation of the VPN provider interface.

Features:
- Upload and store OpenVPN profiles (.ovpn)
- Support for embedded certificates
- Support for username/password authentication
- Start/stop/restart VPN connections
- Monitor VPN status from logs

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import Limits
from exceptions import (
    VPNProfileNotFoundError,
    VPNProfileActiveError,
    VPNConnectionError,
    FileTooLargeError,
    ValidationError,
)
from utils.command_runner import run_command, CommandRunner
from utils.sanitizers import sanitize_filename

from .base import VPNProvider, VPNType, VPNConnectionStatus, VPNTransferStats, VPNProfileInfo

logger = logging.getLogger("rose-link.vpn.openvpn")

# OpenVPN configuration
OPENVPN_PROFILES_DIR = Path("/etc/openvpn/client")
OPENVPN_ACTIVE_CONF = Path("/etc/openvpn/client/active.conf")
OPENVPN_AUTH_FILE = Path("/etc/openvpn/client/auth.txt")
OPENVPN_SERVICE = "openvpn-client@active"
OPENVPN_STATUS_FILE = Path("/var/run/openvpn/active.status")


class OpenVPNProvider(VPNProvider):
    """
    OpenVPN VPN provider implementation.

    Manages OpenVPN VPN profiles and connections using
    openvpn systemd service.
    """

    @property
    def vpn_type(self) -> VPNType:
        return VPNType.OPENVPN

    @property
    def interface_name(self) -> str:
        return "tun0"

    @property
    def profiles_dir(self) -> Path:
        return OPENVPN_PROFILES_DIR

    @property
    def file_extension(self) -> str:
        return ".ovpn"

    def get_status(self) -> VPNConnectionStatus:
        """
        Get current OpenVPN connection status.

        Parses status from the OpenVPN status file and journalctl.
        """
        status = VPNConnectionStatus(
            vpn_type=VPNType.OPENVPN,
            interface=self.interface_name,
        )

        # Check if service is running
        if not CommandRunner.is_service_active(OPENVPN_SERVICE):
            return status

        # Check if interface exists
        ret, out, _ = run_command(f"ip addr show {self.interface_name}", timeout=5)
        if ret != 0:
            return status

        status.active = True

        # Parse interface IP
        ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', out)
        if ip_match:
            status.local_ip = ip_match.group(1)

        # Try to get status from status file
        if OPENVPN_STATUS_FILE.exists():
            try:
                status_data = self._parse_status_file()
                if status_data:
                    status.connected_since = status_data.get("connected_since")
                    status.endpoint = status_data.get("endpoint")
                    status.transfer = status_data.get("transfer", VPNTransferStats())
            except Exception as e:
                logger.debug(f"Error parsing OpenVPN status file: {e}")

        # Fallback: get info from journalctl
        if not status.endpoint:
            endpoint = self._get_endpoint_from_logs()
            if endpoint:
                status.endpoint = endpoint

        return status

    def _parse_status_file(self) -> Optional[dict]:
        """Parse OpenVPN status file for connection details."""
        if not OPENVPN_STATUS_FILE.exists():
            return None

        try:
            with open(OPENVPN_STATUS_FILE, "r") as f:
                content = f.read()

            result = {}

            # Parse connected since
            connected_match = re.search(r'Connected Since[,:](.+)', content)
            if connected_match:
                result["connected_since"] = connected_match.group(1).strip()

            # Parse transfer stats
            # Format: "TUN/TAP read bytes,123456" or similar
            recv_match = re.search(r'TUN/TAP read bytes[,:](\d+)', content)
            sent_match = re.search(r'TUN/TAP write bytes[,:](\d+)', content)

            if recv_match or sent_match:
                recv_bytes = int(recv_match.group(1)) if recv_match else 0
                sent_bytes = int(sent_match.group(1)) if sent_match else 0

                result["transfer"] = VPNTransferStats(
                    received=self._format_bytes(recv_bytes),
                    sent=self._format_bytes(sent_bytes),
                    received_bytes=recv_bytes,
                    sent_bytes=sent_bytes,
                )

            return result

        except Exception as e:
            logger.debug(f"Error reading status file: {e}")
            return None

    def _get_endpoint_from_logs(self) -> Optional[str]:
        """Extract endpoint from OpenVPN logs."""
        try:
            ret, out, _ = run_command(
                f"journalctl -u {OPENVPN_SERVICE} -n 50 --no-pager",
                timeout=10
            )
            if ret != 0:
                return None

            # Look for connection line: "TCP/UDP: Connecting to [AF_INET]1.2.3.4:1194"
            match = re.search(r'Connecting to \[AF_INET\]([0-9.:]+)', out)
            if match:
                return match.group(1)

            # Alternative format: "peer info: IV_PLAT=..."
            match = re.search(r'Peer Connection Initiated with \[AF_INET\]([0-9.:]+)', out)
            if match:
                return match.group(1)

        except Exception as e:
            logger.debug(f"Error getting endpoint from logs: {e}")

        return None

    def _format_bytes(self, size: int) -> str:
        """Format bytes to human-readable string."""
        for unit in ["B", "KiB", "MiB", "GiB", "TiB"]:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PiB"

    def list_profiles(self) -> list[VPNProfileInfo]:
        """List all available OpenVPN profiles."""
        profiles = []

        if not self.profiles_dir.exists():
            return profiles

        active_profile_path = self._get_active_profile_path()

        for conf_file in self.profiles_dir.glob("*.ovpn"):
            is_active = False

            if active_profile_path:
                try:
                    is_active = conf_file.resolve() == active_profile_path
                except OSError:
                    pass

            profiles.append(VPNProfileInfo(
                name=conf_file.stem,
                vpn_type=VPNType.OPENVPN,
                active=is_active,
                filename=conf_file.name,
            ))

        return profiles

    def _get_active_profile_path(self) -> Optional[Path]:
        """Get the path of the currently active profile."""
        if not OPENVPN_ACTIVE_CONF.exists():
            return None

        try:
            if OPENVPN_ACTIVE_CONF.is_symlink():
                return OPENVPN_ACTIVE_CONF.resolve()
            return OPENVPN_ACTIVE_CONF
        except OSError:
            return None

    def upload_profile(self, filename: str, content: bytes) -> str:
        """Upload a new OpenVPN profile without activating it."""
        # Check file size
        if len(content) > Limits.MAX_VPN_PROFILE_SIZE:
            raise FileTooLargeError(
                max_size=Limits.MAX_VPN_PROFILE_SIZE,
                actual_size=len(content),
            )

        # Sanitize filename
        safe_filename = sanitize_filename(filename)
        if not safe_filename.endswith('.ovpn'):
            safe_filename += '.ovpn'

        # Validate OpenVPN config
        self.validate_config(content)

        # Save profile
        profile_path = self.profiles_dir / safe_filename
        self._ensure_profiles_dir()

        with open(profile_path, "wb") as f:
            f.write(content)

        # Set secure permissions
        os.chmod(profile_path, 0o600)

        logger.info(f"OpenVPN profile uploaded: {safe_filename}")
        return safe_filename

    def import_profile(self, filename: str, content: bytes) -> str:
        """Import and immediately activate an OpenVPN profile."""
        safe_filename = self.upload_profile(filename, content)
        profile_name = safe_filename.replace('.ovpn', '')

        self.activate_profile(profile_name)

        logger.info(f"OpenVPN profile imported and activated: {profile_name}")
        return profile_name

    def activate_profile(self, name: str) -> bool:
        """Activate an OpenVPN profile."""
        safe_name = sanitize_filename(name)
        if safe_name.endswith('.ovpn'):
            safe_name = safe_name[:-5]

        profile_path = self.profiles_dir / f"{safe_name}.ovpn"

        if not profile_path.exists():
            raise VPNProfileNotFoundError(safe_name)

        # Stop current VPN
        self.stop()

        # Update symlink
        self._update_active_symlink(profile_path)

        # Start VPN with new profile
        self.start()

        logger.info(f"OpenVPN profile activated: {safe_name}")
        return True

    def delete_profile(self, name: str) -> bool:
        """Delete an OpenVPN profile."""
        safe_name = sanitize_filename(name)
        if safe_name.endswith('.ovpn'):
            safe_name = safe_name[:-5]

        profile_path = self.profiles_dir / f"{safe_name}.ovpn"

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

        logger.info(f"OpenVPN profile deleted: {safe_name}")
        return True

    def _update_active_symlink(self, profile_path: Path) -> None:
        """Update the active profile symlink."""
        if OPENVPN_ACTIVE_CONF.exists() or OPENVPN_ACTIVE_CONF.is_symlink():
            OPENVPN_ACTIVE_CONF.unlink()

        OPENVPN_ACTIVE_CONF.symlink_to(profile_path)

    def _ensure_profiles_dir(self) -> None:
        """Ensure the profiles directory exists."""
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def start(self) -> bool:
        """Start the OpenVPN VPN connection."""
        logger.info("Starting OpenVPN VPN")

        if not CommandRunner.start_service(OPENVPN_SERVICE):
            raise VPNConnectionError("Failed to start OpenVPN VPN", operation="start")

        return True

    def stop(self) -> bool:
        """Stop the OpenVPN VPN connection."""
        logger.info("Stopping OpenVPN VPN")

        # Stop service (ignore errors if not running)
        CommandRunner.stop_service(OPENVPN_SERVICE)
        return True

    def restart(self) -> bool:
        """Restart the OpenVPN VPN connection."""
        logger.info("Restarting OpenVPN VPN")

        if not CommandRunner.restart_service(OPENVPN_SERVICE):
            raise VPNConnectionError("Failed to restart OpenVPN VPN", operation="restart")

        return True

    def is_active(self) -> bool:
        """Quick check if OpenVPN VPN is currently active."""
        return CommandRunner.is_service_active(OPENVPN_SERVICE)

    def validate_config(self, content: bytes) -> bool:
        """
        Validate an OpenVPN configuration file.

        Checks for required directives and dangerous options.
        """
        try:
            config_text = content.decode("utf-8")
        except UnicodeDecodeError:
            raise ValidationError("OpenVPN config must be valid UTF-8 text")

        lines = config_text.strip().split("\n")

        if not lines:
            raise ValidationError("OpenVPN config file is empty")

        # Check for at least a remote directive or embedded config
        has_remote = False
        has_client = False

        for line in lines:
            line = line.strip().lower()

            # Skip comments and empty lines
            if not line or line.startswith("#") or line.startswith(";"):
                continue

            if line.startswith("remote "):
                has_remote = True
            elif line == "client":
                has_client = True

            # Check for dangerous directives
            dangerous = [
                "script-security",
                "up ",
                "down ",
                "route-up",
                "route-pre-down",
                "ipchange",
                "client-connect",
                "client-disconnect",
                "learn-address",
                "auth-user-pass-verify",
                "tls-verify",
            ]

            for d in dangerous:
                if line.startswith(d):
                    logger.warning(f"OpenVPN config contains potentially dangerous directive: {d}")
                    # We allow these but log a warning

        # Check for <connection> blocks (alternative to remote)
        if "<connection>" in config_text.lower():
            has_remote = True

        if not has_remote:
            raise ValidationError(
                "OpenVPN config must contain a 'remote' directive or <connection> block"
            )

        if not has_client:
            logger.warning("OpenVPN config doesn't have 'client' directive, may not work as expected")

        return True

    def set_credentials(self, username: str, password: str) -> bool:
        """
        Set credentials for OpenVPN auth-user-pass.

        Creates an auth file that OpenVPN can use for automatic login.

        Args:
            username: VPN username
            password: VPN password

        Returns:
            True if successful
        """
        try:
            self._ensure_profiles_dir()

            with open(OPENVPN_AUTH_FILE, "w") as f:
                f.write(f"{username}\n{password}\n")

            os.chmod(OPENVPN_AUTH_FILE, 0o600)

            logger.info("OpenVPN credentials saved")
            return True

        except Exception as e:
            logger.error(f"Failed to save OpenVPN credentials: {e}")
            return False

    def clear_credentials(self) -> bool:
        """
        Clear saved OpenVPN credentials.

        Returns:
            True if successful
        """
        try:
            if OPENVPN_AUTH_FILE.exists():
                OPENVPN_AUTH_FILE.unlink()
                logger.info("OpenVPN credentials cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear OpenVPN credentials: {e}")
            return False
