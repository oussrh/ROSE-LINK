"""
Pytest Configuration and Shared Fixtures
=========================================

This module provides shared fixtures and configuration for all tests.

Key Features:
- Mock command executor for isolated testing
- Temporary directory fixtures for file operations
- FastAPI test client configuration
- Environment variable isolation

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from utils.command_runner import (
    CommandResult,
    ICommandExecutor,
    set_executor,
    reset_executor,
)


# =============================================================================
# Command Executor Fixtures
# =============================================================================


class MockCommandExecutor(ICommandExecutor):
    """
    Mock command executor for testing.

    This executor records all commands and returns configurable responses.
    """

    def __init__(self) -> None:
        self.calls: list[tuple[list[str], int]] = []
        self.responses: dict[str, CommandResult] = {}
        self.default_response = CommandResult(0, "", "")

    def execute(
        self,
        cmd: list[str],
        timeout: int = 30,
    ) -> CommandResult:
        """Record the command and return a mock response."""
        self.calls.append((cmd, timeout))

        # Check for specific command responses
        cmd_key = " ".join(cmd)
        if cmd_key in self.responses:
            return self.responses[cmd_key]

        # Check for partial matches (first few elements)
        for key, response in self.responses.items():
            if cmd_key.startswith(key):
                return response

        return self.default_response

    def set_response(
        self,
        cmd: str,
        return_code: int = 0,
        stdout: str = "",
        stderr: str = "",
    ) -> None:
        """Set a response for a specific command."""
        self.responses[cmd] = CommandResult(return_code, stdout, stderr)

    def reset(self) -> None:
        """Reset all recorded calls and responses."""
        self.calls.clear()
        self.responses.clear()


@pytest.fixture
def mock_executor() -> Generator[MockCommandExecutor, None, None]:
    """
    Fixture providing a mock command executor.

    This fixture automatically:
    - Sets up the mock executor before each test
    - Resets to the real executor after each test

    Example:
        def test_something(mock_executor):
            mock_executor.set_response("sudo systemctl start foo", return_code=0)
            # ... test code that calls commands ...
            assert len(mock_executor.calls) == 1
    """
    executor = MockCommandExecutor()
    set_executor(executor)
    yield executor
    reset_executor()


# =============================================================================
# File System Fixtures
# =============================================================================


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """
    Fixture providing a temporary directory.

    The directory is automatically cleaned up after the test.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_config_dir(temp_dir: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """
    Fixture providing a temporary configuration directory.

    Sets environment variables to use temporary paths:
    - ROSE_LINK_DIR
    - ROSE_WG_DIR

    This isolates tests from the actual system configuration.
    """
    rose_link_dir = temp_dir / "rose-link"
    wg_dir = temp_dir / "wireguard"

    rose_link_dir.mkdir(parents=True)
    (rose_link_dir / "system").mkdir()
    (rose_link_dir / "web").mkdir()
    wg_dir.mkdir(parents=True)
    (wg_dir / "profiles").mkdir()

    monkeypatch.setenv("ROSE_LINK_DIR", str(rose_link_dir))
    monkeypatch.setenv("ROSE_WG_DIR", str(wg_dir))

    return rose_link_dir


# =============================================================================
# FastAPI Test Client Fixtures
# =============================================================================


@pytest.fixture
def client(mock_executor: MockCommandExecutor) -> Generator[TestClient, None, None]:
    """
    Fixture providing a FastAPI test client.

    The test client uses the mock executor to avoid actual system calls.

    Example:
        def test_health_endpoint(client):
            response = client.get("/api/health")
            assert response.status_code == 200
    """
    # Import here to avoid side effects at module load time
    from main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def authenticated_client(
    client: TestClient,
    temp_config_dir: Path,
) -> TestClient:
    """
    Fixture providing an authenticated test client.

    Creates a valid API key and adds it to the client headers.
    """
    # Create API key in temp directory
    api_key = "test-api-key-12345"
    api_key_file = temp_config_dir / "system" / ".api_key"
    api_key_file.write_text(api_key)

    import hashlib
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    hash_file = temp_config_dir / "system" / ".api_key_hash"
    hash_file.write_text(key_hash)

    # Add API key header
    client.headers["X-API-Key"] = api_key
    return client


# =============================================================================
# Pytest Configuration
# =============================================================================


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    )
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests (require real system access)",
    )
