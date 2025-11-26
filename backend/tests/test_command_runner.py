"""
Command Runner Tests
====================

Unit tests for the command execution layer.

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import pytest

from utils.command_runner import (
    CommandResult,
    CommandRunner,
    run_command,
    ICommandExecutor,
    SubprocessExecutor,
    set_executor,
    reset_executor,
    get_executor,
)
from tests.conftest import MockCommandExecutor


class TestCommandResult:
    """Tests for CommandResult dataclass."""

    def test_success_property_true_when_return_code_zero(self) -> None:
        """CommandResult.success should be True when return_code is 0."""
        result = CommandResult(return_code=0, stdout="output", stderr="")
        assert result.success is True

    def test_success_property_false_when_return_code_nonzero(self) -> None:
        """CommandResult.success should be False when return_code is not 0."""
        result = CommandResult(return_code=1, stdout="", stderr="error")
        assert result.success is False

    def test_success_property_false_when_return_code_negative(self) -> None:
        """CommandResult.success should be False when return_code is -1 (exception)."""
        result = CommandResult(return_code=-1, stdout="", stderr="timeout")
        assert result.success is False


class TestMockExecutor:
    """Tests for the mock executor infrastructure."""

    def test_mock_executor_records_calls(self, mock_executor: MockCommandExecutor) -> None:
        """Mock executor should record all command calls."""
        run_command(["ls", "-la"])
        run_command(["cat", "/etc/hosts"])

        assert len(mock_executor.calls) == 2
        assert mock_executor.calls[0][0] == ["ls", "-la"]
        assert mock_executor.calls[1][0] == ["cat", "/etc/hosts"]

    def test_mock_executor_returns_configured_response(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Mock executor should return configured responses."""
        mock_executor.set_response("ls -la", return_code=0, stdout="file1\nfile2")

        ret, out, err = run_command(["ls", "-la"])

        assert ret == 0
        assert out == "file1\nfile2"
        assert err == ""

    def test_mock_executor_returns_default_when_no_match(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Mock executor should return default response for unknown commands."""
        ret, out, err = run_command(["unknown", "command"])

        assert ret == 0
        assert out == ""
        assert err == ""


class TestRunCommand:
    """Tests for the run_command function."""

    def test_run_command_returns_tuple(self, mock_executor: MockCommandExecutor) -> None:
        """run_command should return a tuple of (return_code, stdout, stderr)."""
        mock_executor.set_response("echo hello", return_code=0, stdout="hello\n")

        result = run_command(["echo", "hello"])

        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_run_command_passes_timeout_to_executor(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """run_command should pass timeout to the executor."""
        run_command(["sleep", "5"], timeout=60)

        assert mock_executor.calls[0][1] == 60


class TestCommandRunner:
    """Tests for CommandRunner class methods."""

    def test_execute_returns_command_result(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """CommandRunner.execute should return a CommandResult object."""
        mock_executor.set_response("ls", return_code=0, stdout="files")

        result = CommandRunner.execute(["ls"])

        assert isinstance(result, CommandResult)
        assert result.success is True
        assert result.stdout == "files"

    def test_systemctl_start_service(self, mock_executor: MockCommandExecutor) -> None:
        """CommandRunner.start_service should call systemctl start."""
        mock_executor.set_response("sudo systemctl start nginx", return_code=0)

        result = CommandRunner.start_service("nginx")

        assert result is True
        assert mock_executor.calls[0][0] == ["sudo", "systemctl", "start", "nginx"]

    def test_systemctl_stop_service(self, mock_executor: MockCommandExecutor) -> None:
        """CommandRunner.stop_service should call systemctl stop."""
        mock_executor.set_response("sudo systemctl stop nginx", return_code=0)

        result = CommandRunner.stop_service("nginx")

        assert result is True
        assert mock_executor.calls[0][0] == ["sudo", "systemctl", "stop", "nginx"]

    def test_systemctl_restart_service(self, mock_executor: MockCommandExecutor) -> None:
        """CommandRunner.restart_service should call systemctl restart."""
        mock_executor.set_response("sudo systemctl restart nginx", return_code=0)

        result = CommandRunner.restart_service("nginx")

        assert result is True
        assert mock_executor.calls[0][0] == ["sudo", "systemctl", "restart", "nginx"]

    def test_is_service_active_returns_true_when_active(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """CommandRunner.is_service_active should return True when service is active."""
        mock_executor.set_response(
            "systemctl is-active nginx", return_code=0, stdout="active\n"
        )

        result = CommandRunner.is_service_active("nginx")

        assert result is True

    def test_is_service_active_returns_false_when_inactive(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """CommandRunner.is_service_active should return False when service is inactive."""
        mock_executor.set_response(
            "systemctl is-active nginx", return_code=3, stdout="inactive\n"
        )

        result = CommandRunner.is_service_active("nginx")

        assert result is False

    def test_wifi_scan_calls_nmcli(self, mock_executor: MockCommandExecutor) -> None:
        """CommandRunner.wifi_scan should call nmcli."""
        mock_executor.set_response(
            "sudo nmcli -t -f SSID,SIGNAL,SECURITY device wifi list",
            return_code=0,
            stdout="MyNetwork:75:WPA2\n",
        )

        ret, out, err = CommandRunner.wifi_scan()

        assert ret == 0
        assert "MyNetwork" in out

    def test_wg_show_calls_wg(self, mock_executor: MockCommandExecutor) -> None:
        """CommandRunner.wg_show should call wg show."""
        mock_executor.set_response(
            "sudo wg show wg0",
            return_code=0,
            stdout="interface: wg0\n",
        )

        ret, out, err = CommandRunner.wg_show()

        assert ret == 0
        assert "wg0" in out


class TestExecutorDependencyInjection:
    """Tests for executor dependency injection."""

    def test_set_executor_changes_global_executor(self) -> None:
        """set_executor should change the global executor instance."""
        mock = MockCommandExecutor()
        mock.set_response("test", return_code=42, stdout="mocked")

        original = get_executor()
        set_executor(mock)

        try:
            ret, out, _ = run_command(["test"])
            assert ret == 42
            assert out == "mocked"
        finally:
            set_executor(original)

    def test_reset_executor_restores_default(self) -> None:
        """reset_executor should restore the default SubprocessExecutor."""
        mock = MockCommandExecutor()
        set_executor(mock)

        reset_executor()

        assert isinstance(get_executor(), SubprocessExecutor)
