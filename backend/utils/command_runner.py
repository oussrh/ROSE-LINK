"""
System Command Execution
========================

This module provides safe and consistent execution of system commands.
It wraps subprocess calls with proper error handling, timeouts, and logging.

Key Features:
- Configurable timeout with sensible defaults
- Structured return values (return_code, stdout, stderr)
- Automatic exception handling
- Convenience methods for common systemd operations
- Abstract interface for dependency injection and testing

Architecture:
- ICommandExecutor: Abstract interface for command execution
- SubprocessExecutor: Production implementation using subprocess
- CommandRunner: High-level convenience methods using ICommandExecutor

For testing, inject a mock ICommandExecutor via set_executor() to
avoid actual system calls.

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import logging
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from config import Limits

logger = logging.getLogger("rose-link.commands")


@dataclass
class CommandResult:
    """
    Result of a system command execution.

    Attributes:
        return_code: Exit code (0 = success, non-zero = error, -1 = exception)
        stdout: Standard output as string
        stderr: Standard error as string
        success: True if return_code is 0
    """

    return_code: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        """Check if command executed successfully."""
        return self.return_code == 0


# =============================================================================
# Abstract Command Executor Interface
# =============================================================================


class ICommandExecutor(ABC):
    """
    Abstract interface for command execution.

    This interface allows for dependency injection and mocking in tests.
    Production code uses SubprocessExecutor, while tests can inject
    a mock implementation.
    """

    @abstractmethod
    def execute(
        self,
        cmd: list[str],
        timeout: int = Limits.DEFAULT_COMMAND_TIMEOUT,
    ) -> CommandResult:
        """
        Execute a command and return the result.

        Args:
            cmd: Command and arguments as a list
            timeout: Command timeout in seconds

        Returns:
            CommandResult with return_code, stdout, stderr
        """
        pass


class SubprocessExecutor(ICommandExecutor):
    """
    Production implementation of ICommandExecutor using subprocess.

    This executor runs actual system commands and should only be used
    in production or integration tests.
    """

    def execute(
        self,
        cmd: list[str],
        timeout: int = Limits.DEFAULT_COMMAND_TIMEOUT,
    ) -> CommandResult:
        """Execute a command using subprocess.run()."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout,
            )
            return CommandResult(
                return_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )

        except subprocess.TimeoutExpired:
            logger.warning(f"Command timed out after {timeout}s: {' '.join(cmd[:3])}...")
            return CommandResult(-1, "", "Command timed out")

        except FileNotFoundError:
            logger.error(f"Command not found: {cmd[0]}")
            return CommandResult(-1, "", f"Command not found: {cmd[0]}")

        except PermissionError:
            logger.error(f"Permission denied: {cmd[0]}")
            return CommandResult(-1, "", f"Permission denied: {cmd[0]}")

        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return CommandResult(-1, "", str(e))


# Global executor instance (can be replaced for testing)
_executor: ICommandExecutor = SubprocessExecutor()


def get_executor() -> ICommandExecutor:
    """Get the current command executor instance."""
    return _executor


def set_executor(executor: ICommandExecutor) -> None:
    """
    Set the command executor instance.

    This is primarily used for testing to inject a mock executor.

    Args:
        executor: The ICommandExecutor implementation to use

    Example:
        >>> from unittest.mock import MagicMock
        >>> mock_executor = MagicMock(spec=ICommandExecutor)
        >>> mock_executor.execute.return_value = CommandResult(0, "output", "")
        >>> set_executor(mock_executor)
        >>> # Now all command execution will use the mock
    """
    global _executor
    _executor = executor


def reset_executor() -> None:
    """Reset the executor to the default SubprocessExecutor."""
    global _executor
    _executor = SubprocessExecutor()


def run_command(
    cmd: list[str],
    check: bool = True,
    timeout: int = Limits.DEFAULT_COMMAND_TIMEOUT,
) -> tuple[int, str, str]:
    """
    Execute a shell command and return the result.

    This is the primary function for executing system commands throughout
    the application. It provides consistent error handling and timeout
    management.

    Uses the global ICommandExecutor instance, which can be replaced
    for testing via set_executor().

    Args:
        cmd: Command and arguments as a list (e.g., ["ls", "-la"])
        check: If True, would normally raise on non-zero exit (ignored for compatibility)
        timeout: Command timeout in seconds (default: 30)

    Returns:
        Tuple of (return_code, stdout, stderr)
        - return_code: 0 for success, non-zero for errors, -1 for exceptions
        - stdout: Standard output as string
        - stderr: Standard error as string

    Example:
        >>> ret, out, err = run_command(["ls", "-la", "/tmp"])
        >>> if ret == 0:
        ...     print(f"Files: {out}")
        ... else:
        ...     print(f"Error: {err}")
    """
    result = _executor.execute(cmd, timeout)
    return result.return_code, result.stdout, result.stderr


class CommandRunner:
    """
    Utility class providing high-level command execution methods.

    This class provides convenience methods for common system operations,
    particularly systemd service management.

    Example:
        >>> runner = CommandRunner()
        >>> if runner.restart_service("hostapd"):
        ...     print("Hostapd restarted successfully")
    """

    @staticmethod
    def execute(
        cmd: list[str],
        timeout: int = Limits.DEFAULT_COMMAND_TIMEOUT,
    ) -> CommandResult:
        """
        Execute a command and return a structured result.

        Args:
            cmd: Command and arguments as a list
            timeout: Command timeout in seconds

        Returns:
            CommandResult with return_code, stdout, stderr, and success property
        """
        ret, out, err = run_command(cmd, check=False, timeout=timeout)
        return CommandResult(return_code=ret, stdout=out, stderr=err)

    # =========================================================================
    # Systemctl Operations
    # =========================================================================

    @staticmethod
    def systemctl(action: str, service: str) -> bool:
        """
        Execute a systemctl action on a service.

        Args:
            action: Systemctl action (start, stop, restart, reload, status)
            service: Service name

        Returns:
            True if successful, False otherwise
        """
        ret, _, err = run_command(
            ["sudo", "systemctl", action, service],
            check=False,
        )
        if ret != 0:
            logger.warning(f"systemctl {action} {service} failed: {err}")
        return ret == 0

    @staticmethod
    def start_service(service: str) -> bool:
        """Start a systemd service."""
        logger.info(f"Starting service: {service}")
        return CommandRunner.systemctl("start", service)

    @staticmethod
    def stop_service(service: str) -> bool:
        """Stop a systemd service."""
        logger.info(f"Stopping service: {service}")
        return CommandRunner.systemctl("stop", service)

    @staticmethod
    def restart_service(service: str) -> bool:
        """Restart a systemd service."""
        logger.info(f"Restarting service: {service}")
        return CommandRunner.systemctl("restart", service)

    @staticmethod
    def is_service_active(service: str) -> bool:
        """Check if a systemd service is active."""
        ret, out, _ = run_command(
            ["systemctl", "is-active", service],
            check=False,
        )
        return ret == 0 and out.strip() == "active"

    # =========================================================================
    # Network Operations
    # =========================================================================

    @staticmethod
    def get_interface_ip(interface: str) -> Optional[str]:
        """
        Get the IP address of a network interface.

        Args:
            interface: Network interface name (e.g., "eth0", "wlan0")

        Returns:
            IP address string (with CIDR notation) or None if not found
        """
        import re

        ret, out, _ = run_command(
            ["ip", "addr", "show", interface],
            check=False,
        )
        if ret == 0:
            match = re.search(r"inet\s+(\S+)", out)
            if match:
                return match.group(1)
        return None

    @staticmethod
    def wifi_scan() -> tuple[int, str, str]:
        """
        Scan for available WiFi networks using NetworkManager.

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        return run_command(
            ["sudo", "nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "device", "wifi", "list"],
            check=False,
        )

    @staticmethod
    def wifi_connect(ssid: str, password: str) -> tuple[int, str, str]:
        """
        Connect to a WiFi network using NetworkManager.

        Args:
            ssid: Network SSID
            password: Network password

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        return run_command(
            ["sudo", "nmcli", "device", "wifi", "connect", ssid, "password", password],
            check=False,
        )

    @staticmethod
    def wifi_disconnect(interface: str) -> tuple[int, str, str]:
        """
        Disconnect a WiFi interface using NetworkManager.

        Args:
            interface: WiFi interface name

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        return run_command(
            ["sudo", "nmcli", "device", "disconnect", interface],
            check=False,
        )

    # =========================================================================
    # WireGuard Operations
    # =========================================================================

    @staticmethod
    def wg_show(interface: str = "wg0") -> tuple[int, str, str]:
        """
        Get WireGuard interface status.

        Args:
            interface: WireGuard interface name (default: wg0)

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        return run_command(
            ["sudo", "wg", "show", interface],
            check=False,
        )

    @staticmethod
    def wg_start() -> bool:
        """Start WireGuard VPN."""
        return CommandRunner.start_service("wg-quick@wg0")

    @staticmethod
    def wg_stop() -> bool:
        """Stop WireGuard VPN."""
        return CommandRunner.stop_service("wg-quick@wg0")

    @staticmethod
    def wg_restart() -> bool:
        """Restart WireGuard VPN."""
        return CommandRunner.restart_service("wg-quick@wg0")

    # =========================================================================
    # Hotspot Operations
    # =========================================================================

    @staticmethod
    def get_station_dump(interface: str) -> tuple[int, str, str]:
        """
        Get connected stations for a WiFi interface.

        Args:
            interface: WiFi AP interface name

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        return run_command(
            ["iw", "dev", interface, "station", "dump"],
            check=False,
        )

    @staticmethod
    def restart_hotspot() -> bool:
        """Restart hotspot services (hostapd and dnsmasq)."""
        hostapd_ok = CommandRunner.restart_service("hostapd")
        dnsmasq_ok = CommandRunner.restart_service("dnsmasq")
        return hostapd_ok and dnsmasq_ok

    # =========================================================================
    # System Operations
    # =========================================================================

    @staticmethod
    def get_journalctl_logs(service: str, lines: int = 100) -> tuple[int, str, str]:
        """
        Get systemd journal logs for a service.

        Args:
            service: Service name
            lines: Number of lines to retrieve

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        return run_command(
            ["sudo", "journalctl", "-u", service, "-n", str(lines), "--no-pager"],
            check=False,
        )

    @staticmethod
    def reboot() -> bool:
        """Initiate system reboot."""
        logger.info("Initiating system reboot")
        ret, _, _ = run_command(["sudo", "reboot"], check=False)
        return ret == 0
