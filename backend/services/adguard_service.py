"""
AdGuard Home Service
====================

Manages AdGuard Home DNS-level ad blocking integration.

Features:
- Check AdGuard Home installation status
- Enable/disable DNS filtering
- Get blocking statistics
- Manage AdGuard Home service

AdGuard Home API is accessed at http://127.0.0.1:3000

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import aiohttp

from config import Paths
from utils.command_runner import CommandRunner

logger = logging.getLogger("rose-link.adguard")

# AdGuard Home configuration
ADGUARD_API_URL = "http://127.0.0.1:3000"
ADGUARD_CONFIG_PATH = Path("/opt/AdGuardHome/AdGuardHome.yaml")
ADGUARD_BINARY_PATH = Path("/opt/AdGuardHome/AdGuardHome")
ADGUARD_SERVICE_NAME = "AdGuardHome"


@dataclass
class AdGuardStats:
    """AdGuard Home blocking statistics."""

    num_dns_queries: int = 0
    num_blocked_filtering: int = 0
    num_replaced_safebrowsing: int = 0
    num_replaced_safesearch: int = 0
    num_replaced_parental: int = 0
    avg_processing_time: float = 0.0
    top_blocked_domains: list[dict[str, Any]] = field(default_factory=list)
    top_clients: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        blocked_total = (
            self.num_blocked_filtering +
            self.num_replaced_safebrowsing +
            self.num_replaced_parental
        )
        blocked_percent = 0.0
        if self.num_dns_queries > 0:
            blocked_percent = round((blocked_total / self.num_dns_queries) * 100, 1)

        return {
            "dns_queries": self.num_dns_queries,
            "blocked_filtering": self.num_blocked_filtering,
            "blocked_safebrowsing": self.num_replaced_safebrowsing,
            "blocked_safesearch": self.num_replaced_safesearch,
            "blocked_parental": self.num_replaced_parental,
            "blocked_total": blocked_total,
            "blocked_percent": blocked_percent,
            "avg_processing_time_ms": round(self.avg_processing_time, 2),
            "top_blocked_domains": self.top_blocked_domains[:5],
            "top_clients": self.top_clients[:5],
        }


@dataclass
class AdGuardStatus:
    """AdGuard Home status."""

    installed: bool = False
    running: bool = False
    version: str = ""
    protection_enabled: bool = False
    filtering_enabled: bool = False
    dns_addresses: list[str] = field(default_factory=list)
    stats: Optional[AdGuardStats] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "installed": self.installed,
            "running": self.running,
            "version": self.version,
            "protection_enabled": self.protection_enabled,
            "filtering_enabled": self.filtering_enabled,
            "dns_addresses": self.dns_addresses,
        }
        if self.stats:
            result["stats"] = self.stats.to_dict()
        return result


class AdGuardService:
    """
    Service for AdGuard Home management.

    This service handles all AdGuard Home operations including
    status checking, enabling/disabling filtering, and statistics.
    """

    @classmethod
    async def get_status(cls) -> AdGuardStatus:
        """
        Get current AdGuard Home status.

        Checks if AdGuard Home is installed, running, and gets
        protection status and statistics.

        Returns:
            AdGuardStatus with installation and protection details
        """
        status = AdGuardStatus()

        # Check if AdGuard Home is installed
        status.installed = ADGUARD_BINARY_PATH.exists()
        if not status.installed:
            return status

        # Check if service is running
        status.running = CommandRunner.is_service_active(ADGUARD_SERVICE_NAME)

        if not status.running:
            return status

        # Get status from AdGuard API
        try:
            async with aiohttp.ClientSession() as session:
                # Get general status
                async with session.get(
                    f"{ADGUARD_API_URL}/control/status",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        status.version = data.get("version", "")
                        status.protection_enabled = data.get("protection_enabled", False)
                        status.filtering_enabled = data.get("filtering_enabled", False)
                        status.dns_addresses = data.get("dns_addresses", [])

                # Get statistics
                status.stats = await cls._get_stats(session)

        except aiohttp.ClientError as e:
            logger.warning(f"Failed to connect to AdGuard Home API: {e}")
        except Exception as e:
            logger.error(f"Error getting AdGuard status: {e}")

        return status

    @classmethod
    async def _get_stats(cls, session: aiohttp.ClientSession) -> Optional[AdGuardStats]:
        """
        Get AdGuard Home statistics.

        Args:
            session: aiohttp session for API requests

        Returns:
            AdGuardStats or None if unavailable
        """
        try:
            async with session.get(
                f"{ADGUARD_API_URL}/control/stats",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return AdGuardStats(
                        num_dns_queries=data.get("num_dns_queries", 0),
                        num_blocked_filtering=data.get("num_blocked_filtering", 0),
                        num_replaced_safebrowsing=data.get("num_replaced_safebrowsing", 0),
                        num_replaced_safesearch=data.get("num_replaced_safesearch", 0),
                        num_replaced_parental=data.get("num_replaced_parental", 0),
                        avg_processing_time=data.get("avg_processing_time", 0.0),
                        top_blocked_domains=data.get("top_blocked_domains", []),
                        top_clients=data.get("top_clients", []),
                    )
        except Exception as e:
            logger.debug(f"Failed to get AdGuard stats: {e}")
        return None

    @classmethod
    async def enable_protection(cls) -> bool:
        """
        Enable AdGuard Home protection.

        Returns:
            True if successful
        """
        return await cls._set_protection(True)

    @classmethod
    async def disable_protection(cls) -> bool:
        """
        Disable AdGuard Home protection.

        Returns:
            True if successful
        """
        return await cls._set_protection(False)

    @classmethod
    async def _set_protection(cls, enabled: bool) -> bool:
        """
        Set AdGuard Home protection state.

        Args:
            enabled: Whether to enable or disable protection

        Returns:
            True if successful
        """
        try:
            async with aiohttp.ClientSession() as session:
                # Use the dns_config endpoint which is the correct API for protection
                async with session.post(
                    f"{ADGUARD_API_URL}/control/dns_config",
                    json={"protection_enabled": enabled},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        action = "enabled" if enabled else "disabled"
                        logger.info(f"AdGuard protection {action}")
                        return True
                    else:
                        body = await resp.text()
                        logger.error(f"Failed to set protection: HTTP {resp.status} - {body}")
                        return False
        except Exception as e:
            logger.error(f"Error setting AdGuard protection: {e}")
            return False

    @classmethod
    async def enable_filtering(cls) -> bool:
        """
        Enable AdGuard Home DNS filtering.

        Returns:
            True if successful
        """
        return await cls._set_filtering(True)

    @classmethod
    async def disable_filtering(cls) -> bool:
        """
        Disable AdGuard Home DNS filtering.

        Returns:
            True if successful
        """
        return await cls._set_filtering(False)

    @classmethod
    async def _set_filtering(cls, enabled: bool) -> bool:
        """
        Set AdGuard Home filtering state.

        Args:
            enabled: Whether to enable or disable filtering

        Returns:
            True if successful
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{ADGUARD_API_URL}/control/filtering/config",
                    json={"enabled": enabled, "interval": 24},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        action = "enabled" if enabled else "disabled"
                        logger.info(f"AdGuard filtering {action}")
                        return True
                    else:
                        body = await resp.text()
                        logger.error(f"Failed to set filtering: HTTP {resp.status} - {body}")
                        return False
        except Exception as e:
            logger.error(f"Error setting AdGuard filtering: {e}")
            return False

    @classmethod
    async def get_stats(cls) -> Optional[AdGuardStats]:
        """
        Get AdGuard Home statistics.

        Returns:
            AdGuardStats or None if unavailable
        """
        try:
            async with aiohttp.ClientSession() as session:
                return await cls._get_stats(session)
        except Exception as e:
            logger.error(f"Error getting AdGuard stats: {e}")
            return None

    @classmethod
    def is_installed(cls) -> bool:
        """
        Check if AdGuard Home is installed.

        Returns:
            True if AdGuard Home binary exists
        """
        return ADGUARD_BINARY_PATH.exists()

    @classmethod
    def start(cls) -> bool:
        """
        Start AdGuard Home service.

        Returns:
            True if successful
        """
        if not cls.is_installed():
            logger.error("AdGuard Home is not installed")
            return False

        return CommandRunner.start_service(ADGUARD_SERVICE_NAME)

    @classmethod
    def stop(cls) -> bool:
        """
        Stop AdGuard Home service.

        Returns:
            True if successful
        """
        return CommandRunner.stop_service(ADGUARD_SERVICE_NAME)

    @classmethod
    def restart(cls) -> bool:
        """
        Restart AdGuard Home service.

        Returns:
            True if successful
        """
        return CommandRunner.restart_service(ADGUARD_SERVICE_NAME)

    @classmethod
    async def reset_stats(cls) -> bool:
        """
        Reset AdGuard Home statistics.

        Returns:
            True if successful
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{ADGUARD_API_URL}/control/stats_reset",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        logger.info("AdGuard stats reset")
                        return True
                    else:
                        logger.error(f"Failed to reset stats: HTTP {resp.status}")
                        return False
        except Exception as e:
            logger.error(f"Error resetting AdGuard stats: {e}")
            return False

    @classmethod
    async def get_query_log(cls, limit: int = 100) -> list[dict[str, Any]]:
        """
        Get recent DNS query log entries.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of query log entries
        """
        try:
            async with aiohttp.ClientSession() as session:
                params = {"limit": limit, "response_status": "all"}
                async with session.get(
                    f"{ADGUARD_API_URL}/control/querylog",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("data", [])
                    else:
                        logger.error(f"Failed to get query log: HTTP {resp.status}")
                        return []
        except Exception as e:
            logger.error(f"Error getting query log: {e}")
            return []
