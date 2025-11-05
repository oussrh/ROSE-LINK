#!/bin/bash
#
# ROSE Link Installation Script
# Installs and configures ROSE Link VPN router on Raspberry Pi 4
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/rose-link"
USER="rose"
GROUP="rose"

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════╗"
echo "║   🌹 ROSE Link Installation 🌹       ║"
echo "║   Routeur VPN sur Raspberry Pi 4     ║"
echo "╚═══════════════════════════════════════╝"
echo -e "${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Erreur: Ce script doit être exécuté en tant que root (sudo)${NC}"
    exit 1
fi

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo -e "${YELLOW}⚠️  Attention: Ce système ne semble pas être une Raspberry Pi${NC}"
    read -p "Voulez-vous continuer quand même ? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${GREEN}📦 Installation des dépendances système...${NC}"
apt-get update
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    nginx \
    hostapd \
    dnsmasq \
    wireguard \
    wireguard-tools \
    iptables \
    iptables-persistent \
    network-manager \
    iw \
    rfkill

echo -e "${GREEN}👤 Création de l'utilisateur ${USER}...${NC}"
if ! id -u "$USER" &>/dev/null; then
    useradd -r -s /bin/bash -d "$INSTALL_DIR" -m "$USER"
    echo -e "${GREEN}✅ Utilisateur $USER créé${NC}"
else
    echo -e "${YELLOW}⚠️  L'utilisateur $USER existe déjà${NC}"
fi

echo -e "${GREEN}📂 Installation des fichiers...${NC}"
mkdir -p "$INSTALL_DIR"/{backend,web,system}
mkdir -p /etc/wireguard/profiles

# Copy files
cp -r backend/* "$INSTALL_DIR/backend/"
cp -r web/* "$INSTALL_DIR/web/"
cp -r system/* "$INSTALL_DIR/system/"

# Set permissions
chown -R "$USER:$GROUP" "$INSTALL_DIR"
chmod +x "$INSTALL_DIR/system/rose-watchdog.sh"
chmod 755 "$INSTALL_DIR/backend"
chmod 644 "$INSTALL_DIR/backend/main.py"

echo -e "${GREEN}🐍 Configuration de l'environnement Python...${NC}"
python3 -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/backend/requirements.txt"

echo -e "${GREEN}🔧 Configuration du système...${NC}"

# Configure hostapd
cp "$INSTALL_DIR/system/hostapd.conf" /etc/hostapd/hostapd.conf
sed -i 's|#DAEMON_CONF=""|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd || true

# Configure dnsmasq
mv /etc/dnsmasq.conf /etc/dnsmasq.conf.backup 2>/dev/null || true
cp "$INSTALL_DIR/system/dnsmasq.conf" /etc/dnsmasq.conf

# Configure dhcpcd for static IP on wlan1
if ! grep -q "interface wlan1" /etc/dhcpcd.conf; then
    cat "$INSTALL_DIR/system/dhcpcd.conf.append" >> /etc/dhcpcd.conf
fi

# Install sudoers file
cp "$INSTALL_DIR/system/rose-sudoers" /etc/sudoers.d/rose
chmod 440 /etc/sudoers.d/rose

# Install systemd services
cp "$INSTALL_DIR/system/rose-backend.service" /etc/systemd/system/
cp "$INSTALL_DIR/system/rose-watchdog.service" /etc/systemd/system/

echo -e "${GREEN}🔐 Configuration de Nginx (HTTPS)...${NC}"

# Create SSL directory
mkdir -p /etc/nginx/ssl

# Generate self-signed certificate
if [ ! -f /etc/nginx/ssl/roselink.crt ]; then
    openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
        -keyout /etc/nginx/ssl/roselink.key \
        -out /etc/nginx/ssl/roselink.crt \
        -subj "/C=BE/ST=Brussels/L=Brussels/O=ROSE Link/OU=VPN/CN=roselink.local"
    chmod 600 /etc/nginx/ssl/roselink.key
fi

# Install Nginx config
cp "$INSTALL_DIR/system/nginx/roselink" /etc/nginx/sites-available/roselink
ln -sf /etc/nginx/sites-available/roselink /etc/nginx/sites-enabled/roselink
rm -f /etc/nginx/sites-enabled/default

# Test Nginx config
nginx -t

echo -e "${GREEN}🔥 Configuration du pare-feu et du routage...${NC}"

# Enable IP forwarding
sed -i 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/' /etc/sysctl.conf
sysctl -p

# Configure iptables rules
iptables -t nat -F
iptables -F FORWARD

# NAT for VPN (wg0 -> Internet)
iptables -t nat -A POSTROUTING -o wg0 -j MASQUERADE

# Allow forwarding from AP (wlan1) to VPN (wg0)
iptables -A FORWARD -i wlan1 -o wg0 -j ACCEPT
iptables -A FORWARD -i wg0 -o wlan1 -m state --state RELATED,ESTABLISHED -j ACCEPT

# Kill-switch: block forwarding if wg0 is down
iptables -A FORWARD -i wlan1 ! -o wg0 -j REJECT

# Allow forwarding from WAN to VPN (for accessing Belgian LAN)
iptables -A FORWARD -i eth0 -o wg0 -j ACCEPT
iptables -A FORWARD -i wlan0 -o wg0 -j ACCEPT
iptables -A FORWARD -i wg0 -m state --state RELATED,ESTABLISHED -j ACCEPT

# Save iptables rules
iptables-save > /etc/iptables/rules.v4

echo -e "${GREEN}🚀 Activation des services...${NC}"

# Reload systemd
systemctl daemon-reload

# Enable services
systemctl enable rose-backend
systemctl enable rose-watchdog
systemctl enable hostapd
systemctl enable dnsmasq
systemctl enable nginx

# Start services
systemctl restart nginx
systemctl restart dhcpcd
systemctl restart dnsmasq
systemctl restart hostapd
systemctl restart rose-backend

# Note: wg-quick@wg0 will be started after importing a profile
# systemctl enable wg-quick@wg0

echo -e "${GREEN}✅ Installation terminée !${NC}"
echo ""
echo -e "${BLUE}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          🌹 ROSE Link est prêt ! 🌹                   ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}📱 Accès à l'interface Web :${NC}"
echo -e "   • https://roselink.local"
echo -e "   • https://192.168.50.1 (depuis le hotspot)"
echo ""
echo -e "${YELLOW}⚠️  Note: Le certificat SSL est auto-signé.${NC}"
echo -e "   Acceptez l'avertissement de sécurité dans votre navigateur."
echo ""
echo -e "${GREEN}📶 Configuration du Hotspot :${NC}"
echo -e "   • SSID par défaut: ROSE-Link"
echo -e "   • Mot de passe par défaut: RoseLink2024"
echo -e "   • Modifiez-les via l'interface Web !"
echo ""
echo -e "${GREEN}🔐 Prochaines étapes :${NC}"
echo -e "   1. Connectez-vous au hotspot ROSE-Link"
echo -e "   2. Ouvrez https://roselink.local dans votre navigateur"
echo -e "   3. Allez dans l'onglet VPN"
echo -e "   4. Importez votre fichier .conf WireGuard (Fritz!Box)"
echo -e "   5. Le tunnel VPN démarrera automatiquement"
echo ""
echo -e "${GREEN}🎉 Profitez de votre connexion sécurisée vers la Belgique ! 🇧🇪${NC}"
echo ""

# Show service status
echo -e "${BLUE}📊 Statut des services :${NC}"
systemctl --no-pager status rose-backend rose-watchdog hostapd dnsmasq nginx | grep -E "Active:|Loaded:" || true
