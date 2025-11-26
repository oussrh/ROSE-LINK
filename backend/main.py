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
Version: 0.2.1
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from fastapi import Depends, FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

# =============================================================================
# Logging Configuration
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger("rose-link")

# =============================================================================
# Application Configuration
# =============================================================================

app = FastAPI(
    title="ROSE Link API",
    description="REST API for ROSE Link VPN Router",
    version="0.2.1",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# =============================================================================
# Security Configuration
# =============================================================================

# CORS - Restricted to local network only (security fix)
# Only allow requests from the local network and localhost
ALLOWED_ORIGINS = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
    "https://localhost",
    "https://127.0.0.1",
    "http://192.168.50.1",
    "https://192.168.50.1",
    "https://roselink.local",
    "http://roselink.local",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "X-API-Key", "Authorization"],
)

# =============================================================================
# API Key Authentication
# =============================================================================

# API key file path
API_KEY_FILE = Path("/opt/rose-link/system/.api_key")
API_KEY_HASH_FILE = Path("/opt/rose-link/system/.api_key_hash")

# Session tokens (in-memory, reset on restart)
_active_sessions: dict[str, datetime] = {}
SESSION_DURATION = timedelta(hours=24)


def get_or_create_api_key() -> str:
    """
    Get existing API key or create a new one.

    Returns:
        The API key string
    """
    if API_KEY_FILE.exists():
        try:
            return API_KEY_FILE.read_text().strip()
        except (IOError, OSError):
            pass

    # Generate new API key
    api_key = secrets.token_urlsafe(32)

    try:
        API_KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
        API_KEY_FILE.write_text(api_key)
        os.chmod(API_KEY_FILE, 0o600)

        # Store hash for verification
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        API_KEY_HASH_FILE.write_text(key_hash)
        os.chmod(API_KEY_HASH_FILE, 0o600)

        logger.info("Generated new API key")
    except (IOError, OSError) as e:
        logger.warning(f"Could not persist API key: {e}")

    return api_key


def verify_api_key(api_key: str) -> bool:
    """
    Verify an API key against the stored hash.

    Args:
        api_key: The API key to verify

    Returns:
        True if valid, False otherwise
    """
    if not api_key:
        return False

    try:
        if API_KEY_HASH_FILE.exists():
            stored_hash = API_KEY_HASH_FILE.read_text().strip()
            provided_hash = hashlib.sha256(api_key.encode()).hexdigest()
            return hmac.compare_digest(stored_hash, provided_hash)
        elif API_KEY_FILE.exists():
            stored_key = API_KEY_FILE.read_text().strip()
            return hmac.compare_digest(stored_key, api_key)
    except (IOError, OSError):
        pass

    return False


def create_session_token() -> str:
    """Create a new session token."""
    token = secrets.token_urlsafe(32)
    _active_sessions[token] = datetime.now() + SESSION_DURATION

    # Clean up expired sessions
    now = datetime.now()
    expired = [t for t, exp in _active_sessions.items() if exp < now]
    for t in expired:
        del _active_sessions[t]

    return token


def verify_session_token(token: str) -> bool:
    """Verify a session token is valid and not expired."""
    if not token or token not in _active_sessions:
        return False

    if _active_sessions[token] < datetime.now():
        del _active_sessions[token]
        return False

    return True


async def require_auth(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None),
) -> bool:
    """
    Dependency to require authentication for sensitive endpoints.

    Accepts either:
    - X-API-Key header with the API key
    - Authorization: Bearer <session_token>

    Raises:
        HTTPException: If authentication fails
    """
    # Check API key
    if x_api_key and verify_api_key(x_api_key):
        logger.debug("Authenticated via API key")
        return True

    # Check session token
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        if verify_session_token(token):
            logger.debug("Authenticated via session token")
            return True

    logger.warning("Authentication failed")
    raise HTTPException(
        status_code=401,
        detail="Authentication required. Provide X-API-Key header or valid session token.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def optional_auth(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None),
) -> bool:
    """
    Optional authentication - returns True if authenticated, False otherwise.
    Does not raise exceptions.
    """
    if x_api_key and verify_api_key(x_api_key):
        return True

    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        if verify_session_token(token):
            return True

    return False


# Initialize API key on startup
_api_key = get_or_create_api_key()
logger.info(f"API key available at {API_KEY_FILE}")

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
    return {"status": "ok", "service": "ROSE Link", "version": "0.2.1"}


# =============================================================================
# API Endpoints - Authentication
# =============================================================================


class LoginRequest(BaseModel):
    """Request model for login."""

    api_key: str = Field(..., min_length=1, description="API key for authentication")


class LoginResponse(BaseModel):
    """Response model for successful login."""

    token: str
    expires_in: int
    message: str


@app.post("/api/auth/login", tags=["Auth"], response_model=LoginResponse)
async def auth_login(request: LoginRequest) -> LoginResponse:
    """
    Authenticate with API key and receive a session token.

    The session token can be used for subsequent requests via
    the Authorization: Bearer <token> header.

    Args:
        request: Login credentials with API key

    Returns:
        Session token and expiration info
    """
    if not verify_api_key(request.api_key):
        logger.warning("Login attempt with invalid API key")
        raise HTTPException(status_code=401, detail="Invalid API key")

    token = create_session_token()
    logger.info("User authenticated successfully")

    return LoginResponse(
        token=token,
        expires_in=int(SESSION_DURATION.total_seconds()),
        message="Authentication successful"
    )


@app.post("/api/auth/logout", tags=["Auth"])
async def auth_logout(
    authorization: Optional[str] = Header(None),
) -> dict[str, str]:
    """
    Invalidate the current session token.

    Args:
        authorization: Bearer token header

    Returns:
        Logout confirmation
    """
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        if token in _active_sessions:
            del _active_sessions[token]
            logger.info("User logged out")

    return {"status": "logged_out"}


@app.get("/api/auth/check", tags=["Auth"])
async def auth_check(authenticated: bool = Depends(optional_auth)) -> dict[str, Any]:
    """
    Check if current request is authenticated.

    Returns:
        Authentication status
    """
    return {
        "authenticated": authenticated,
        "message": "Authenticated" if authenticated else "Not authenticated"
    }


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
async def wifi_connect(
    request: WifiConnectRequest,
    authenticated: bool = Depends(require_auth)
) -> dict[str, str]:
    """
    Connect to a WiFi network as WAN.

    Requires authentication.

    Args:
        request: WiFi connection credentials

    Returns:
        Connection status
    """
    logger.info(f"WiFi connection requested: SSID={request.ssid}")
    ret, out, err = run_command([
        "sudo", "nmcli", "device", "wifi", "connect",
        request.ssid, "password", request.password
    ], check=False)

    if ret != 0:
        logger.error(f"WiFi connection failed: {err}")
        raise HTTPException(status_code=500, detail=f"Connection failed: {err}")

    logger.info(f"WiFi connected successfully: SSID={request.ssid}")
    return {"status": "connected", "ssid": request.ssid}


@app.post("/api/wifi/disconnect", tags=["WiFi"])
async def wifi_disconnect(authenticated: bool = Depends(require_auth)) -> dict[str, str]:
    """
    Disconnect from WiFi WAN.

    Requires authentication.
    Uses the configured WiFi WAN interface from interfaces.conf.

    Returns:
        Disconnection status
    """
    # Use dynamic interface instead of hardcoded wlan0
    iface_config = get_interface_config()
    wifi_wan_iface = iface_config["wifi_wan"]

    logger.info(f"WiFi disconnect requested: interface={wifi_wan_iface}")
    ret, out, err = run_command(
        ["sudo", "nmcli", "device", "disconnect", wifi_wan_iface],
        check=False
    )

    if ret != 0:
        logger.error(f"WiFi disconnect failed: {err}")
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


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent path traversal attacks.

    Args:
        filename: The original filename

    Returns:
        Sanitized filename with only alphanumeric, dash, underscore, and dot

    Raises:
        ValueError: If filename is invalid
    """
    if not filename:
        raise ValueError("Filename is required")

    # Get only the base name (remove any path components)
    basename = os.path.basename(filename)

    # Remove any potentially dangerous characters
    # Only allow alphanumeric, dash, underscore, and dot
    sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', basename)

    # Ensure it doesn't start with a dot (hidden file)
    if sanitized.startswith('.'):
        sanitized = '_' + sanitized[1:]

    # Ensure reasonable length
    if len(sanitized) > 100:
        sanitized = sanitized[:100]

    if not sanitized:
        raise ValueError("Invalid filename")

    return sanitized


def validate_wireguard_config(content: bytes) -> bool:
    """
    Basic validation of WireGuard configuration file.

    Args:
        content: File content as bytes

    Returns:
        True if valid, False otherwise
    """
    try:
        text = content.decode('utf-8')

        # Must contain [Interface] section
        if '[Interface]' not in text:
            return False

        # Check for required fields in Interface section
        if 'PrivateKey' not in text:
            return False

        # Should have at least one peer (for client config)
        # Note: Server configs might not have peers initially
        # if '[Peer]' not in text:
        #     return False

        return True
    except (UnicodeDecodeError, AttributeError):
        return False


# Maximum file size for VPN profiles (1 MB)
MAX_VPN_PROFILE_SIZE = 1024 * 1024


@app.post("/api/vpn/upload", tags=["VPN"])
async def vpn_upload_profile(
    file: UploadFile = File(...),
    authenticated: bool = Depends(require_auth)
) -> dict[str, str]:
    """
    Upload a new VPN profile without activating it.

    Requires authentication.

    Args:
        file: WireGuard .conf file

    Returns:
        Upload status
    """
    if not file.filename or not file.filename.endswith(".conf"):
        raise HTTPException(status_code=400, detail="File must be a .conf file")

    try:
        # Sanitize filename to prevent path traversal
        safe_filename = sanitize_filename(file.filename)
        if not safe_filename.endswith('.conf'):
            safe_filename += '.conf'

        # Read content with size limit
        content = await file.read()
        if len(content) > MAX_VPN_PROFILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large (max 1MB)")

        # Validate WireGuard config format
        if not validate_wireguard_config(content):
            raise HTTPException(
                status_code=400,
                detail="Invalid WireGuard configuration file"
            )

        profile_path = WG_PROFILES_DIR / safe_filename

        with open(profile_path, "wb") as f:
            f.write(content)

        # Set secure permissions (readable only by root/owner)
        os.chmod(profile_path, 0o600)

        logger.info(f"VPN profile uploaded: {safe_filename}")
        return {"status": "uploaded", "name": safe_filename}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"VPN profile upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/api/vpn/import", tags=["VPN"])
async def vpn_import_profile(
    file: UploadFile = File(...),
    authenticated: bool = Depends(require_auth)
) -> dict[str, str]:
    """
    Import and immediately activate a VPN profile.

    Requires authentication.

    Args:
        file: WireGuard .conf file

    Returns:
        Import and activation status
    """
    if not file.filename or not file.filename.endswith(".conf"):
        raise HTTPException(status_code=400, detail="File must be a .conf file")

    try:
        # Sanitize filename to prevent path traversal
        safe_filename = sanitize_filename(file.filename)
        if not safe_filename.endswith('.conf'):
            safe_filename += '.conf'

        # Read content with size limit
        content = await file.read()
        if len(content) > MAX_VPN_PROFILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large (max 1MB)")

        # Validate WireGuard config format
        if not validate_wireguard_config(content):
            raise HTTPException(
                status_code=400,
                detail="Invalid WireGuard configuration file"
            )

        # Save to profiles directory
        profile_path = WG_PROFILES_DIR / safe_filename

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

        logger.info(f"VPN profile imported and activated: {safe_filename}")
        return {"status": "imported", "name": safe_filename}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"VPN profile import failed: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@app.post("/api/vpn/activate", tags=["VPN"])
async def vpn_activate_profile(
    profile: VPNProfile,
    authenticated: bool = Depends(require_auth)
) -> dict[str, str]:
    """
    Activate an existing VPN profile.

    Requires authentication.

    Args:
        profile: Profile name to activate

    Returns:
        Activation status
    """
    # Sanitize profile name to prevent path traversal
    safe_name = sanitize_filename(profile.name)
    if safe_name.endswith('.conf'):
        safe_name = safe_name[:-5]  # Remove .conf if present

    profile_path = WG_PROFILES_DIR / f"{safe_name}.conf"

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

        logger.info(f"VPN profile activated: {safe_name}")
        return {"status": "activated", "name": safe_name}
    except Exception as e:
        logger.error(f"VPN profile activation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Activation failed: {str(e)}")


@app.post("/api/vpn/restart", tags=["VPN"])
async def vpn_restart(authenticated: bool = Depends(require_auth)) -> dict[str, str]:
    """Restart the VPN connection. Requires authentication."""
    logger.info("VPN restart requested")
    ret, out, err = run_command(
        ["sudo", "systemctl", "restart", "wg-quick@wg0"],
        check=False
    )

    if ret != 0:
        logger.error(f"VPN restart failed: {err}")
        raise HTTPException(status_code=500, detail=f"Restart failed: {err}")

    return {"status": "restarted"}


@app.post("/api/vpn/stop", tags=["VPN"])
async def vpn_stop(authenticated: bool = Depends(require_auth)) -> dict[str, str]:
    """Stop the VPN connection. Requires authentication."""
    logger.info("VPN stop requested")
    ret, out, err = run_command(
        ["sudo", "systemctl", "stop", "wg-quick@wg0"],
        check=False
    )

    if ret != 0:
        logger.error(f"VPN stop failed: {err}")
        raise HTTPException(status_code=500, detail=f"Stop failed: {err}")

    return {"status": "stopped"}


@app.post("/api/vpn/start", tags=["VPN"])
async def vpn_start(authenticated: bool = Depends(require_auth)) -> dict[str, str]:
    """Start the VPN connection. Requires authentication."""
    logger.info("VPN start requested")
    ret, out, err = run_command(
        ["sudo", "systemctl", "start", "wg-quick@wg0"],
        check=False
    )

    if ret != 0:
        logger.error(f"VPN start failed: {err}")
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


def escape_hostapd_value(value: str) -> str:
    """
    Escape a value for safe use in hostapd configuration.

    Removes or escapes characters that could break config parsing
    or enable injection attacks.

    Args:
        value: The value to escape

    Returns:
        Escaped value safe for hostapd config
    """
    # Remove newlines and carriage returns (could inject new config lines)
    value = value.replace('\n', '').replace('\r', '')
    # Remove null bytes
    value = value.replace('\x00', '')
    # Remove comment characters at start
    value = value.lstrip('#')
    return value


def validate_ssid(ssid: str) -> str:
    """
    Validate and sanitize SSID.

    Args:
        ssid: The SSID to validate

    Returns:
        Sanitized SSID

    Raises:
        ValueError: If SSID is invalid
    """
    if not ssid or len(ssid) < 1:
        raise ValueError("SSID cannot be empty")
    if len(ssid) > 32:
        raise ValueError("SSID cannot exceed 32 characters")

    # Escape dangerous characters
    ssid = escape_hostapd_value(ssid)

    if not ssid:
        raise ValueError("Invalid SSID")

    return ssid


def validate_wpa_password(password: str) -> str:
    """
    Validate and sanitize WPA password.

    Args:
        password: The password to validate

    Returns:
        Sanitized password

    Raises:
        ValueError: If password is invalid
    """
    if not password or len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    if len(password) > 63:
        raise ValueError("Password cannot exceed 63 characters")

    # Escape dangerous characters
    password = escape_hostapd_value(password)

    if len(password) < 8:
        raise ValueError("Invalid password after sanitization")

    return password


@app.post("/api/hotspot/apply", tags=["Hotspot"])
async def hotspot_apply(
    config: HotspotConfig,
    authenticated: bool = Depends(require_auth)
) -> dict[str, Any]:
    """
    Apply new hotspot configuration.

    Requires authentication.
    Supports both 2.4GHz and 5GHz bands with automatic channel validation.

    Args:
        config: New hotspot configuration

    Returns:
        Applied configuration status
    """
    try:
        # Validate and sanitize SSID and password
        try:
            safe_ssid = validate_ssid(config.ssid)
            safe_password = validate_wpa_password(config.password)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Validate country code (2 uppercase letters)
        safe_country = config.country.upper()[:2]
        if not re.match(r'^[A-Z]{2}$', safe_country):
            safe_country = "US"  # Default

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

        # Generate hostapd configuration with escaped values
        hostapd_config = f"""# ROSE Link Hotspot Configuration
# Auto-generated via Web API
# Band: {config.band}

interface={ap_iface}
driver=nl80211

# Network settings
ssid={safe_ssid}
hw_mode={hw_mode}
channel={config.channel}
country_code={safe_country}

# 802.11n support
ieee80211n=1
wmm_enabled=1
{extra_config}

# Security
auth_algs=1
{wpa_config}
wpa_passphrase={safe_password}
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

        logger.info(f"Hotspot configuration applied: SSID={safe_ssid}, channel={config.channel}")
        return {
            "status": "applied",
            "config": config.model_dump(),
            "interface": ap_iface
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Hotspot configuration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Apply failed: {str(e)}")


@app.post("/api/hotspot/restart", tags=["Hotspot"])
async def hotspot_restart(authenticated: bool = Depends(require_auth)) -> dict[str, str]:
    """Restart the hotspot services (hostapd and dnsmasq). Requires authentication."""
    logger.info("Hotspot restart requested")
    ret1, _, err1 = run_command(["sudo", "systemctl", "restart", "hostapd"], check=False)
    ret2, _, err2 = run_command(["sudo", "systemctl", "restart", "dnsmasq"], check=False)

    if ret1 != 0 or ret2 != 0:
        logger.error(f"Hotspot restart failed: {err1} {err2}")
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
async def system_reboot(authenticated: bool = Depends(require_auth)) -> dict[str, str]:
    """
    Reboot the Raspberry Pi.

    Requires authentication.

    Returns:
        Reboot confirmation status
    """
    logger.info("System reboot requested")
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


def validate_ping_host(host: str) -> str:
    """
    Validate a ping host to ensure it's safe.

    Args:
        host: IP address or hostname

    Returns:
        Validated host string

    Raises:
        ValueError: If host is invalid
    """
    if not host:
        raise ValueError("Ping host is required")

    # Remove any whitespace
    host = host.strip()

    # Check for valid IPv4 address
    ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    # Check for valid hostname (alphanumeric, dots, hyphens)
    hostname_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-\.]*[a-zA-Z0-9])?$'

    if not (re.match(ipv4_pattern, host) or re.match(hostname_pattern, host)):
        raise ValueError("Invalid IP address or hostname")

    # Prevent command injection by checking for shell metacharacters
    dangerous_chars = ['&', '|', ';', '$', '`', '(', ')', '{', '}', '[', ']', '<', '>', '!', '\n', '\r']
    for char in dangerous_chars:
        if char in host:
            raise ValueError("Invalid characters in ping host")

    return host


@app.post("/api/settings/vpn", tags=["Settings"])
async def update_vpn_settings(
    settings: VPNSettings,
    authenticated: bool = Depends(require_auth)
) -> dict[str, Any]:
    """
    Update VPN watchdog settings.

    Requires authentication.

    Args:
        settings: New VPN watchdog configuration

    Returns:
        Confirmation with saved settings
    """
    # Validate ping host
    try:
        safe_ping_host = validate_ping_host(settings.ping_host)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    settings_dict = {
        "ping_host": safe_ping_host,
        "check_interval": settings.check_interval
    }

    if save_vpn_settings(settings_dict):
        logger.info(f"VPN settings updated: ping_host={safe_ping_host}, interval={settings.check_interval}")
        return {"status": "saved", "settings": settings_dict}
    else:
        logger.error("Failed to save VPN settings")
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
