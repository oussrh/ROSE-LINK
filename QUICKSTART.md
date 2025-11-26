# 🚀 ROSE Link - Quick Start Guide

Get up and running with ROSE Link in 10 minutes!

> 🧭 **Tip:** Run through the pre-flight checklist below before starting the installer to avoid common setup hiccups.

## 📋 Prerequisites

### Quick Pre-Flight Checklist

- Update your Pi so the installer can fetch dependencies:
  ```bash
  sudo apt update && sudo apt upgrade -y
  ```
- Make sure your Raspberry Pi has Internet access (Ethernet is easiest for first-time setup).
- Enable SSH if you plan to manage the device headlessly (`sudo raspi-config` → Interface Options → SSH).
- Have your WireGuard `.conf` file ready on your laptop or phone for the import step.

### Hardware Requirements
- **Raspberry Pi** (one of the following):
  - Raspberry Pi 5 (recommended - full 5GHz support)
  - Raspberry Pi 4 (recommended - full 5GHz support)
  - Raspberry Pi 3 (supported - 2.4GHz WiFi only)
  - Raspberry Pi Zero 2 W (basic support - light usage)

- **Storage**: microSD card (16GB+) with Raspberry Pi OS
- **Memory**: 512MB RAM minimum, 1GB+ recommended
- **Network**: Ethernet cable (for initial setup)

### Software Requirements
- **OS**: Raspberry Pi OS (Bullseye or Bookworm) or Debian 11/12
- **Architecture**: armhf (32-bit) or arm64 (64-bit)

### What You'll Need
- WireGuard configuration file (.conf) from your Fritz!Box or VPN provider
- A device (laptop/phone) to connect to the hotspot

## ⚡ Installation

### Option 1: One-Line Install (Recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/oussrh/ROSE-LINK/main/install.sh | sudo bash
```

### Option 2: Download and Install

```bash
# Download the installer
wget https://github.com/oussrh/ROSE-LINK/releases/latest/download/rose-link-pro.tar.gz

# Extract
tar -xzf rose-link-pro.tar.gz
cd rose-link

# Install (interactive mode)
sudo bash install.sh

# Or install with custom options
sudo bash install.sh --ssid "MyRouter" --country FR
```

### Option 3: Debian Package (Best for Updates)

```bash
# Download the package
wget https://github.com/oussrh/ROSE-LINK/releases/latest/download/rose-link-pro_0.2.0-1_all.deb

# Install with apt (handles dependencies automatically)
sudo apt install ./rose-link-pro_0.2.0-1_all.deb
```

### Installation Options

The installer supports several command-line options:

| Option | Description |
|--------|-------------|
| `-h, --help` | Show help message |
| `-y, --yes` | Non-interactive mode (accept all defaults) |
| `-f, --force` | Force installation (skip hardware checks) |
| `--ssid NAME` | Set custom WiFi SSID (default: ROSE-Link) |
| `--password PASS` | Set custom WiFi password (min 8 chars) |
| `--country CODE` | Set country code (default: BE) |

**Examples:**
```bash
# Interactive installation
sudo bash install.sh

# Non-interactive with defaults
sudo bash install.sh -y

# Custom SSID and country
sudo bash install.sh --ssid "HomeVPN" --password "MySecure123" --country US

# Force install on non-Pi hardware (for testing)
sudo bash install.sh -f
```

## 🎯 Initial Setup (5 Minutes)

### Step 1: Connect to Hotspot

After installation completes, the Raspberry Pi creates a WiFi hotspot.

**Default credentials:**
- **SSID**: `ROSE-Link` (or your custom name)
- **Password**: Displayed at end of installation (randomly generated for security)

Connect your laptop or phone to this network.

### Step 2: Open Web Interface

Open your browser and navigate to:
- `https://roselink.local` (recommended)
- `https://192.168.50.1` (direct IP)

> ⚠️ **Note**: You'll see a certificate warning (normal for self-signed certificates). Click "Advanced" → "Proceed to roselink.local".

### Step 3: Import VPN Profile

1. Click the **🔐 VPN** tab
2. Click **"Importer un profil WireGuard (.conf)"**
3. Select your `.conf` file from Fritz!Box or VPN provider
4. Click **"Importer et Activer"**

✅ The VPN should connect automatically!

### Step 4: Customize Hotspot (Optional)

1. Click the **📶 Hotspot** tab
2. Configure your preferences:
   - Change SSID (network name)
   - Set a custom password (min. 8 characters)
   - Select country code
   - Choose WiFi channel (if experiencing interference)
3. Click **"Appliquer la configuration"**

The hotspot will restart with your new settings.

## 🧪 Verify Your Setup

### Test 1: Check Your Public IP

From a device connected to the ROSE Link hotspot:

```bash
curl ifconfig.me
```

You should see your VPN exit IP (Belgian IP if using Fritz!Box) 🇧🇪

### Test 2: Verify VPN Connection

```bash
# Ping your home network (Fritz!Box)
ping 192.168.178.1

# Access Fritz!Box web interface
# Open http://192.168.178.1 in your browser
```

### Test 3: Web Interface Status

In the web interface, go to **🔐 VPN** tab. You should see:
- ✅ "VPN actif" (green indicator)
- Endpoint information
- Data transfer statistics (TX/RX)

## 🎉 You're Done!

ROSE Link is now:
- ✅ Creating a secure WiFi hotspot
- ✅ Routing all traffic through your VPN
- ✅ Protecting you with an automatic kill-switch
- ✅ Auto-reconnecting if VPN drops
- ✅ Monitoring connection health

## 📱 Daily Use

### Connect to Hotspot

Simply connect any device to your ROSE Link WiFi:
- All traffic automatically goes through VPN
- Access both Internet and your home network
- No configuration needed on client devices

### Monitor Status

Visit `https://roselink.local` to see:
- WAN connection status (Ethernet/WiFi)
- VPN status and statistics
- Connected clients
- System health (CPU, memory, temperature)

## 🔧 Advanced Configuration

### WiFi WAN Connection (Optional)

If you want to use WiFi instead of Ethernet for Internet:

1. Go to **📡 WiFi WAN** tab
2. Click **"Scanner les réseaux"**
3. Select your network and click **"Se connecter"**
4. Enter the password

The system auto-prioritizes: Ethernet → WiFi → Offline

### Multiple VPN Profiles

1. Go to **🔐 VPN** tab
2. Upload multiple `.conf` files
3. Switch between profiles by clicking **"Activer"**

### Country-Specific WiFi Regulations

Set your country code to ensure WiFi channels comply with local regulations:

```bash
# During installation
sudo bash install.sh --country US

# Or via web interface: Hotspot tab → Country Code
```

## 🐛 Troubleshooting

### Can't Connect to Hotspot

```bash
# SSH into your Raspberry Pi
ssh pi@raspberrypi.local

# Check hostapd status
sudo systemctl status hostapd

# View hostapd logs
sudo journalctl -u hostapd -n 50

# Restart hotspot
sudo systemctl restart hostapd
```

### VPN Not Connecting

```bash
# Check VPN service status
sudo systemctl status wg-quick@wg0

# View VPN logs
sudo journalctl -u wg-quick@wg0 -n 50

# Check WireGuard interface
sudo wg show

# Restart VPN
sudo systemctl restart wg-quick@wg0
```

### No Internet on Connected Devices

```bash
# Check if VPN is up
sudo wg show

# Check IP forwarding
cat /proc/sys/net/ipv4/ip_forward
# Should return: 1

# Check NAT rules
sudo iptables -t nat -L -v

# Check firewall rules
sudo iptables -L FORWARD -v
```

### Web Interface Not Loading

```bash
# Check backend service
sudo systemctl status rose-backend

# Check Nginx
sudo systemctl status nginx

# View backend logs
sudo journalctl -u rose-backend -f

# Test Nginx configuration
sudo nginx -t
```

### Check All Services at Once

```bash
# Quick status check
for svc in rose-backend rose-watchdog hostapd dnsmasq nginx; do
    status=$(systemctl is-active $svc 2>/dev/null || echo "inactive")
    echo "$svc: $status"
done
```

## 🔄 Updating ROSE Link

### If Installed via Script

```bash
cd ~/rose-link
git pull
sudo bash install.sh
```

### If Installed via Debian Package

```bash
# Download new version
wget https://github.com/oussrh/ROSE-LINK/releases/latest/download/rose-link-pro_VERSION_all.deb

# Upgrade
sudo apt install ./rose-link-pro_VERSION_all.deb
```

## 🗑️ Uninstalling

### Interactive Uninstall

```bash
sudo bash uninstall.sh
```

### Quick Uninstall (Keep VPN Profiles)

```bash
sudo bash uninstall.sh -y
```

### Complete Removal

```bash
sudo bash uninstall.sh -y -f
```

### If Installed via Debian Package

```bash
# Remove keeping config
sudo apt remove rose-link-pro

# Remove everything
sudo apt purge rose-link-pro
```

## 📚 More Resources

- [Full Documentation](README.md)
- [Development Guide](DEVELOPMENT.md)
- [API Reference](README.md#-api-rest)
- [Report Issues](https://github.com/oussrh/ROSE-LINK/issues)
- [Discussions](https://github.com/oussrh/ROSE-LINK/discussions)

---

🌹 **Enjoy secure access to your home network from anywhere!**
