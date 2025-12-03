"""
Input Validation Functions
==========================

This module contains functions for validating user input before processing.
Validation ensures data meets requirements and helps prevent security issues.

Each validator raises a specific exception type on failure, making error
handling clear and consistent throughout the application.

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import re

from config import Limits, Patterns
from exceptions import (
    InvalidFilenameError,
    InvalidSSIDError,
    InvalidPasswordError,
    InvalidHostError,
    InvalidWireGuardConfigError,
)


def validate_filename(filename: str) -> str:
    """
    Validate a filename for safety.

    Ensures the filename:
    - Is not empty
    - Contains only safe characters (alphanumeric, dash, underscore, dot)
    - Doesn't exceed maximum length
    - Doesn't start with a dot (hidden files)
    - Has no path components

    Args:
        filename: The filename to validate

    Returns:
        The validated filename (may be modified for safety)

    Raises:
        InvalidFilenameError: If filename is invalid or unsafe
    """
    if not filename:
        raise InvalidFilenameError("Filename is required")

    # Get only the base name (remove any path components)
    import os
    basename = os.path.basename(filename)

    if not basename:
        raise InvalidFilenameError("Invalid filename")

    # Check for only allowed characters
    sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', basename)

    # Ensure it doesn't start with a dot (hidden file)
    if sanitized.startswith('.'):
        sanitized = '_' + sanitized[1:]

    # Ensure reasonable length
    if len(sanitized) > Limits.MAX_FILENAME_LENGTH:
        sanitized = sanitized[:Limits.MAX_FILENAME_LENGTH]

    if not sanitized:
        raise InvalidFilenameError("Invalid filename after sanitization")

    return sanitized


def validate_ssid(ssid: str) -> str:
    """
    Validate a WiFi SSID.

    SSIDs must:
    - Not be empty
    - Not exceed 32 characters (WiFi standard limit)
    - Not contain control characters or newlines

    Args:
        ssid: The SSID to validate

    Returns:
        The validated SSID

    Raises:
        InvalidSSIDError: If SSID is invalid
    """
    if not ssid or len(ssid) < 1:
        raise InvalidSSIDError("SSID cannot be empty")

    if len(ssid) > Limits.MAX_SSID_LENGTH:
        raise InvalidSSIDError(f"SSID cannot exceed {Limits.MAX_SSID_LENGTH} characters")

    # Remove control characters
    cleaned = ssid.replace('\n', '').replace('\r', '').replace('\x00', '')

    # Remove leading comment character
    cleaned = cleaned.lstrip('#')

    if not cleaned:
        raise InvalidSSIDError("Invalid SSID after sanitization")

    return cleaned


def validate_wpa_password(password: str) -> str:
    """
    Validate a WPA/WPA2/WPA3 password.

    Passwords must:
    - Be at least 8 characters (WPA requirement)
    - Not exceed 63 characters (WPA requirement)
    - Not contain control characters

    Args:
        password: The password to validate

    Returns:
        The validated password

    Raises:
        InvalidPasswordError: If password doesn't meet requirements
    """
    if not password:
        raise InvalidPasswordError("Password is required")

    if len(password) < Limits.MIN_PASSWORD_LENGTH:
        raise InvalidPasswordError(
            f"Password must be at least {Limits.MIN_PASSWORD_LENGTH} characters"
        )

    if len(password) > Limits.MAX_PASSWORD_LENGTH:
        raise InvalidPasswordError(
            f"Password cannot exceed {Limits.MAX_PASSWORD_LENGTH} characters"
        )

    # Remove control characters
    cleaned = password.replace('\n', '').replace('\r', '').replace('\x00', '')

    # Remove leading comment character
    cleaned = cleaned.lstrip('#')

    if len(cleaned) < Limits.MIN_PASSWORD_LENGTH:
        raise InvalidPasswordError("Invalid password after sanitization")

    return cleaned


def validate_ping_host(host: str) -> str:
    """
    Validate a ping host (IP address or hostname).

    Ensures the host:
    - Is not empty
    - Is a valid IPv4 address or hostname
    - Contains no shell metacharacters

    Args:
        host: IP address or hostname to validate

    Returns:
        The validated host string

    Raises:
        InvalidHostError: If host is invalid or contains dangerous characters
    """
    if not host:
        raise InvalidHostError("Ping host is required")

    # Remove whitespace
    host = host.strip()

    if not host:
        raise InvalidHostError("Ping host cannot be empty")

    # Check for valid IPv4 address or hostname
    is_ipv4 = re.match(Patterns.IPV4_ADDRESS, host) is not None
    is_hostname = re.match(Patterns.HOSTNAME, host) is not None

    if not (is_ipv4 or is_hostname):
        raise InvalidHostError("Invalid IP address or hostname format")

    # Check for shell metacharacters (security)
    for char in Patterns.DANGEROUS_CHARS:
        if char in host:
            raise InvalidHostError("Invalid characters in ping host")

    return host


def validate_wireguard_config(content: bytes) -> bool:
    """
    Validate a WireGuard configuration file.

    Performs basic validation to ensure the config:
    - Is valid UTF-8 text
    - Contains an [Interface] section
    - Contains a PrivateKey field

    Args:
        content: File content as bytes

    Returns:
        True if the config appears valid

    Raises:
        InvalidWireGuardConfigError: If the config is invalid
    """
    try:
        text = content.decode('utf-8')
    except (UnicodeDecodeError, AttributeError):
        raise InvalidWireGuardConfigError("Config file must be valid UTF-8 text")

    # Must contain [Interface] section
    if '[Interface]' not in text:
        raise InvalidWireGuardConfigError(
            "Config must contain an [Interface] section"
        )

    # Check for required fields in Interface section
    if 'PrivateKey' not in text:
        raise InvalidWireGuardConfigError(
            "Config must contain a PrivateKey field"
        )

    return True


def validate_country_code(code: str) -> str:
    """
    Validate a country code for WiFi regulation.

    Args:
        code: Two-letter country code

    Returns:
        Validated uppercase country code, or "US" as default

    Example:
        >>> validate_country_code("be")
        'BE'
        >>> validate_country_code("invalid")
        'US'
    """
    if not code:
        return "US"

    code = code.upper()[:2]

    if re.match(Patterns.COUNTRY_CODE, code):
        return code

    return "US"


def validate_wifi_channel(channel: int, band: str) -> int:
    """
    Validate a WiFi channel for the given band.

    Args:
        channel: Channel number
        band: WiFi band ("2.4GHz" or "5GHz")

    Returns:
        Valid channel number (may be adjusted if out of range)
    """
    from config import Network

    if band == "5GHz":
        if channel in Network.VALID_5GHZ_CHANNELS:
            return channel
        return Network.DEFAULT_5GHZ_CHANNEL
    else:
        # 2.4GHz: channels 1-13
        if 1 <= channel <= 13:
            return channel
        return Network.DEFAULT_2GHZ_CHANNEL


def validate_check_interval(interval: int) -> int:
    """
    Validate a VPN watchdog check interval.

    Args:
        interval: Interval in seconds

    Returns:
        Valid interval (clamped to allowed range)
    """
    if interval < Limits.MIN_CHECK_INTERVAL:
        return Limits.MIN_CHECK_INTERVAL
    if interval > Limits.MAX_CHECK_INTERVAL:
        return Limits.MAX_CHECK_INTERVAL
    return interval
