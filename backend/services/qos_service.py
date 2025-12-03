"""
QoS Service
===========

Simple Quality of Service (traffic prioritization) management.

For v1.0, implements a simple "Prioritize VPN Traffic" toggle.
Uses Linux tc (traffic control) and iptables for packet marking.

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from config import Paths, Network
from utils.command_runner import run_command

logger = logging.getLogger("rose-link.qos")

# QoS configuration file
QOS_CONFIG_FILE = Paths.ROSE_LINK_DIR / "data" / "qos.json"

# Default bandwidth limits (Mbps)
DEFAULT_TOTAL_BANDWIDTH = 100  # 100 Mbps
DEFAULT_VPN_BANDWIDTH = 80     # 80% for VPN
DEFAULT_OTHER_BANDWIDTH = 20   # 20% for other traffic


@dataclass
class QoSConfig:
    """QoS configuration settings."""

    enabled: bool = False
    prioritize_vpn: bool = True
    total_bandwidth_mbps: int = DEFAULT_TOTAL_BANDWIDTH
    vpn_bandwidth_percent: int = 80
    interface: str = "eth0"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "enabled": self.enabled,
            "prioritize_vpn": self.prioritize_vpn,
            "total_bandwidth_mbps": self.total_bandwidth_mbps,
            "vpn_bandwidth_percent": self.vpn_bandwidth_percent,
            "interface": self.interface,
        }


@dataclass
class QoSStatus:
    """Current QoS status."""

    enabled: bool = False
    config: QoSConfig = field(default_factory=QoSConfig)
    tc_rules_active: bool = False
    iptables_rules_active: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "enabled": self.enabled,
            "config": self.config.to_dict(),
            "tc_rules_active": self.tc_rules_active,
            "iptables_rules_active": self.iptables_rules_active,
        }


class QoSService:
    """
    Service for QoS traffic prioritization.

    Implements simple VPN traffic prioritization using Linux tc and iptables.
    """

    @classmethod
    def get_status(cls) -> QoSStatus:
        """
        Get current QoS status.

        Returns:
            QoSStatus with configuration and active state
        """
        config = cls._load_config()
        status = QoSStatus(
            enabled=config.enabled,
            config=config,
        )

        # Check if tc rules are active
        status.tc_rules_active = cls._check_tc_rules(config.interface)

        # Check if iptables rules are active
        status.iptables_rules_active = cls._check_iptables_rules()

        return status

    @classmethod
    def enable(cls) -> bool:
        """
        Enable QoS traffic prioritization.

        Returns:
            True if successful
        """
        config = cls._load_config()
        config.enabled = True

        # Detect WAN interface
        config.interface = cls._detect_wan_interface()

        # Apply tc rules
        if not cls._apply_tc_rules(config):
            logger.error("Failed to apply tc rules")
            return False

        # Apply iptables marking rules
        if not cls._apply_iptables_rules():
            logger.error("Failed to apply iptables rules")
            cls._remove_tc_rules(config.interface)
            return False

        # Save configuration
        cls._save_config(config)

        logger.info("QoS enabled")
        return True

    @classmethod
    def disable(cls) -> bool:
        """
        Disable QoS traffic prioritization.

        Returns:
            True if successful
        """
        config = cls._load_config()

        # Remove tc rules
        cls._remove_tc_rules(config.interface)

        # Remove iptables rules
        cls._remove_iptables_rules()

        # Update configuration
        config.enabled = False
        cls._save_config(config)

        logger.info("QoS disabled")
        return True

    @classmethod
    def update_config(
        cls,
        total_bandwidth_mbps: Optional[int] = None,
        vpn_bandwidth_percent: Optional[int] = None,
    ) -> bool:
        """
        Update QoS configuration.

        Args:
            total_bandwidth_mbps: Total bandwidth in Mbps
            vpn_bandwidth_percent: Percentage of bandwidth for VPN

        Returns:
            True if successful
        """
        config = cls._load_config()

        if total_bandwidth_mbps is not None:
            config.total_bandwidth_mbps = max(1, min(1000, total_bandwidth_mbps))

        if vpn_bandwidth_percent is not None:
            config.vpn_bandwidth_percent = max(10, min(90, vpn_bandwidth_percent))

        cls._save_config(config)

        # Re-apply rules if enabled
        if config.enabled:
            cls._remove_tc_rules(config.interface)
            cls._apply_tc_rules(config)

        logger.info(f"QoS config updated: {config.total_bandwidth_mbps}Mbps, {config.vpn_bandwidth_percent}% VPN")
        return True

    @classmethod
    def _detect_wan_interface(cls) -> str:
        """
        Detect the WAN interface.

        Returns:
            WAN interface name (eth0 or similar)
        """
        # Check for default route
        ret, out, _ = run_command("ip route show default", timeout=5)
        if ret == 0 and out:
            # Parse: default via X.X.X.X dev eth0
            parts = out.split()
            if "dev" in parts:
                idx = parts.index("dev")
                if idx + 1 < len(parts):
                    return parts[idx + 1]

        # Fallback to eth0
        return Network.DEFAULT_ETH_INTERFACE

    @classmethod
    def _apply_tc_rules(cls, config: QoSConfig) -> bool:
        """
        Apply tc (traffic control) rules for QoS.

        Sets up HTB (Hierarchical Token Bucket) queueing with:
        - High priority class for VPN traffic (marked packets)
        - Lower priority class for other traffic
        """
        interface = config.interface
        total_rate = f"{config.total_bandwidth_mbps}mbit"
        vpn_rate = f"{int(config.total_bandwidth_mbps * config.vpn_bandwidth_percent / 100)}mbit"
        other_rate = f"{int(config.total_bandwidth_mbps * (100 - config.vpn_bandwidth_percent) / 100)}mbit"

        commands = [
            # Remove existing qdisc (ignore errors)
            f"tc qdisc del dev {interface} root 2>/dev/null || true",

            # Add root HTB qdisc
            f"tc qdisc add dev {interface} root handle 1: htb default 20",

            # Add root class
            f"tc class add dev {interface} parent 1: classid 1:1 htb rate {total_rate}",

            # Add VPN priority class (1:10)
            f"tc class add dev {interface} parent 1:1 classid 1:10 htb rate {vpn_rate} prio 1",

            # Add other traffic class (1:20)
            f"tc class add dev {interface} parent 1:1 classid 1:20 htb rate {other_rate} prio 2",

            # Add filter for marked VPN packets (mark 10)
            f"tc filter add dev {interface} parent 1: prio 1 handle 10 fw flowid 1:10",

            # Add SFQ (Stochastic Fair Queuing) to classes
            f"tc qdisc add dev {interface} parent 1:10 handle 10: sfq perturb 10",
            f"tc qdisc add dev {interface} parent 1:20 handle 20: sfq perturb 10",
        ]

        for cmd in commands:
            ret, _, err = run_command(f"sudo {cmd}", timeout=10)
            if ret != 0 and "del" not in cmd:
                logger.error(f"tc command failed: {cmd} - {err}")
                return False

        logger.debug("tc rules applied")
        return True

    @classmethod
    def _remove_tc_rules(cls, interface: str) -> bool:
        """
        Remove tc QoS rules.

        Args:
            interface: Network interface

        Returns:
            True if successful
        """
        ret, _, _ = run_command(
            f"sudo tc qdisc del dev {interface} root 2>/dev/null || true",
            timeout=10
        )
        logger.debug("tc rules removed")
        return True

    @classmethod
    def _apply_iptables_rules(cls) -> bool:
        """
        Apply iptables rules to mark VPN traffic.

        Marks outgoing packets on VPN interfaces (wg0, tun0) with mark 10.
        """
        commands = [
            # Mark WireGuard traffic
            "iptables -t mangle -A OUTPUT -o wg0 -j MARK --set-mark 10",
            "iptables -t mangle -A FORWARD -o wg0 -j MARK --set-mark 10",

            # Mark OpenVPN traffic
            "iptables -t mangle -A OUTPUT -o tun0 -j MARK --set-mark 10",
            "iptables -t mangle -A FORWARD -o tun0 -j MARK --set-mark 10",
        ]

        for cmd in commands:
            ret, _, err = run_command(f"sudo {cmd}", timeout=10)
            if ret != 0:
                # Ignore errors for interfaces that don't exist
                if "No such device" not in err:
                    logger.warning(f"iptables command failed: {cmd} - {err}")

        logger.debug("iptables marking rules applied")
        return True

    @classmethod
    def _remove_iptables_rules(cls) -> bool:
        """
        Remove iptables marking rules.

        Returns:
            True if successful
        """
        commands = [
            "iptables -t mangle -D OUTPUT -o wg0 -j MARK --set-mark 10",
            "iptables -t mangle -D FORWARD -o wg0 -j MARK --set-mark 10",
            "iptables -t mangle -D OUTPUT -o tun0 -j MARK --set-mark 10",
            "iptables -t mangle -D FORWARD -o tun0 -j MARK --set-mark 10",
        ]

        for cmd in commands:
            run_command(f"sudo {cmd} 2>/dev/null || true", timeout=10)

        logger.debug("iptables marking rules removed")
        return True

    @classmethod
    def _check_tc_rules(cls, interface: str) -> bool:
        """
        Check if tc rules are active.

        Args:
            interface: Network interface

        Returns:
            True if tc rules are configured
        """
        ret, out, _ = run_command(f"tc qdisc show dev {interface}", timeout=5)
        if ret == 0 and "htb" in out:
            return True
        return False

    @classmethod
    def _check_iptables_rules(cls) -> bool:
        """
        Check if iptables marking rules are active.

        Returns:
            True if iptables rules are configured
        """
        ret, out, _ = run_command("sudo iptables -t mangle -L OUTPUT -n", timeout=5)
        if ret == 0 and "MARK" in out and "0xa" in out:
            return True
        return False

    @classmethod
    def _load_config(cls) -> QoSConfig:
        """Load QoS configuration from file."""
        if not QOS_CONFIG_FILE.exists():
            return QoSConfig()

        try:
            with open(QOS_CONFIG_FILE, "r") as f:
                data = json.load(f)
                return QoSConfig(
                    enabled=data.get("enabled", False),
                    prioritize_vpn=data.get("prioritize_vpn", True),
                    total_bandwidth_mbps=data.get("total_bandwidth_mbps", DEFAULT_TOTAL_BANDWIDTH),
                    vpn_bandwidth_percent=data.get("vpn_bandwidth_percent", 80),
                    interface=data.get("interface", "eth0"),
                )
        except Exception as e:
            logger.debug(f"Error loading QoS config: {e}")
            return QoSConfig()

    @classmethod
    def _save_config(cls, config: QoSConfig) -> None:
        """Save QoS configuration to file."""
        try:
            QOS_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(QOS_CONFIG_FILE, "w") as f:
                json.dump(config.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving QoS config: {e}")
