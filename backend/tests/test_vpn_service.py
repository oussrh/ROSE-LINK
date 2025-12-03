"""
VPN Service Tests
=================

Unit tests for the VPN service with mocked command execution.

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from tests.conftest import MockCommandExecutor


class TestVPNServiceStatus:
    """Tests for VPN status retrieval."""

    def test_get_status_inactive_when_wg_fails(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """get_status should return inactive when wg show fails."""
        mock_executor.set_response("sudo wg show wg0", return_code=1, stdout="")

        from services.vpn_service import VPNService

        status = VPNService.get_status()

        assert status.active is False

    def test_get_status_active_when_wg_succeeds(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """get_status should return active when wg show succeeds."""
        wg_output = """interface: wg0
  public key: abc123
  private key: (hidden)
  listening port: 51820

peer: def456
  endpoint: 192.168.1.1:51820
  latest handshake: 2 minutes, 30 seconds ago
  transfer: 1.23 MiB received, 456 KiB sent
"""
        mock_executor.set_response("sudo wg show wg0", return_code=0, stdout=wg_output)

        from services.vpn_service import VPNService

        status = VPNService.get_status()

        assert status.active is True
        assert status.endpoint == "192.168.1.1:51820"
        assert "minutes" in status.latest_handshake

    def test_get_status_parses_transfer_stats(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """get_status should parse transfer statistics."""
        wg_output = """interface: wg0
transfer: 1.23 MiB received, 456 KiB sent
"""
        mock_executor.set_response("sudo wg show wg0", return_code=0, stdout=wg_output)

        from services.vpn_service import VPNService

        status = VPNService.get_status()

        assert status.transfer is not None
        assert "1.23 MiB" in status.transfer.received
        assert "456 KiB" in status.transfer.sent


class TestVPNServiceProfiles:
    """Tests for VPN profile management."""

    def test_list_profiles_empty_directory(self, temp_dir: Path) -> None:
        """list_profiles should return empty list when no profiles exist."""
        profiles_dir = temp_dir / "profiles"
        profiles_dir.mkdir()

        with patch("services.vpn_service.Paths") as mock_paths:
            mock_paths.WG_PROFILES_DIR = profiles_dir
            mock_paths.WG_ACTIVE_CONF = temp_dir / "wg0.conf"

            from services.vpn_service import VPNService

            profiles = VPNService.list_profiles()

            assert profiles == []

    def test_list_profiles_finds_conf_files(self, temp_dir: Path) -> None:
        """list_profiles should find all .conf files."""
        profiles_dir = temp_dir / "profiles"
        profiles_dir.mkdir()

        # Create some profile files
        (profiles_dir / "server1.conf").write_text("[Interface]\nPrivateKey=abc")
        (profiles_dir / "server2.conf").write_text("[Interface]\nPrivateKey=def")

        with patch("services.vpn_service.Paths") as mock_paths:
            mock_paths.WG_PROFILES_DIR = profiles_dir
            mock_paths.WG_ACTIVE_CONF = temp_dir / "wg0.conf"

            from services.vpn_service import VPNService

            profiles = VPNService.list_profiles()

            assert len(profiles) == 2
            names = [p.name for p in profiles]
            assert "server1" in names
            assert "server2" in names

    def test_list_profiles_identifies_active(self, temp_dir: Path) -> None:
        """list_profiles should mark the active profile."""
        profiles_dir = temp_dir / "profiles"
        profiles_dir.mkdir()

        profile_path = profiles_dir / "active.conf"
        profile_path.write_text("[Interface]\nPrivateKey=abc")

        wg0_conf = temp_dir / "wg0.conf"
        wg0_conf.symlink_to(profile_path)

        with patch("services.vpn_service.Paths") as mock_paths:
            mock_paths.WG_PROFILES_DIR = profiles_dir
            mock_paths.WG_ACTIVE_CONF = wg0_conf

            from services.vpn_service import VPNService

            profiles = VPNService.list_profiles()

            assert len(profiles) == 1
            assert profiles[0].active is True

    def test_upload_profile_validates_size(self, temp_dir: Path) -> None:
        """upload_profile should reject files exceeding size limit."""
        profiles_dir = temp_dir / "profiles"
        profiles_dir.mkdir()

        # Create content larger than 1MB limit
        large_content = b"x" * (1024 * 1024 + 1)

        with patch("services.vpn_service.Paths") as mock_paths:
            mock_paths.WG_PROFILES_DIR = profiles_dir
            mock_paths.MAX_VPN_PROFILE_SIZE = 1024 * 1024

            from services.vpn_service import VPNService
            from exceptions import FileTooLargeError

            with pytest.raises(FileTooLargeError):
                VPNService.upload_profile("test.conf", large_content)

    def test_upload_profile_validates_config(self, temp_dir: Path) -> None:
        """upload_profile should validate WireGuard config format."""
        profiles_dir = temp_dir / "profiles"
        profiles_dir.mkdir()

        invalid_content = b"This is not a valid WireGuard config"

        with patch("services.vpn_service.Paths") as mock_paths:
            mock_paths.WG_PROFILES_DIR = profiles_dir

            from services.vpn_service import VPNService
            from exceptions import InvalidWireGuardConfigError

            with pytest.raises(InvalidWireGuardConfigError):
                VPNService.upload_profile("test.conf", invalid_content)

    def test_upload_profile_saves_valid_config(self, temp_dir: Path) -> None:
        """upload_profile should save valid WireGuard config."""
        profiles_dir = temp_dir / "profiles"
        profiles_dir.mkdir()

        valid_content = b"""[Interface]
PrivateKey = abc123

[Peer]
PublicKey = def456
"""

        with patch("services.vpn_service.Paths") as mock_paths:
            mock_paths.WG_PROFILES_DIR = profiles_dir

            from services.vpn_service import VPNService

            filename = VPNService.upload_profile("test.conf", valid_content)

            assert filename.endswith(".conf")
            assert (profiles_dir / filename).exists()

    def test_upload_profile_sanitizes_filename(self, temp_dir: Path) -> None:
        """upload_profile should sanitize the filename."""
        profiles_dir = temp_dir / "profiles"
        profiles_dir.mkdir()

        valid_content = b"[Interface]\nPrivateKey = abc123"

        with patch("services.vpn_service.Paths") as mock_paths:
            mock_paths.WG_PROFILES_DIR = profiles_dir

            from services.vpn_service import VPNService

            filename = VPNService.upload_profile("../../../etc/passwd", valid_content)

            # Should not contain path traversal
            assert ".." not in filename
            assert "/" not in filename


class TestVPNServiceActivation:
    """Tests for VPN profile activation."""

    def test_activate_profile_not_found(
        self, temp_dir: Path, mock_executor: MockCommandExecutor
    ) -> None:
        """activate_profile should raise error for non-existent profile."""
        profiles_dir = temp_dir / "profiles"
        profiles_dir.mkdir()

        with patch("services.vpn_service.Paths") as mock_paths:
            mock_paths.WG_PROFILES_DIR = profiles_dir
            mock_paths.WG_ACTIVE_CONF = temp_dir / "wg0.conf"

            from services.vpn_service import VPNService
            from exceptions import VPNProfileNotFoundError

            with pytest.raises(VPNProfileNotFoundError):
                VPNService.activate_profile("nonexistent")

    def test_activate_profile_creates_symlink(
        self, temp_dir: Path, mock_executor: MockCommandExecutor
    ) -> None:
        """activate_profile should create symlink to profile."""
        profiles_dir = temp_dir / "profiles"
        profiles_dir.mkdir()

        profile_path = profiles_dir / "server.conf"
        profile_path.write_text("[Interface]\nPrivateKey=abc")

        wg0_conf = temp_dir / "wg0.conf"

        mock_executor.set_response("sudo systemctl stop wg-quick@wg0", return_code=0)
        mock_executor.set_response("sudo systemctl start wg-quick@wg0", return_code=0)

        with patch("services.vpn_service.Paths") as mock_paths:
            mock_paths.WG_PROFILES_DIR = profiles_dir
            mock_paths.WG_ACTIVE_CONF = wg0_conf

            from services.vpn_service import VPNService

            VPNService.activate_profile("server")

            assert wg0_conf.is_symlink()
            assert wg0_conf.resolve() == profile_path.resolve()


class TestVPNServiceConnection:
    """Tests for VPN connection control."""

    def test_start_calls_wg_start(self, mock_executor: MockCommandExecutor) -> None:
        """start should call wg_start command."""
        mock_executor.set_response("sudo systemctl start wg-quick@wg0", return_code=0)

        from services.vpn_service import VPNService

        result = VPNService.start()

        assert result is True
        assert any("wg-quick@wg0" in " ".join(c[0]) for c in mock_executor.calls)

    def test_start_raises_on_failure(self, mock_executor: MockCommandExecutor) -> None:
        """start should raise VPNConnectionError on failure."""
        mock_executor.set_response("sudo systemctl start wg-quick@wg0", return_code=1)

        from services.vpn_service import VPNService
        from exceptions import VPNConnectionError

        with pytest.raises(VPNConnectionError):
            VPNService.start()

    def test_stop_calls_wg_stop(self, mock_executor: MockCommandExecutor) -> None:
        """stop should call wg_stop command."""
        mock_executor.set_response("sudo systemctl stop wg-quick@wg0", return_code=0)

        from services.vpn_service import VPNService

        result = VPNService.stop()

        assert result is True

    def test_restart_calls_wg_restart(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """restart should call wg_restart command."""
        mock_executor.set_response("sudo systemctl restart wg-quick@wg0", return_code=0)

        from services.vpn_service import VPNService

        result = VPNService.restart()

        assert result is True


class TestVPNServiceSettings:
    """Tests for VPN watchdog settings."""

    def test_get_settings_returns_defaults(self, temp_dir: Path) -> None:
        """get_settings should return defaults when no config exists."""
        with patch("services.vpn_service.Paths") as mock_paths:
            mock_paths.VPN_SETTINGS_CONF = temp_dir / "nonexistent.conf"

            from services.vpn_service import VPNService

            settings = VPNService.get_settings()

            assert settings.ping_host == "8.8.8.8"
            assert settings.check_interval == 60

    def test_get_settings_reads_config(self, temp_dir: Path) -> None:
        """get_settings should read values from config file."""
        config_file = temp_dir / "vpn-settings.conf"
        config_file.write_text("""# VPN Settings
PING_HOST=1.1.1.1
CHECK_INTERVAL=120
""")

        with patch("services.vpn_service.Paths") as mock_paths:
            mock_paths.VPN_SETTINGS_CONF = config_file

            from services.vpn_service import VPNService

            settings = VPNService.get_settings()

            assert settings.ping_host == "1.1.1.1"
            assert settings.check_interval == 120

    def test_save_settings_writes_config(
        self, temp_dir: Path, mock_executor: MockCommandExecutor
    ) -> None:
        """save_settings should write config file."""
        config_file = temp_dir / "vpn-settings.conf"

        mock_executor.set_response("sudo systemctl restart", return_code=0)

        with patch("services.vpn_service.Paths") as mock_paths:
            mock_paths.VPN_SETTINGS_CONF = config_file

            from services.vpn_service import VPNService
            from models import VPNSettings

            settings = VPNSettings(ping_host="1.1.1.1", check_interval=90)
            result = VPNService.save_settings(settings)

            assert result is True
            assert config_file.exists()

            content = config_file.read_text()
            assert "1.1.1.1" in content
            assert "90" in content


class TestVPNServiceIsActive:
    """Tests for the is_active convenience method."""

    def test_is_active_returns_true_when_connected(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """is_active should return True when VPN is connected."""
        mock_executor.set_response(
            "sudo wg show wg0",
            return_code=0,
            stdout="interface: wg0\n",
        )

        from services.vpn_service import VPNService

        assert VPNService.is_active() is True

    def test_is_active_returns_false_when_disconnected(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """is_active should return False when VPN is not connected."""
        mock_executor.set_response("sudo wg show wg0", return_code=1, stdout="")

        from services.vpn_service import VPNService

        assert VPNService.is_active() is False
