"""
ROSE Link Custom Exceptions
===========================

This module defines a hierarchy of custom exceptions for the ROSE Link
application. Using specific exception types makes error handling more
precise and debugging easier.

Exception Hierarchy:
    RoseLinkError (base)
    ├── AuthenticationError
    ├── ValidationError
    ├── ConfigurationError
    ├── VPNError
    │   ├── VPNProfileNotFoundError
    │   ├── VPNProfileActiveError
    │   └── VPNConnectionError
    ├── HotspotError
    ├── WifiError
    ├── SystemCommandError
    └── ServiceError

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

from typing import Optional


class RoseLinkError(Exception):
    """
    Base exception for all ROSE Link errors.

    All custom exceptions inherit from this class, allowing for
    catch-all error handling when needed.

    Attributes:
        message: Human-readable error message
        error_code: Optional machine-readable error code
        details: Optional additional error details
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)

    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message

    def to_dict(self) -> dict:
        """Convert exception to dictionary for API responses."""
        result = {"detail": self.message}
        if self.error_code:
            result["error_code"] = self.error_code
        if self.details:
            result["details"] = self.details
        return result


# =============================================================================
# Authentication Errors
# =============================================================================

class AuthenticationError(RoseLinkError):
    """
    Raised when authentication fails.

    This includes invalid API keys, expired sessions, and missing credentials.
    """

    def __init__(
        self,
        message: str = "Authentication required",
        error_code: str = "AUTH_REQUIRED",
        details: Optional[dict] = None,
    ):
        super().__init__(message, error_code, details)


class InvalidApiKeyError(AuthenticationError):
    """Raised when the provided API key is invalid."""

    def __init__(self, message: str = "Invalid API key"):
        super().__init__(message, error_code="INVALID_API_KEY")


class SessionExpiredError(AuthenticationError):
    """Raised when the session token has expired."""

    def __init__(self, message: str = "Session has expired"):
        super().__init__(message, error_code="SESSION_EXPIRED")


# =============================================================================
# Validation Errors
# =============================================================================

class ValidationError(RoseLinkError):
    """
    Raised when input validation fails.

    This is used for validating user input like filenames, SSIDs, passwords, etc.
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        error_code: str = "VALIDATION_ERROR",
    ):
        details = {"field": field} if field else {}
        super().__init__(message, error_code, details)
        self.field = field


class InvalidFilenameError(ValidationError):
    """Raised when a filename is invalid or unsafe."""

    def __init__(self, message: str = "Invalid filename"):
        super().__init__(message, field="filename", error_code="INVALID_FILENAME")


class InvalidSSIDError(ValidationError):
    """Raised when an SSID is invalid."""

    def __init__(self, message: str = "Invalid SSID"):
        super().__init__(message, field="ssid", error_code="INVALID_SSID")


class InvalidPasswordError(ValidationError):
    """Raised when a password doesn't meet requirements."""

    def __init__(self, message: str = "Invalid password"):
        super().__init__(message, field="password", error_code="INVALID_PASSWORD")


class InvalidHostError(ValidationError):
    """Raised when a hostname or IP address is invalid."""

    def __init__(self, message: str = "Invalid host"):
        super().__init__(message, field="host", error_code="INVALID_HOST")


# =============================================================================
# Configuration Errors
# =============================================================================

class ConfigurationError(RoseLinkError):
    """
    Raised when there's a configuration problem.

    This includes missing config files, invalid config values, etc.
    """

    def __init__(
        self,
        message: str,
        config_file: Optional[str] = None,
        error_code: str = "CONFIG_ERROR",
    ):
        details = {"config_file": config_file} if config_file else {}
        super().__init__(message, error_code, details)


# =============================================================================
# VPN Errors
# =============================================================================

class VPNError(RoseLinkError):
    """
    Base exception for VPN-related errors.

    Subclasses provide more specific error types for common VPN issues.
    """

    def __init__(
        self,
        message: str,
        error_code: str = "VPN_ERROR",
        details: Optional[dict] = None,
    ):
        super().__init__(message, error_code, details)


class VPNProfileNotFoundError(VPNError):
    """Raised when a VPN profile doesn't exist."""

    def __init__(self, profile_name: str):
        super().__init__(
            message=f"VPN profile not found: {profile_name}",
            error_code="VPN_PROFILE_NOT_FOUND",
            details={"profile": profile_name},
        )
        self.profile_name = profile_name


class VPNProfileActiveError(VPNError):
    """Raised when trying to delete an active VPN profile."""

    def __init__(self, profile_name: str):
        super().__init__(
            message=f"Cannot delete active profile: {profile_name}. Activate another profile first.",
            error_code="VPN_PROFILE_ACTIVE",
            details={"profile": profile_name},
        )
        self.profile_name = profile_name


class VPNConnectionError(VPNError):
    """Raised when VPN connection operations fail."""

    def __init__(self, message: str, operation: str):
        super().__init__(
            message=message,
            error_code="VPN_CONNECTION_ERROR",
            details={"operation": operation},
        )
        self.operation = operation


class InvalidWireGuardConfigError(VPNError):
    """Raised when a WireGuard config file is invalid."""

    def __init__(self, message: str = "Invalid WireGuard configuration file"):
        super().__init__(message, error_code="INVALID_WG_CONFIG")


# =============================================================================
# Hotspot Errors
# =============================================================================

class HotspotError(RoseLinkError):
    """
    Raised for hotspot-related errors.

    This includes configuration errors and service failures.
    """

    def __init__(
        self,
        message: str,
        error_code: str = "HOTSPOT_ERROR",
        details: Optional[dict] = None,
    ):
        super().__init__(message, error_code, details)


class HotspotConfigurationError(HotspotError):
    """Raised when hotspot configuration fails."""

    def __init__(self, message: str):
        super().__init__(message, error_code="HOTSPOT_CONFIG_ERROR")


# =============================================================================
# WiFi Errors
# =============================================================================

class WifiError(RoseLinkError):
    """
    Raised for WiFi-related errors.

    This includes scan failures and connection errors.
    """

    def __init__(
        self,
        message: str,
        error_code: str = "WIFI_ERROR",
        details: Optional[dict] = None,
    ):
        super().__init__(message, error_code, details)


class WifiScanError(WifiError):
    """Raised when WiFi scanning fails."""

    def __init__(self, message: str):
        super().__init__(message, error_code="WIFI_SCAN_ERROR")


class WifiConnectionError(WifiError):
    """Raised when WiFi connection fails."""

    def __init__(self, message: str, ssid: Optional[str] = None):
        details = {"ssid": ssid} if ssid else {}
        super().__init__(message, error_code="WIFI_CONNECTION_ERROR", details=details)
        self.ssid = ssid


# =============================================================================
# System Errors
# =============================================================================

class SystemCommandError(RoseLinkError):
    """
    Raised when a system command fails.

    Contains details about the command that failed and its output.
    """

    def __init__(
        self,
        message: str,
        command: Optional[str] = None,
        return_code: Optional[int] = None,
        stderr: Optional[str] = None,
    ):
        details = {}
        if command:
            details["command"] = command
        if return_code is not None:
            details["return_code"] = return_code
        if stderr:
            details["stderr"] = stderr

        super().__init__(message, error_code="SYSTEM_COMMAND_ERROR", details=details)
        self.command = command
        self.return_code = return_code
        self.stderr = stderr


class ServiceError(RoseLinkError):
    """
    Raised when a systemd service operation fails.

    Includes the service name and operation that failed.
    """

    def __init__(
        self,
        message: str,
        service: str,
        operation: str,
    ):
        super().__init__(
            message,
            error_code="SERVICE_ERROR",
            details={"service": service, "operation": operation},
        )
        self.service = service
        self.operation = operation


# =============================================================================
# File Errors
# =============================================================================

class FileOperationError(RoseLinkError):
    """Raised when file operations fail."""

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        operation: str = "unknown",
    ):
        details = {"operation": operation}
        if file_path:
            details["file_path"] = file_path

        super().__init__(message, error_code="FILE_OPERATION_ERROR", details=details)


class FileTooLargeError(FileOperationError):
    """Raised when an uploaded file exceeds size limits."""

    def __init__(self, max_size: int, actual_size: int):
        super().__init__(
            message=f"File too large. Maximum size: {max_size} bytes, got: {actual_size} bytes",
            operation="upload",
        )
        self.max_size = max_size
        self.actual_size = actual_size
