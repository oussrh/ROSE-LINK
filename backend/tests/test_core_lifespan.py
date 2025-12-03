"""
Lifespan Management Tests
=========================

Tests for the application lifecycle management (startup/shutdown).

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from core.lifespan import (
    startup_tasks,
    shutdown_tasks,
    _ensure_directories,
    _initialize_auth,
    lifespan_handler,
)


class TestStartupTasks:
    """Tests for startup task execution."""

    @pytest.mark.asyncio
    async def test_startup_tasks_logs_start_message(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Startup should log application start message."""
        with patch("core.lifespan._ensure_directories", new_callable=AsyncMock):
            with patch("core.lifespan._initialize_auth", new_callable=AsyncMock):
                with caplog.at_level(logging.INFO, logger="rose-link.lifespan"):
                    await startup_tasks()

                assert "Starting ROSE Link" in caplog.text

    @pytest.mark.asyncio
    async def test_startup_tasks_logs_completion(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Startup should log completion message."""
        with patch("core.lifespan._ensure_directories", new_callable=AsyncMock):
            with patch("core.lifespan._initialize_auth", new_callable=AsyncMock):
                with caplog.at_level(logging.INFO, logger="rose-link.lifespan"):
                    await startup_tasks()

                assert "Startup complete" in caplog.text

    @pytest.mark.asyncio
    async def test_startup_tasks_calls_ensure_directories(self) -> None:
        """Startup should call _ensure_directories."""
        with patch(
            "core.lifespan._ensure_directories", new_callable=AsyncMock
        ) as mock_dirs:
            with patch("core.lifespan._initialize_auth", new_callable=AsyncMock):
                await startup_tasks()

                mock_dirs.assert_called_once()

    @pytest.mark.asyncio
    async def test_startup_tasks_calls_initialize_auth(self) -> None:
        """Startup should call _initialize_auth."""
        with patch("core.lifespan._ensure_directories", new_callable=AsyncMock):
            with patch(
                "core.lifespan._initialize_auth", new_callable=AsyncMock
            ) as mock_auth:
                await startup_tasks()

                mock_auth.assert_called_once()


class TestShutdownTasks:
    """Tests for shutdown task execution."""

    @pytest.mark.asyncio
    async def test_shutdown_tasks_logs_message(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Shutdown should log shutdown message."""
        with caplog.at_level(logging.INFO, logger="rose-link.lifespan"):
            await shutdown_tasks()

        assert "Shutting down ROSE Link" in caplog.text


class TestEnsureDirectories:
    """Tests for directory creation."""

    @pytest.mark.asyncio
    async def test_ensure_directories_creates_wg_dir(self, temp_dir: Path) -> None:
        """Should create WireGuard profiles directory."""
        wg_profiles_dir = temp_dir / "wireguard" / "profiles"

        with patch("core.lifespan.Paths") as mock_paths:
            mock_paths.WG_PROFILES_DIR = wg_profiles_dir

            await _ensure_directories()

            assert wg_profiles_dir.exists()

    @pytest.mark.asyncio
    async def test_ensure_directories_handles_permission_error(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Should handle permission errors gracefully."""
        mock_path = MagicMock()
        mock_path.mkdir.side_effect = PermissionError("Access denied")

        with patch("core.lifespan.Paths") as mock_paths:
            mock_paths.WG_PROFILES_DIR = mock_path

            with caplog.at_level(logging.ERROR, logger="rose-link.lifespan"):
                await _ensure_directories()

            assert "Permission denied" in caplog.text

    @pytest.mark.asyncio
    async def test_ensure_directories_handles_os_error(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Should handle OS errors gracefully."""
        mock_path = MagicMock()
        mock_path.mkdir.side_effect = OSError("Disk full")

        with patch("core.lifespan.Paths") as mock_paths:
            mock_paths.WG_PROFILES_DIR = mock_path

            with caplog.at_level(logging.ERROR, logger="rose-link.lifespan"):
                await _ensure_directories()

            assert "Failed to create directory" in caplog.text


class TestInitializeAuth:
    """Tests for authentication initialization."""

    @pytest.mark.asyncio
    async def test_initialize_auth_gets_or_creates_key(self) -> None:
        """Should call get_or_create_api_key."""
        with patch("core.lifespan.AuthService") as mock_auth:
            mock_auth.get_or_create_api_key.return_value = "test-key"

            await _initialize_auth()

            mock_auth.get_or_create_api_key.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_auth_logs_success(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Should log success when key is available."""
        with patch("core.lifespan.AuthService") as mock_auth:
            mock_auth.get_or_create_api_key.return_value = "test-key"
            with patch("core.lifespan.Paths") as mock_paths:
                mock_paths.API_KEY_FILE = Path("/test/api_key")

                with caplog.at_level(logging.INFO, logger="rose-link.lifespan"):
                    await _initialize_auth()

                assert "API key available" in caplog.text

    @pytest.mark.asyncio
    async def test_initialize_auth_warns_empty_key(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Should warn when key is empty."""
        with patch("core.lifespan.AuthService") as mock_auth:
            mock_auth.get_or_create_api_key.return_value = ""

            with caplog.at_level(logging.WARNING, logger="rose-link.lifespan"):
                await _initialize_auth()

            assert "empty key" in caplog.text

    @pytest.mark.asyncio
    async def test_initialize_auth_handles_permission_error(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Should handle permission errors gracefully."""
        with patch("core.lifespan.AuthService") as mock_auth:
            mock_auth.get_or_create_api_key.side_effect = PermissionError("Access denied")

            with caplog.at_level(logging.ERROR, logger="rose-link.lifespan"):
                await _initialize_auth()

            assert "Permission denied" in caplog.text

    @pytest.mark.asyncio
    async def test_initialize_auth_handles_os_error(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Should handle OS errors gracefully."""
        with patch("core.lifespan.AuthService") as mock_auth:
            mock_auth.get_or_create_api_key.side_effect = OSError("Disk error")

            with caplog.at_level(logging.ERROR, logger="rose-link.lifespan"):
                await _initialize_auth()

            assert "Failed to initialize API key" in caplog.text


class TestLifespanHandler:
    """Tests for the main lifespan context manager."""

    @pytest.mark.asyncio
    async def test_lifespan_handler_runs_startup_and_shutdown(self) -> None:
        """Lifespan handler should run startup and shutdown."""
        mock_app = MagicMock()
        startup_called = False
        shutdown_called = False

        async def mock_startup():
            nonlocal startup_called
            startup_called = True

        async def mock_shutdown():
            nonlocal shutdown_called
            shutdown_called = True

        with patch("core.lifespan.startup_tasks", side_effect=mock_startup):
            with patch("core.lifespan.shutdown_tasks", side_effect=mock_shutdown):
                async with lifespan_handler(mock_app):
                    assert startup_called is True
                    assert shutdown_called is False

                assert shutdown_called is True

    @pytest.mark.asyncio
    async def test_lifespan_handler_yields_control(self) -> None:
        """Lifespan handler should yield control to the application."""
        mock_app = MagicMock()
        app_ran = False

        with patch("core.lifespan.startup_tasks", new_callable=AsyncMock):
            with patch("core.lifespan.shutdown_tasks", new_callable=AsyncMock):
                async with lifespan_handler(mock_app):
                    app_ran = True

        assert app_ran is True
