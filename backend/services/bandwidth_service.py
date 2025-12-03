"""
Bandwidth Service
=================

Tracks network bandwidth statistics for all interfaces.

Features:
- Real-time bandwidth monitoring
- Per-interface statistics (bytes, packets)
- Historical data tracking
- Bandwidth rate calculation

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from config import Paths, Network

logger = logging.getLogger("rose-link.bandwidth")


@dataclass
class InterfaceStats:
    """Statistics for a single network interface."""
    rx_bytes: int = 0
    tx_bytes: int = 0
    rx_packets: int = 0
    tx_packets: int = 0
    rx_errors: int = 0
    tx_errors: int = 0
    rx_dropped: int = 0
    tx_dropped: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "rx_bytes": self.rx_bytes,
            "tx_bytes": self.tx_bytes,
            "rx_packets": self.rx_packets,
            "tx_packets": self.tx_packets,
            "rx_errors": self.rx_errors,
            "tx_errors": self.tx_errors,
            "rx_dropped": self.rx_dropped,
            "tx_dropped": self.tx_dropped,
            "rx_bytes_formatted": self._format_bytes(self.rx_bytes),
            "tx_bytes_formatted": self._format_bytes(self.tx_bytes),
        }

    @staticmethod
    def _format_bytes(size: int) -> str:
        """Format bytes to human-readable string."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if abs(size) < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"


@dataclass
class BandwidthSnapshot:
    """A snapshot of bandwidth data at a specific time."""
    timestamp: float
    stats: Dict[str, InterfaceStats] = field(default_factory=dict)


class BandwidthService:
    """
    Service for monitoring network bandwidth.

    This service reads interface statistics from /sys/class/net/
    and provides real-time bandwidth monitoring.
    """

    # Store previous snapshot for rate calculation
    _previous_snapshot: Optional[BandwidthSnapshot] = None
    _history: list[Dict[str, Any]] = []
    _max_history: int = 60  # Keep 60 samples (1 minute at 1s interval)

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """
        Get current bandwidth statistics for all interfaces.

        Returns:
            Dictionary containing:
            - interfaces: Per-interface statistics
            - rates: Bandwidth rates (bytes/second) since last call
            - totals: Total bandwidth across all interfaces
            - timestamp: Current timestamp
        """
        current_snapshot = cls._capture_snapshot()
        rates = cls._calculate_rates(current_snapshot)

        # Update history
        cls._update_history(current_snapshot, rates)

        # Store for next rate calculation
        cls._previous_snapshot = current_snapshot

        # Calculate totals
        totals = cls._calculate_totals(current_snapshot)

        return {
            "interfaces": {
                name: stats.to_dict()
                for name, stats in current_snapshot.stats.items()
            },
            "rates": rates,
            "totals": totals,
            "timestamp": datetime.utcnow().isoformat(),
        }

    @classmethod
    def get_interface_stats(cls, interface: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a specific interface.

        Args:
            interface: Interface name (e.g., 'eth0', 'wlan0')

        Returns:
            Interface statistics or None if not found
        """
        stats = cls._read_interface_stats(interface)
        if stats:
            return stats.to_dict()
        return None

    @classmethod
    def get_history(cls) -> list[Dict[str, Any]]:
        """
        Get historical bandwidth data.

        Returns:
            List of historical snapshots with timestamps
        """
        return cls._history.copy()

    @classmethod
    def _capture_snapshot(cls) -> BandwidthSnapshot:
        """
        Capture current statistics for all interfaces.

        Returns:
            BandwidthSnapshot with current timestamp and stats
        """
        snapshot = BandwidthSnapshot(timestamp=time.time())

        # Get list of network interfaces
        try:
            net_path = Paths.SYS_NET
            if net_path.exists():
                for iface_path in net_path.iterdir():
                    if iface_path.is_dir():
                        name = iface_path.name
                        # Skip loopback
                        if name == 'lo':
                            continue
                        stats = cls._read_interface_stats(name)
                        if stats:
                            snapshot.stats[name] = stats
        except (OSError, PermissionError) as e:
            logger.debug(f"Error reading network interfaces: {e}")

        return snapshot

    @classmethod
    def _read_interface_stats(cls, interface: str) -> Optional[InterfaceStats]:
        """
        Read statistics for a single interface.

        Args:
            interface: Interface name

        Returns:
            InterfaceStats or None if read fails
        """
        stats_path = Paths.SYS_NET / interface / "statistics"

        if not stats_path.exists():
            return None

        try:
            return InterfaceStats(
                rx_bytes=cls._read_stat_file(stats_path / "rx_bytes"),
                tx_bytes=cls._read_stat_file(stats_path / "tx_bytes"),
                rx_packets=cls._read_stat_file(stats_path / "rx_packets"),
                tx_packets=cls._read_stat_file(stats_path / "tx_packets"),
                rx_errors=cls._read_stat_file(stats_path / "rx_errors"),
                tx_errors=cls._read_stat_file(stats_path / "tx_errors"),
                rx_dropped=cls._read_stat_file(stats_path / "rx_dropped"),
                tx_dropped=cls._read_stat_file(stats_path / "tx_dropped"),
            )
        except Exception as e:
            logger.debug(f"Error reading stats for {interface}: {e}")
            return None

    @classmethod
    def _read_stat_file(cls, path: Path) -> int:
        """Read a statistics file and return integer value."""
        try:
            return int(path.read_text().strip())
        except (IOError, ValueError):
            return 0

    @classmethod
    def _calculate_rates(cls, current: BandwidthSnapshot) -> Dict[str, Dict[str, float]]:
        """
        Calculate bandwidth rates since previous snapshot.

        Args:
            current: Current bandwidth snapshot

        Returns:
            Dictionary of rates per interface (bytes/second)
        """
        rates: Dict[str, Dict[str, float]] = {}

        if cls._previous_snapshot is None:
            return rates

        elapsed = current.timestamp - cls._previous_snapshot.timestamp
        if elapsed <= 0:
            return rates

        for name, stats in current.stats.items():
            prev_stats = cls._previous_snapshot.stats.get(name)
            if prev_stats is None:
                continue

            rx_diff = stats.rx_bytes - prev_stats.rx_bytes
            tx_diff = stats.tx_bytes - prev_stats.tx_bytes

            # Handle counter wrap-around (rare but possible)
            if rx_diff < 0:
                rx_diff = stats.rx_bytes
            if tx_diff < 0:
                tx_diff = stats.tx_bytes

            rates[name] = {
                "rx_rate": round(rx_diff / elapsed, 2),
                "tx_rate": round(tx_diff / elapsed, 2),
                "rx_rate_formatted": InterfaceStats._format_bytes(int(rx_diff / elapsed)) + "/s",
                "tx_rate_formatted": InterfaceStats._format_bytes(int(tx_diff / elapsed)) + "/s",
            }

        return rates

    @classmethod
    def _calculate_totals(cls, snapshot: BandwidthSnapshot) -> Dict[str, Any]:
        """
        Calculate total bandwidth across all interfaces.

        Args:
            snapshot: Current bandwidth snapshot

        Returns:
            Dictionary with total statistics
        """
        total_rx = sum(s.rx_bytes for s in snapshot.stats.values())
        total_tx = sum(s.tx_bytes for s in snapshot.stats.values())
        total_rx_packets = sum(s.rx_packets for s in snapshot.stats.values())
        total_tx_packets = sum(s.tx_packets for s in snapshot.stats.values())

        return {
            "rx_bytes": total_rx,
            "tx_bytes": total_tx,
            "rx_packets": total_rx_packets,
            "tx_packets": total_tx_packets,
            "rx_bytes_formatted": InterfaceStats._format_bytes(total_rx),
            "tx_bytes_formatted": InterfaceStats._format_bytes(total_tx),
        }

    @classmethod
    def _update_history(
        cls,
        snapshot: BandwidthSnapshot,
        rates: Dict[str, Dict[str, float]]
    ) -> None:
        """
        Update historical data.

        Args:
            snapshot: Current snapshot
            rates: Current rates
        """
        entry = {
            "timestamp": datetime.fromtimestamp(snapshot.timestamp).isoformat(),
            "rates": rates,
        }

        cls._history.append(entry)

        # Trim history to max size
        if len(cls._history) > cls._max_history:
            cls._history = cls._history[-cls._max_history:]

    @classmethod
    def reset_history(cls) -> None:
        """Clear historical data."""
        cls._history.clear()
        cls._previous_snapshot = None
