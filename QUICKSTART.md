# 🚀 ROSE Link - Quick Start Guide

Get up and running with ROSE Link in 10 minutes!

## 📋 Prerequisites

- ✅ Raspberry Pi 4 (2 GB or more)
- ✅ microSD card with Raspberry Pi OS (32 or 64-bit)
- ✅ Ethernet cable (for initial setup)
- ✅ WireGuard configuration file (.conf) from your Fritz!Box

## ⚡ Installation (Choose One Method)

### Option 1: One-Line Install (Easiest)

```bash
curl -fsSL https://raw.githubusercontent.com/USERNAME/ROSE-LINK/main/install.sh | sudo bash
```

### Option 2: Download and Install

```bash
# Download
wget https://github.com/USERNAME/ROSE-LINK/releases/latest/download/rose-link-pro.tar.gz

# Extract
tar -xzf rose-link-pro.tar.gz
cd rose-link

# Install
sudo bash install.sh
```

### Option 3: Debian Package

```bash
wget https://github.com/USERNAME/ROSE-LINK/releases/latest/download/rose-link-pro_0.1.0-1_all.deb
sudo apt install ./rose-link-pro_0.1.0-1_all.deb
```

## 🎯 Initial Setup (5 Minutes)

### Step 1: Connect to Hotspot

After installation, the Raspberry Pi creates a WiFi hotspot:

- **SSID**: `ROSE-Link`
- **Password**: `RoseLink2024`

Connect your laptop/phone to this network.

### Step 2: Open Web Interface

Open your web browser and go to:
- `https://roselink.local` (recommended)
- or `https://192.168.50.1`

⚠️ You'll see a certificate warning (normal for self-signed cert). Click "Advanced" → "Proceed to roselink.local".

### Step 3: Configure VPN

1. Click the **🔐 VPN** tab
2. Click **"Importer un profil WireGuard (.conf)"**
3. Select your `.conf` file from Fritz!Box
4. Click **"Importer et Activer"**

✅ The VPN should connect automatically!

### Step 4: Customize Hotspot (Optional)

1. Click the **📶 Hotspot** tab
2. Change:
   - SSID (network name)
   - Password (min. 8 characters)
   - Country code
   - Channel
3. Click **"Appliquer la configuration"**

The hotspot will restart with your new settings.

## 🧪 Test Your Setup

### Test 1: Check Your IP

From a device connected to the ROSE Link hotspot:

```bash
curl ifconfig.me
```

You should see a **Belgian IP address**! 🇧🇪

### Test 2: Access Belgian Network

```bash
# Ping your Fritz!Box
ping 192.168.178.1

# Access Fritz!Box web interface
# Open http://192.168.178.1 in your browser
```

### Test 3: Check VPN Status

In the web interface, go to **🔐 VPN** tab. You should see:
- ✅ "VPN actif" (green indicator)
- Endpoint information
- Data transfer statistics

## 🎉 You're Done!

ROSE Link is now:
- ✅ Creating a secure WiFi hotspot
- ✅ Routing all traffic through Belgium
- ✅ Protecting you with a kill-switch
- ✅ Auto-reconnecting if VPN drops

## 📱 Daily Use

### Connect to Hotspot

Simply connect to your ROSE Link WiFi:
- All traffic automatically goes through VPN
- Access both Internet and Belgian local network
- No configuration needed on your devices

### Monitor Status

Open `https://roselink.local` to see:
- WAN connection status
- VPN status and data transfer
- Connected clients
- System health

## 🔧 Advanced Setup

### Connect WiFi WAN (Optional)

If you want to use WiFi instead of Ethernet:

1. Go to **📡 WiFi WAN** tab
2. Click **"Scanner les réseaux"**
3. Click **"Se connecter"** next to your network
4. Enter password

The system will auto-failover: Ethernet → WiFi → No connection.

### Add More VPN Profiles

1. Go to **🔐 VPN** tab
2. Upload multiple `.conf` files
3. Switch between profiles by clicking **"Activer"**

### Change Hotspot Settings

Go to **📶 Hotspot** tab anytime to:
- Change SSID/password
- Select different channel (if WiFi congested)
- Switch country code
- Enable WPA3 (if supported)

## 🐛 Troubleshooting

### Can't Connect to Hotspot

```bash
# SSH into Raspberry Pi
ssh pi@raspberrypi.local

# Check hostapd
sudo systemctl status hostapd

# Restart if needed
sudo systemctl restart hostapd
```

### VPN Not Connecting

```bash
# Check VPN status
sudo systemctl status wg-quick@wg0

# View logs
journalctl -u wg-quick@wg0 -n 50

# Restart VPN
sudo systemctl restart wg-quick@wg0
```

### No Internet on Clients

```bash
# Check if VPN is up
sudo wg show

# Check IP forwarding
cat /proc/sys/net/ipv4/ip_forward
# Should show: 1

# Check iptables
sudo iptables -t nat -L -v
```

### Web Interface Not Loading

```bash
# Check backend
sudo systemctl status rose-backend

# Check nginx
sudo systemctl status nginx

# View logs
journalctl -u rose-backend -f
```

## 📚 Next Steps

- Read the [full README](README.md) for advanced features
- Check the [API documentation](README.md#-api-rest)
- Join discussions on GitHub
- Star the project if you find it useful! ⭐

## 🆘 Get Help

- 📖 [Full Documentation](README.md)
- 🐛 [Report Issues](https://github.com/USERNAME/ROSE-LINK/issues)
- 💬 [Discussions](https://github.com/USERNAME/ROSE-LINK/discussions)

---

🌹 **Enjoy secure access to your Belgian network from anywhere!**
