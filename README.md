<div align="center">

<img src="web/Logo.webp" alt="ROSE Link Logo" width="200">

# ROSE Link

**Home VPN Router on Raspberry Pi**

<img src="web/icon.webp" alt="ROSE Link Icon" width="64">

Transform your Raspberry Pi into a professional WiFi router/access point that establishes a secure VPN tunnel to your remote network, allowing you to access local resources and obtain the public IP of your VPN server from anywhere in the world.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi%203%2F4%2F5%2FZero%202W-red)

**[Version Francaise](README.fr.md)**

</div>

---

## Objective

ROSE Link creates a complete VPN solution that:

- **Connects to Internet** via Ethernet RJ45 (priority) or WiFi client (automatic fallback)
- **Establishes a WireGuard tunnel** to your VPN server (Fritz!Box, pfSense, OpenWrt, VPS...)
- **Creates a local WiFi hotspot** for your devices (PC, smartphone, tablet)
- **Routes all traffic** through VPN for remote network access + server's public IP
- **Modern Web interface** to configure WAN, VPN and Hotspot easily
- **Flexible configuration** via web interface (country, WiFi channels, VPN settings)

```
[PC/Smartphone] ~~~WiFi~~~> Raspberry Pi (ROSE Link Hotspot)
                                    |
                              WireGuard (wg0)
                                    |
                              Remote VPN Server
                              (Fritz!Box, VPS, etc.)
                                    |
                          Remote Network + Internet
```

---

## Features

### Intelligent WAN Connectivity
- Auto-failover: Ethernet RJ45 priority -> WiFi client fallback
- Easy configuration: Scan and connect to WiFi from web interface
- Real-time monitoring: WAN connection status

### Multi-Protocol VPN Support
- **WireGuard**: Fast, modern VPN with .conf file import
- **OpenVPN**: Support for .ovpn files with embedded certificates
- Multi-profile: Import and manage multiple VPN configurations
- Kill-switch: Blocks all traffic if VPN drops (no leaks)
- Watchdog: Automatic monitoring and reconnection
- Detailed status: Handshake, endpoint, data transfer

### AdGuard Home Integration (DNS Ad Blocking)
- DNS-level ad blocking: Pi-hole alternative built-in
- Blocking statistics: Queries, blocked percentage, top domains
- Easy toggle: Enable/disable from web interface
- AdGuard web UI: Full access to AdGuard Home settings

### Configurable WiFi Hotspot
- Custom SSID: Choose your network name
- WPA2/WPA3 security: WPA3 if hardware supports it
- Country configuration: Channels and power compliant with regulations
- Channel selection: Optimize performance (2.4GHz and 5GHz)
- Connected clients: Real-time counter

### Connected Clients Management
- Device tracking: See all connected and historical devices
- Device identification: Auto-detect manufacturer and device type
- Custom naming: Assign friendly names to devices
- Client control: Block, unblock, or kick devices
- Per-client statistics: Traffic and connection history

### QoS Traffic Prioritization
- VPN priority: Prioritize VPN traffic over local traffic
- Simple toggle: Enable/disable from web interface
- Bandwidth allocation: Configure VPN vs other traffic ratio

### First-Time Setup Wizard
- Guided configuration: Step-by-step initial setup
- Network setup: Configure WAN connection
- VPN import: Upload VPN profile during setup
- Hotspot configuration: Set SSID and password
- Security setup: Configure admin password

### Modern User Interface
- Dark mode: Elegant and eye-friendly interface
- Responsive: Works on desktop, tablet and mobile
- Real-time: WebSocket-based live status updates
- HTTPS: Secure connection (self-signed certificate)
- Bilingual: English and French support

### Enhanced Security
- **Backend isolation**: API accessible only via Nginx reverse proxy
- **Restricted sudoers**: Minimal system command access with validation
- **Protected files**: VPN configurations in mode 600, WireGuard directory mode 700
- **iptables kill-switch**: Leak protection blocks all traffic if VPN drops
- **SSL/TLS**: RSA 4096-bit certificates with Subject Alternative Names
- **Secure passwords**: Auto-generated 12-character random WiFi passwords
- **Systemd hardening**: `ProtectSystem=strict`, `PrivateTmp=true`, `NoNewPrivileges=true`
- **Resource limits**: Memory and CPU limits on backend service

---

## Installation

### Prerequisites

- **Hardware**: Raspberry Pi 3, 4, 5, or Zero 2W
- **OS**: Raspberry Pi OS (Bullseye/Bookworm) or Debian 11/12
- **Memory**: 512MB RAM minimum, 1GB+ recommended
- **Storage**: 300MB free disk space minimum

### Method 1: One-Line Install (Quickest)

```bash
curl -fsSL https://raw.githubusercontent.com/oussrh/ROSE-LINK/main/install.sh | sudo bash
```

### Method 2: Download and Install (Recommended)

```bash
# Download archive
wget https://github.com/oussrh/ROSE-LINK/releases/latest/download/rose-link-pro.tar.gz

# Extract
tar -xzf rose-link-pro.tar.gz
cd rose-link

# Interactive installation
sudo bash install.sh

# Or with custom options
sudo bash install.sh --ssid "MyVPN" --country US
```

### Method 3: Debian Package (Best for Updates)

```bash
# Download package
wget https://github.com/oussrh/ROSE-LINK/releases/latest/download/rose-link-pro_0.2.0-1_all.deb

# Install with apt (handles dependencies)
sudo apt install ./rose-link-pro_0.2.0-1_all.deb
```

### Installation Options

| Option | Description |
|--------|-------------|
| `-h, --help` | Show help message |
| `-y, --yes` | Non-interactive mode (accept defaults) |
| `-f, --force` | Force installation (skip hardware checks) |
| `--ssid NAME` | Custom WiFi SSID (default: ROSE-Link) |
| `--password PASS` | Custom WiFi password (min 8 chars, auto-generated if not set) |
| `--country CODE` | Country code for WiFi regulations (default: BE) |

**Examples:**
```bash
# Silent installation with defaults
sudo bash install.sh -y

# Custom hotspot configuration
sudo bash install.sh --ssid "HomeVPN" --password "MySecure123" --country FR

# Force install on non-Pi hardware (testing)
sudo bash install.sh -f
```

### Uninstallation

```bash
# Interactive uninstall
sudo bash uninstall.sh

# Quick uninstall (keep VPN profiles)
sudo bash uninstall.sh -y

# Complete removal
sudo bash uninstall.sh -y -f

# If installed via Debian package
sudo apt remove rose-link-pro    # Keep config
sudo apt purge rose-link-pro     # Remove all
```

---

## Quick Configuration

### 1. Access the Web Interface

After installation, connect to the hotspot:
- **SSID**: `ROSE-Link` (or your custom name)
- **Password**: Displayed at end of installation (randomly generated for security)

Then open your browser:
- **URL**: `https://roselink.local` or `https://192.168.50.1`

> **Note**: Accept the self-signed certificate warning (the certificate uses RSA 4096-bit encryption)

### 2. Configure WireGuard VPN

1. Go to the **VPN** tab
2. Click **"Import WireGuard profile (.conf)"**
3. Select your `.conf` file from your VPN server
4. The VPN starts automatically!

### 3. Customize the Hotspot

1. Go to the **Hotspot** tab
2. Configure:
   - SSID (network name)
   - Password (min. 8 characters)
   - Country (regulatory settings)
   - Channel (1, 6 or 11 recommended for 2.4GHz)
   - Band (2.4GHz or 5GHz)
   - WPA3 (check if supported)
3. Click **"Apply"**

### 4. Configure VPN Watchdog

1. Go to the **System** tab
2. Set the ping IP to verify VPN connectivity
3. Adjust check interval if needed
4. Save settings

---

## Supported Hardware

### Compatible Raspberry Pi Models

| Model | Support | WiFi | Notes |
|-------|---------|------|-------|
| **Raspberry Pi 5** | Full | 2.4GHz + 5GHz | Optimal performance, WiFi 802.11ac |
| **Raspberry Pi 4** | Full | 2.4GHz + 5GHz | Recommended, good price/performance |
| **Raspberry Pi 3 B+** | Limited | 2.4GHz only | Reduced performance, suitable for light use |
| **Raspberry Pi Zero 2 W** | Basic | 2.4GHz only | Limited resources, personal use only |

### Recommended Configuration

#### Raspberry Pi 5 / Pi 4 (Recommended)
- **RAM**: 2 GB minimum, 4 GB recommended
- **Power**: 5V 3A USB-C (5V 5A for Pi 5)
- **microSD card**: Class A2, 32-64 GB
- **Case with fan** (active cooling recommended)

### Connectivity

| Interface | Usage | Pi 5 | Pi 4 | Pi 3 | Zero 2W |
|-----------|-------|------|------|------|---------|
| **Ethernet RJ45** | WAN priority | Gigabit | Gigabit | 100Mbps | - |
| **Built-in WiFi** | Hotspot AP | 5GHz/ac | 5GHz/ac | 2.4GHz | 2.4GHz |
| **USB WiFi Dongle** | WAN + AP separate | Yes | Yes | Yes | Yes |

### Automatic Hardware Detection

ROSE Link automatically detects:
- **Raspberry Pi model** and capabilities
- **Network interfaces** (Ethernet, built-in WiFi, USB WiFi)
- **WiFi capabilities** (5GHz, 802.11ac/ax, AP mode)
- **System resources** (RAM, disk space, CPU temperature)

---

## REST API

### Available Endpoints

#### Health and Status
- `GET /api/health` - Health check
- `GET /api/status` - Global status (WAN, VPN, AP)
- `GET /api/metrics` - Prometheus metrics endpoint
- `GET /api/metrics/performance` - Request latency and performance metrics (JSON)

#### WebSocket
- `WS /api/ws` - Real-time status updates
- `GET /api/ws/status` - WebSocket connection info

#### WiFi WAN
- `POST /api/wifi/scan` - Scan WiFi networks *(requires auth)*
- `POST /api/wifi/connect` - Connect to network *(requires auth)*
- `POST /api/wifi/disconnect` - Disconnect *(requires auth)*

#### VPN (WireGuard + OpenVPN)
- `GET /api/vpn/status` - VPN status
- `GET /api/vpn/profiles` - List profiles *(requires auth)*
- `POST /api/vpn/upload` - Upload profile *(requires auth)*
- `POST /api/vpn/import` - Import and activate *(requires auth)*
- `POST /api/vpn/activate` - Activate existing profile *(requires auth)*
- `POST /api/vpn/start` - Start VPN *(requires auth)*
- `POST /api/vpn/stop` - Stop VPN *(requires auth)*
- `POST /api/vpn/restart` - Restart VPN *(requires auth)*

#### AdGuard Home (v1.0.0+)
- `GET /api/adguard/status` - AdGuard status and stats
- `POST /api/adguard/enable` - Enable DNS protection
- `POST /api/adguard/disable` - Disable DNS protection
- `GET /api/adguard/stats` - Blocking statistics
- `GET /api/adguard/querylog` - DNS query log

#### Connected Clients (v1.0.0+)
- `GET /api/clients` - List all clients
- `GET /api/clients/connected` - Currently connected clients
- `GET /api/clients/{mac}` - Get client details
- `PUT /api/clients/{mac}` - Update client name
- `POST /api/clients/{mac}/block` - Block client
- `POST /api/clients/{mac}/unblock` - Unblock client
- `POST /api/clients/{mac}/kick` - Disconnect client

#### QoS (v1.0.0+)
- `GET /api/qos/status` - QoS status and config
- `POST /api/qos/enable` - Enable traffic prioritization
- `POST /api/qos/disable` - Disable QoS
- `PUT /api/qos/config` - Update QoS settings

#### Setup Wizard (v1.0.0+)
- `GET /api/setup/status` - Check if setup required
- `POST /api/setup/start` - Start setup wizard
- `GET /api/setup/step/{step}` - Get step data
- `POST /api/setup/step/{step}` - Submit step data
- `POST /api/setup/complete` - Complete setup
- `POST /api/setup/skip` - Skip setup

#### Hotspot
- `GET /api/hotspot/status` - Hotspot status
- `GET /api/hotspot/clients` - List connected clients *(requires auth)*
- `POST /api/hotspot/apply` - Apply configuration *(requires auth)*
- `POST /api/hotspot/restart` - Restart hotspot *(requires auth)*

#### Backup/Restore
- `GET /api/backup/list` - List available backups
- `POST /api/backup/create` - Create new backup
- `POST /api/backup/restore/{filename}` - Restore from backup
- `GET /api/backup/download/{filename}` - Download backup file
- `POST /api/backup/upload` - Upload backup file
- `DELETE /api/backup/{filename}` - Delete backup

#### Speed Test
- `GET /api/speedtest/status` - Check if test running
- `POST /api/speedtest/run` - Start speed test
- `GET /api/speedtest/history` - Get test history
- `GET /api/speedtest/last` - Get last result

#### SSL Certificates
- `GET /api/ssl/status` - Certificate status
- `POST /api/ssl/request` - Request Let's Encrypt certificate
- `POST /api/ssl/renew` - Renew certificates
- `POST /api/ssl/self-signed` - Generate self-signed certificate

#### Settings
- `GET /api/settings/vpn` - Get VPN watchdog settings *(requires auth)*
- `POST /api/settings/vpn` - Update VPN watchdog settings *(requires auth)*

#### System
- `GET /api/system/info` - System information (Pi model, RAM, CPU, WiFi)
- `GET /api/system/interfaces` - Detected network interfaces
- `GET /api/system/logs?service=xxx` - Service logs *(requires auth)*
- `POST /api/system/reboot` - Reboot system *(requires auth)*

### Usage Example

```bash
# Health check
curl -k https://roselink.local/api/health

# Global status
curl -k https://roselink.local/api/status | jq

# Scan WiFi
curl -k -X POST https://roselink.local/api/wifi/scan | jq

# VPN status
curl -k https://roselink.local/api/vpn/status | jq

# System information
curl -k https://roselink.local/api/system/info | jq
```

---

## Roadmap

### Version 1.0.0 (Current - Production Ready)
- [x] **AdGuard Home Integration**: DNS-level ad blocking with statistics
- [x] **OpenVPN Support**: In addition to WireGuard (.ovpn file import)
- [x] **Connected Clients Management**: Track, name, block/unblock devices
- [x] **Simple QoS**: VPN traffic prioritization
- [x] **Ready-to-Flash SD Image**: Pre-configured Raspberry Pi image
- [x] **First-Time Setup Wizard**: Guided initial configuration
- [x] **Full Test Suite**: 90%+ code coverage

### Previous Releases

#### Version 0.3.0
- [x] WebSocket for real-time status updates
- [x] Configuration backup/restore
- [x] Let's Encrypt SSL certificate option
- [x] Speed test integration
- [x] Prometheus metrics endpoint (/api/metrics)
- [x] Bandwidth usage statistics

#### Version 0.2.x
- [x] Complete i18n support (English & French)
- [x] Mobile-first responsive design
- [x] Dynamic interface detection
- [x] API documentation endpoints

### Future Releases (v1.x)
- [ ] Email notifications for VPN failures
- [ ] Full QoS profiles (Gaming, Streaming, Work)
- [ ] Grafana metrics dashboard
- [ ] Multi-WAN load balancing
- [ ] Automatic updates

---

## Troubleshooting

### Quick Service Check

```bash
# Check all ROSE Link services at once
for svc in rose-backend rose-watchdog hostapd dnsmasq nginx; do
    status=$(systemctl is-active $svc 2>/dev/null || echo "inactive")
    echo "$svc: $status"
done
```

### Common Issues

| Problem | Solution |
|---------|----------|
| Can't connect to hotspot | `sudo systemctl restart hostapd` |
| VPN not connecting | `sudo systemctl restart wg-quick@wg0` |
| Web interface not loading | `sudo systemctl restart nginx rose-backend` |
| No internet on clients | Check VPN: `sudo wg show` and IP forwarding: `cat /proc/sys/net/ipv4/ip_forward` |

### View Logs

```bash
# Backend logs
sudo journalctl -u rose-backend -f

# VPN logs
sudo journalctl -u wg-quick@wg0 -n 50

# Hotspot logs
sudo journalctl -u hostapd -n 50

# Installation log
cat /var/log/rose-link-install.log
```

### Full Documentation

See [QUICKSTART.md](QUICKSTART.md) for detailed troubleshooting steps.

---

## Contributing

Contributions are welcome!

### How to Contribute

1. Fork the project
2. Create a branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Local Development

```bash
# Clone
git clone https://github.com/oussrh/ROSE-LINK.git
cd ROSE-LINK

# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py

# Web: open web/index.html in a browser
```

---

## License

This project is under MIT License. See the `LICENSE` file for details.

---

## Acknowledgments

- **WireGuard**: Modern and performant VPN
- **FastAPI**: Fast and elegant Python framework
- **Tailwind CSS**: Utility-first CSS framework
- **htmx**: Modern HTML interactivity
- **Raspberry Pi Foundation**: Extraordinary hardware

---

## Support

- **Documentation**: [GitHub Wiki](https://github.com/oussrh/ROSE-LINK/wiki)
- **Issues**: [GitHub Issues](https://github.com/oussrh/ROSE-LINK/issues)
- **Discussions**: [GitHub Discussions](https://github.com/oussrh/ROSE-LINK/discussions)

---

<div align="center">

**Made with love for secure remote access**

[Star this project](https://github.com/oussrh/ROSE-LINK) | [Report a bug](https://github.com/oussrh/ROSE-LINK/issues) | [Suggest a feature](https://github.com/oussrh/ROSE-LINK/issues)

</div>
