"""
Input Sanitization Functions
============================

This module contains functions for sanitizing user input to prevent
security vulnerabilities like injection attacks.

Sanitization differs from validation:
- Validation checks if input meets requirements (may reject input)
- Sanitization modifies input to make it safe (always produces output)

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import os
import re

from config import Limits


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent path traversal attacks.

    This function:
    1. Extracts only the base filename (removes path components)
    2. Replaces unsafe characters with underscores
    3. Removes leading dots (prevents hidden files)
    4. Truncates to maximum allowed length

    Args:
        filename: The original filename

    Returns:
        Sanitized filename with only safe characters

    Raises:
        ValueError: If filename is empty or invalid

    Example:
        >>> sanitize_filename("../../../etc/passwd")
        'passwd'
        >>> sanitize_filename("my config.conf")
        'my_config.conf'
        >>> sanitize_filename(".hidden")
        '_hidden'
    """
    if not filename:
        raise ValueError("Filename is required")

    # Get only the base name (remove any path components)
    # This prevents path traversal attacks like "../../../etc/passwd"
    basename = os.path.basename(filename)

    if not basename:
        raise ValueError("Invalid filename")

    # Remove any potentially dangerous characters
    # Only allow: alphanumeric, dash, underscore, and dot
    sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', basename)

    # Ensure it doesn't start with a dot (hidden file)
    if sanitized.startswith('.'):
        sanitized = '_' + sanitized[1:]

    # Ensure reasonable length
    if len(sanitized) > Limits.MAX_FILENAME_LENGTH:
        sanitized = sanitized[:Limits.MAX_FILENAME_LENGTH]

    if not sanitized:
        raise ValueError("Invalid filename after sanitization")

    return sanitized


def escape_hostapd_value(value: str) -> str:
    """
    Escape a value for safe use in hostapd configuration.

    Removes or escapes characters that could:
    - Break configuration file parsing
    - Enable injection attacks
    - Create hidden configuration lines

    Args:
        value: The value to escape

    Returns:
        Escaped value safe for hostapd config files

    Example:
        >>> escape_hostapd_value("MyNetwork\\nssid=evil")
        'MyNetworkssid=evil'
        >>> escape_hostapd_value("#CommentedOut")
        'CommentedOut'
    """
    # Remove newlines and carriage returns
    # These could inject new config lines
    value = value.replace('\n', '')
    value = value.replace('\r', '')

    # Remove null bytes
    value = value.replace('\x00', '')

    # Remove leading comment characters
    # Prevents commenting out the intended value
    value = value.lstrip('#')

    return value


def sanitize_service_name(service: str, allowed_services: tuple[str, ...]) -> str:
    """
    Sanitize a service name against an allowlist.

    This prevents arbitrary service manipulation by only allowing
    known, approved service names.

    Args:
        service: The service name to sanitize
        allowed_services: Tuple of allowed service names

    Returns:
        The service name if valid

    Raises:
        ValueError: If service is not in the allowed list
    """
    if service not in allowed_services:
        raise ValueError(
            f"Invalid service. Allowed: {', '.join(allowed_services)}"
        )
    return service


def sanitize_log_lines(lines: int, max_lines: int = 1000) -> int:
    """
    Sanitize the number of log lines requested.

    Ensures the number is within reasonable bounds to prevent
    excessive resource usage.

    Args:
        lines: Requested number of lines
        max_lines: Maximum allowed lines

    Returns:
        Sanitized line count (clamped to valid range)
    """
    if lines < 1:
        return 1
    if lines > max_lines:
        return max_lines
    return lines


def strip_ansi_codes(text: str) -> str:
    """
    Remove ANSI escape codes from text.

    Useful for cleaning command output before displaying or logging.

    Args:
        text: Text potentially containing ANSI codes

    Returns:
        Text with ANSI codes removed
    """
    ansi_pattern = re.compile(r'\x1b\[[0-9;]*m')
    return ansi_pattern.sub('', text)


def normalize_mac_address(mac: str) -> str:
    """
    Normalize a MAC address to lowercase with colons.

    Args:
        mac: MAC address in various formats

    Returns:
        Normalized MAC address (lowercase, colon-separated)

    Example:
        >>> normalize_mac_address("AA-BB-CC-DD-EE-FF")
        'aa:bb:cc:dd:ee:ff'
        >>> normalize_mac_address("AABBCCDDEEFF")
        'aa:bb:cc:dd:ee:ff'
    """
    # Remove common separators and convert to lowercase
    clean = mac.lower().replace('-', '').replace(':', '').replace('.', '')

    if len(clean) != 12:
        return mac.lower()  # Return original if invalid

    # Insert colons
    return ':'.join(clean[i:i+2] for i in range(0, 12, 2))
