<div align="center">

<img src="web/Logo.webp" alt="ROSE Link Logo" width="200">

# ROSE Link

**Home VPN Router on Raspberry Pi**

<img src="web/icon.webp" alt="ROSE Link Icon" width="64">

Transform your Raspberry Pi into a professional WiFi router/access point that establishes a secure VPN tunnel to your remote network, allowing you to access local resources and obtain the public IP of your VPN server from anywhere in the world.

![Version](https://img.shields.io/badge/version-1.6.4-blue)
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
📱 Device ── WiFi ──▶ 🍓 ROSE Link (Pi) ── WireGuard ──▶ 🔐 VPN Server ──▶ 🌍 Internet
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

### Grafana Monitoring Dashboard
- **Native installation**: Runs directly on Raspberry Pi (no Docker required)
- **Docker option**: Also available via Docker Compose for development
- Status overview: VPN, WAN, Hotspot, Clients, Uptime, Temperature
- System resources: CPU, Memory, Disk gauges and history
- Network traffic: Throughput, packets, total traffic per interface
- Prometheus alerts: VPN/WAN down, high CPU temp, low disk space
- Resource-optimized: Memory/CPU limits for Raspberry Pi

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

### Method 1: APT Repository (Recommended)

```bash
# Quick setup - adds repository and installs
curl -sSL https://oussrh.github.io/ROSE-LINK/install.sh | sudo bash
sudo apt install rose-link
```

Or manually:
```bash
# Add GPG key
curl -fsSL https://oussrh.github.io/ROSE-LINK/gpg.key | sudo gpg --dearmor -o /usr/share/keyrings/rose-link.gpg

# Add repository
echo "deb [arch=arm64,armhf signed-by=/usr/share/keyrings/rose-link.gpg] https://oussrh.github.io/ROSE-LINK stable main" | sudo tee /etc/apt/sources.list.d/rose-link.list

# Install
sudo apt update
sudo apt install rose-link
```

### Method 2: One-Line Install

```bash
curl -fsSL https://raw.githubusercontent.com/oussrh/ROSE-LINK/main/install.sh | sudo bash
```

### Method 3: Download and Install

```bash
# Download archive
wget https://github.com/oussrh/ROSE-LINK/releases/latest/download/rose-link.tar.gz

# Extract and install
tar -xzf rose-link.tar.gz
cd rose-link
sudo bash install.sh

# Or with custom options
sudo bash install.sh --ssid "MyVPN" --country US
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

## Monitoring Stack (Optional)

ROSE Link includes a built-in Grafana + Prometheus monitoring stack optimized for Raspberry Pi. The monitoring is **included in the package** but **not enabled by default** to keep the system lightweight.

### Enable Monitoring

After installing ROSE Link, enable monitoring with a single command:

```bash
# Enable monitoring (downloads and configures Prometheus + Grafana)
sudo rose-monitoring enable

# Or with custom Grafana password
sudo GRAFANA_PASSWORD=MySecurePass rose-monitoring enable
```

### Monitoring Commands

```bash
rose-monitoring status      # Check monitoring status
sudo rose-monitoring enable   # Install and enable monitoring
sudo rose-monitoring disable  # Stop services (keeps installed)
sudo rose-monitoring restart  # Restart all monitoring services
sudo rose-monitoring uninstall # Completely remove monitoring
```

### What Gets Installed

| Component | Version | Port | Purpose |
|-----------|---------|------|---------|
| Prometheus | 2.47.0 | 9090 | Metrics collection & storage |
| Node Exporter | 1.6.1 | 9100 | System metrics (CPU, RAM, disk) |
| Grafana | Latest | 3000 | Dashboard visualization |

### Access Dashboards

After enabling:
- **Grafana**: `https://roselink.local/grafana/` or `http://192.168.50.1:3000`
- **Prometheus**: `http://192.168.50.1:9090`

Default Grafana credentials:
- Username: `admin`
- Password: `roselink` (or your custom password)

### Pre-configured Alerts

The monitoring stack includes alerts for:
- VPN disconnected (critical)
- WAN disconnected (critical)
- High CPU temperature > 70°C (warning) / > 80°C (critical)
- High memory usage > 85% (warning) / > 95% (critical)
- Low disk space > 80% (warning) / > 95% (critical)
- Hotspot inactive (warning)
- ROSE Link backend down (critical)

### Resource Limits

Optimized for Raspberry Pi with strict resource limits:
- Prometheus: max 256MB RAM, 50% CPU
- Node Exporter: max 64MB RAM, 20% CPU
- Data retention: 15 days (saves disk space)

### Requirements

- Raspberry Pi 4 or 5 recommended (1GB+ RAM)
- ~500MB additional disk space
- Internet connection (to download Prometheus/Grafana on first enable)

### Docker Alternative (Development)

For development or systems with more resources, you can use the Docker Compose stack instead:

```bash
cd monitoring
docker-compose up -d
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

## Device Compatibility

ROSE Link intelligently detects your hardware and adapts its configuration accordingly. The key factors are:

- **WiFi Interfaces**: Single vs Dual WiFi (determines if WiFi WAN is available)
- **Ethernet Port**: Required for single-WiFi devices, optional for dual-WiFi
- **WiFi Bands**: 2.4GHz only vs Dual-band (2.4GHz + 5GHz)

### Compatibility Matrix

#### Raspberry Pi Devices (Officially Supported)

| Device | WiFi Interfaces | Ethernet | WiFi WAN | Hotspot Band | Support Level |
|--------|----------------|----------|----------|--------------|---------------|
| **Raspberry Pi 5** | 1 (Dual-band) | Gigabit | ❌ Ethernet only | 5GHz / 2.4GHz | ⭐⭐⭐⭐⭐ Full |
| **Raspberry Pi 4 Model B** | 1 (Dual-band) | Gigabit | ❌ Ethernet only | 5GHz / 2.4GHz | ⭐⭐⭐⭐⭐ Full |
| **Raspberry Pi 4 + USB WiFi** | 2 | Gigabit | ✅ Yes | 5GHz / 2.4GHz | ⭐⭐⭐⭐⭐ Full |
| **Raspberry Pi 3 Model B+** | 1 (2.4GHz only) | 100Mbps | ❌ Ethernet only | 2.4GHz | ⭐⭐⭐ Limited |
| **Raspberry Pi 3 Model B** | 1 (2.4GHz only) | 100Mbps | ❌ Ethernet only | 2.4GHz | ⭐⭐⭐ Limited |
| **Raspberry Pi Zero 2 W** | 1 (2.4GHz only) | ❌ None | ❌ USB Ethernet req. | 2.4GHz | ⭐⭐ Basic |
| **Raspberry Pi 400** | 1 (Dual-band) | Gigabit | ❌ Ethernet only | 5GHz / 2.4GHz | ⭐⭐⭐⭐ Good |
| **Raspberry Pi CM4 + IO Board** | 1 (Dual-band) | Gigabit | ❌ Ethernet only | 5GHz / 2.4GHz | ⭐⭐⭐⭐⭐ Full |

#### Other ARM Single-Board Computers (Community Tested)

| Device | WiFi Interfaces | Ethernet | WiFi WAN | Hotspot Band | Support Level |
|--------|----------------|----------|----------|--------------|---------------|
| **Orange Pi 5** | 1 (Dual-band) | Gigabit | ❌ Ethernet only | 5GHz / 2.4GHz | ⭐⭐⭐⭐ Good* |
| **Banana Pi M5** | 1 (Dual-band) | Gigabit | ❌ Ethernet only | 5GHz / 2.4GHz | ⭐⭐⭐⭐ Good* |
| **ODROID-C4** | ❌ None | Gigabit | ❌ USB WiFi req. | USB WiFi | ⭐⭐⭐ Limited* |
| **Rock Pi 4** | 1 (Dual-band) | Gigabit | ❌ Ethernet only | 5GHz / 2.4GHz | ⭐⭐⭐⭐ Good* |
| **Libre Computer Le Potato** | ❌ None | 100Mbps | ❌ USB WiFi req. | USB WiFi | ⭐⭐⭐ Limited* |
| **Khadas VIM3** | 1 (Dual-band) | Gigabit | ❌ Ethernet only | 5GHz / 2.4GHz | ⭐⭐⭐⭐ Good* |
| **NanoPi R4S** | ❌ None | Dual Gigabit | ❌ USB WiFi req. | USB WiFi | ⭐⭐⭐⭐ Good* |
| **BeagleBone Black** | ❌ None | 100Mbps | ❌ USB WiFi req. | USB WiFi | ⭐⭐ Basic* |

> **\*** Community tested - may require manual configuration. These devices must run Debian-based Linux (Armbian, DietPi, etc.) and may need driver installation for WiFi chipsets.

### Understanding Single vs Dual WiFi

#### Single WiFi Interface (Most Common)
Most Raspberry Pi models have **only one WiFi interface**. In this configuration:
- The WiFi is **reserved for the hotspot** (Access Point mode)
- Internet connection **must come from Ethernet** (RJ45)
- WiFi WAN scanning is **automatically disabled** in the web interface

```
🌐 Internet ── Ethernet ──▶ 🍓 ROSE Link ── WiFi Hotspot ──▶ 📱 Your Devices
                                   │
                                   └── WireGuard VPN ──▶ 🔐 VPN Server
```

#### Dual WiFi Interface (With USB Adapter)
Adding a USB WiFi adapter gives you **two WiFi interfaces**:
- One WiFi for **WAN connection** (connects to your existing WiFi)
- One WiFi for **Hotspot** (creates the ROSE-Link network)
- Ethernet becomes **optional** (but still prioritized if connected)

```
🌐 Internet ── WiFi WAN ──▶ 🍓 ROSE Link ── WiFi Hotspot ──▶ 📱 Your Devices
                                   │
                                   └── WireGuard VPN ──▶ 🔐 VPN Server
```

### Recommended Configurations

#### Best Performance (Recommended)
- **Raspberry Pi 5** or **Raspberry Pi 4** (4GB RAM)
- **Ethernet connection** for WAN (most stable)
- **5GHz hotspot** for faster client connections
- **Active cooling** (fan or heatsink)

#### Budget Option
- **Raspberry Pi 3 Model B+**
- **Ethernet connection** required
- **2.4GHz hotspot** only
- Suitable for 1-5 devices, light usage

#### Portable/Travel Setup
- **Raspberry Pi 4** + USB WiFi adapter
- **WiFi WAN** (connect to hotel/cafe WiFi)
- **USB-C power bank** compatible
- No Ethernet required

### Hardware Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **RAM** | 512 MB | 2 GB+ |
| **Storage** | 8 GB microSD | 32 GB Class A2 |
| **Power** | 5V 2.5A | 5V 3A (5V 5A for Pi 5) |
| **OS** | Raspberry Pi OS Lite | Raspberry Pi OS (64-bit) |
| **Debian** | Bullseye (11) | Bookworm (12) / Trixie (13) |

### Automatic Hardware Detection

ROSE Link automatically detects and adapts to your hardware:
- **Raspberry Pi model** and generation
- **Number of WiFi interfaces** (single vs dual)
- **WiFi capabilities** (2.4GHz only, 5GHz, 802.11ac/ax)
- **Ethernet availability** and link status
- **System resources** (RAM, disk space, CPU temperature)

When a single WiFi interface is detected:
- WiFi WAN options are **hidden** in the web interface
- Setup wizard shows an **"Ethernet Required"** notice
- Installation displays a clear warning about the limitation

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

### Version 1.6.4 (Current - Latest)
- [x] **AdGuard Home v0.107+ Support**: Updated configuration schema for latest AdGuard
- [x] **DNS Resolution Fix**: System DNS now properly configured for VPN hostname resolution
- [x] **dnsmasq/AdGuard Integration**: Port conflict resolution and proper upstream DNS forwarding

### Version 1.6.0 - 1.6.3
- [x] **Single WiFi Device Detection**: Smart detection hides WiFi WAN on single-interface devices
- [x] **Extended VPN File Support**: Import .conf, .wg, .wireguard, .vpn files
- [x] **Expanded Countries List**: 40+ countries with region-appropriate WiFi regulations
- [x] **Pydantic/FastAPI Fix**: Resolved UploadFile compatibility issues
- [x] **resolvconf Dependency**: Added openresolv for WireGuard DNS management
- [x] **UX Improvements**: Reboot/restart confirmation buttons, wizard skip button fix

### Version 1.5.x
- [x] **AdGuard UI Fixes**: Buttons properly hidden when not installed
- [x] **VPN UI Improvements**: Better error handling and button states
- [x] **FastAPI Response Model Fixes**: Return type validation corrections

### Version 1.3.x
- [x] **AdGuard Home Integration**: New "Ad Blocker" tab in web UI
  - Real-time protection status and controls (enable/disable/restart)
  - Blocking statistics dashboard (DNS queries, blocked count, block rate)
  - Top blocked domains and clients lists
  - DNS query log viewer
- [x] **Dynamic Version System**: Version fetched from single `VERSION` file
- [x] **Single-WiFi Hotspot Fix**: Fixed hotspot on Pi 3B/Zero 2W with Ethernet

### Version 1.2.x
- [x] **Grafana Monitoring Dashboard**: Complete monitoring stack with Docker Compose
  - Grafana + Prometheus + Node Exporter
  - Status overview, system resources, network traffic panels
  - Template variables for interface/instance filtering
  - Pre-configured Prometheus alert rules
- [x] **E2E Test Improvements**: Comprehensive Playwright tests
- [x] **Accessibility Enhancements**: Keyboard navigation, ARIA labels

### Version 1.0.0 - 1.1.0 (Production Ready)
- [x] **AdGuard Home Integration**: DNS-level ad blocking with statistics
- [x] **OpenVPN Support**: In addition to WireGuard (.ovpn file import)
- [x] **Connected Clients Management**: Track, name, block/unblock devices
- [x] **Simple QoS**: VPN traffic prioritization
- [x] **First-Time Setup Wizard**: Guided initial configuration
- [x] Performance metrics endpoint (`/api/metrics/performance`)
- [x] Rate limiting for API abuse protection

### Previous Releases (v0.x)
- [x] WebSocket for real-time status updates
- [x] Configuration backup/restore
- [x] Let's Encrypt SSL certificate option
- [x] Speed test integration
- [x] Prometheus metrics endpoint
- [x] Complete i18n support (English & French)
- [x] Mobile-first responsive design

### Future Releases
- [ ] Email notifications for VPN failures
- [ ] Full QoS profiles (Gaming, Streaming, Work)
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
