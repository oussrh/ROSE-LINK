"""
ROSE Link Services
==================

This package contains business logic services for each major component:
- AuthService: API key and session management
- WANService: Ethernet and WiFi WAN connection management
- VPNService: WireGuard VPN profile management
- HotspotService: WiFi access point configuration
- SystemService: System information and monitoring
- BandwidthService: Network bandwidth monitoring
- BackupService: Configuration backup and restore
- SpeedTestService: Internet speed testing
- SSLService: SSL certificate management

Services encapsulate all the logic for interacting with the underlying
system, making the API routes thin and focused on HTTP concerns.

Author: ROSE Link Team
License: MIT
"""

from services.auth_service import AuthService
from services.wan_service import WANService
from services.vpn_service import VPNService
from services.hotspot_service import HotspotService
from services.system_service import SystemService
from services.interface_service import InterfaceService
from services.bandwidth_service import BandwidthService
from services.backup_service import BackupService
from services.speedtest_service import SpeedTestService
from services.ssl_service import SSLService

__all__ = [
    "AuthService",
    "WANService",
    "VPNService",
    "HotspotService",
    "SystemService",
    "InterfaceService",
    "BandwidthService",
    "BackupService",
    "SpeedTestService",
    "SSLService",
]
