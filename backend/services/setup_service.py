"""
Setup Wizard Service
====================

Manages the first-time setup wizard for ROSE Link.

Features:
- First-run detection
- Step-by-step configuration
- Network, VPN, Hotspot, and Security setup
- Configuration validation at each step

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import json
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from config import Paths
from services.hotspot_service import HotspotService
from services.wan_service import WANService
from services.auth_service import AuthService
from services.adguard_service import AdGuardService
from utils.command_runner import run_command

logger = logging.getLogger("rose-link.setup")

# Setup state file
INITIALIZED_FILE = Paths.ROSE_LINK_DIR / ".initialized"
SETUP_STATE_FILE = Paths.ROSE_LINK_DIR / "data" / "setup_state.json"


class SetupStep(str, Enum):
    """Setup wizard steps."""
    WELCOME = "welcome"
    NETWORK = "network"
    VPN = "vpn"
    HOTSPOT = "hotspot"
    SECURITY = "security"
    ADGUARD = "adguard"
    SUMMARY = "summary"
    COMPLETE = "complete"


@dataclass
class SetupState:
    """Current setup wizard state."""

    current_step: SetupStep = SetupStep.WELCOME
    completed_steps: list[str] = field(default_factory=list)
    language: str = "en"

    # Network configuration
    network_type: Optional[str] = None  # "ethernet" or "wifi"
    wifi_ssid: Optional[str] = None
    network_configured: bool = False

    # VPN configuration
    vpn_configured: bool = False
    vpn_skipped: bool = False
    vpn_type: Optional[str] = None
    vpn_profile: Optional[str] = None

    # Hotspot configuration
    hotspot_ssid: str = "ROSE-Link"
    hotspot_password: Optional[str] = None
    hotspot_country: str = "US"
    hotspot_channel: int = 6
    hotspot_configured: bool = False

    # Security configuration
    admin_password_set: bool = False

    # AdGuard configuration
    adguard_enabled: bool = False
    adguard_skipped: bool = False

    # Timestamps
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "current_step": self.current_step.value,
            "completed_steps": self.completed_steps,
            "language": self.language,
            "network_type": self.network_type,
            "wifi_ssid": self.wifi_ssid,
            "network_configured": self.network_configured,
            "vpn_configured": self.vpn_configured,
            "vpn_skipped": self.vpn_skipped,
            "vpn_type": self.vpn_type,
            "vpn_profile": self.vpn_profile,
            "hotspot_ssid": self.hotspot_ssid,
            "hotspot_country": self.hotspot_country,
            "hotspot_channel": self.hotspot_channel,
            "hotspot_configured": self.hotspot_configured,
            "admin_password_set": self.admin_password_set,
            "adguard_enabled": self.adguard_enabled,
            "adguard_skipped": self.adguard_skipped,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


class SetupService:
    """
    Service for managing the first-time setup wizard.

    Guides users through initial ROSE Link configuration.
    """

    STEP_ORDER = [
        SetupStep.WELCOME,
        SetupStep.NETWORK,
        SetupStep.VPN,
        SetupStep.HOTSPOT,
        SetupStep.SECURITY,
        SetupStep.ADGUARD,
        SetupStep.SUMMARY,
        SetupStep.COMPLETE,
    ]

    @classmethod
    def is_first_run(cls) -> bool:
        """
        Check if this is the first run (setup not completed).

        Returns:
            True if setup has not been completed
        """
        return not INITIALIZED_FILE.exists()

    @classmethod
    def get_status(cls) -> dict[str, Any]:
        """
        Get setup wizard status.

        Returns:
            Dict with setup status information
        """
        is_first_run = cls.is_first_run()
        state = cls._load_state()

        return {
            "required": is_first_run,
            "in_progress": is_first_run and state.started_at is not None,
            "completed": not is_first_run,
            "current_step": state.current_step.value,
            "completed_steps": state.completed_steps,
            "total_steps": len(cls.STEP_ORDER) - 1,  # Exclude COMPLETE
        }

    @classmethod
    def get_state(cls) -> SetupState:
        """
        Get current setup state.

        Returns:
            SetupState with all configuration
        """
        return cls._load_state()

    @classmethod
    def start_setup(cls, language: str = "en") -> SetupState:
        """
        Start the setup wizard.

        Args:
            language: UI language (en, fr)

        Returns:
            Initial setup state
        """
        state = SetupState(
            current_step=SetupStep.WELCOME,
            language=language,
            started_at=datetime.now().isoformat(),
        )
        cls._save_state(state)

        logger.info(f"Setup wizard started, language: {language}")
        return state

    @classmethod
    def get_step_data(cls, step: str) -> dict[str, Any]:
        """
        Get data needed for a specific step.

        Args:
            step: Step name

        Returns:
            Step-specific data
        """
        state = cls._load_state()

        if step == SetupStep.WELCOME.value:
            return {
                "step": step,
                "language": state.language,
                "app_version": "1.0.0",
            }

        elif step == SetupStep.NETWORK.value:
            # Get current network status
            wan_status = WANService.get_status()
            return {
                "step": step,
                "ethernet_connected": wan_status.ethernet.connected,
                "ethernet_ip": wan_status.ethernet.ip,
                "wifi_connected": wan_status.wifi.connected,
                "wifi_ssid": wan_status.wifi.ssid,
                "current_config": {
                    "type": state.network_type,
                    "wifi_ssid": state.wifi_ssid,
                },
            }

        elif step == SetupStep.VPN.value:
            return {
                "step": step,
                "configured": state.vpn_configured,
                "skipped": state.vpn_skipped,
                "vpn_type": state.vpn_type,
                "profile": state.vpn_profile,
                "supported_types": ["wireguard", "openvpn"],
            }

        elif step == SetupStep.HOTSPOT.value:
            # Get current hotspot status
            hotspot_status = HotspotService.get_status()
            return {
                "step": step,
                "current_ssid": hotspot_status.ssid or state.hotspot_ssid,
                "current_channel": hotspot_status.channel or state.hotspot_channel,
                "suggested_ssid": state.hotspot_ssid,
                "suggested_password": cls._generate_password(),
                "country": state.hotspot_country,
            }

        elif step == SetupStep.SECURITY.value:
            return {
                "step": step,
                "password_set": state.admin_password_set,
            }

        elif step == SetupStep.ADGUARD.value:
            return {
                "step": step,
                "installed": AdGuardService.is_installed(),
                "enabled": state.adguard_enabled,
                "skipped": state.adguard_skipped,
            }

        elif step == SetupStep.SUMMARY.value:
            return {
                "step": step,
                "state": state.to_dict(),
            }

        return {"step": step}

    @classmethod
    def submit_step(cls, step: str, data: dict[str, Any]) -> dict[str, Any]:
        """
        Submit data for a setup step.

        Args:
            step: Step name
            data: Step data

        Returns:
            Result with next step information
        """
        state = cls._load_state()

        try:
            if step == SetupStep.WELCOME.value:
                state.language = data.get("language", "en")
                state.current_step = SetupStep.NETWORK
                state.completed_steps.append(step)

            elif step == SetupStep.NETWORK.value:
                result = cls._configure_network(state, data)
                if not result["success"]:
                    return result
                state.current_step = SetupStep.VPN
                state.completed_steps.append(step)

            elif step == SetupStep.VPN.value:
                result = cls._configure_vpn(state, data)
                if not result["success"]:
                    return result
                state.current_step = SetupStep.HOTSPOT
                state.completed_steps.append(step)

            elif step == SetupStep.HOTSPOT.value:
                result = cls._configure_hotspot(state, data)
                if not result["success"]:
                    return result
                state.current_step = SetupStep.SECURITY
                state.completed_steps.append(step)

            elif step == SetupStep.SECURITY.value:
                result = cls._configure_security(state, data)
                if not result["success"]:
                    return result
                state.current_step = SetupStep.ADGUARD
                state.completed_steps.append(step)

            elif step == SetupStep.ADGUARD.value:
                result = cls._configure_adguard(state, data)
                if not result["success"]:
                    return result
                state.current_step = SetupStep.SUMMARY
                state.completed_steps.append(step)

            elif step == SetupStep.SUMMARY.value:
                state.current_step = SetupStep.COMPLETE
                state.completed_steps.append(step)

            cls._save_state(state)

            return {
                "success": True,
                "next_step": state.current_step.value,
                "state": state.to_dict(),
            }

        except Exception as e:
            logger.error(f"Error in setup step {step}: {e}")
            return {
                "success": False,
                "error": str(e),
                "current_step": step,
            }

    @classmethod
    def complete_setup(cls) -> dict[str, Any]:
        """
        Finalize the setup wizard.

        Creates the initialized file and marks setup as complete.

        Returns:
            Completion result
        """
        state = cls._load_state()
        state.completed_at = datetime.now().isoformat()
        state.current_step = SetupStep.COMPLETE

        # Create initialized file
        INITIALIZED_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(INITIALIZED_FILE, "w") as f:
            f.write(f"Initialized: {state.completed_at}\n")

        cls._save_state(state)

        logger.info("Setup wizard completed")

        return {
            "success": True,
            "message": "Setup completed successfully",
            "state": state.to_dict(),
        }

    @classmethod
    def skip_setup(cls) -> dict[str, Any]:
        """
        Skip the setup wizard (for advanced users).

        Returns:
            Skip result
        """
        # Create initialized file
        INITIALIZED_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(INITIALIZED_FILE, "w") as f:
            f.write(f"Skipped: {datetime.now().isoformat()}\n")

        logger.info("Setup wizard skipped")

        return {
            "success": True,
            "message": "Setup skipped",
        }

    @classmethod
    def reset_setup(cls) -> bool:
        """
        Reset setup wizard (for testing/re-configuration).

        Returns:
            True if successful
        """
        if INITIALIZED_FILE.exists():
            INITIALIZED_FILE.unlink()

        if SETUP_STATE_FILE.exists():
            SETUP_STATE_FILE.unlink()

        logger.info("Setup wizard reset")
        return True

    @classmethod
    def _configure_network(cls, state: SetupState, data: dict) -> dict:
        """Configure network in setup."""
        network_type = data.get("type", "ethernet")
        state.network_type = network_type

        if network_type == "wifi":
            ssid = data.get("ssid")
            password = data.get("password")

            if not ssid or not password:
                return {"success": False, "error": "WiFi SSID and password required"}

            state.wifi_ssid = ssid
            # Actual WiFi connection would happen here
            # For now, just mark as configured

        state.network_configured = True
        return {"success": True}

    @classmethod
    def _configure_vpn(cls, state: SetupState, data: dict) -> dict:
        """Configure VPN in setup."""
        if data.get("skip"):
            state.vpn_skipped = True
            state.vpn_configured = False
            return {"success": True}

        vpn_type = data.get("vpn_type")
        profile_name = data.get("profile_name")

        if vpn_type and profile_name:
            state.vpn_type = vpn_type
            state.vpn_profile = profile_name
            state.vpn_configured = True

        return {"success": True}

    @classmethod
    def _configure_hotspot(cls, state: SetupState, data: dict) -> dict:
        """Configure hotspot in setup."""
        ssid = data.get("ssid", "ROSE-Link")
        password = data.get("password")
        country = data.get("country", "US")
        channel = data.get("channel", 6)

        if not password or len(password) < 8:
            return {"success": False, "error": "Password must be at least 8 characters"}

        state.hotspot_ssid = ssid
        state.hotspot_password = password
        state.hotspot_country = country
        state.hotspot_channel = channel

        # Apply hotspot configuration
        try:
            from models import HotspotConfig
            config = HotspotConfig(
                ssid=ssid,
                password=password,
                country=country,
                channel=channel,
            )
            HotspotService.apply_config(config)
            state.hotspot_configured = True
        except Exception as e:
            logger.error(f"Failed to configure hotspot: {e}")
            return {"success": False, "error": f"Hotspot configuration failed: {e}"}

        return {"success": True}

    @classmethod
    def _configure_security(cls, state: SetupState, data: dict) -> dict:
        """Configure security (admin password) in setup."""
        password = data.get("password")

        if not password or len(password) < 8:
            return {"success": False, "error": "Password must be at least 8 characters"}

        # Set the API key (admin password)
        try:
            AuthService.set_api_key(password)
            state.admin_password_set = True
        except Exception as e:
            logger.error(f"Failed to set admin password: {e}")
            return {"success": False, "error": f"Failed to set password: {e}"}

        return {"success": True}

    @classmethod
    def _configure_adguard(cls, state: SetupState, data: dict) -> dict:
        """Configure AdGuard Home in setup."""
        if data.get("skip"):
            state.adguard_skipped = True
            state.adguard_enabled = False
            return {"success": True}

        if data.get("enable"):
            if AdGuardService.is_installed():
                state.adguard_enabled = True
            else:
                state.adguard_skipped = True
                logger.warning("AdGuard Home not installed, skipping")

        return {"success": True}

    @classmethod
    def _generate_password(cls) -> str:
        """Generate a secure random password."""
        return secrets.token_urlsafe(12)

    @classmethod
    def _load_state(cls) -> SetupState:
        """Load setup state from file."""
        if not SETUP_STATE_FILE.exists():
            return SetupState()

        try:
            with open(SETUP_STATE_FILE, "r") as f:
                data = json.load(f)
                return SetupState(
                    current_step=SetupStep(data.get("current_step", "welcome")),
                    completed_steps=data.get("completed_steps", []),
                    language=data.get("language", "en"),
                    network_type=data.get("network_type"),
                    wifi_ssid=data.get("wifi_ssid"),
                    network_configured=data.get("network_configured", False),
                    vpn_configured=data.get("vpn_configured", False),
                    vpn_skipped=data.get("vpn_skipped", False),
                    vpn_type=data.get("vpn_type"),
                    vpn_profile=data.get("vpn_profile"),
                    hotspot_ssid=data.get("hotspot_ssid", "ROSE-Link"),
                    hotspot_password=data.get("hotspot_password"),
                    hotspot_country=data.get("hotspot_country", "US"),
                    hotspot_channel=data.get("hotspot_channel", 6),
                    hotspot_configured=data.get("hotspot_configured", False),
                    admin_password_set=data.get("admin_password_set", False),
                    adguard_enabled=data.get("adguard_enabled", False),
                    adguard_skipped=data.get("adguard_skipped", False),
                    started_at=data.get("started_at"),
                    completed_at=data.get("completed_at"),
                )
        except Exception as e:
            logger.debug(f"Error loading setup state: {e}")
            return SetupState()

    @classmethod
    def _save_state(cls, state: SetupState) -> None:
        """Save setup state to file."""
        try:
            SETUP_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(SETUP_STATE_FILE, "w") as f:
                json.dump(state.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving setup state: {e}")
