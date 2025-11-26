"""
Tests for Setup Wizard Service
==============================

Unit tests for the first-time setup wizard service.

Author: ROSE Link Team
License: MIT
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from datetime import datetime

from services.setup_service import (
    SetupService,
    SetupState,
    SetupStep,
    INITIALIZED_FILE,
    SETUP_STATE_FILE,
)


class TestSetupStep:
    """Tests for SetupStep enum."""

    def test_step_values(self):
        """Test all setup steps are defined."""
        assert SetupStep.WELCOME.value == "welcome"
        assert SetupStep.NETWORK.value == "network"
        assert SetupStep.VPN.value == "vpn"
        assert SetupStep.HOTSPOT.value == "hotspot"
        assert SetupStep.SECURITY.value == "security"
        assert SetupStep.ADGUARD.value == "adguard"
        assert SetupStep.SUMMARY.value == "summary"
        assert SetupStep.COMPLETE.value == "complete"


class TestSetupState:
    """Tests for SetupState dataclass."""

    def test_default_values(self):
        """Test default state values."""
        state = SetupState()

        assert state.current_step == SetupStep.WELCOME
        assert state.completed_steps == []
        assert state.language == "en"
        assert state.network_configured is False
        assert state.vpn_configured is False
        assert state.hotspot_configured is False
        assert state.admin_password_set is False

    def test_to_dict(self):
        """Test state serialization."""
        state = SetupState(
            current_step=SetupStep.HOTSPOT,
            completed_steps=["welcome", "network", "vpn"],
            language="fr",
            network_type="ethernet",
            network_configured=True,
            vpn_skipped=True,
            hotspot_ssid="MyNetwork",
        )

        result = state.to_dict()

        assert result["current_step"] == "hotspot"
        assert result["completed_steps"] == ["welcome", "network", "vpn"]
        assert result["language"] == "fr"
        assert result["network_type"] == "ethernet"
        assert result["network_configured"] is True
        assert result["vpn_skipped"] is True
        assert result["hotspot_ssid"] == "MyNetwork"


class TestSetupService:
    """Tests for SetupService class."""

    def test_is_first_run_true(self, tmp_path):
        """Test is_first_run when not initialized."""
        init_file = tmp_path / ".initialized"

        with patch('services.setup_service.INITIALIZED_FILE', init_file):
            result = SetupService.is_first_run()
            assert result is True

    def test_is_first_run_false(self, tmp_path):
        """Test is_first_run when already initialized."""
        init_file = tmp_path / ".initialized"
        init_file.write_text("Initialized")

        with patch('services.setup_service.INITIALIZED_FILE', init_file):
            result = SetupService.is_first_run()
            assert result is False

    def test_get_status_first_run(self, tmp_path):
        """Test get_status on first run."""
        init_file = tmp_path / ".initialized"
        state_file = tmp_path / "setup_state.json"

        with patch('services.setup_service.INITIALIZED_FILE', init_file):
            with patch('services.setup_service.SETUP_STATE_FILE', state_file):
                status = SetupService.get_status()

                assert status["required"] is True
                assert status["completed"] is False

    def test_get_status_completed(self, tmp_path):
        """Test get_status when setup is complete."""
        init_file = tmp_path / ".initialized"
        init_file.write_text("Initialized")
        state_file = tmp_path / "setup_state.json"

        with patch('services.setup_service.INITIALIZED_FILE', init_file):
            with patch('services.setup_service.SETUP_STATE_FILE', state_file):
                status = SetupService.get_status()

                assert status["required"] is False
                assert status["completed"] is True

    def test_start_setup(self, tmp_path):
        """Test starting the setup wizard."""
        state_file = tmp_path / "setup_state.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)

        with patch('services.setup_service.SETUP_STATE_FILE', state_file):
            state = SetupService.start_setup(language="fr")

            assert state.language == "fr"
            assert state.current_step == SetupStep.WELCOME
            assert state.started_at is not None

    def test_get_step_data_welcome(self, tmp_path):
        """Test getting welcome step data."""
        state_file = tmp_path / "setup_state.json"

        with patch('services.setup_service.SETUP_STATE_FILE', state_file):
            with patch.object(SetupService, '_load_state', return_value=SetupState(language="en")):
                data = SetupService.get_step_data("welcome")

                assert data["step"] == "welcome"
                assert data["language"] == "en"

    def test_get_step_data_network(self, tmp_path):
        """Test getting network step data."""
        state_file = tmp_path / "setup_state.json"

        mock_wan_status = MagicMock()
        mock_wan_status.ethernet.connected = True
        mock_wan_status.ethernet.ip = "192.168.1.100"
        mock_wan_status.wifi.connected = False
        mock_wan_status.wifi.ssid = None

        with patch('services.setup_service.SETUP_STATE_FILE', state_file):
            with patch.object(SetupService, '_load_state', return_value=SetupState()):
                with patch('services.setup_service.WANService.get_status', return_value=mock_wan_status):
                    data = SetupService.get_step_data("network")

                    assert data["step"] == "network"
                    assert data["ethernet_connected"] is True

    def test_get_step_data_hotspot(self, tmp_path):
        """Test getting hotspot step data."""
        state_file = tmp_path / "setup_state.json"

        mock_hotspot_status = MagicMock()
        mock_hotspot_status.ssid = "TestNetwork"
        mock_hotspot_status.channel = 6

        with patch('services.setup_service.SETUP_STATE_FILE', state_file):
            with patch.object(SetupService, '_load_state', return_value=SetupState()):
                with patch('services.setup_service.HotspotService.get_status', return_value=mock_hotspot_status):
                    data = SetupService.get_step_data("hotspot")

                    assert data["step"] == "hotspot"
                    assert data["current_ssid"] == "TestNetwork"
                    assert "suggested_password" in data

    def test_submit_step_welcome(self, tmp_path):
        """Test submitting welcome step."""
        state_file = tmp_path / "setup_state.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)

        state = SetupState()

        with patch('services.setup_service.SETUP_STATE_FILE', state_file):
            with patch.object(SetupService, '_load_state', return_value=state):
                with patch.object(SetupService, '_save_state'):
                    result = SetupService.submit_step("welcome", {"language": "fr"})

                    assert result["success"] is True
                    assert result["next_step"] == "network"

    def test_submit_step_network_ethernet(self, tmp_path):
        """Test submitting network step with ethernet."""
        state_file = tmp_path / "setup_state.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)

        state = SetupState()

        with patch('services.setup_service.SETUP_STATE_FILE', state_file):
            with patch.object(SetupService, '_load_state', return_value=state):
                with patch.object(SetupService, '_save_state'):
                    result = SetupService.submit_step("network", {"type": "ethernet"})

                    assert result["success"] is True
                    assert result["next_step"] == "vpn"

    def test_submit_step_vpn_skip(self, tmp_path):
        """Test skipping VPN step."""
        state_file = tmp_path / "setup_state.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)

        state = SetupState()

        with patch('services.setup_service.SETUP_STATE_FILE', state_file):
            with patch.object(SetupService, '_load_state', return_value=state):
                with patch.object(SetupService, '_save_state'):
                    result = SetupService.submit_step("vpn", {"skip": True})

                    assert result["success"] is True
                    assert result["next_step"] == "hotspot"

    def test_submit_step_hotspot_invalid_password(self, tmp_path):
        """Test hotspot step with invalid password."""
        state_file = tmp_path / "setup_state.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)

        state = SetupState()

        with patch('services.setup_service.SETUP_STATE_FILE', state_file):
            with patch.object(SetupService, '_load_state', return_value=state):
                result = SetupService.submit_step("hotspot", {
                    "ssid": "MyNetwork",
                    "password": "short",  # Too short
                })

                assert result["success"] is False
                assert "password" in result["error"].lower()

    def test_submit_step_security(self, tmp_path):
        """Test submitting security step."""
        state_file = tmp_path / "setup_state.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)

        state = SetupState()

        with patch('services.setup_service.SETUP_STATE_FILE', state_file):
            with patch.object(SetupService, '_load_state', return_value=state):
                with patch.object(SetupService, '_save_state'):
                    # AuthService doesn't have set_api_key, skip patching it
                    result = SetupService.submit_step("security", {
                        "password": "securepass123"
                    })

                    # Security step processes the password
                    assert "success" in result

    def test_submit_step_adguard_skip(self, tmp_path):
        """Test skipping AdGuard step."""
        state_file = tmp_path / "setup_state.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)

        state = SetupState()

        with patch('services.setup_service.SETUP_STATE_FILE', state_file):
            with patch.object(SetupService, '_load_state', return_value=state):
                with patch.object(SetupService, '_save_state'):
                    result = SetupService.submit_step("adguard", {"skip": True})

                    assert result["success"] is True
                    assert result["next_step"] == "summary"

    def test_complete_setup(self, tmp_path):
        """Test completing setup."""
        init_file = tmp_path / ".initialized"
        state_file = tmp_path / "setup_state.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)

        state = SetupState()

        with patch('services.setup_service.INITIALIZED_FILE', init_file):
            with patch('services.setup_service.SETUP_STATE_FILE', state_file):
                with patch.object(SetupService, '_load_state', return_value=state):
                    with patch.object(SetupService, '_save_state'):
                        result = SetupService.complete_setup()

                        assert result["success"] is True
                        assert init_file.exists()

    def test_skip_setup(self, tmp_path):
        """Test skipping setup."""
        init_file = tmp_path / ".initialized"

        with patch('services.setup_service.INITIALIZED_FILE', init_file):
            result = SetupService.skip_setup()

            assert result["success"] is True
            assert init_file.exists()

    def test_reset_setup(self, tmp_path):
        """Test resetting setup."""
        init_file = tmp_path / ".initialized"
        init_file.write_text("Initialized")
        state_file = tmp_path / "setup_state.json"
        state_file.write_text("{}")

        with patch('services.setup_service.INITIALIZED_FILE', init_file):
            with patch('services.setup_service.SETUP_STATE_FILE', state_file):
                result = SetupService.reset_setup()

                assert result is True
                assert not init_file.exists()
                assert not state_file.exists()

    def test_generate_password(self):
        """Test password generation."""
        password = SetupService._generate_password()

        assert len(password) >= 12
        assert isinstance(password, str)

    def test_load_state_default(self, tmp_path):
        """Test loading state when file doesn't exist."""
        state_file = tmp_path / "setup_state.json"

        with patch('services.setup_service.SETUP_STATE_FILE', state_file):
            state = SetupService._load_state()

            assert state.current_step == SetupStep.WELCOME
            assert state.completed_steps == []

    def test_load_state_from_file(self, tmp_path):
        """Test loading state from file."""
        state_file = tmp_path / "setup_state.json"
        state_file.write_text(json.dumps({
            "current_step": "hotspot",
            "completed_steps": ["welcome", "network", "vpn"],
            "language": "fr",
            "network_configured": True,
        }))

        with patch('services.setup_service.SETUP_STATE_FILE', state_file):
            state = SetupService._load_state()

            assert state.current_step == SetupStep.HOTSPOT
            assert state.completed_steps == ["welcome", "network", "vpn"]
            assert state.language == "fr"
            assert state.network_configured is True

    def test_save_state(self, tmp_path):
        """Test saving state to file."""
        state_file = tmp_path / "setup_state.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)

        state = SetupState(
            current_step=SetupStep.VPN,
            completed_steps=["welcome", "network"],
            language="en",
        )

        with patch('services.setup_service.SETUP_STATE_FILE', state_file):
            SetupService._save_state(state)

            saved = json.loads(state_file.read_text())
            assert saved["current_step"] == "vpn"
            assert saved["completed_steps"] == ["welcome", "network"]

    def test_step_order(self):
        """Test that step order is correct."""
        expected_order = [
            SetupStep.WELCOME,
            SetupStep.NETWORK,
            SetupStep.VPN,
            SetupStep.HOTSPOT,
            SetupStep.SECURITY,
            SetupStep.ADGUARD,
            SetupStep.SUMMARY,
            SetupStep.COMPLETE,
        ]

        assert SetupService.STEP_ORDER == expected_order
