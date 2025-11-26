#!/bin/bash
#
# ROSE Link Uninstallation Script
# Removes ROSE Link VPN router from Raspberry Pi
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/rose-link"
USER="rose"
GROUP="rose"

echo -e "${RED}"
echo "╔═══════════════════════════════════════════════════╗"
echo "║      🌹 ROSE Link Uninstallation 🌹               ║"
echo "║   This will remove ROSE Link from your system     ║"
echo "╚═══════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Error: This script must be run as root (sudo)${NC}"
    exit 1
fi

# Confirmation
echo -e "${YELLOW}⚠️  Warning: This will remove all ROSE Link components:${NC}"
echo "   • ROSE Link backend service"
echo "   • ROSE Link watchdog service"
echo "   • Hostapd configuration"
echo "   • dnsmasq configuration"
echo "   • Nginx ROSE Link site"
echo "   • SSL certificates"
echo "   • WireGuard profiles"
echo "   • Firewall (iptables) rules"
echo "   • Installation directory ($INSTALL_DIR)"
echo ""
read -p "Are you sure you want to continue? (yes/NO) " -r
echo
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${YELLOW}Uninstallation cancelled.${NC}"
    exit 0
fi

echo -e "${BLUE}🛑 Stopping services...${NC}"
systemctl stop rose-backend 2>/dev/null || true
systemctl stop rose-watchdog 2>/dev/null || true
systemctl stop wg-quick@wg0 2>/dev/null || true

echo -e "${BLUE}🔧 Disabling services...${NC}"
systemctl disable rose-backend 2>/dev/null || true
systemctl disable rose-watchdog 2>/dev/null || true
systemctl disable wg-quick@wg0 2>/dev/null || true

echo -e "${BLUE}🗑️  Removing systemd service files...${NC}"
rm -f /etc/systemd/system/rose-backend.service
rm -f /etc/systemd/system/rose-watchdog.service
systemctl daemon-reload

echo -e "${BLUE}🔒 Removing sudoers file...${NC}"
rm -f /etc/sudoers.d/rose

echo -e "${BLUE}🌐 Removing Nginx configuration...${NC}"
rm -f /etc/nginx/sites-enabled/roselink
rm -f /etc/nginx/sites-available/roselink
# Restore default site if available
if [ -f /etc/nginx/sites-available/default ]; then
    ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default 2>/dev/null || true
fi
systemctl restart nginx 2>/dev/null || true

echo -e "${BLUE}🔐 Removing SSL certificates...${NC}"
rm -f /etc/nginx/ssl/roselink.key
rm -f /etc/nginx/ssl/roselink.crt
rmdir /etc/nginx/ssl 2>/dev/null || true

echo -e "${BLUE}📶 Removing hostapd configuration...${NC}"
rm -f /etc/hostapd/hostapd.conf
# Restore default hostapd config
sed -i 's|DAEMON_CONF="/etc/hostapd/hostapd.conf"|#DAEMON_CONF=""|' /etc/default/hostapd 2>/dev/null || true
systemctl stop hostapd 2>/dev/null || true
systemctl disable hostapd 2>/dev/null || true

echo -e "${BLUE}🌐 Restoring dnsmasq configuration...${NC}"
if [ -f /etc/dnsmasq.conf.backup ]; then
    mv /etc/dnsmasq.conf.backup /etc/dnsmasq.conf
    echo -e "   ${GREEN}✓ Original dnsmasq.conf restored${NC}"
else
    rm -f /etc/dnsmasq.conf
    echo -e "   ${YELLOW}⚠️  No backup found, dnsmasq.conf removed${NC}"
fi
systemctl stop dnsmasq 2>/dev/null || true
systemctl disable dnsmasq 2>/dev/null || true

echo -e "${BLUE}🔧 Cleaning up dhcpcd configuration...${NC}"
# Remove ROSE Link AP configuration from dhcpcd.conf
if grep -q "# ROSE Link AP Configuration" /etc/dhcpcd.conf 2>/dev/null; then
    # Remove the ROSE Link section
    sed -i '/# ROSE Link AP Configuration/,/^$/d' /etc/dhcpcd.conf
    echo -e "   ${GREEN}✓ dhcpcd.conf cleaned${NC}"
fi

echo -e "${BLUE}🔥 Cleaning up iptables rules...${NC}"
# Flush ROSE Link specific rules
iptables -t nat -F 2>/dev/null || true
iptables -F FORWARD 2>/dev/null || true
# Save clean rules
iptables-save > /etc/iptables/rules.v4 2>/dev/null || true
echo -e "   ${GREEN}✓ iptables rules cleared${NC}"

echo -e "${BLUE}🗑️  Removing WireGuard profiles...${NC}"
read -p "Remove WireGuard profiles in /etc/wireguard/profiles? (y/N) " -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf /etc/wireguard/profiles
    rm -f /etc/wireguard/wg0.conf
    echo -e "   ${GREEN}✓ WireGuard profiles removed${NC}"
else
    echo -e "   ${YELLOW}⚠️  WireGuard profiles kept${NC}"
fi

echo -e "${BLUE}📂 Removing installation directory...${NC}"
if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
    echo -e "   ${GREEN}✓ $INSTALL_DIR removed${NC}"
fi

echo -e "${BLUE}👤 User account cleanup...${NC}"
read -p "Remove the '$USER' user account? (y/N) " -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    userdel -r "$USER" 2>/dev/null || userdel "$USER" 2>/dev/null || true
    echo -e "   ${GREEN}✓ User '$USER' removed${NC}"
else
    echo -e "   ${YELLOW}⚠️  User '$USER' kept${NC}"
fi

echo -e "${BLUE}📦 Package cleanup...${NC}"
echo "The following packages were installed by ROSE Link:"
echo "   hostapd, dnsmasq, wireguard, wireguard-tools"
echo "   iptables-persistent, network-manager"
echo ""
read -p "Remove these packages? (NOT recommended if used by other services) (y/N) " -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    apt-get remove -y hostapd dnsmasq iptables-persistent 2>/dev/null || true
    echo -e "   ${GREEN}✓ Selected packages removed${NC}"
    echo -e "   ${YELLOW}Note: wireguard and network-manager were kept for safety${NC}"
else
    echo -e "   ${YELLOW}⚠️  Packages kept${NC}"
fi

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║      🌹 ROSE Link has been uninstalled 🌹             ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Note: You may need to reboot for all changes to take effect.${NC}"
echo ""
read -p "Reboot now? (y/N) " -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Rebooting...${NC}"
    reboot
fi

echo -e "${GREEN}✅ Uninstallation complete!${NC}"
