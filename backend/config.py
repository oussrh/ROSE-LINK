"""
ROSE Link Configuration Module
==============================

Centralized configuration for all paths, constants, and settings.
This module provides a single source of truth for configuration values,
making the codebase easier to maintain and debug.

Configuration can be customized via environment variables:
- ROSE_LINK_DIR: Base installation directory (default: /opt/rose-link)
- ROSE_WG_DIR: WireGuard configuration directory (default: /etc/wireguard)
- ROSE_HOSTAPD_CONF: hostapd config path (default: /etc/hostapd/hostapd.conf)
- ROSE_DNSMASQ_LEASES: dnsmasq leases path (default: /var/lib/misc/dnsmasq.leases)
- ROSE_DEFAULT_ETH_INTERFACE: Default ethernet interface (default: eth0)
- ROSE_DEFAULT_WIFI_WAN_INTERFACE: Default WiFi WAN interface (default: wlan0)
- ROSE_DEFAULT_WIFI_AP_INTERFACE: Default WiFi AP interface (default: wlan0)
- ROSE_SERVER_HOST: API server bind host (default: 127.0.0.1)
- ROSE_SERVER_PORT: API server bind port (default: 8000)
- ROSE_LOG_LEVEL: Logging level (default: info)
- ROSE_COMMAND_TIMEOUT: Default command timeout in seconds (default: 30)

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path
from typing import Final


def _get_env_path(key: str, default: str) -> Path:
    """Get a path from environment variable or use default."""
    return Path(os.environ.get(key, default))


def _get_env_str(key: str, default: str) -> str:
    """Get a string from environment variable or use default."""
    return os.environ.get(key, default)


def _get_env_int(key: str, default: int) -> int:
    """Get an integer from environment variable or use default."""
    value = os.environ.get(key)
    if value is not None:
        try:
            return int(value)
        except ValueError:
            pass
    return default


# =============================================================================
# Application Metadata
# =============================================================================

def _load_version() -> str:
    """Load version from VERSION file or return default."""
    version_paths = [
        Path(__file__).parent.parent / "VERSION",  # Development: repo root
        Path("/opt/rose-link/VERSION"),             # Production: installed
        Path(__file__).parent / "VERSION",          # Alternative location
    ]
    for version_path in version_paths:
        if version_path.exists():
            try:
                return version_path.read_text().strip()
            except (OSError, IOError):
                pass
    return "1.0.0"  # Fallback version

APP_NAME: Final[str] = "ROSE Link"
APP_VERSION: Final[str] = _load_version()
APP_DESCRIPTION: Final[str] = "REST API for ROSE Link VPN Router"


# =============================================================================
# File System Paths
# =============================================================================

class Paths:
    """
    Centralized file system paths used throughout the application.

    All paths are defined as Path objects for type safety and
    cross-platform compatibility.

    Paths can be customized via environment variables:
    - ROSE_LINK_DIR: Base installation directory
    - ROSE_WG_DIR: WireGuard directory
    - ROSE_HOSTAPD_CONF: hostapd configuration file
    - ROSE_DNSMASQ_LEASES: dnsmasq leases file
    """

    # Base directories (configurable via environment)
    ROSE_LINK_DIR: Final[Path] = _get_env_path("ROSE_LINK_DIR", "/opt/rose-link")
    SYSTEM_DIR: Final[Path] = ROSE_LINK_DIR / "system"
    WEB_DIR: Final[Path] = ROSE_LINK_DIR / "web"

    # API Key files (sensitive - stored with 0o600 permissions)
    API_KEY_FILE: Final[Path] = SYSTEM_DIR / ".api_key"
    API_KEY_HASH_FILE: Final[Path] = SYSTEM_DIR / ".api_key_hash"

    # WireGuard VPN paths (configurable via environment)
    WG_DIR: Final[Path] = _get_env_path("ROSE_WG_DIR", "/etc/wireguard")
    WG_PROFILES_DIR: Final[Path] = WG_DIR / "profiles"
    WG_ACTIVE_CONF: Final[Path] = WG_DIR / "wg0.conf"

    # Network service configuration files (configurable via environment)
    HOSTAPD_CONF: Final[Path] = _get_env_path(
        "ROSE_HOSTAPD_CONF", "/etc/hostapd/hostapd.conf"
    )
    DNSMASQ_LEASES: Final[Path] = _get_env_path(
        "ROSE_DNSMASQ_LEASES", "/var/lib/misc/dnsmasq.leases"
    )

    # ROSE Link configuration files
    INTERFACES_CONF: Final[Path] = SYSTEM_DIR / "interfaces.conf"
    VPN_SETTINGS_CONF: Final[Path] = SYSTEM_DIR / "vpn-settings.conf"

    # System information paths
    DEVICE_TREE_MODEL: Final[Path] = Path("/proc/device-tree/model")
    OS_RELEASE: Final[Path] = Path("/etc/os-release")
    THERMAL_ZONE: Final[Path] = Path("/sys/class/thermal/thermal_zone0/temp")
    PROC_UPTIME: Final[Path] = Path("/proc/uptime")
    PROC_STAT: Final[Path] = Path("/proc/stat")
    SYS_NET: Final[Path] = Path("/sys/class/net")


# =============================================================================
# Security Settings
# =============================================================================

class Security:
    """Security-related configuration constants."""

    # Session management
    SESSION_DURATION: Final[timedelta] = timedelta(hours=24)

    # File permissions
    SECURE_FILE_MODE: Final[int] = 0o600  # Owner read/write only

    # API key settings
    API_KEY_LENGTH: Final[int] = 32  # bytes for token_urlsafe

    # CORS - Allowed origins (local network only)
    ALLOWED_ORIGINS: Final[list[str]] = [
        "http://localhost",
        "http://localhost:8000",
        "http://127.0.0.1",
        "http://127.0.0.1:8000",
        "https://localhost",
        "https://127.0.0.1",
        "http://192.168.50.1",
        "https://192.168.50.1",
        "https://roselink.local",
        "http://roselink.local",
    ]

    # Allowed HTTP methods
    ALLOWED_METHODS: Final[list[str]] = ["GET", "POST", "DELETE"]

    # Allowed headers
    ALLOWED_HEADERS: Final[list[str]] = [
        "Content-Type",
        "X-API-Key",
        "Authorization",
    ]


# =============================================================================
# Limits and Constraints
# =============================================================================

class Limits:
    """
    Application limits and constraints.

    Configurable via environment variables:
    - ROSE_COMMAND_TIMEOUT: Default command timeout in seconds
    """

    # File size limits
    MAX_VPN_PROFILE_SIZE: Final[int] = 1024 * 1024  # 1 MB
    MAX_FILENAME_LENGTH: Final[int] = 100

    # WiFi constraints
    MAX_SSID_LENGTH: Final[int] = 32
    MIN_PASSWORD_LENGTH: Final[int] = 8
    MAX_PASSWORD_LENGTH: Final[int] = 63

    # VPN watchdog settings
    MIN_CHECK_INTERVAL: Final[int] = 30  # seconds
    MAX_CHECK_INTERVAL: Final[int] = 300  # seconds
    DEFAULT_CHECK_INTERVAL: Final[int] = 60
    DEFAULT_PING_HOST: Final[str] = "8.8.8.8"

    # Command execution (configurable via environment)
    DEFAULT_COMMAND_TIMEOUT: Final[int] = _get_env_int("ROSE_COMMAND_TIMEOUT", 30)

    # Log retrieval
    DEFAULT_LOG_LINES: Final[int] = 100


# =============================================================================
# Network Configuration
# =============================================================================

class Network:
    """
    Network-related configuration.

    Configurable via environment variables:
    - ROSE_DEFAULT_ETH_INTERFACE: Default ethernet interface
    - ROSE_DEFAULT_WIFI_WAN_INTERFACE: Default WiFi WAN interface
    - ROSE_DEFAULT_WIFI_AP_INTERFACE: Default WiFi AP interface
    """

    # Default interface names (configurable via environment)
    DEFAULT_ETH_INTERFACE: Final[str] = _get_env_str(
        "ROSE_DEFAULT_ETH_INTERFACE", "eth0"
    )
    DEFAULT_WIFI_WAN_INTERFACE: Final[str] = _get_env_str(
        "ROSE_DEFAULT_WIFI_WAN_INTERFACE", "wlan0"
    )
    DEFAULT_WIFI_AP_INTERFACE: Final[str] = _get_env_str(
        "ROSE_DEFAULT_WIFI_AP_INTERFACE", "wlan0"
    )

    # Alternative interface names (for different Pi models)
    ALT_ETH_INTERFACES: Final[tuple[str, ...]] = ("eth0", "end0", "enp1s0")

    # WireGuard interface
    WG_INTERFACE: Final[str] = "wg0"

    # Valid 5GHz WiFi channels
    VALID_5GHZ_CHANNELS: Final[tuple[int, ...]] = (
        36, 40, 44, 48, 52, 56, 60, 64,
        100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140,
        149, 153, 157, 161, 165,
    )

    # Default channel settings
    DEFAULT_2GHZ_CHANNEL: Final[int] = 6
    DEFAULT_5GHZ_CHANNEL: Final[int] = 36


# =============================================================================
# Service Names
# =============================================================================

class Services:
    """Systemd service names."""

    # ROSE Link services
    ROSE_BACKEND: Final[str] = "rose-backend"
    ROSE_WATCHDOG: Final[str] = "rose-watchdog"

    # Network services
    HOSTAPD: Final[str] = "hostapd"
    DNSMASQ: Final[str] = "dnsmasq"

    # WireGuard service
    WG_QUICK: Final[str] = "wg-quick@wg0"

    # Valid services for log viewing
    VALID_LOG_SERVICES: Final[tuple[str, ...]] = (
        "rose-backend",
        "rose-watchdog",
        "hostapd",
        "dnsmasq",
        "wg-quick@wg0",
    )


# =============================================================================
# Validation Patterns
# =============================================================================

class Patterns:
    """Regular expression patterns for validation."""

    # Filename validation (alphanumeric, dash, underscore, dot)
    SAFE_FILENAME: Final[str] = r'^[a-zA-Z0-9._-]+$'

    # IP address validation
    IPV4_ADDRESS: Final[str] = r'^(\d{1,3}\.){3}\d{1,3}$'

    # Hostname validation
    HOSTNAME: Final[str] = r'^[a-zA-Z0-9]([a-zA-Z0-9\-\.]*[a-zA-Z0-9])?$'

    # Country code validation
    COUNTRY_CODE: Final[str] = r'^[A-Z]{2}$'

    # Characters dangerous for shell commands
    DANGEROUS_CHARS: Final[tuple[str, ...]] = (
        '&', '|', ';', '$', '`', '(', ')', '{', '}',
        '[', ']', '<', '>', '!', '\n', '\r',
    )


# =============================================================================
# Server Configuration
# =============================================================================

class Server:
    """
    Server configuration for uvicorn.

    Configurable via environment variables:
    - ROSE_SERVER_HOST: API server bind host
    - ROSE_SERVER_PORT: API server bind port
    - ROSE_LOG_LEVEL: Logging level
    """

    HOST: Final[str] = _get_env_str("ROSE_SERVER_HOST", "127.0.0.1")
    PORT: Final[int] = _get_env_int("ROSE_SERVER_PORT", 8000)
    LOG_LEVEL: Final[str] = _get_env_str("ROSE_LOG_LEVEL", "info")
