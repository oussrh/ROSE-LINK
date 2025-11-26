<div align="center">

<img src="web/Logo.webp" alt="ROSE Link Logo" width="200">

# ROSE Link

**Home VPN Router on Raspberry Pi**

<img src="web/icon.webp" alt="ROSE Link Icon" width="64">

Transform your Raspberry Pi into a professional WiFi router/access point that establishes a secure VPN tunnel to your remote network, allowing you to access local resources and obtain the public IP of your VPN server from anywhere in the world.

![Version](https://img.shields.io/badge/version-0.3.0-blue)
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

### Advanced WireGuard VPN
- Multi-profile: Import and manage multiple VPN configurations
- .conf import: Direct upload of WireGuard files
- Kill-switch: Blocks all traffic if VPN drops (no leaks)
- Watchdog: Automatic monitoring and reconnection
- Detailed status: Handshake, endpoint, data transfer

### Configurable WiFi Hotspot
- Custom SSID: Choose your network name
- WPA2/WPA3 security: WPA3 if hardware supports it
- Country configuration: Channels and power compliant with regulations
- Channel selection: Optimize performance (2.4GHz and 5GHz)
- Connected clients: Real-time counter

### Modern User Interface
- Dark mode: Elegant and eye-friendly interface
- Responsive: Works on desktop, tablet and mobile
- Real-time: Automatic status refresh
- HTTPS: Secure connection (self-signed certificate)
- Bilingual: English and French support

### Enhanced Security
- Backend isolation: API accessible only via Nginx
- Restricted sudoers: Minimal system command access
- Protected files: VPN configurations in mode 600
- iptables kill-switch: Leak protection

---

## Installation

### Method 1: Archive (recommended for testing)

```bash
# Download archive
wget https://github.com/oussrh/ROSE-LINK/releases/latest/download/rose-link-pro.tar.gz

# Extract
tar -xzf rose-link-pro.tar.gz
cd rose-link

# Install
sudo bash install.sh
```

### Method 2: Debian Package (clean)

```bash
# Download package
wget https://github.com/oussrh/ROSE-LINK/releases/latest/download/rose-link-pro_0.2.0-1_all.deb

# Install
sudo apt-get install ./rose-link-pro_0.2.0-1_all.deb
```

### Method 3: APT Repository (production)

```bash
# One-line installation
curl -fsSL https://oussrh.github.io/roselink-repo/install.sh | sudo bash
```

---

## Quick Configuration

### 1. Access the Web Interface

After installation, connect to the default hotspot:
- **SSID**: `ROSE-Link`
- **Password**: `RoseLink2024`

Then open your browser:
- **URL**: `https://roselink.local` or `https://192.168.50.1`

> **Note**: Accept the self-signed certificate warning

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

#### WebSocket (v0.3.0+)
- `WS /api/ws` - Real-time status updates
- `GET /api/ws/status` - WebSocket connection info

#### WiFi WAN
- `POST /api/wifi/scan` - Scan WiFi networks
- `POST /api/wifi/connect` - Connect to network
- `POST /api/wifi/disconnect` - Disconnect

#### VPN
- `GET /api/vpn/status` - VPN status
- `GET /api/vpn/profiles` - List profiles
- `POST /api/vpn/upload` - Upload profile (without activating)
- `POST /api/vpn/import` - Import and activate
- `POST /api/vpn/activate` - Activate existing profile
- `POST /api/vpn/start` - Start VPN
- `POST /api/vpn/stop` - Stop VPN
- `POST /api/vpn/restart` - Restart VPN

#### Hotspot
- `GET /api/hotspot/status` - Hotspot status
- `POST /api/hotspot/apply` - Apply configuration
- `POST /api/hotspot/restart` - Restart hotspot

#### Backup/Restore (v0.3.0+)
- `GET /api/backup/list` - List available backups
- `POST /api/backup/create` - Create new backup
- `POST /api/backup/restore/{filename}` - Restore from backup
- `GET /api/backup/download/{filename}` - Download backup file
- `POST /api/backup/upload` - Upload backup file
- `DELETE /api/backup/{filename}` - Delete backup

#### Speed Test (v0.3.0+)
- `GET /api/speedtest/status` - Check if test running
- `POST /api/speedtest/run` - Start speed test
- `GET /api/speedtest/history` - Get test history
- `GET /api/speedtest/last` - Get last result

#### SSL Certificates (v0.3.0+)
- `GET /api/ssl/status` - Certificate status
- `POST /api/ssl/request` - Request Let's Encrypt certificate
- `POST /api/ssl/renew` - Renew certificates
- `POST /api/ssl/self-signed` - Generate self-signed certificate

#### Settings
- `GET /api/settings/vpn` - Get VPN watchdog settings
- `POST /api/settings/vpn` - Update VPN watchdog settings

#### System
- `GET /api/system/info` - System information (Pi model, RAM, CPU, WiFi)
- `GET /api/system/interfaces` - Detected network interfaces
- `GET /api/system/logs?service=xxx` - Service logs
- `POST /api/system/reboot` - Reboot system

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

### Version 0.2.x (Released)
- [x] Complete i18n support (English & French)
- [x] Mobile-first responsive design for all screen sizes
- [x] Code optimization with comprehensive docstrings and type hints
- [x] Dynamic interface detection (fixed hardcoded wlan0)
- [x] Upgraded to cutting-edge package versions (FastAPI 0.115+, Pydantic 2.10+, htmx 2.0.3)
- [x] Toast notifications and loading spinners
- [x] Accessibility improvements (ARIA labels, semantic HTML)
- [x] API documentation endpoints (/api/docs, /api/redoc)

### Version 0.3.0 (Released)
- [x] WebSocket for real-time status updates (replaces polling)
- [x] Configuration backup/restore (VPN profiles, hotspot config, settings)
- [x] Let's Encrypt SSL certificate option (+ self-signed generation)
- [x] Speed test integration (speedtest-cli, Ookla)
- [x] Prometheus metrics endpoint (/api/metrics)
- [x] Bandwidth usage statistics (per-interface, real-time)

### Version 0.4.0 (In Progress)
- [ ] Email notifications for VPN failures
- [ ] Simple QoS (traffic prioritization)
- [ ] Integrated AdGuard Home (DNS + ad blocking)
- [ ] OpenVPN support in addition to WireGuard
- [ ] Grafana metrics dashboard
- [ ] Connected clients management

### Version 1.0.0 (Future)
- [ ] Ready-to-flash SD image
- [ ] First-time setup wizard
- [ ] Multi-WAN support (load balancing)
- [ ] iOS/Android mobile app
- [ ] Automatic updates
- [ ] Full test suite

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
