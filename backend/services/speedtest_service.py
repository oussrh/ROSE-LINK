"""
Speed Test Service
==================

Handles internet speed testing functionality.

Features:
- Run speed tests (download, upload, ping)
- Store test history
- Async execution for long-running tests

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import Paths
from utils.command_runner import run_command

logger = logging.getLogger("rose-link.speedtest")


@dataclass
class SpeedTestResult:
    """Result of a speed test."""
    timestamp: str
    download_mbps: float
    upload_mbps: float
    ping_ms: float
    server: str = ""
    isp: str = ""
    success: bool = True
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp,
            "download_mbps": round(self.download_mbps, 2),
            "upload_mbps": round(self.upload_mbps, 2),
            "ping_ms": round(self.ping_ms, 2),
            "download_formatted": f"{self.download_mbps:.2f} Mbps",
            "upload_formatted": f"{self.upload_mbps:.2f} Mbps",
            "ping_formatted": f"{self.ping_ms:.1f} ms",
            "server": self.server,
            "isp": self.isp,
            "success": self.success,
            "error": self.error,
        }


class SpeedTestService:
    """
    Service for internet speed testing.

    This service runs speed tests and maintains a history
    of test results.
    """

    # History file path
    HISTORY_FILE = Paths.SYSTEM_DIR / "speedtest_history.json"

    # Maximum history entries
    MAX_HISTORY = 50

    # Flag to track if a test is in progress
    _test_in_progress: bool = False
    _current_result: Optional[SpeedTestResult] = None

    @classmethod
    def is_test_running(cls) -> bool:
        """Check if a speed test is currently running."""
        return cls._test_in_progress

    @classmethod
    async def run_test(cls) -> SpeedTestResult:
        """
        Run a speed test.

        Returns:
            SpeedTestResult with test results

        Raises:
            RuntimeError: If a test is already running
        """
        if cls._test_in_progress:
            raise RuntimeError("A speed test is already in progress")

        cls._test_in_progress = True
        cls._current_result = None

        try:
            result = await cls._execute_speedtest()
            cls._current_result = result

            # Save to history
            cls._save_to_history(result)

            return result

        finally:
            cls._test_in_progress = False

    @classmethod
    async def _execute_speedtest(cls) -> SpeedTestResult:
        """
        Execute the speed test command.

        Tries speedtest-cli first, then falls back to ookla speedtest.

        Returns:
            SpeedTestResult with test results
        """
        # Try speedtest-cli (Python package)
        result = await cls._run_speedtest_cli()
        if result.success:
            return result

        # Try ookla speedtest
        result = await cls._run_ookla_speedtest()
        if result.success:
            return result

        # Fall back to basic ping test
        result = await cls._run_basic_test()
        return result

    @classmethod
    async def _run_speedtest_cli(cls) -> SpeedTestResult:
        """
        Run speed test using speedtest-cli.

        Returns:
            SpeedTestResult
        """
        try:
            # Run speedtest-cli with JSON output
            ret, out, err = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: run_command(
                    ["speedtest-cli", "--json"],
                    timeout=120
                )
            )

            if ret != 0:
                return SpeedTestResult(
                    timestamp=datetime.now().isoformat(),
                    download_mbps=0,
                    upload_mbps=0,
                    ping_ms=0,
                    success=False,
                    error="speedtest-cli failed"
                )

            # Parse JSON output
            data = json.loads(out)

            # Convert bits/s to Mbps
            download_mbps = data.get("download", 0) / 1_000_000
            upload_mbps = data.get("upload", 0) / 1_000_000
            ping_ms = data.get("ping", 0)

            server = data.get("server", {})
            server_name = f"{server.get('sponsor', '')} ({server.get('name', '')})"

            return SpeedTestResult(
                timestamp=datetime.now().isoformat(),
                download_mbps=download_mbps,
                upload_mbps=upload_mbps,
                ping_ms=ping_ms,
                server=server_name,
                isp=data.get("client", {}).get("isp", ""),
                success=True,
            )

        except json.JSONDecodeError as e:
            logger.debug(f"Failed to parse speedtest-cli output: {e}")
            return SpeedTestResult(
                timestamp=datetime.now().isoformat(),
                download_mbps=0,
                upload_mbps=0,
                ping_ms=0,
                success=False,
                error="Failed to parse speedtest output"
            )
        except FileNotFoundError:
            logger.debug("speedtest-cli not found")
            return SpeedTestResult(
                timestamp=datetime.now().isoformat(),
                download_mbps=0,
                upload_mbps=0,
                ping_ms=0,
                success=False,
                error="speedtest-cli not installed"
            )
        except Exception as e:
            logger.error(f"speedtest-cli error: {e}")
            return SpeedTestResult(
                timestamp=datetime.now().isoformat(),
                download_mbps=0,
                upload_mbps=0,
                ping_ms=0,
                success=False,
                error=str(e)
            )

    @classmethod
    async def _run_ookla_speedtest(cls) -> SpeedTestResult:
        """
        Run speed test using Ookla speedtest CLI.

        Returns:
            SpeedTestResult
        """
        try:
            # Run ookla speedtest with JSON output
            ret, out, err = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: run_command(
                    ["speedtest", "--format=json", "--accept-license"],
                    timeout=120
                )
            )

            if ret != 0:
                return SpeedTestResult(
                    timestamp=datetime.now().isoformat(),
                    download_mbps=0,
                    upload_mbps=0,
                    ping_ms=0,
                    success=False,
                    error="ookla speedtest failed"
                )

            # Parse JSON output
            data = json.loads(out)

            # Convert bytes/s to Mbps
            download_mbps = data.get("download", {}).get("bandwidth", 0) * 8 / 1_000_000
            upload_mbps = data.get("upload", {}).get("bandwidth", 0) * 8 / 1_000_000
            ping_ms = data.get("ping", {}).get("latency", 0)

            server = data.get("server", {})
            server_name = f"{server.get('name', '')} ({server.get('location', '')})"

            return SpeedTestResult(
                timestamp=datetime.now().isoformat(),
                download_mbps=download_mbps,
                upload_mbps=upload_mbps,
                ping_ms=ping_ms,
                server=server_name,
                isp=data.get("isp", ""),
                success=True,
            )

        except json.JSONDecodeError as e:
            logger.debug(f"Failed to parse ookla speedtest output: {e}")
            return SpeedTestResult(
                timestamp=datetime.now().isoformat(),
                download_mbps=0,
                upload_mbps=0,
                ping_ms=0,
                success=False,
                error="Failed to parse speedtest output"
            )
        except FileNotFoundError:
            logger.debug("ookla speedtest not found")
            return SpeedTestResult(
                timestamp=datetime.now().isoformat(),
                download_mbps=0,
                upload_mbps=0,
                ping_ms=0,
                success=False,
                error="speedtest not installed"
            )
        except Exception as e:
            logger.error(f"ookla speedtest error: {e}")
            return SpeedTestResult(
                timestamp=datetime.now().isoformat(),
                download_mbps=0,
                upload_mbps=0,
                ping_ms=0,
                success=False,
                error=str(e)
            )

    @classmethod
    async def _run_basic_test(cls) -> SpeedTestResult:
        """
        Run a basic connectivity test using ping.

        Returns:
            SpeedTestResult with ping only
        """
        try:
            ret, out, err = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: run_command(
                    ["ping", "-c", "5", "-W", "2", "8.8.8.8"],
                    timeout=30
                )
            )

            ping_ms = 0
            if ret == 0:
                # Parse ping output for average time
                match = re.search(r"rtt min/avg/max/mdev = [\d.]+/([\d.]+)/", out)
                if match:
                    ping_ms = float(match.group(1))

            return SpeedTestResult(
                timestamp=datetime.now().isoformat(),
                download_mbps=0,
                upload_mbps=0,
                ping_ms=ping_ms,
                success=True if ret == 0 else False,
                error="" if ret == 0 else "Ping test failed - no internet connection",
                server="Google DNS (8.8.8.8)",
            )

        except Exception as e:
            return SpeedTestResult(
                timestamp=datetime.now().isoformat(),
                download_mbps=0,
                upload_mbps=0,
                ping_ms=0,
                success=False,
                error=str(e)
            )

    @classmethod
    def get_history(cls) -> List[SpeedTestResult]:
        """
        Get speed test history.

        Returns:
            List of SpeedTestResult objects
        """
        if not cls.HISTORY_FILE.exists():
            return []

        try:
            data = json.loads(cls.HISTORY_FILE.read_text())
            return [
                SpeedTestResult(**entry)
                for entry in data
            ]
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to read history: {e}")
            return []

    @classmethod
    def _save_to_history(cls, result: SpeedTestResult) -> None:
        """
        Save a result to history.

        Args:
            result: SpeedTestResult to save
        """
        history = cls.get_history()
        history.insert(0, result)

        # Trim to max size
        history = history[:cls.MAX_HISTORY]

        try:
            cls.HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            cls.HISTORY_FILE.write_text(
                json.dumps([r.to_dict() for r in history], indent=2)
            )
        except OSError as e:
            logger.error(f"Failed to save history: {e}")

    @classmethod
    def clear_history(cls) -> bool:
        """
        Clear speed test history.

        Returns:
            True if cleared successfully
        """
        try:
            if cls.HISTORY_FILE.exists():
                cls.HISTORY_FILE.unlink()
            return True
        except OSError as e:
            logger.error(f"Failed to clear history: {e}")
            return False

    @classmethod
    def get_last_result(cls) -> Optional[SpeedTestResult]:
        """
        Get the most recent test result.

        Returns:
            Last SpeedTestResult or None
        """
        if cls._current_result:
            return cls._current_result

        history = cls.get_history()
        return history[0] if history else None
