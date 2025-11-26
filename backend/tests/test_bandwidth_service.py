"""
Bandwidth Service Tests
=======================

Unit tests for the bandwidth monitoring service.

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import patch

import pytest

from services.bandwidth_service import (
    BandwidthService,
    BandwidthSnapshot,
    InterfaceStats,
)


class TestInterfaceStats:
    """Tests for InterfaceStats dataclass."""

    def test_to_dict_basic(self) -> None:
        """Should convert InterfaceStats to dictionary."""
        stats = InterfaceStats(
            rx_bytes=1000,
            tx_bytes=500,
            rx_packets=10,
            tx_packets=5,
            rx_errors=0,
            tx_errors=0,
            rx_dropped=0,
            tx_dropped=0,
        )
        result = stats.to_dict()

        assert result["rx_bytes"] == 1000
        assert result["tx_bytes"] == 500
        assert result["rx_packets"] == 10
        assert result["tx_packets"] == 5

    def test_to_dict_includes_formatted_bytes(self) -> None:
        """Should include formatted byte values."""
        stats = InterfaceStats(rx_bytes=1024, tx_bytes=2048)
        result = stats.to_dict()

        assert "rx_bytes_formatted" in result
        assert "tx_bytes_formatted" in result

    def test_format_bytes_bytes(self) -> None:
        """Should format bytes correctly."""
        result = InterfaceStats._format_bytes(512)
        assert "B" in result
        assert "512" in result

    def test_format_bytes_kilobytes(self) -> None:
        """Should format kilobytes correctly."""
        result = InterfaceStats._format_bytes(2048)
        assert "KB" in result

    def test_format_bytes_megabytes(self) -> None:
        """Should format megabytes correctly."""
        result = InterfaceStats._format_bytes(2 * 1024 * 1024)
        assert "MB" in result

    def test_format_bytes_gigabytes(self) -> None:
        """Should format gigabytes correctly."""
        result = InterfaceStats._format_bytes(2 * 1024 * 1024 * 1024)
        assert "GB" in result

    def test_format_bytes_terabytes(self) -> None:
        """Should format terabytes correctly."""
        result = InterfaceStats._format_bytes(2 * 1024 * 1024 * 1024 * 1024)
        assert "TB" in result


class TestBandwidthServiceGetStats:
    """Tests for get_stats method."""

    def test_returns_stats_dictionary(self, temp_dir: Path) -> None:
        """Should return dictionary with stats."""
        sys_net = temp_dir / "sys" / "class" / "net"
        eth0_stats = sys_net / "eth0" / "statistics"
        eth0_stats.mkdir(parents=True)
        (eth0_stats / "rx_bytes").write_text("1000")
        (eth0_stats / "tx_bytes").write_text("500")
        (eth0_stats / "rx_packets").write_text("10")
        (eth0_stats / "tx_packets").write_text("5")
        (eth0_stats / "rx_errors").write_text("0")
        (eth0_stats / "tx_errors").write_text("0")
        (eth0_stats / "rx_dropped").write_text("0")
        (eth0_stats / "tx_dropped").write_text("0")

        BandwidthService._previous_snapshot = None
        BandwidthService._history = []

        with patch("services.bandwidth_service.Paths") as mock_paths:
            mock_paths.SYS_NET = sys_net

            result = BandwidthService.get_stats()

        assert "interfaces" in result
        assert "rates" in result
        assert "totals" in result
        assert "timestamp" in result

    def test_includes_interface_stats(self, temp_dir: Path) -> None:
        """Should include per-interface statistics."""
        sys_net = temp_dir / "sys" / "class" / "net"
        eth0_stats = sys_net / "eth0" / "statistics"
        eth0_stats.mkdir(parents=True)
        for stat in ["rx_bytes", "tx_bytes", "rx_packets", "tx_packets",
                     "rx_errors", "tx_errors", "rx_dropped", "tx_dropped"]:
            (eth0_stats / stat).write_text("100")

        BandwidthService._previous_snapshot = None
        BandwidthService._history = []

        with patch("services.bandwidth_service.Paths") as mock_paths:
            mock_paths.SYS_NET = sys_net

            result = BandwidthService.get_stats()

        assert "eth0" in result["interfaces"]
        assert result["interfaces"]["eth0"]["rx_bytes"] == 100

    def test_skips_loopback_interface(self, temp_dir: Path) -> None:
        """Should skip loopback interface."""
        sys_net = temp_dir / "sys" / "class" / "net"
        lo_stats = sys_net / "lo" / "statistics"
        lo_stats.mkdir(parents=True)
        for stat in ["rx_bytes", "tx_bytes", "rx_packets", "tx_packets",
                     "rx_errors", "tx_errors", "rx_dropped", "tx_dropped"]:
            (lo_stats / stat).write_text("100")

        BandwidthService._previous_snapshot = None
        BandwidthService._history = []

        with patch("services.bandwidth_service.Paths") as mock_paths:
            mock_paths.SYS_NET = sys_net

            result = BandwidthService.get_stats()

        assert "lo" not in result["interfaces"]


class TestBandwidthServiceGetInterfaceStats:
    """Tests for get_interface_stats method."""

    def test_returns_stats_for_interface(self, temp_dir: Path) -> None:
        """Should return stats for specific interface."""
        sys_net = temp_dir / "sys" / "class" / "net"
        eth0_stats = sys_net / "eth0" / "statistics"
        eth0_stats.mkdir(parents=True)
        (eth0_stats / "rx_bytes").write_text("1000")
        (eth0_stats / "tx_bytes").write_text("500")
        (eth0_stats / "rx_packets").write_text("10")
        (eth0_stats / "tx_packets").write_text("5")
        (eth0_stats / "rx_errors").write_text("0")
        (eth0_stats / "tx_errors").write_text("0")
        (eth0_stats / "rx_dropped").write_text("0")
        (eth0_stats / "tx_dropped").write_text("0")

        with patch("services.bandwidth_service.Paths") as mock_paths:
            mock_paths.SYS_NET = sys_net

            result = BandwidthService.get_interface_stats("eth0")

        assert result is not None
        assert result["rx_bytes"] == 1000
        assert result["tx_bytes"] == 500

    def test_returns_none_for_missing_interface(self, temp_dir: Path) -> None:
        """Should return None for non-existent interface."""
        sys_net = temp_dir / "sys" / "class" / "net"
        sys_net.mkdir(parents=True)

        with patch("services.bandwidth_service.Paths") as mock_paths:
            mock_paths.SYS_NET = sys_net

            result = BandwidthService.get_interface_stats("eth99")

        assert result is None


class TestBandwidthServiceCaptureSnapshot:
    """Tests for _capture_snapshot method."""

    def test_captures_timestamp(self, temp_dir: Path) -> None:
        """Should capture current timestamp."""
        sys_net = temp_dir / "sys" / "class" / "net"
        sys_net.mkdir(parents=True)

        with patch("services.bandwidth_service.Paths") as mock_paths:
            mock_paths.SYS_NET = sys_net

            before = time.time()
            result = BandwidthService._capture_snapshot()
            after = time.time()

        assert before <= result.timestamp <= after

    def test_captures_all_interfaces(self, temp_dir: Path) -> None:
        """Should capture stats for all interfaces."""
        sys_net = temp_dir / "sys" / "class" / "net"
        for iface in ["eth0", "wlan0"]:
            stats_dir = sys_net / iface / "statistics"
            stats_dir.mkdir(parents=True)
            for stat in ["rx_bytes", "tx_bytes", "rx_packets", "tx_packets",
                         "rx_errors", "tx_errors", "rx_dropped", "tx_dropped"]:
                (stats_dir / stat).write_text("100")

        with patch("services.bandwidth_service.Paths") as mock_paths:
            mock_paths.SYS_NET = sys_net

            result = BandwidthService._capture_snapshot()

        assert "eth0" in result.stats
        assert "wlan0" in result.stats


class TestBandwidthServiceCalculateRates:
    """Tests for _calculate_rates method."""

    def test_returns_empty_without_previous_snapshot(self) -> None:
        """Should return empty dict without previous snapshot."""
        BandwidthService._previous_snapshot = None

        current = BandwidthSnapshot(
            timestamp=time.time(),
            stats={"eth0": InterfaceStats(rx_bytes=1000, tx_bytes=500)},
        )

        result = BandwidthService._calculate_rates(current)

        assert result == {}

    def test_calculates_rates_correctly(self) -> None:
        """Should calculate bandwidth rates correctly."""
        now = time.time()

        # Previous snapshot: 1 second ago
        previous = BandwidthSnapshot(
            timestamp=now - 1.0,
            stats={"eth0": InterfaceStats(rx_bytes=0, tx_bytes=0)},
        )
        BandwidthService._previous_snapshot = previous

        # Current snapshot
        current = BandwidthSnapshot(
            timestamp=now,
            stats={"eth0": InterfaceStats(rx_bytes=1000, tx_bytes=500)},
        )

        result = BandwidthService._calculate_rates(current)

        assert "eth0" in result
        assert result["eth0"]["rx_rate"] == 1000.0
        assert result["eth0"]["tx_rate"] == 500.0

    def test_includes_formatted_rates(self) -> None:
        """Should include formatted rate values."""
        now = time.time()

        previous = BandwidthSnapshot(
            timestamp=now - 1.0,
            stats={"eth0": InterfaceStats(rx_bytes=0, tx_bytes=0)},
        )
        BandwidthService._previous_snapshot = previous

        current = BandwidthSnapshot(
            timestamp=now,
            stats={"eth0": InterfaceStats(rx_bytes=1024, tx_bytes=512)},
        )

        result = BandwidthService._calculate_rates(current)

        assert "rx_rate_formatted" in result["eth0"]
        assert "/s" in result["eth0"]["rx_rate_formatted"]

    def test_handles_counter_wraparound(self) -> None:
        """Should handle counter wraparound."""
        now = time.time()

        # Previous has higher value (simulating wraparound)
        previous = BandwidthSnapshot(
            timestamp=now - 1.0,
            stats={"eth0": InterfaceStats(rx_bytes=1000, tx_bytes=1000)},
        )
        BandwidthService._previous_snapshot = previous

        # Current has lower value
        current = BandwidthSnapshot(
            timestamp=now,
            stats={"eth0": InterfaceStats(rx_bytes=500, tx_bytes=500)},
        )

        result = BandwidthService._calculate_rates(current)

        # Should use current value as rate when wraparound detected
        assert result["eth0"]["rx_rate"] == 500.0


class TestBandwidthServiceCalculateTotals:
    """Tests for _calculate_totals method."""

    def test_calculates_totals_correctly(self) -> None:
        """Should sum totals across all interfaces."""
        snapshot = BandwidthSnapshot(
            timestamp=time.time(),
            stats={
                "eth0": InterfaceStats(
                    rx_bytes=1000, tx_bytes=500,
                    rx_packets=10, tx_packets=5
                ),
                "wlan0": InterfaceStats(
                    rx_bytes=2000, tx_bytes=1000,
                    rx_packets=20, tx_packets=10
                ),
            },
        )

        result = BandwidthService._calculate_totals(snapshot)

        assert result["rx_bytes"] == 3000
        assert result["tx_bytes"] == 1500
        assert result["rx_packets"] == 30
        assert result["tx_packets"] == 15

    def test_includes_formatted_totals(self) -> None:
        """Should include formatted total values."""
        snapshot = BandwidthSnapshot(
            timestamp=time.time(),
            stats={"eth0": InterfaceStats(rx_bytes=1024, tx_bytes=512)},
        )

        result = BandwidthService._calculate_totals(snapshot)

        assert "rx_bytes_formatted" in result
        assert "tx_bytes_formatted" in result


class TestBandwidthServiceHistory:
    """Tests for history management."""

    def test_get_history_returns_copy(self) -> None:
        """Should return a copy of history."""
        BandwidthService._history = [{"test": "data"}]

        result = BandwidthService.get_history()

        assert result == [{"test": "data"}]
        assert result is not BandwidthService._history

        BandwidthService._history = []

    def test_update_history_adds_entry(self) -> None:
        """Should add entry to history."""
        BandwidthService._history = []

        snapshot = BandwidthSnapshot(timestamp=time.time(), stats={})
        rates = {"eth0": {"rx_rate": 100, "tx_rate": 50}}

        BandwidthService._update_history(snapshot, rates)

        assert len(BandwidthService._history) == 1
        assert "timestamp" in BandwidthService._history[0]
        assert "rates" in BandwidthService._history[0]

        BandwidthService._history = []

    def test_update_history_limits_size(self) -> None:
        """Should limit history to max size."""
        BandwidthService._history = []
        BandwidthService._max_history = 3

        for i in range(5):
            snapshot = BandwidthSnapshot(timestamp=time.time() + i, stats={})
            BandwidthService._update_history(snapshot, {})

        assert len(BandwidthService._history) == 3

        BandwidthService._history = []
        BandwidthService._max_history = 60

    def test_reset_history_clears_all(self) -> None:
        """Should clear all history data."""
        BandwidthService._history = [{"test": "data"}]
        BandwidthService._previous_snapshot = BandwidthSnapshot(
            timestamp=time.time(), stats={}
        )

        BandwidthService.reset_history()

        assert BandwidthService._history == []
        assert BandwidthService._previous_snapshot is None


class TestBandwidthServiceReadStatFile:
    """Tests for _read_stat_file method."""

    def test_reads_integer_value(self, temp_dir: Path) -> None:
        """Should read integer value from file."""
        stat_file = temp_dir / "rx_bytes"
        stat_file.write_text("12345\n")

        result = BandwidthService._read_stat_file(stat_file)

        assert result == 12345

    def test_returns_zero_on_missing_file(self, temp_dir: Path) -> None:
        """Should return 0 for missing file."""
        stat_file = temp_dir / "missing"

        result = BandwidthService._read_stat_file(stat_file)

        assert result == 0

    def test_returns_zero_on_invalid_content(self, temp_dir: Path) -> None:
        """Should return 0 for non-integer content."""
        stat_file = temp_dir / "rx_bytes"
        stat_file.write_text("not a number")

        result = BandwidthService._read_stat_file(stat_file)

        assert result == 0
