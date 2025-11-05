#!/usr/bin/env python3
"""
ROSE Link - Backend API
Routeur VPN domestique sur Raspberry Pi 4
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List
import subprocess
import json
import os
import re
from pathlib import Path

app = FastAPI(title="ROSE Link API", version="0.1.0")

# Paths
WG_PROFILES_DIR = Path("/etc/wireguard/profiles")
WG_ACTIVE_CONF = Path("/etc/wireguard/wg0.conf")
HOSTAPD_CONF = Path("/etc/hostapd/hostapd.conf")

# Ensure directories exist
WG_PROFILES_DIR.mkdir(parents=True, exist_ok=True)


# ===== Models =====

class WifiConnectRequest(BaseModel):
    ssid: str
    password: str


class HotspotConfig(BaseModel):
    ssid: str
    password: str
    country: str = "BE"
    channel: int = 6
    wpa3: bool = False


class VPNProfile(BaseModel):
    name: str
    active: bool = False


# ===== Helper Functions =====

def run_command(cmd: List[str], check=True) -> tuple:
    """Execute command and return (returncode, stdout, stderr)"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=check
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout, e.stderr
    except Exception as e:
        return -1, "", str(e)


def get_wan_status() -> dict:
    """Get WAN connection status (Ethernet + WiFi)"""
    status = {
        "ethernet": {"connected": False, "ip": None},
        "wifi": {"connected": False, "ssid": None, "ip": None}
    }

    # Check Ethernet (eth0)
    ret, out, _ = run_command(["ip", "addr", "show", "eth0"], check=False)
    if ret == 0 and "inet " in out:
        status["ethernet"]["connected"] = True
        match = re.search(r'inet\s+(\S+)', out)
        if match:
            status["ethernet"]["ip"] = match.group(1)

    # Check WiFi WAN (wlan0 in client mode)
    ret, out, _ = run_command(["nmcli", "-t", "-f", "DEVICE,STATE,CONNECTION", "device"], check=False)
    if ret == 0:
        for line in out.splitlines():
            parts = line.split(":")
            if len(parts) >= 3 and parts[0] == "wlan0" and parts[1] == "connected":
                status["wifi"]["connected"] = True
                status["wifi"]["ssid"] = parts[2]

                # Get IP
                ret2, out2, _ = run_command(["ip", "addr", "show", "wlan0"], check=False)
                if ret2 == 0:
                    match = re.search(r'inet\s+(\S+)', out2)
                    if match:
                        status["wifi"]["ip"] = match.group(1)

    return status


def get_vpn_status() -> dict:
    """Get WireGuard VPN status"""
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
                    status["transfer"]["received"] = parts[0].strip().split()[0] + " " + parts[0].strip().split()[1]
                    status["transfer"]["sent"] = parts[1].strip().split()[0] + " " + parts[1].strip().split()[1]

    return status


def get_ap_status() -> dict:
    """Get Access Point (Hotspot) status"""
    status = {
        "active": False,
        "ssid": None,
        "channel": None,
        "clients": 0
    }

    # Check if hostapd is running
    ret, out, _ = run_command(["systemctl", "is-active", "hostapd"], check=False)
    if ret == 0 and out.strip() == "active":
        status["active"] = True

        # Read SSID from config
        if HOSTAPD_CONF.exists():
            with open(HOSTAPD_CONF, 'r') as f:
                for line in f:
                    if line.startswith("ssid="):
                        status["ssid"] = line.split("=", 1)[1].strip()
                    elif line.startswith("channel="):
                        status["channel"] = int(line.split("=", 1)[1].strip())

        # Count connected clients
        ret2, out2, _ = run_command(["iw", "dev", "wlan1", "station", "dump"], check=False)
        if ret2 == 0:
            status["clients"] = out2.count("Station ")

    return status


# ===== API Endpoints =====

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "ROSE Link"}


@app.get("/api/status")
async def get_status():
    """Get overall system status"""
    return {
        "wan": get_wan_status(),
        "vpn": get_vpn_status(),
        "ap": get_ap_status()
    }


# ===== WiFi WAN Endpoints =====

@app.post("/api/wifi/scan")
async def wifi_scan():
    """Scan for available WiFi networks"""
    ret, out, err = run_command(["sudo", "nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "device", "wifi", "list"], check=False)

    if ret != 0:
        raise HTTPException(status_code=500, detail=f"Scan failed: {err}")

    networks = []
    seen_ssids = set()

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

    # Sort by signal strength
    networks.sort(key=lambda x: x["signal"], reverse=True)

    return {"networks": networks}


@app.post("/api/wifi/connect")
async def wifi_connect(request: WifiConnectRequest):
    """Connect to WiFi network (WAN)"""
    ret, out, err = run_command([
        "sudo", "nmcli", "device", "wifi", "connect",
        request.ssid, "password", request.password
    ], check=False)

    if ret != 0:
        raise HTTPException(status_code=500, detail=f"Connection failed: {err}")

    return {"status": "connected", "ssid": request.ssid}


@app.post("/api/wifi/disconnect")
async def wifi_disconnect():
    """Disconnect from WiFi WAN"""
    ret, out, err = run_command(["sudo", "nmcli", "device", "disconnect", "wlan0"], check=False)

    if ret != 0:
        raise HTTPException(status_code=500, detail=f"Disconnect failed: {err}")

    return {"status": "disconnected"}


# ===== VPN Endpoints =====

@app.get("/api/vpn/status")
async def vpn_status():
    """Get VPN status"""
    return get_vpn_status()


@app.get("/api/vpn/profiles")
async def vpn_list_profiles():
    """List available VPN profiles"""
    profiles = []

    if WG_PROFILES_DIR.exists():
        for conf_file in WG_PROFILES_DIR.glob("*.conf"):
            is_active = WG_ACTIVE_CONF.exists() and WG_ACTIVE_CONF.resolve() == conf_file.resolve()
            profiles.append({
                "name": conf_file.stem,
                "active": is_active
            })

    return {"profiles": profiles}


@app.post("/api/vpn/upload")
async def vpn_upload_profile(file: UploadFile = File(...)):
    """Upload a new VPN profile"""
    if not file.filename.endswith(".conf"):
        raise HTTPException(status_code=400, detail="File must be a .conf file")

    # Save profile
    profile_path = WG_PROFILES_DIR / file.filename

    try:
        content = await file.read()
        with open(profile_path, 'wb') as f:
            f.write(content)

        # Set permissions
        os.chmod(profile_path, 0o600)

        return {"status": "uploaded", "name": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/api/vpn/import")
async def vpn_import_profile(file: UploadFile = File(...)):
    """Import and activate VPN profile"""
    if not file.filename.endswith(".conf"):
        raise HTTPException(status_code=400, detail="File must be a .conf file")

    try:
        # Save to profiles
        profile_path = WG_PROFILES_DIR / file.filename
        content = await file.read()
        with open(profile_path, 'wb') as f:
            f.write(content)
        os.chmod(profile_path, 0o600)

        # Activate it
        if WG_ACTIVE_CONF.exists():
            WG_ACTIVE_CONF.unlink()

        WG_ACTIVE_CONF.symlink_to(profile_path)

        # Restart WireGuard
        run_command(["sudo", "systemctl", "restart", "wg-quick@wg0"], check=False)

        return {"status": "imported", "name": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@app.post("/api/vpn/activate")
async def vpn_activate_profile(profile: VPNProfile):
    """Activate a VPN profile"""
    profile_path = WG_PROFILES_DIR / f"{profile.name}.conf"

    if not profile_path.exists():
        raise HTTPException(status_code=404, detail="Profile not found")

    try:
        # Stop current VPN
        run_command(["sudo", "systemctl", "stop", "wg-quick@wg0"], check=False)

        # Update symlink
        if WG_ACTIVE_CONF.exists():
            WG_ACTIVE_CONF.unlink()

        WG_ACTIVE_CONF.symlink_to(profile_path)

        # Start VPN
        run_command(["sudo", "systemctl", "start", "wg-quick@wg0"], check=False)

        return {"status": "activated", "name": profile.name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Activation failed: {str(e)}")


@app.post("/api/vpn/restart")
async def vpn_restart():
    """Restart VPN"""
    ret, out, err = run_command(["sudo", "systemctl", "restart", "wg-quick@wg0"], check=False)

    if ret != 0:
        raise HTTPException(status_code=500, detail=f"Restart failed: {err}")

    return {"status": "restarted"}


@app.post("/api/vpn/stop")
async def vpn_stop():
    """Stop VPN"""
    ret, out, err = run_command(["sudo", "systemctl", "stop", "wg-quick@wg0"], check=False)

    if ret != 0:
        raise HTTPException(status_code=500, detail=f"Stop failed: {err}")

    return {"status": "stopped"}


@app.post("/api/vpn/start")
async def vpn_start():
    """Start VPN"""
    ret, out, err = run_command(["sudo", "systemctl", "start", "wg-quick@wg0"], check=False)

    if ret != 0:
        raise HTTPException(status_code=500, detail=f"Start failed: {err}")

    return {"status": "started"}


# ===== Hotspot Endpoints =====

@app.get("/api/hotspot/status")
async def hotspot_status():
    """Get hotspot status"""
    return get_ap_status()


@app.post("/api/hotspot/apply")
async def hotspot_apply(config: HotspotConfig):
    """Apply hotspot configuration"""
    try:
        # Validate password length
        if len(config.password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

        # Generate hostapd.conf
        wpa_mode = "wpa=2" if not config.wpa3 else "wpa=2\nwpa_key_mgmt=SAE"

        hostapd_config = f"""# ROSE Link Hotspot Configuration
interface=wlan1
driver=nl80211
ssid={config.ssid}
hw_mode=g
channel={config.channel}
country_code={config.country}
ieee80211n=1
wmm_enabled=1

# Security
auth_algs=1
{wpa_mode}
wpa_passphrase={config.password}
rsn_pairwise=CCMP
"""

        # Write config
        with open(HOSTAPD_CONF, 'w') as f:
            f.write(hostapd_config)

        # Restart hostapd
        run_command(["sudo", "systemctl", "restart", "hostapd"], check=False)
        run_command(["sudo", "systemctl", "restart", "dnsmasq"], check=False)

        return {"status": "applied", "config": config.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Apply failed: {str(e)}")


@app.post("/api/hotspot/restart")
async def hotspot_restart():
    """Restart hotspot"""
    ret1, _, err1 = run_command(["sudo", "systemctl", "restart", "hostapd"], check=False)
    ret2, _, err2 = run_command(["sudo", "systemctl", "restart", "dnsmasq"], check=False)

    if ret1 != 0 or ret2 != 0:
        raise HTTPException(status_code=500, detail=f"Restart failed: {err1} {err2}")

    return {"status": "restarted"}


# ===== System Endpoints =====

@app.post("/api/system/reboot")
async def system_reboot():
    """Reboot system"""
    run_command(["sudo", "reboot"], check=False)
    return {"status": "rebooting"}


@app.get("/api/system/logs")
async def system_logs(service: str = "rose-backend"):
    """Get system logs"""
    valid_services = ["rose-backend", "rose-watchdog", "hostapd", "dnsmasq", "wg-quick@wg0"]

    if service not in valid_services:
        raise HTTPException(status_code=400, detail="Invalid service")

    ret, out, err = run_command(["sudo", "journalctl", "-u", service, "-n", "100", "--no-pager"], check=False)

    return {"service": service, "logs": out}


# Serve static files (web UI)
app.mount("/", StaticFiles(directory="/opt/rose-link/web", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
