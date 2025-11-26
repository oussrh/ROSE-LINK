#!/usr/bin/env python3
"""
ROSE Link - Backend API
=======================

A modern FastAPI-based REST API for managing a VPN router on Raspberry Pi.
Supports Raspberry Pi 3, 4, 5, and Zero 2W.

Features:
- WiFi WAN management (scan, connect, disconnect)
- WireGuard VPN management (profiles, start/stop/restart)
- WiFi Hotspot configuration (SSID, password, channel, WPA3)
- System monitoring (CPU, RAM, disk, temperature)
- VPN watchdog settings

Author: ROSE Link Team
License: MIT
Version: 0.2.0
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

# =============================================================================
# Application Configuration
# =============================================================================

app = FastAPI(
    title="ROSE Link API",
    description="REST API for ROSE Link VPN Router",
    version="0.2.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS middleware for development and external access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# Path Constants
# =============================================================================

WG_PROFILES_DIR = Path("/etc/wireguard/profiles")
WG_ACTIVE_CONF = Path("/etc/wireguard/wg0.conf")
HOSTAPD_CONF = Path("/etc/hostapd/hostapd.conf")
INTERFACES_CONF = Path("/opt/rose-link/system/interfaces.conf")
VPN_SETTINGS_FILE = Path("/opt/rose-link/system/vpn-settings.conf")

# Ensure required directories exist
WG_PROFILES_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# Pydantic Models
# =============================================================================

class WifiConnectRequest(BaseModel):
    """Request model for WiFi connection."""

    ssid: str = Field(..., min_length=1, max_length=32, description="WiFi network SSID")
    password: str = Field(..., min_length=8, max_length=63, description="WiFi password")


class HotspotConfig(BaseModel):
    """Configuration model for WiFi hotspot settings."""

    ssid: str = Field(default="ROSE-Link", min_length=1, max_length=32, description="Hotspot SSID")
    password: str = Field(..., min_length=8, max_length=63, description="Hotspot password")
    country: str = Field(default="BE", min_length=2, max_length=2, description="Country code for WiFi regulation")
    channel: int = Field(default=6, ge=1, le=165, description="WiFi channel")
    wpa3: bool = Field(default=False, description="Enable WPA3 security")
    band: str = Field(default="2.4GHz", description="WiFi band (2.4GHz or 5GHz)")

    @field_validator("band")
    @classmethod
    def validate_band(cls, v: str) -> str:
        """Validate WiFi band selection."""
        if v not in ("2.4GHz", "5GHz"):
            raise ValueError("Band must be '2.4GHz' or '5GHz'")
        return v


class VPNProfile(BaseModel):
    """Model for VPN profile activation."""

    name: str = Field(..., min_length=1, description="VPN profile name")
    active: bool = Field(default=False, description="Whether profile is active")


class VPNSettings(BaseModel):
    """Configuration model for VPN watchdog settings."""

    ping_host: str = Field(default="8.8.8.8", min_length=4, description="Host to ping for VPN health check")
    check_interval: int = Field(default=60, ge=30, le=300, description="Check interval in seconds")


# =============================================================================
# Helper Functions
# =============================================================================

def run_command(cmd: list[str], check: bool = True, timeout: int = 30) -> tuple[int, str, str]:
    """
    Execute a shell command and return the result.

    Args:
        cmd: Command and arguments as a list
        check: Whether to raise exception on non-zero return code
        timeout: Command timeout in seconds

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=check,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout or "", e.stderr or ""
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


def get_interface_config() -> dict[str, str]:
    """
    Get configured network interface names from interfaces.conf.

    Falls back to auto-detection if config file doesn't exist.

    Returns:
        Dictionary with 'eth', 'wifi_wan', and 'wifi_ap' interface names
    """
    config = {
        "eth": "eth0",
        "wifi_wan": "wlan0",
        "wifi_ap": "wlan1"
    }

    # Try to load from config file first
    if INTERFACES_CONF.exists():
        try:
            with open(INTERFACES_CONF, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("#") or "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    key = key.strip().upper()
                    value = value.strip().strip('"')

                    if key == "ETH_INTERFACE" and value:
                        config["eth"] = value
                    elif key == "WIFI_WAN_INTERFACE" and value:
                        config["wifi_wan"] = value
                    elif key == "WIFI_AP_INTERFACE" and value:
                        config["wifi_ap"] = value
        except (IOError, OSError, ValueError):
            pass
    else:
        # Auto-detect interfaces if config is missing
        config = _detect_interfaces()

    return config


def _detect_interfaces() -> dict[str, str]:
    """
    Auto-detect network interfaces when config file is missing.

    Returns:
        Dictionary with detected interface names
    """
    config = {
        "eth": "eth0",
        "wifi_wan": "wlan0",
        "wifi_ap": "wlan0"
    }

    # Detect Ethernet interface (Pi 5 uses end0)
    for iface in ["eth0", "end0", "enp1s0"]:
        if os.path.exists(f"/sys/class/net/{iface}"):
            config["eth"] = iface
            break

    # Detect WiFi interfaces
    wifi_ifaces = []
    try:
        for iface in os.listdir("/sys/class/net/"):
            if os.path.exists(f"/sys/class/net/{iface}/wireless"):
                wifi_ifaces.append(iface)
    except OSError:
        pass

    if wifi_ifaces:
        wifi_ifaces.sort()  # Ensure consistent ordering
        config["wifi_ap"] = wifi_ifaces[0]
        config["wifi_wan"] = wifi_ifaces[0]
        if len(wifi_ifaces) > 1:
            config["wifi_wan"] = wifi_ifaces[1]

    return config


def parse_config_file(filepath: Path, keys_map: dict[str, str]) -> dict[str, Any]:
    """
    Generic parser for key=value configuration files.

    Args:
        filepath: Path to the configuration file
        keys_map: Mapping of config keys (uppercase) to result dict keys

    Returns:
        Dictionary with parsed values
    """
    result = {}

    if not filepath.exists():
        return result

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip().upper()
                value = value.strip().strip('"')

                if key in keys_map:
                    result[keys_map[key]] = value
    except (IOError, OSError, ValueError):
        pass

    return result


# =============================================================================
# Status Functions
# =============================================================================

def get_wan_status() -> dict[str, Any]:
    """
    Get WAN connection status for both Ethernet and WiFi.

    Returns:
        Dictionary with ethernet and wifi connection status
    """
    iface_config = get_interface_config()

    status = {
        "ethernet": {
            "connected": False,
            "ip": None,
            "interface": iface_config["eth"]
        },
        "wifi": {
            "connected": False,
            "ssid": None,
            "ip": None,
            "interface": iface_config["wifi_wan"]
        }
    }

    # Check Ethernet connection
    eth_iface = iface_config["eth"]
    if eth_iface:
        ret, out, _ = run_command(["ip", "addr", "show", eth_iface], check=False)
        if ret == 0 and "inet " in out:
            status["ethernet"]["connected"] = True
            match = re.search(r"inet\s+(\S+)", out)
            if match:
                status["ethernet"]["ip"] = match.group(1)

    # Check WiFi WAN connection using NetworkManager
    wifi_wan_iface = iface_config["wifi_wan"]
    if wifi_wan_iface:
        ret, out, _ = run_command(
            ["nmcli", "-t", "-f", "DEVICE,STATE,CONNECTION", "device"],
            check=False
        )
        if ret == 0:
            for line in out.splitlines():
                parts = line.split(":")
                if len(parts) >= 3 and parts[0] == wifi_wan_iface and parts[1] == "connected":
                    status["wifi"]["connected"] = True
                    status["wifi"]["ssid"] = parts[2]

                    # Get IP address
                    ret2, out2, _ = run_command(
                        ["ip", "addr", "show", wifi_wan_iface],
                        check=False
                    )
                    if ret2 == 0:
                        match = re.search(r"inet\s+(\S+)", out2)
                        if match:
                            status["wifi"]["ip"] = match.group(1)

    return status


def get_vpn_status() -> dict[str, Any]:
    """
    Get WireGuard VPN connection status.

    Returns:
        Dictionary with VPN status including endpoint, handshake, and transfer stats
    """
    status = {
        "active": False,
        "interface": "wg0",
        "endpoint": None,
        "latest_handshake": None,
        "transfer": {"received": "0 B", "sent": "0 B"}
    }

    ret, out, _ = run_command(["sudo", "wg", "show", "wg0"], check=False)
    if ret == 0 and out:
        status["active"] = True

        # Parse wg show output
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("endpoint:"):
                status["endpoint"] = line.split(":", 1)[1].strip()
            elif line.startswith("latest handshake:"):
                status["latest_handshake"] = line.split(":", 1)[1].strip()
            elif line.startswith("transfer:"):
                transfer = line.split(":", 1)[1].strip()
                parts = transfer.split(",")
                if len(parts) == 2:
                    try:
                        recv_parts = parts[0].strip().split()
                        sent_parts = parts[1].strip().split()
                        if len(recv_parts) >= 2 and len(sent_parts) >= 2:
                            status["transfer"]["received"] = f"{recv_parts[0]} {recv_parts[1]}"
                            status["transfer"]["sent"] = f"{sent_parts[0]} {sent_parts[1]}"
                    except (IndexError, ValueError):
                        pass

    return status


def get_ap_status() -> dict[str, Any]:
    """
    Get WiFi Access Point (Hotspot) status.

    Returns:
        Dictionary with hotspot status including SSID, channel, and client count
    """
    iface_config = get_interface_config()
    ap_iface = iface_config["wifi_ap"]

    status = {
        "active": False,
        "ssid": None,
        "channel": None,
        "clients": 0,
        "interface": ap_iface,
        "hw_mode": None,
        "frequency": None
    }

    # Check if hostapd is running
    ret, out, _ = run_command(["systemctl", "is-active", "hostapd"], check=False)
    if ret == 0 and out.strip() == "active":
        status["active"] = True

        # Read configuration from hostapd.conf
        if HOSTAPD_CONF.exists():
            try:
                with open(HOSTAPD_CONF, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("ssid="):
                            status["ssid"] = line.split("=", 1)[1].strip()
                        elif line.startswith("channel="):
                            status["channel"] = int(line.split("=", 1)[1].strip())
                        elif line.startswith("hw_mode="):
                            hw_mode = line.split("=", 1)[1].strip()
                            status["hw_mode"] = hw_mode
                            status["frequency"] = "5GHz" if hw_mode == "a" else "2.4GHz"
            except (IOError, OSError, ValueError):
                pass

        # Count connected clients
        ret2, out2, _ = run_command(["iw", "dev", ap_iface, "station", "dump"], check=False)
        if ret2 == 0:
            status["clients"] = out2.count("Station ")

    return status


# =============================================================================
# API Endpoints - Health & Status
# =============================================================================

@app.get("/api/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """
    Health check endpoint for monitoring.

    Returns:
        Status information for the ROSE Link service
    """
    return {"status": "ok", "service": "ROSE Link", "version": "0.2.0"}


@app.get("/api/status", tags=["Status"])
async def get_status() -> dict[str, Any]:
    """
    Get overall system status including WAN, VPN, and hotspot.

    Returns:
        Combined status of all major components
    """
    return {
        "wan": get_wan_status(),
        "vpn": get_vpn_status(),
        "ap": get_ap_status()
    }


# =============================================================================
# API Endpoints - WiFi WAN
# =============================================================================

@app.post("/api/wifi/scan", tags=["WiFi"])
async def wifi_scan() -> dict[str, list]:
    """
    Scan for available WiFi networks.

    Returns:
        List of networks with SSID, signal strength, and security type
    """
    ret, out, err = run_command(
        ["sudo", "nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "device", "wifi", "list"],
        check=False
    )

    if ret != 0:
        raise HTTPException(status_code=500, detail=f"Scan failed: {err}")

    networks = []
    seen_ssids: set[str] = set()

    for line in out.splitlines():
        parts = line.split(":")
        if len(parts) >= 3:
            ssid = parts[0].strip()
            if ssid and ssid not in seen_ssids:
                seen_ssids.add(ssid)
                networks.append({
                    "ssid": ssid,
                    "signal": int(parts[1]) if parts[1].isdigit() else 0,
                    "security": parts[2] if len(parts) > 2 else "Open"
                })

    # Sort by signal strength (strongest first)
    networks.sort(key=lambda x: x["signal"], reverse=True)

    return {"networks": networks}


@app.post("/api/wifi/connect", tags=["WiFi"])
async def wifi_connect(request: WifiConnectRequest) -> dict[str, str]:
    """
    Connect to a WiFi network as WAN.

    Args:
        request: WiFi connection credentials

    Returns:
        Connection status
    """
    ret, out, err = run_command([
        "sudo", "nmcli", "device", "wifi", "connect",
        request.ssid, "password", request.password
    ], check=False)

    if ret != 0:
        raise HTTPException(status_code=500, detail=f"Connection failed: {err}")

    return {"status": "connected", "ssid": request.ssid}


@app.post("/api/wifi/disconnect", tags=["WiFi"])
async def wifi_disconnect() -> dict[str, str]:
    """
    Disconnect from WiFi WAN.

    Uses the configured WiFi WAN interface from interfaces.conf.

    Returns:
        Disconnection status
    """
    # Use dynamic interface instead of hardcoded wlan0
    iface_config = get_interface_config()
    wifi_wan_iface = iface_config["wifi_wan"]

    ret, out, err = run_command(
        ["sudo", "nmcli", "device", "disconnect", wifi_wan_iface],
        check=False
    )

    if ret != 0:
        raise HTTPException(status_code=500, detail=f"Disconnect failed: {err}")

    return {"status": "disconnected"}


# =============================================================================
# API Endpoints - VPN
# =============================================================================

@app.get("/api/vpn/status", tags=["VPN"])
async def vpn_status() -> dict[str, Any]:
    """
    Get current VPN connection status.

    Returns:
        VPN status including connection state, endpoint, and transfer stats
    """
    return get_vpn_status()


@app.get("/api/vpn/profiles", tags=["VPN"])
async def vpn_list_profiles() -> dict[str, list]:
    """
    List all available VPN profiles.

    Returns:
        List of VPN profiles with their activation status
    """
    profiles = []

    if WG_PROFILES_DIR.exists():
        for conf_file in WG_PROFILES_DIR.glob("*.conf"):
            # Check if this profile is currently active
            is_active = False
            if WG_ACTIVE_CONF.exists():
                try:
                    is_active = WG_ACTIVE_CONF.resolve() == conf_file.resolve()
                except OSError:
                    pass

            profiles.append({
                "name": conf_file.stem,
                "active": is_active
            })

    return {"profiles": profiles}


@app.post("/api/vpn/upload", tags=["VPN"])
async def vpn_upload_profile(file: UploadFile = File(...)) -> dict[str, str]:
    """
    Upload a new VPN profile without activating it.

    Args:
        file: WireGuard .conf file

    Returns:
        Upload status
    """
    if not file.filename or not file.filename.endswith(".conf"):
        raise HTTPException(status_code=400, detail="File must be a .conf file")

    profile_path = WG_PROFILES_DIR / file.filename

    try:
        content = await file.read()
        with open(profile_path, "wb") as f:
            f.write(content)

        # Set secure permissions (readable only by root/owner)
        os.chmod(profile_path, 0o600)

        return {"status": "uploaded", "name": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/api/vpn/import", tags=["VPN"])
async def vpn_import_profile(file: UploadFile = File(...)) -> dict[str, str]:
    """
    Import and immediately activate a VPN profile.

    Args:
        file: WireGuard .conf file

    Returns:
        Import and activation status
    """
    if not file.filename or not file.filename.endswith(".conf"):
        raise HTTPException(status_code=400, detail="File must be a .conf file")

    try:
        # Save to profiles directory
        profile_path = WG_PROFILES_DIR / file.filename
        content = await file.read()

        with open(profile_path, "wb") as f:
            f.write(content)
        os.chmod(profile_path, 0o600)

        # Stop existing VPN if running
        run_command(["sudo", "systemctl", "stop", "wg-quick@wg0"], check=False)

        # Update symlink to new profile
        if WG_ACTIVE_CONF.exists() or WG_ACTIVE_CONF.is_symlink():
            WG_ACTIVE_CONF.unlink()
        WG_ACTIVE_CONF.symlink_to(profile_path)

        # Start WireGuard with new profile
        run_command(["sudo", "systemctl", "start", "wg-quick@wg0"], check=False)

        return {"status": "imported", "name": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@app.post("/api/vpn/activate", tags=["VPN"])
async def vpn_activate_profile(profile: VPNProfile) -> dict[str, str]:
    """
    Activate an existing VPN profile.

    Args:
        profile: Profile name to activate

    Returns:
        Activation status
    """
    profile_path = WG_PROFILES_DIR / f"{profile.name}.conf"

    if not profile_path.exists():
        raise HTTPException(status_code=404, detail="Profile not found")

    try:
        # Stop current VPN
        run_command(["sudo", "systemctl", "stop", "wg-quick@wg0"], check=False)

        # Update symlink
        if WG_ACTIVE_CONF.exists() or WG_ACTIVE_CONF.is_symlink():
            WG_ACTIVE_CONF.unlink()
        WG_ACTIVE_CONF.symlink_to(profile_path)

        # Start VPN with new profile
        run_command(["sudo", "systemctl", "start", "wg-quick@wg0"], check=False)

        return {"status": "activated", "name": profile.name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Activation failed: {str(e)}")


@app.post("/api/vpn/restart", tags=["VPN"])
async def vpn_restart() -> dict[str, str]:
    """Restart the VPN connection."""
    ret, out, err = run_command(
        ["sudo", "systemctl", "restart", "wg-quick@wg0"],
        check=False
    )

    if ret != 0:
        raise HTTPException(status_code=500, detail=f"Restart failed: {err}")

    return {"status": "restarted"}


@app.post("/api/vpn/stop", tags=["VPN"])
async def vpn_stop() -> dict[str, str]:
    """Stop the VPN connection."""
    ret, out, err = run_command(
        ["sudo", "systemctl", "stop", "wg-quick@wg0"],
        check=False
    )

    if ret != 0:
        raise HTTPException(status_code=500, detail=f"Stop failed: {err}")

    return {"status": "stopped"}


@app.post("/api/vpn/start", tags=["VPN"])
async def vpn_start() -> dict[str, str]:
    """Start the VPN connection."""
    ret, out, err = run_command(
        ["sudo", "systemctl", "start", "wg-quick@wg0"],
        check=False
    )

    if ret != 0:
        raise HTTPException(status_code=500, detail=f"Start failed: {err}")

    return {"status": "started"}


# =============================================================================
# API Endpoints - Hotspot
# =============================================================================

@app.get("/api/hotspot/status", tags=["Hotspot"])
async def hotspot_status() -> dict[str, Any]:
    """
    Get current hotspot status.

    Returns:
        Hotspot status including SSID, channel, frequency, and connected clients
    """
    return get_ap_status()


@app.post("/api/hotspot/apply", tags=["Hotspot"])
async def hotspot_apply(config: HotspotConfig) -> dict[str, Any]:
    """
    Apply new hotspot configuration.

    Supports both 2.4GHz and 5GHz bands with automatic channel validation.

    Args:
        config: New hotspot configuration

    Returns:
        Applied configuration status
    """
    try:
        # Get dynamic interface name
        iface_config = get_interface_config()
        ap_iface = iface_config["wifi_ap"]

        # Configure based on band selection
        if config.band == "5GHz":
            hw_mode = "a"
            # Validate 5GHz channel
            valid_5ghz_channels = [
                36, 40, 44, 48, 52, 56, 60, 64,
                100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140,
                149, 153, 157, 161, 165
            ]
            if config.channel not in valid_5ghz_channels:
                config.channel = 36  # Default to channel 36 for 5GHz

            extra_config = """
# 802.11ac (WiFi 5) support
ieee80211ac=1
vht_oper_chwidth=1
vht_oper_centr_freq_seg0_idx=42
vht_capab=[MAX-MPDU-11454][SHORT-GI-80][TX-STBC-2BY1][RX-STBC-1]"""
        else:
            hw_mode = "g"
            # Validate 2.4GHz channel
            if config.channel < 1 or config.channel > 13:
                config.channel = 6  # Default to channel 6 for 2.4GHz
            extra_config = ""

        # Generate WPA configuration
        if config.wpa3:
            wpa_config = """wpa=2
wpa_key_mgmt=SAE WPA-PSK
ieee80211w=1"""
        else:
            wpa_config = """wpa=2
wpa_key_mgmt=WPA-PSK"""

        # Generate hostapd configuration
        hostapd_config = f"""# ROSE Link Hotspot Configuration
# Auto-generated via Web API
# Band: {config.band}

interface={ap_iface}
driver=nl80211

# Network settings
ssid={config.ssid}
hw_mode={hw_mode}
channel={config.channel}
country_code={config.country}

# 802.11n support
ieee80211n=1
wmm_enabled=1
{extra_config}

# Security
auth_algs=1
{wpa_config}
wpa_passphrase={config.password}
rsn_pairwise=CCMP

# Logging
logger_syslog=-1
logger_syslog_level=2
"""

        # Write configuration file
        with open(HOSTAPD_CONF, "w", encoding="utf-8") as f:
            f.write(hostapd_config)

        # Restart services to apply changes
        run_command(["sudo", "systemctl", "restart", "hostapd"], check=False)
        run_command(["sudo", "systemctl", "restart", "dnsmasq"], check=False)

        return {
            "status": "applied",
            "config": config.model_dump(),
            "interface": ap_iface
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Apply failed: {str(e)}")


@app.post("/api/hotspot/restart", tags=["Hotspot"])
async def hotspot_restart() -> dict[str, str]:
    """Restart the hotspot services (hostapd and dnsmasq)."""
    ret1, _, err1 = run_command(["sudo", "systemctl", "restart", "hostapd"], check=False)
    ret2, _, err2 = run_command(["sudo", "systemctl", "restart", "dnsmasq"], check=False)

    if ret1 != 0 or ret2 != 0:
        raise HTTPException(status_code=500, detail=f"Restart failed: {err1} {err2}")

    return {"status": "restarted"}


# =============================================================================
# API Endpoints - System
# =============================================================================

@app.get("/api/system/info", tags=["System"])
async def system_info() -> dict[str, Any]:
    """
    Get comprehensive Raspberry Pi system information.

    Returns:
        System info including model, RAM, disk, CPU, interfaces, and WiFi capabilities
    """
    info = {
        "model": "unknown",
        "model_short": "unknown",
        "architecture": "unknown",
        "ram_mb": 0,
        "ram_free_mb": 0,
        "disk_total_gb": 0,
        "disk_free_gb": 0,
        "cpu_temp_c": 0,
        "cpu_usage_percent": 0,
        "uptime_seconds": 0,
        "interfaces": {
            "ethernet": None,
            "wifi_ap": None,
            "wifi_wan": None
        },
        "wifi_capabilities": {
            "supports_5ghz": False,
            "supports_ac": False,
            "supports_ax": False,
            "ap_mode": False
        },
        "kernel_version": "unknown",
        "os_version": "unknown"
    }

    # Get Pi model from device tree
    try:
        with open("/proc/device-tree/model", "r", encoding="utf-8") as f:
            info["model"] = f.read().strip("\x00")
            # Extract short model name
            model = info["model"]
            if "Raspberry Pi 5" in model:
                info["model_short"] = "Pi 5"
            elif "Raspberry Pi 4" in model:
                info["model_short"] = "Pi 4"
            elif "Raspberry Pi 3" in model:
                info["model_short"] = "Pi 3"
            elif "Raspberry Pi Zero 2" in model:
                info["model_short"] = "Zero 2W"
            elif "Raspberry Pi" in model:
                info["model_short"] = "Pi"
    except (IOError, OSError):
        pass

    # Get architecture
    ret, out, _ = run_command(["uname", "-m"], check=False)
    if ret == 0:
        info["architecture"] = out.strip()

    # Get kernel version
    ret, out, _ = run_command(["uname", "-r"], check=False)
    if ret == 0:
        info["kernel_version"] = out.strip()

    # Get OS version
    try:
        with open("/etc/os-release", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    info["os_version"] = line.split("=", 1)[1].strip().strip('"')
                    break
    except (IOError, OSError):
        pass

    # Get RAM info
    ret, out, _ = run_command(["free", "-m"], check=False)
    if ret == 0:
        for line in out.splitlines():
            if line.startswith("Mem:"):
                parts = line.split()
                if len(parts) >= 4:
                    info["ram_mb"] = int(parts[1])
                    info["ram_free_mb"] = int(parts[3])
                break

    # Get disk info
    ret, out, _ = run_command(["df", "-BG", "/"], check=False)
    if ret == 0:
        lines = out.strip().split("\n")
        if len(lines) >= 2:
            parts = lines[1].split()
            if len(parts) >= 4:
                info["disk_total_gb"] = int(parts[1].rstrip("G"))
                info["disk_free_gb"] = int(parts[3].rstrip("G"))

    # Get CPU temperature
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r", encoding="utf-8") as f:
            info["cpu_temp_c"] = int(f.read().strip()) // 1000
    except (IOError, OSError, ValueError):
        pass

    # Get CPU usage (simple calculation)
    ret, out, _ = run_command(["grep", "cpu ", "/proc/stat"], check=False)
    if ret == 0:
        parts = out.split()
        if len(parts) >= 5:
            try:
                idle = int(parts[4])
                total = sum(int(x) for x in parts[1:])
                if total > 0:
                    info["cpu_usage_percent"] = round(100 * (1 - idle / total), 1)
            except (ValueError, IndexError):
                pass

    # Get uptime
    try:
        with open("/proc/uptime", "r", encoding="utf-8") as f:
            info["uptime_seconds"] = int(float(f.read().split()[0]))
    except (IOError, OSError, ValueError):
        pass

    # Get interface configuration
    iface_config = get_interface_config()
    info["interfaces"]["ethernet"] = iface_config["eth"]
    info["interfaces"]["wifi_ap"] = iface_config["wifi_ap"]
    info["interfaces"]["wifi_wan"] = iface_config["wifi_wan"]

    # Check WiFi capabilities
    ret, out, _ = run_command(["iw", "list"], check=False)
    if ret == 0:
        if re.search(r"5[0-9]{3} MHz", out):
            info["wifi_capabilities"]["supports_5ghz"] = True
        if "VHT" in out:
            info["wifi_capabilities"]["supports_ac"] = True
        if "HE" in out:
            info["wifi_capabilities"]["supports_ax"] = True
        if "* AP" in out:
            info["wifi_capabilities"]["ap_mode"] = True

    return info


@app.get("/api/system/interfaces", tags=["System"])
async def system_interfaces() -> dict[str, list]:
    """
    Get detailed network interface information.

    Returns:
        Lists of ethernet, wifi, and vpn interfaces with their status
    """
    interfaces: dict[str, list] = {
        "ethernet": [],
        "wifi": [],
        "vpn": []
    }

    # Get all network interfaces using JSON output
    ret, out, _ = run_command(["ip", "-j", "addr", "show"], check=False)
    if ret == 0:
        try:
            ifaces = json.loads(out)
            for iface in ifaces:
                name = iface.get("ifname", "")
                state = iface.get("operstate", "unknown").lower()

                # Get IP addresses
                ips = []
                for addr_info in iface.get("addr_info", []):
                    if addr_info.get("family") == "inet":
                        ips.append(addr_info.get("local", ""))

                iface_info = {
                    "name": name,
                    "state": state,
                    "ip_addresses": ips,
                    "mac": iface.get("address", "")
                }

                # Categorize interface
                if name.startswith(("eth", "end", "enp")):
                    interfaces["ethernet"].append(iface_info)
                elif name.startswith(("wlan", "wlp")):
                    # Determine if built-in or USB
                    device_path = ""
                    try:
                        device_path = os.readlink(f"/sys/class/net/{name}/device")
                    except OSError:
                        pass

                    iface_info["type"] = (
                        "builtin" if "mmc" in device_path or "soc" in device_path
                        else "usb"
                    )

                    # Get driver name
                    try:
                        driver_path = os.readlink(f"/sys/class/net/{name}/device/driver")
                        iface_info["driver"] = os.path.basename(driver_path)
                    except OSError:
                        iface_info["driver"] = "unknown"

                    interfaces["wifi"].append(iface_info)
                elif name.startswith("wg"):
                    interfaces["vpn"].append(iface_info)
        except json.JSONDecodeError:
            pass

    return interfaces


@app.post("/api/system/reboot", tags=["System"])
async def system_reboot() -> dict[str, str]:
    """
    Reboot the Raspberry Pi.

    Returns:
        Reboot confirmation status
    """
    run_command(["sudo", "reboot"], check=False)
    return {"status": "rebooting"}


# =============================================================================
# API Endpoints - Settings
# =============================================================================

def load_vpn_settings() -> dict[str, Any]:
    """
    Load VPN watchdog settings from configuration file.

    Returns:
        Dictionary with ping_host and check_interval settings
    """
    settings = {
        "ping_host": "8.8.8.8",
        "check_interval": 60
    }

    if VPN_SETTINGS_FILE.exists():
        try:
            with open(VPN_SETTINGS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("#") or "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    key = key.strip().lower()
                    value = value.strip().strip('"')

                    if key == "ping_host":
                        settings["ping_host"] = value
                    elif key == "check_interval":
                        settings["check_interval"] = int(value)
        except (IOError, OSError, ValueError):
            pass

    return settings


def save_vpn_settings(settings: dict[str, Any]) -> bool:
    """
    Save VPN watchdog settings to configuration file.

    Args:
        settings: Dictionary with ping_host and check_interval

    Returns:
        True if save was successful, False otherwise
    """
    try:
        config_content = f"""# ROSE Link VPN Watchdog Settings
# Auto-generated via Web API

# IP/Host to ping through VPN to verify connectivity
PING_HOST={settings.get('ping_host', '8.8.8.8')}

# Check interval in seconds (30-300)
CHECK_INTERVAL={settings.get('check_interval', 60)}
"""
        with open(VPN_SETTINGS_FILE, "w", encoding="utf-8") as f:
            f.write(config_content)

        # Restart watchdog to apply new settings
        run_command(["sudo", "systemctl", "restart", "rose-watchdog"], check=False)
        return True
    except (IOError, OSError):
        return False


@app.get("/api/settings/vpn", tags=["Settings"])
async def get_vpn_settings() -> dict[str, Any]:
    """
    Get current VPN watchdog settings.

    Returns:
        Current ping_host and check_interval values
    """
    return load_vpn_settings()


@app.post("/api/settings/vpn", tags=["Settings"])
async def update_vpn_settings(settings: VPNSettings) -> dict[str, Any]:
    """
    Update VPN watchdog settings.

    Args:
        settings: New VPN watchdog configuration

    Returns:
        Confirmation with saved settings
    """
    settings_dict = {
        "ping_host": settings.ping_host,
        "check_interval": settings.check_interval
    }

    if save_vpn_settings(settings_dict):
        return {"status": "saved", "settings": settings_dict}
    else:
        raise HTTPException(status_code=500, detail="Failed to save settings")


@app.get("/api/system/logs", tags=["System"])
async def system_logs(service: str = "rose-backend") -> dict[str, str]:
    """
    Get system logs for a specific service.

    Args:
        service: Service name to get logs for

    Returns:
        Recent log entries for the specified service
    """
    valid_services = [
        "rose-backend",
        "rose-watchdog",
        "hostapd",
        "dnsmasq",
        "wg-quick@wg0"
    ]

    if service not in valid_services:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid service. Valid options: {', '.join(valid_services)}"
        )

    ret, out, err = run_command(
        ["sudo", "journalctl", "-u", service, "-n", "100", "--no-pager"],
        check=False
    )

    return {"service": service, "logs": out}


# =============================================================================
# Static Files & Application Entry Point
# =============================================================================

# Serve static files (web UI) - must be last to not override API routes
app.mount("/", StaticFiles(directory="/opt/rose-link/web", html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        access_log=True
    )
