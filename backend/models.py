"""
ROSE Link Data Models
=====================

This module contains all Pydantic models and dataclasses used throughout
the application. Using typed models improves code clarity, enables
automatic validation, and makes debugging easier.

Models are organized by domain:
- Request models: Input validation for API endpoints
- Response models: Structured API responses
- Data models: Internal data structures

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Authentication Models
# =============================================================================

class LoginRequest(BaseModel):
    """Request model for user login."""

    api_key: str = Field(
        ...,
        min_length=1,
        description="API key for authentication"
    )


class LoginResponse(BaseModel):
    """Response model for successful login."""

    token: str = Field(..., description="Session token for subsequent requests")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    message: str = Field(default="Authentication successful")


class AuthStatus(BaseModel):
    """Response model for authentication check."""

    authenticated: bool
    message: str


# =============================================================================
# WiFi Models
# =============================================================================

class WifiConnectRequest(BaseModel):
    """Request model for WiFi connection."""

    ssid: str = Field(
        ...,
        min_length=1,
        max_length=32,
        description="WiFi network SSID"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=63,
        description="WiFi password"
    )


class WifiNetwork(BaseModel):
    """Model representing a WiFi network from scan results."""

    ssid: str
    signal: int = Field(ge=0, le=100, description="Signal strength percentage")
    security: str = Field(default="Open", description="Security type (WPA2, WPA3, etc.)")


class WifiScanResponse(BaseModel):
    """Response model for WiFi scan."""

    networks: list[WifiNetwork]


# =============================================================================
# VPN Models
# =============================================================================

class VPNProfile(BaseModel):
    """Model for VPN profile activation request."""

    name: str = Field(
        ...,
        min_length=1,
        description="VPN profile name (without .conf extension)"
    )
    active: bool = Field(
        default=False,
        description="Whether profile should be activated"
    )


class VPNProfileInfo(BaseModel):
    """Information about a VPN profile."""

    name: str
    active: bool = False


class VPNSettings(BaseModel):
    """Configuration model for VPN watchdog settings."""

    ping_host: str = Field(
        default="8.8.8.8",
        min_length=4,
        description="Host to ping for VPN health check"
    )
    check_interval: int = Field(
        default=60,
        ge=30,
        le=300,
        description="Check interval in seconds"
    )


@dataclass
class TransferStats:
    """VPN transfer statistics."""

    received: str = "0 B"
    sent: str = "0 B"


@dataclass
class VPNStatus:
    """Current VPN connection status."""

    active: bool = False
    interface: str = "wg0"
    endpoint: Optional[str] = None
    latest_handshake: Optional[str] = None
    transfer: TransferStats = field(default_factory=TransferStats)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "active": self.active,
            "interface": self.interface,
            "endpoint": self.endpoint,
            "latest_handshake": self.latest_handshake,
            "transfer": {
                "received": self.transfer.received,
                "sent": self.transfer.sent,
            }
        }


# =============================================================================
# Hotspot Models
# =============================================================================

class HotspotConfig(BaseModel):
    """Configuration model for WiFi hotspot settings."""

    ssid: str = Field(
        default="ROSE-Link",
        min_length=1,
        max_length=32,
        description="Hotspot SSID"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=63,
        description="Hotspot password"
    )
    country: str = Field(
        default="BE",
        min_length=2,
        max_length=2,
        description="Country code for WiFi regulation"
    )
    channel: int = Field(
        default=6,
        ge=1,
        le=165,
        description="WiFi channel"
    )
    wpa3: bool = Field(
        default=False,
        description="Enable WPA3 security"
    )
    band: str = Field(
        default="2.4GHz",
        description="WiFi band (2.4GHz or 5GHz)"
    )

    @field_validator("band")
    @classmethod
    def validate_band(cls, v: str) -> str:
        """Validate WiFi band selection."""
        if v not in ("2.4GHz", "5GHz"):
            raise ValueError("Band must be '2.4GHz' or '5GHz'")
        return v


@dataclass
class HotspotClient:
    """Connected client information."""

    mac: str
    signal: str = "N/A"
    rx_bytes: int = 0
    tx_bytes: int = 0
    inactive_time: Optional[str] = None
    ip: Optional[str] = None
    hostname: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: dict[str, Any] = {
            "mac": self.mac,
            "signal": self.signal,
            "rx_bytes": self.rx_bytes,
            "tx_bytes": self.tx_bytes,
        }
        if self.inactive_time:
            result["inactive_time"] = self.inactive_time
        if self.ip:
            result["ip"] = self.ip
        if self.hostname:
            result["hostname"] = self.hostname
        return result


@dataclass
class HotspotStatus:
    """Current hotspot status."""

    active: bool = False
    ssid: Optional[str] = None
    channel: Optional[int] = None
    clients: int = 0
    interface: str = "wlan0"
    hw_mode: Optional[str] = None
    frequency: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "active": self.active,
            "ssid": self.ssid,
            "channel": self.channel,
            "clients": self.clients,
            "interface": self.interface,
            "hw_mode": self.hw_mode,
            "frequency": self.frequency,
        }


# =============================================================================
# WAN Status Models
# =============================================================================

@dataclass
class EthernetStatus:
    """Ethernet connection status."""

    connected: bool = False
    ip: Optional[str] = None
    interface: str = "eth0"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "connected": self.connected,
            "ip": self.ip,
            "interface": self.interface,
        }


@dataclass
class WifiWanStatus:
    """WiFi WAN connection status."""

    connected: bool = False
    ssid: Optional[str] = None
    ip: Optional[str] = None
    interface: str = "wlan0"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "connected": self.connected,
            "ssid": self.ssid,
            "ip": self.ip,
            "interface": self.interface,
        }


@dataclass
class WANStatus:
    """Combined WAN status for ethernet and WiFi."""

    ethernet: EthernetStatus = field(default_factory=EthernetStatus)
    wifi: WifiWanStatus = field(default_factory=WifiWanStatus)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "ethernet": self.ethernet.to_dict(),
            "wifi": self.wifi.to_dict(),
        }


# =============================================================================
# System Information Models
# =============================================================================

@dataclass
class NetworkInterfaces:
    """Configured network interface names."""

    ethernet: str = "eth0"
    wifi_ap: str = "wlan0"
    wifi_wan: str = "wlan0"

    @property
    def single_wifi(self) -> bool:
        """
        Check if device has only one WiFi interface.

        When there's only one WiFi, it must be used for the hotspot (AP),
        so WiFi WAN is not available and Ethernet is required.

        Returns:
            True if wifi_ap and wifi_wan are the same interface
        """
        return self.wifi_ap == self.wifi_wan

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "ethernet": self.ethernet,
            "wifi_ap": self.wifi_ap,
            "wifi_wan": self.wifi_wan,
            "single_wifi": self.single_wifi,
        }


@dataclass
class WiFiCapabilities:
    """WiFi hardware capabilities."""

    supports_5ghz: bool = False
    supports_ac: bool = False
    supports_ax: bool = False
    ap_mode: bool = False

    def to_dict(self) -> dict[str, bool]:
        """Convert to dictionary for JSON serialization."""
        return {
            "supports_5ghz": self.supports_5ghz,
            "supports_ac": self.supports_ac,
            "supports_ax": self.supports_ax,
            "ap_mode": self.ap_mode,
        }


@dataclass
class SystemInfo:
    """Comprehensive system information."""

    # Hardware
    model: str = "unknown"
    model_short: str = "unknown"
    architecture: str = "unknown"

    # Resources
    ram_mb: int = 0
    ram_free_mb: int = 0
    disk_total_gb: int = 0
    disk_free_gb: int = 0

    # Performance
    cpu_temp_c: int = 0
    cpu_usage_percent: float = 0.0
    uptime_seconds: int = 0

    # Software
    kernel_version: str = "unknown"
    os_version: str = "unknown"

    # Network
    interfaces: NetworkInterfaces = field(default_factory=NetworkInterfaces)
    wifi_capabilities: WiFiCapabilities = field(default_factory=WiFiCapabilities)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "model": self.model,
            "model_short": self.model_short,
            "architecture": self.architecture,
            "ram_mb": self.ram_mb,
            "ram_free_mb": self.ram_free_mb,
            "disk_total_gb": self.disk_total_gb,
            "disk_free_gb": self.disk_free_gb,
            "cpu_temp_c": self.cpu_temp_c,
            "cpu_usage_percent": self.cpu_usage_percent,
            "uptime_seconds": self.uptime_seconds,
            "kernel_version": self.kernel_version,
            "os_version": self.os_version,
            "interfaces": self.interfaces.to_dict(),
            "wifi_capabilities": self.wifi_capabilities.to_dict(),
        }


@dataclass
class InterfaceInfo:
    """Detailed network interface information."""

    name: str
    state: str = "unknown"
    ip_addresses: list[str] = field(default_factory=list)
    mac: str = ""
    type: Optional[str] = None  # "builtin" or "usb" for WiFi
    driver: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: dict[str, Any] = {
            "name": self.name,
            "state": self.state,
            "ip_addresses": self.ip_addresses,
            "mac": self.mac,
        }
        if self.type:
            result["type"] = self.type
        if self.driver:
            result["driver"] = self.driver
        return result


# =============================================================================
# Generic Response Models
# =============================================================================

class StatusResponse(BaseModel):
    """Generic status response."""

    status: str


class OperationResponse(BaseModel):
    """Response for operations with status and optional name."""

    status: str
    name: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response model."""

    detail: str
    error_code: Optional[str] = None
