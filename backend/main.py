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
    band: str = "2.4GHz"  # "2.4GHz" or "5GHz"


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


def get_interface_config() -> dict:
    """Get configured interface names from interfaces.conf"""
    config = {
        "eth": "eth0",
        "wifi_wan": "wlan0",
        "wifi_ap": "wlan1"
    }

    interfaces_conf = Path("/opt/rose-link/system/interfaces.conf")
    if interfaces_conf.exists():
        try:
            with open(interfaces_conf, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('#') or '=' not in line:
                        continue
                    key, value = line.split('=', 1)
                    key = key.strip().upper()
                    value = value.strip().strip('"')
                    if key == "ETH_INTERFACE" and value:
                        config["eth"] = value
                    elif key == "WIFI_WAN_INTERFACE" and value:
                        config["wifi_wan"] = value
                    elif key == "WIFI_AP_INTERFACE" and value:
                        config["wifi_ap"] = value
        except:
            pass

    # Fallback: detect interfaces if config is missing
    if not interfaces_conf.exists():
        # Try to find Ethernet interface
        for iface in ["eth0", "end0", "enp1s0"]:
            if os.path.exists(f"/sys/class/net/{iface}"):
                config["eth"] = iface
                break

        # Try to find WiFi interfaces
        wifi_ifaces = []
        for iface in os.listdir("/sys/class/net/"):
            if os.path.exists(f"/sys/class/net/{iface}/wireless"):
                wifi_ifaces.append(iface)

        if wifi_ifaces:
            config["wifi_ap"] = wifi_ifaces[0]
            config["wifi_wan"] = wifi_ifaces[0]
            if len(wifi_ifaces) > 1:
                config["wifi_wan"] = wifi_ifaces[1]

    return config


def get_wan_status() -> dict:
    """Get WAN connection status (Ethernet + WiFi)"""
    iface_config = get_interface_config()

    status = {
        "ethernet": {"connected": False, "ip": None, "interface": iface_config["eth"]},
        "wifi": {"connected": False, "ssid": None, "ip": None, "interface": iface_config["wifi_wan"]}
    }

    # Check Ethernet (dynamic interface name)
    eth_iface = iface_config["eth"]
    if eth_iface:
        ret, out, _ = run_command(["ip", "addr", "show", eth_iface], check=False)
        if ret == 0 and "inet " in out:
            status["ethernet"]["connected"] = True
            match = re.search(r'inet\s+(\S+)', out)
            if match:
                status["ethernet"]["ip"] = match.group(1)

    # Check WiFi WAN (dynamic interface name)
    wifi_wan_iface = iface_config["wifi_wan"]
    if wifi_wan_iface:
        ret, out, _ = run_command(["nmcli", "-t", "-f", "DEVICE,STATE,CONNECTION", "device"], check=False)
        if ret == 0:
            for line in out.splitlines():
                parts = line.split(":")
                if len(parts) >= 3 and parts[0] == wifi_wan_iface and parts[1] == "connected":
                    status["wifi"]["connected"] = True
                    status["wifi"]["ssid"] = parts[2]

                    # Get IP
                    ret2, out2, _ = run_command(["ip", "addr", "show", wifi_wan_iface], check=False)
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

        # Read config from hostapd.conf
        if HOSTAPD_CONF.exists():
            with open(HOSTAPD_CONF, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("ssid="):
                        status["ssid"] = line.split("=", 1)[1].strip()
                    elif line.startswith("channel="):
                        status["channel"] = int(line.split("=", 1)[1].strip())
                    elif line.startswith("hw_mode="):
                        hw_mode = line.split("=", 1)[1].strip()
                        status["hw_mode"] = hw_mode
                        # Determine frequency band
                        if hw_mode == "a":
                            status["frequency"] = "5GHz"
                        else:
                            status["frequency"] = "2.4GHz"

        # Count connected clients (using dynamic interface name)
        ret2, out2, _ = run_command(["iw", "dev", ap_iface, "station", "dump"], check=False)
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
    """Apply hotspot configuration with 5GHz support"""
    try:
        # Validate password length
        if len(config.password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

        # Get dynamic interface name
        iface_config = get_interface_config()
        ap_iface = iface_config["wifi_ap"]

        # Determine hw_mode and extra config based on band
        if config.band == "5GHz":
            hw_mode = "a"
            # Validate 5GHz channel
            valid_5ghz_channels = [36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140, 149, 153, 157, 161, 165]
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

        # Write config
        with open(HOSTAPD_CONF, 'w') as f:
            f.write(hostapd_config)

        # Restart hostapd
        run_command(["sudo", "systemctl", "restart", "hostapd"], check=False)
        run_command(["sudo", "systemctl", "restart", "dnsmasq"], check=False)

        return {"status": "applied", "config": config.dict(), "interface": ap_iface}
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

INTERFACES_CONF = Path("/opt/rose-link/system/interfaces.conf")


def parse_interfaces_conf() -> dict:
    """Parse the interfaces configuration file"""
    config = {
        "eth_interface": "eth0",
        "wifi_ap_interface": "wlan1",
        "wifi_wan_interface": "wlan0",
        "pi_model": "unknown",
        "pi_version": "unknown"
    }

    if INTERFACES_CONF.exists():
        with open(INTERFACES_CONF, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#') or '=' not in line:
                    continue
                key, value = line.split('=', 1)
                key = key.strip().lower()
                value = value.strip().strip('"')
                if key == "eth_interface":
                    config["eth_interface"] = value
                elif key == "wifi_ap_interface":
                    config["wifi_ap_interface"] = value
                elif key == "wifi_wan_interface":
                    config["wifi_wan_interface"] = value
                elif key == "pi_model":
                    config["pi_model"] = value
                elif key == "pi_version":
                    config["pi_version"] = value

    return config


@app.get("/api/system/info")
async def system_info():
    """Get Raspberry Pi system information and hardware details"""
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
        with open("/proc/device-tree/model", 'r') as f:
            info["model"] = f.read().strip('\x00')
            # Extract short model name
            if "Raspberry Pi 5" in info["model"]:
                info["model_short"] = "Pi 5"
            elif "Raspberry Pi 4" in info["model"]:
                info["model_short"] = "Pi 4"
            elif "Raspberry Pi 3" in info["model"]:
                info["model_short"] = "Pi 3"
            elif "Raspberry Pi Zero 2" in info["model"]:
                info["model_short"] = "Zero 2W"
            elif "Raspberry Pi" in info["model"]:
                info["model_short"] = "Pi"
    except:
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
        with open("/etc/os-release", 'r') as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    info["os_version"] = line.split("=", 1)[1].strip().strip('"')
                    break
    except:
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
        lines = out.strip().split('\n')
        if len(lines) >= 2:
            parts = lines[1].split()
            if len(parts) >= 4:
                info["disk_total_gb"] = int(parts[1].rstrip('G'))
                info["disk_free_gb"] = int(parts[3].rstrip('G'))

    # Get CPU temperature
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", 'r') as f:
            info["cpu_temp_c"] = int(f.read().strip()) // 1000
    except:
        pass

    # Get CPU usage
    ret, out, _ = run_command(["grep", "cpu ", "/proc/stat"], check=False)
    if ret == 0:
        parts = out.split()
        if len(parts) >= 5:
            idle = int(parts[4])
            total = sum(int(x) for x in parts[1:])
            if total > 0:
                info["cpu_usage_percent"] = round(100 * (1 - idle / total), 1)

    # Get uptime
    try:
        with open("/proc/uptime", 'r') as f:
            info["uptime_seconds"] = int(float(f.read().split()[0]))
    except:
        pass

    # Get interface configuration
    iface_config = parse_interfaces_conf()
    info["interfaces"]["ethernet"] = iface_config["eth_interface"]
    info["interfaces"]["wifi_ap"] = iface_config["wifi_ap_interface"]
    info["interfaces"]["wifi_wan"] = iface_config["wifi_wan_interface"]

    # Check WiFi capabilities
    ret, out, _ = run_command(["iw", "list"], check=False)
    if ret == 0:
        if re.search(r'5[0-9]{3} MHz', out):
            info["wifi_capabilities"]["supports_5ghz"] = True
        if "VHT" in out:
            info["wifi_capabilities"]["supports_ac"] = True
        if "HE" in out:
            info["wifi_capabilities"]["supports_ax"] = True
        if "* AP" in out:
            info["wifi_capabilities"]["ap_mode"] = True

    return info


@app.get("/api/system/interfaces")
async def system_interfaces():
    """Get detected network interfaces and their status"""
    interfaces = {
        "ethernet": [],
        "wifi": [],
        "vpn": []
    }

    # Get all network interfaces
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

                if name.startswith("eth") or name.startswith("end") or name.startswith("enp"):
                    interfaces["ethernet"].append(iface_info)
                elif name.startswith("wlan") or name.startswith("wlp"):
                    # Check if it's built-in or USB
                    device_path = ""
                    try:
                        device_path = os.readlink(f"/sys/class/net/{name}/device")
                    except:
                        pass
                    iface_info["type"] = "builtin" if "mmc" in device_path or "soc" in device_path else "usb"

                    # Get driver
                    try:
                        driver_path = os.readlink(f"/sys/class/net/{name}/device/driver")
                        iface_info["driver"] = os.path.basename(driver_path)
                    except:
                        iface_info["driver"] = "unknown"

                    interfaces["wifi"].append(iface_info)
                elif name.startswith("wg"):
                    interfaces["vpn"].append(iface_info)
        except json.JSONDecodeError:
            pass

    return interfaces


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
