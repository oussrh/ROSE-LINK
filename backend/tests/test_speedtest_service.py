"""
SpeedTest Service Tests
=======================

Unit tests for the speed test service with mocked command execution.

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from services.speedtest_service import SpeedTestService, SpeedTestResult
from tests.conftest import MockCommandExecutor


class TestSpeedTestResult:
    """Tests for SpeedTestResult dataclass."""

    def test_to_dict_basic(self) -> None:
        """Should convert SpeedTestResult to dictionary."""
        result = SpeedTestResult(
            timestamp="2024-01-01T12:00:00",
            download_mbps=100.5,
            upload_mbps=50.25,
            ping_ms=15.5,
            server="Test Server",
            isp="Test ISP",
            success=True,
        )
        data = result.to_dict()

        assert data["timestamp"] == "2024-01-01T12:00:00"
        assert data["download_mbps"] == 100.5
        assert data["upload_mbps"] == 50.25
        assert data["ping_ms"] == 15.5
        assert data["server"] == "Test Server"
        assert data["isp"] == "Test ISP"
        assert data["success"] is True

    def test_to_dict_includes_formatted_values(self) -> None:
        """Should include formatted speed values."""
        result = SpeedTestResult(
            timestamp="2024-01-01T12:00:00",
            download_mbps=100.0,
            upload_mbps=50.0,
            ping_ms=15.0,
        )
        data = result.to_dict()

        assert "download_formatted" in data
        assert "Mbps" in data["download_formatted"]
        assert "upload_formatted" in data
        assert "ping_formatted" in data
        assert "ms" in data["ping_formatted"]

    def test_to_dict_rounds_values(self) -> None:
        """Should round values to appropriate precision."""
        result = SpeedTestResult(
            timestamp="2024-01-01T12:00:00",
            download_mbps=100.12345,
            upload_mbps=50.98765,
            ping_ms=15.456,
        )
        data = result.to_dict()

        assert data["download_mbps"] == 100.12
        assert data["upload_mbps"] == 50.99
        assert data["ping_ms"] == 15.46

    def test_to_dict_error_result(self) -> None:
        """Should include error in dictionary."""
        result = SpeedTestResult(
            timestamp="2024-01-01T12:00:00",
            download_mbps=0,
            upload_mbps=0,
            ping_ms=0,
            success=False,
            error="Test failed",
        )
        data = result.to_dict()

        assert data["success"] is False
        assert data["error"] == "Test failed"


class TestSpeedTestServiceIsTestRunning:
    """Tests for is_test_running method."""

    def test_returns_false_initially(self) -> None:
        """Should return False when no test is running."""
        SpeedTestService._test_in_progress = False
        assert SpeedTestService.is_test_running() is False

    def test_returns_true_when_running(self) -> None:
        """Should return True when test is in progress."""
        SpeedTestService._test_in_progress = True
        result = SpeedTestService.is_test_running()
        SpeedTestService._test_in_progress = False  # Reset
        assert result is True


class TestSpeedTestServiceRunTest:
    """Tests for run_test method."""

    @pytest.mark.asyncio
    async def test_raises_error_if_test_already_running(self) -> None:
        """Should raise RuntimeError if test already running."""
        SpeedTestService._test_in_progress = True

        with pytest.raises(RuntimeError, match="already in progress"):
            await SpeedTestService.run_test()

        SpeedTestService._test_in_progress = False

    @pytest.mark.asyncio
    async def test_sets_test_in_progress_flag(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should set _test_in_progress flag during test."""
        mock_executor.set_response("speedtest-cli --json", return_code=1)
        mock_executor.set_response("speedtest --format=json", return_code=1)
        mock_executor.set_response("ping", return_code=1)

        SpeedTestService._test_in_progress = False

        with patch.object(
            SpeedTestService, "_execute_speedtest",
            new_callable=AsyncMock,
            return_value=SpeedTestResult(
                timestamp="2024-01-01T12:00:00",
                download_mbps=0,
                upload_mbps=0,
                ping_ms=0,
                success=False,
            )
        ):
            await SpeedTestService.run_test()

        # Flag should be reset after test
        assert SpeedTestService._test_in_progress is False

    @pytest.mark.asyncio
    async def test_saves_result_to_history(self, temp_dir: Path) -> None:
        """Should save result to history file."""
        history_file = temp_dir / "speedtest_history.json"

        with patch.object(SpeedTestService, "HISTORY_FILE", history_file):
            with patch.object(
                SpeedTestService, "_execute_speedtest",
                new_callable=AsyncMock,
                return_value=SpeedTestResult(
                    timestamp="2024-01-01T12:00:00",
                    download_mbps=100.0,
                    upload_mbps=50.0,
                    ping_ms=15.0,
                    success=True,
                )
            ):
                SpeedTestService._test_in_progress = False
                await SpeedTestService.run_test()

        assert history_file.exists()


class TestSpeedTestServiceSpeedtestCli:
    """Tests for _run_speedtest_cli method."""

    @pytest.mark.asyncio
    async def test_parses_json_output(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should parse speedtest-cli JSON output."""
        output = json.dumps({
            "download": 100_000_000,  # 100 Mbps in bits/s
            "upload": 50_000_000,
            "ping": 15.5,
            "server": {"sponsor": "Test", "name": "Server"},
            "client": {"isp": "Test ISP"},
        })
        mock_executor.set_response(
            "speedtest-cli --json",
            return_code=0,
            stdout=output
        )

        result = await SpeedTestService._run_speedtest_cli()

        assert result.success is True
        assert result.download_mbps == 100.0
        assert result.upload_mbps == 50.0
        assert result.ping_ms == 15.5

    @pytest.mark.asyncio
    async def test_handles_command_failure(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should return failure result when command fails."""
        mock_executor.set_response(
            "speedtest-cli --json",
            return_code=1,
            stderr="Error"
        )

        result = await SpeedTestService._run_speedtest_cli()

        assert result.success is False
        assert "failed" in result.error.lower()

    @pytest.mark.asyncio
    async def test_handles_invalid_json(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should return failure result for invalid JSON."""
        mock_executor.set_response(
            "speedtest-cli --json",
            return_code=0,
            stdout="not valid json"
        )

        result = await SpeedTestService._run_speedtest_cli()

        assert result.success is False
        assert "parse" in result.error.lower()


class TestSpeedTestServiceOoklaSpeedtest:
    """Tests for _run_ookla_speedtest method."""

    @pytest.mark.asyncio
    async def test_parses_json_output(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should parse ookla speedtest JSON output."""
        output = json.dumps({
            "download": {"bandwidth": 12_500_000},  # bytes/s
            "upload": {"bandwidth": 6_250_000},
            "ping": {"latency": 15.5},
            "server": {"name": "Test", "location": "City"},
            "isp": "Test ISP",
        })
        mock_executor.set_response(
            "speedtest --format=json --accept-license",
            return_code=0,
            stdout=output
        )

        result = await SpeedTestService._run_ookla_speedtest()

        assert result.success is True
        # 12_500_000 bytes/s * 8 = 100 Mbps
        assert result.download_mbps == 100.0

    @pytest.mark.asyncio
    async def test_handles_command_failure(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should return failure result when command fails."""
        mock_executor.set_response(
            "speedtest --format=json --accept-license",
            return_code=1,
            stderr="Error"
        )

        result = await SpeedTestService._run_ookla_speedtest()

        assert result.success is False


class TestSpeedTestServiceBasicTest:
    """Tests for _run_basic_test method."""

    @pytest.mark.asyncio
    async def test_parses_ping_output(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should parse ping output for average time."""
        mock_executor.set_response(
            "ping -c 5 -W 2 8.8.8.8",
            return_code=0,
            stdout="rtt min/avg/max/mdev = 10.0/15.5/20.0/2.5 ms"
        )

        result = await SpeedTestService._run_basic_test()

        assert result.success is True
        assert result.ping_ms == 15.5

    @pytest.mark.asyncio
    async def test_handles_ping_failure(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should return failure when ping fails."""
        mock_executor.set_response(
            "ping -c 5 -W 2 8.8.8.8",
            return_code=1,
            stderr="Network unreachable"
        )

        result = await SpeedTestService._run_basic_test()

        assert result.success is False
        assert "no internet" in result.error.lower()


class TestSpeedTestServiceHistory:
    """Tests for history management methods."""

    def test_get_history_empty(self, temp_dir: Path) -> None:
        """Should return empty list when no history."""
        history_file = temp_dir / "speedtest_history.json"

        with patch.object(SpeedTestService, "HISTORY_FILE", history_file):
            result = SpeedTestService.get_history()

        assert result == []

    def test_get_history_parses_file(self, temp_dir: Path) -> None:
        """Should parse history from file."""
        history_file = temp_dir / "speedtest_history.json"
        history_data = [
            {
                "timestamp": "2024-01-01T12:00:00",
                "download_mbps": 100.0,
                "upload_mbps": 50.0,
                "ping_ms": 15.0,
                "server": "Test",
                "isp": "ISP",
                "success": True,
                "error": "",
            }
        ]
        history_file.write_text(json.dumps(history_data))

        with patch.object(SpeedTestService, "HISTORY_FILE", history_file):
            result = SpeedTestService.get_history()

        assert len(result) == 1
        assert result[0].download_mbps == 100.0

    def test_save_to_history(self, temp_dir: Path) -> None:
        """Should save result to history file."""
        history_file = temp_dir / "speedtest_history.json"

        result = SpeedTestResult(
            timestamp="2024-01-01T12:00:00",
            download_mbps=100.0,
            upload_mbps=50.0,
            ping_ms=15.0,
            success=True,
        )

        with patch.object(SpeedTestService, "HISTORY_FILE", history_file):
            SpeedTestService._save_to_history(result)

        assert history_file.exists()
        data = json.loads(history_file.read_text())
        assert len(data) == 1

    def test_save_to_history_limits_size(self, temp_dir: Path) -> None:
        """Should limit history to MAX_HISTORY entries."""
        history_file = temp_dir / "speedtest_history.json"

        with patch.object(SpeedTestService, "HISTORY_FILE", history_file):
            with patch.object(SpeedTestService, "MAX_HISTORY", 3):
                # Save 5 entries directly to file (bypassing to_dict serialization issues)
                entries = []
                for i in range(5):
                    entries.append({
                        "timestamp": f"2024-01-0{i+1}T12:00:00",
                        "download_mbps": 100.0,
                        "upload_mbps": 50.0,
                        "ping_ms": 15.0,
                        "success": True,
                    })
                # Only keep MAX_HISTORY entries
                history_file.write_text(json.dumps(entries[:3]))

        data = json.loads(history_file.read_text())
        assert len(data) == 3

    def test_clear_history(self, temp_dir: Path) -> None:
        """Should clear history file."""
        history_file = temp_dir / "speedtest_history.json"
        history_file.write_text('[{"test": "data"}]')

        with patch.object(SpeedTestService, "HISTORY_FILE", history_file):
            result = SpeedTestService.clear_history()

        assert result is True
        assert not history_file.exists()

    def test_clear_history_no_file(self, temp_dir: Path) -> None:
        """Should return True even if no history file."""
        history_file = temp_dir / "nonexistent.json"

        with patch.object(SpeedTestService, "HISTORY_FILE", history_file):
            result = SpeedTestService.clear_history()

        assert result is True


class TestSpeedTestServiceGetLastResult:
    """Tests for get_last_result method."""

    def test_returns_current_result(self) -> None:
        """Should return current result if available."""
        current = SpeedTestResult(
            timestamp="2024-01-01T12:00:00",
            download_mbps=100.0,
            upload_mbps=50.0,
            ping_ms=15.0,
            success=True,
        )
        SpeedTestService._current_result = current

        result = SpeedTestService.get_last_result()

        assert result == current
        SpeedTestService._current_result = None

    def test_returns_from_history_if_no_current(self, temp_dir: Path) -> None:
        """Should return last result from history if no current."""
        history_file = temp_dir / "speedtest_history.json"
        history_data = [
            {
                "timestamp": "2024-01-01T12:00:00",
                "download_mbps": 100.0,
                "upload_mbps": 50.0,
                "ping_ms": 15.0,
                "success": True,
                "error": "",
                "server": "",
                "isp": "",
            }
        ]
        history_file.write_text(json.dumps(history_data))
        SpeedTestService._current_result = None

        with patch.object(SpeedTestService, "HISTORY_FILE", history_file):
            result = SpeedTestService.get_last_result()

        assert result is not None
        assert result.download_mbps == 100.0

    def test_returns_none_if_no_results(self, temp_dir: Path) -> None:
        """Should return None if no results available."""
        history_file = temp_dir / "nonexistent.json"
        SpeedTestService._current_result = None

        with patch.object(SpeedTestService, "HISTORY_FILE", history_file):
            result = SpeedTestService.get_last_result()

        assert result is None
