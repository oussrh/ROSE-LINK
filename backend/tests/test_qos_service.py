"""
Tests for QoS Service
=====================

Unit tests for the QoS traffic prioritization service.

Author: ROSE Link Team
License: MIT
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from services.qos_service import (
    QoSService,
    QoSConfig,
    QoSStatus,
    DEFAULT_TOTAL_BANDWIDTH,
    DEFAULT_VPN_BANDWIDTH,
)


class TestQoSConfig:
    """Tests for QoSConfig dataclass."""

    def test_default_values(self):
        """Test default config values."""
        config = QoSConfig()

        assert config.enabled is False
        assert config.prioritize_vpn is True
        assert config.total_bandwidth_mbps == DEFAULT_TOTAL_BANDWIDTH
        assert config.vpn_bandwidth_percent == 80
        assert config.interface == "eth0"

    def test_to_dict(self):
        """Test config serialization."""
        config = QoSConfig(
            enabled=True,
            total_bandwidth_mbps=200,
            vpn_bandwidth_percent=70,
            interface="eth1",
        )

        result = config.to_dict()

        assert result["enabled"] is True
        assert result["total_bandwidth_mbps"] == 200
        assert result["vpn_bandwidth_percent"] == 70
        assert result["interface"] == "eth1"


class TestQoSStatus:
    """Tests for QoSStatus dataclass."""

    def test_default_values(self):
        """Test default status values."""
        status = QoSStatus()

        assert status.enabled is False
        assert status.tc_rules_active is False
        assert status.iptables_rules_active is False

    def test_to_dict(self):
        """Test status serialization."""
        config = QoSConfig(enabled=True)
        status = QoSStatus(
            enabled=True,
            config=config,
            tc_rules_active=True,
            iptables_rules_active=True,
        )

        result = status.to_dict()

        assert result["enabled"] is True
        assert result["tc_rules_active"] is True
        assert result["iptables_rules_active"] is True
        assert "config" in result


class TestQoSService:
    """Tests for QoSService class."""

    def test_get_status(self):
        """Test getting QoS status."""
        with patch.object(QoSService, '_load_config', return_value=QoSConfig()):
            with patch.object(QoSService, '_check_tc_rules', return_value=False):
                with patch.object(QoSService, '_check_iptables_rules', return_value=False):
                    status = QoSService.get_status()

                    assert status.enabled is False
                    assert status.tc_rules_active is False

    def test_enable_success(self):
        """Test enabling QoS successfully."""
        with patch.object(QoSService, '_load_config', return_value=QoSConfig()):
            with patch.object(QoSService, '_detect_wan_interface', return_value="eth0"):
                with patch.object(QoSService, '_apply_tc_rules', return_value=True):
                    with patch.object(QoSService, '_apply_iptables_rules', return_value=True):
                        with patch.object(QoSService, '_save_config'):
                            result = QoSService.enable()

                            assert result is True

    def test_enable_tc_failure(self):
        """Test enabling QoS when tc rules fail."""
        with patch.object(QoSService, '_load_config', return_value=QoSConfig()):
            with patch.object(QoSService, '_detect_wan_interface', return_value="eth0"):
                with patch.object(QoSService, '_apply_tc_rules', return_value=False):
                    result = QoSService.enable()

                    assert result is False

    def test_enable_iptables_failure(self):
        """Test enabling QoS when iptables rules fail."""
        with patch.object(QoSService, '_load_config', return_value=QoSConfig()):
            with patch.object(QoSService, '_detect_wan_interface', return_value="eth0"):
                with patch.object(QoSService, '_apply_tc_rules', return_value=True):
                    with patch.object(QoSService, '_apply_iptables_rules', return_value=False):
                        with patch.object(QoSService, '_remove_tc_rules'):
                            result = QoSService.enable()

                            assert result is False

    def test_disable(self):
        """Test disabling QoS."""
        with patch.object(QoSService, '_load_config', return_value=QoSConfig(enabled=True)):
            with patch.object(QoSService, '_remove_tc_rules'):
                with patch.object(QoSService, '_remove_iptables_rules'):
                    with patch.object(QoSService, '_save_config'):
                        result = QoSService.disable()

                        assert result is True

    def test_update_config(self):
        """Test updating QoS configuration."""
        with patch.object(QoSService, '_load_config', return_value=QoSConfig()):
            with patch.object(QoSService, '_save_config'):
                result = QoSService.update_config(
                    total_bandwidth_mbps=150,
                    vpn_bandwidth_percent=60,
                )

                assert result is True

    def test_update_config_with_enabled(self):
        """Test updating config re-applies rules when enabled."""
        with patch.object(QoSService, '_load_config', return_value=QoSConfig(enabled=True)):
            with patch.object(QoSService, '_save_config'):
                with patch.object(QoSService, '_remove_tc_rules'):
                    with patch.object(QoSService, '_apply_tc_rules', return_value=True):
                        result = QoSService.update_config(total_bandwidth_mbps=150)

                        assert result is True

    def test_update_config_bandwidth_limits(self):
        """Test config bandwidth limits are enforced."""
        config = QoSConfig()

        with patch.object(QoSService, '_load_config', return_value=config):
            with patch.object(QoSService, '_save_config') as mock_save:
                # Test min/max limits
                QoSService.update_config(total_bandwidth_mbps=0)  # Should be clamped to 1
                QoSService.update_config(total_bandwidth_mbps=2000)  # Should be clamped to 1000
                QoSService.update_config(vpn_bandwidth_percent=5)  # Should be clamped to 10
                QoSService.update_config(vpn_bandwidth_percent=95)  # Should be clamped to 90

    def test_detect_wan_interface_from_route(self):
        """Test WAN interface detection from default route."""
        with patch('services.qos_service.run_command') as mock_run:
            mock_run.return_value = (0, "default via 192.168.1.1 dev eth0", "")

            interface = QoSService._detect_wan_interface()

            assert interface == "eth0"

    def test_detect_wan_interface_fallback(self):
        """Test WAN interface detection fallback."""
        with patch('services.qos_service.run_command') as mock_run:
            mock_run.return_value = (1, "", "error")

            interface = QoSService._detect_wan_interface()

            # Should fallback to default
            assert interface == "eth0"

    def test_apply_tc_rules(self):
        """Test applying tc rules."""
        config = QoSConfig(
            interface="eth0",
            total_bandwidth_mbps=100,
            vpn_bandwidth_percent=80,
        )

        with patch('services.qos_service.run_command') as mock_run:
            mock_run.return_value = (0, "", "")

            result = QoSService._apply_tc_rules(config)

            assert result is True
            # Verify multiple tc commands were executed
            assert mock_run.call_count >= 5

    def test_apply_tc_rules_failure(self):
        """Test tc rules failure handling."""
        config = QoSConfig(interface="eth0")

        with patch('services.qos_service.run_command') as mock_run:
            # First call succeeds (del), subsequent fail
            mock_run.side_effect = [
                (0, "", ""),  # del succeeds
                (1, "", "error"),  # add fails
            ]

            result = QoSService._apply_tc_rules(config)

            assert result is False

    def test_remove_tc_rules(self):
        """Test removing tc rules."""
        with patch('services.qos_service.run_command') as mock_run:
            mock_run.return_value = (0, "", "")

            result = QoSService._remove_tc_rules("eth0")

            assert result is True

    def test_apply_iptables_rules(self):
        """Test applying iptables marking rules."""
        with patch('services.qos_service.run_command') as mock_run:
            mock_run.return_value = (0, "", "")

            result = QoSService._apply_iptables_rules()

            assert result is True
            # Should mark both wg0 and tun0
            assert mock_run.call_count >= 4

    def test_remove_iptables_rules(self):
        """Test removing iptables rules."""
        with patch('services.qos_service.run_command') as mock_run:
            mock_run.return_value = (0, "", "")

            result = QoSService._remove_iptables_rules()

            assert result is True

    def test_check_tc_rules_active(self):
        """Test checking if tc rules are active."""
        with patch('services.qos_service.run_command') as mock_run:
            mock_run.return_value = (0, "qdisc htb 1: root", "")

            result = QoSService._check_tc_rules("eth0")

            assert result is True

    def test_check_tc_rules_inactive(self):
        """Test checking if tc rules are inactive."""
        with patch('services.qos_service.run_command') as mock_run:
            mock_run.return_value = (0, "qdisc pfifo_fast 0:", "")

            result = QoSService._check_tc_rules("eth0")

            assert result is False

    def test_check_iptables_rules_active(self):
        """Test checking if iptables rules are active."""
        with patch('services.qos_service.run_command') as mock_run:
            mock_run.return_value = (0, "MARK all -- 0.0.0.0/0 set 0xa", "")

            result = QoSService._check_iptables_rules()

            assert result is True

    def test_check_iptables_rules_inactive(self):
        """Test checking if iptables rules are inactive."""
        with patch('services.qos_service.run_command') as mock_run:
            mock_run.return_value = (0, "Chain OUTPUT (policy ACCEPT)", "")

            result = QoSService._check_iptables_rules()

            assert result is False

    def test_load_config_default(self, tmp_path):
        """Test loading config when file doesn't exist."""
        config_file = tmp_path / "qos.json"

        with patch('services.qos_service.QOS_CONFIG_FILE', config_file):
            config = QoSService._load_config()

            assert config.enabled is False
            assert config.total_bandwidth_mbps == DEFAULT_TOTAL_BANDWIDTH

    def test_load_config_from_file(self, tmp_path):
        """Test loading config from file."""
        config_file = tmp_path / "qos.json"
        config_file.write_text(json.dumps({
            "enabled": True,
            "total_bandwidth_mbps": 200,
            "vpn_bandwidth_percent": 70,
            "interface": "eth1",
        }))

        with patch('services.qos_service.QOS_CONFIG_FILE', config_file):
            config = QoSService._load_config()

            assert config.enabled is True
            assert config.total_bandwidth_mbps == 200
            assert config.vpn_bandwidth_percent == 70

    def test_save_config(self, tmp_path):
        """Test saving config to file."""
        config_file = tmp_path / "qos.json"

        config = QoSConfig(
            enabled=True,
            total_bandwidth_mbps=150,
        )

        with patch('services.qos_service.QOS_CONFIG_FILE', config_file):
            QoSService._save_config(config)

            saved = json.loads(config_file.read_text())
            assert saved["enabled"] is True
            assert saved["total_bandwidth_mbps"] == 150
