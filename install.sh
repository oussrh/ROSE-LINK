#!/bin/bash
#
# ROSE Link Installation Script
# Installs and configures ROSE Link VPN router on Raspberry Pi
# Supports: Raspberry Pi 3, 4, 5, Zero 2W
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

# Hardware detection variables
PI_MODEL=""
PI_VERSION=""
PI_RAM_MB=0
PI_ARCH=""
WIFI_BUILTIN=""
WIFI_USB=""
WIFI_AP_INTERFACE=""
WIFI_WAN_INTERFACE=""
ETH_INTERFACE=""

# ASCII Art Banner - ROSE Link Logo
echo -e "${RED}"
cat << 'ROSE_LOGO'

                                       ####
                                      #######
                                    ###########
                                  ####### #######
                                 #######   ########
                               #######       ########
                             #######           #######
                           #######               #######
            ####################                  ####################
           ######################                 ######################
           ############# ############          ########## # ############
           #####             ###########   ##########              #####
           #####                 #################                 #####
           #####   ####              #########              ####   #####
           #####   ########      ##########             ########   #####          ####################                ################                ################       #######################
           #####    ####################             ##########    #####          #######################           #####################           #####################    #######################
           #####        #############             ##########       #####          #########################       #########################       ######################     #######################
           #####          ###########         ############         #####          #######          ########      ##########       ##########      ########        #####      #######
           #####          ##############   ###############         #####          #######          ########   #########             ########     ########                   #######
           #####          #####   ################   #####         #####          #######          ########   ########               ########    ##########                 #######
           #####          #####      ##########      #####         #####          #######          ########  ########                ########    ################           #####################
           #####          #####         ###          #####         #####          #######         ########   ########                 #######      #################        #####################
           #####          #####                      #####         #####          #########################   ########                 #######         #################     #####################
           #####          #####                      #####         #####          #######################      #######                ########               ############    #######
           #####          #####                      #####         #####          #####################        ########               ########                  #########    #######
           #####          #####                      #####         #####          #####################         #########           #########     ####           ########    #######
           #####          #####                      #####         #####          #######       #######         ##########       ##########     #########      #########    #######
           #####          #####                      #####         #####          #######        ########        #########################     ########################     #######################
           #######        #####                      #####       #######          #######         ########         #####################         #####################      #######################
             #######      ######                   #######     #######            #######          ########           ###############                ##############         #######################
               #######     #######               #######     #######
                 #######     #######           #######     #######
                   #######     #######       #######     #######                                          #####
                     ##########   #######  #######     #######                                           #######                                  #######
                       #####################################                      #######               #######                                  #######
                         #################################                        #######                ######                                  #######
                                       #####                                      #######                                                        #######
           #####                       #####                        #####         #######               #######      #######    ######           #######        ########
           #########                   #####                    #########         #######               #######      ####### #############       #######      ########
           ##############              #####               ##############         #######               #######      ######################      #######    #########
           ####  ############          #####          ############# #####         #######               #######      #######################     #######  #########
           ####      ###########       #####       ###########      #####         #######               #######      ########       ########     ####### ########
           ####           #######      #####      ########          #####         #######               #######      #######         #######     ###############
           ####              ######    #####     #####              #####         #######               #######      #######         #######     ################
           #####              ######   #####    #####              ######         #######               #######      #######         #######     #################
           #######             ######  #####  ######             #######          #######               #######      #######         #######     ######### #########
             #######            ###### ##### ######             ######            ####################   #######      #######         #######     #######    #########
               ######   #####     ################    ######  #######             ####################   #######      #######         #######     #######     #########
                 ######  #####     ##############    #####  #######               ####################   #######      #######         #######     #######       ########
                  #############     ###########     #############                 ####################   #######      #######         #######     #######       #########
                    #############    #########   ##############
                      ##############  #######  ##############
                              ######## ##### ########
                                 #################
                                   ############
                                      #######
                                       #####
                                       #####
                                       #####
                                       #####
                                       ####
                                       #####
                                       ####
                                       ####
                                       ####
                                       ####
ROSE_LOGO
echo -e "${NC}"
echo ""
echo -e "${BLUE}╔═════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                               Home VPN Router for Raspberry Pi (3/4/5/Zero 2W) - Version 0.2.0                                                         ║${NC}"
echo -e "${BLUE}╚═════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ===== Hardware Detection Functions =====

detect_pi_model() {
    echo -e "${CYAN}🔍 Détection du matériel Raspberry Pi...${NC}"

    if [ -f /proc/device-tree/model ]; then
        PI_MODEL=$(cat /proc/device-tree/model | tr -d '\0')
        echo -e "   Modèle détecté: ${GREEN}$PI_MODEL${NC}"

        case "$PI_MODEL" in
            *"Raspberry Pi 5"*)
                PI_VERSION=5
                echo -e "   ${GREEN}✓ Raspberry Pi 5 - Support complet${NC}"
                ;;
            *"Raspberry Pi 4"*)
                PI_VERSION=4
                echo -e "   ${GREEN}✓ Raspberry Pi 4 - Support complet${NC}"
                ;;
            *"Raspberry Pi 3"*)
                PI_VERSION=3
                echo -e "   ${GREEN}✓ Raspberry Pi 3 - Support avec limitations${NC}"
                echo -e "   ${YELLOW}⚠️  Pi 3: WiFi 2.4GHz uniquement, performances réduites${NC}"
                ;;
            *"Raspberry Pi Zero 2"*)
                PI_VERSION="zero2"
                echo -e "   ${GREEN}✓ Raspberry Pi Zero 2 W - Support basique${NC}"
                echo -e "   ${YELLOW}⚠️  Zero 2W: Ressources limitées, usage léger recommandé${NC}"
                ;;
            *"Raspberry Pi"*)
                PI_VERSION="other"
                echo -e "   ${YELLOW}⚠️  Modèle Pi non testé - installation possible${NC}"
                ;;
            *)
                PI_VERSION="unknown"
                ;;
        esac
    else
        PI_VERSION="unknown"
    fi

    # Detect architecture
    PI_ARCH=$(uname -m)
    echo -e "   Architecture: ${GREEN}$PI_ARCH${NC}"
}

detect_system_resources() {
    echo -e "${CYAN}🔍 Vérification des ressources système...${NC}"

    # Check RAM
    PI_RAM_MB=$(free -m | awk '/^Mem:/{print $2}')
    echo -e "   RAM totale: ${GREEN}${PI_RAM_MB} MB${NC}"

    if [ "$PI_RAM_MB" -lt 512 ]; then
        echo -e "   ${RED}❌ Erreur: Minimum 512MB de RAM requis${NC}"
        exit 1
    elif [ "$PI_RAM_MB" -lt 1024 ]; then
        echo -e "   ${YELLOW}⚠️  Avertissement: 1GB+ de RAM recommandé pour de bonnes performances${NC}"
    elif [ "$PI_RAM_MB" -ge 2048 ]; then
        echo -e "   ${GREEN}✓ RAM suffisante pour usage optimal${NC}"
    fi

    # Check disk space
    DISK_FREE_MB=$(df -m /opt 2>/dev/null | tail -1 | awk '{print $4}')
    if [ -z "$DISK_FREE_MB" ]; then
        DISK_FREE_MB=$(df -m / | tail -1 | awk '{print $4}')
    fi
    echo -e "   Espace disque libre: ${GREEN}${DISK_FREE_MB} MB${NC}"

    if [ "$DISK_FREE_MB" -lt 300 ]; then
        echo -e "   ${RED}❌ Erreur: Minimum 300MB d'espace libre requis${NC}"
        exit 1
    elif [ "$DISK_FREE_MB" -lt 500 ]; then
        echo -e "   ${YELLOW}⚠️  Avertissement: 500MB+ d'espace libre recommandé${NC}"
    fi

    # Check CPU temperature (if available)
    if [ -f /sys/class/thermal/thermal_zone0/temp ]; then
        CPU_TEMP=$(($(cat /sys/class/thermal/thermal_zone0/temp) / 1000))
        echo -e "   Température CPU: ${GREEN}${CPU_TEMP}°C${NC}"

        if [ "$CPU_TEMP" -gt 80 ]; then
            echo -e "   ${RED}⚠️  Température élevée! Refroidissement recommandé${NC}"
        elif [ "$CPU_TEMP" -gt 70 ]; then
            echo -e "   ${YELLOW}⚠️  Température modérée - surveillance conseillée${NC}"
        fi
    fi
}

detect_network_interfaces() {
    echo -e "${CYAN}🔍 Détection des interfaces réseau...${NC}"

    # Detect Ethernet interface (eth0 or end0 on Pi 5)
    for iface in eth0 end0 enp1s0; do
        if [ -d "/sys/class/net/$iface" ]; then
            ETH_INTERFACE=$iface
            echo -e "   Interface Ethernet: ${GREEN}$ETH_INTERFACE${NC}"
            break
        fi
    done

    if [ -z "$ETH_INTERFACE" ]; then
        echo -e "   ${YELLOW}⚠️  Aucune interface Ethernet détectée${NC}"
    fi

    # Detect WiFi interfaces
    echo -e "   ${CYAN}Interfaces WiFi:${NC}"

    for iface in $(ls /sys/class/net/ 2>/dev/null); do
        if [ -d "/sys/class/net/$iface/wireless" ]; then
            # Determine if built-in or USB
            DEVICE_PATH=$(readlink -f /sys/class/net/$iface/device 2>/dev/null || echo "")
            DRIVER=$(basename "$(readlink /sys/class/net/$iface/device/driver 2>/dev/null)" 2>/dev/null || echo "unknown")

            if [[ "$DEVICE_PATH" == *"mmc"* ]] || [[ "$DEVICE_PATH" == *"soc"* ]]; then
                WIFI_BUILTIN=$iface
                echo -e "      ${GREEN}$iface${NC} (intégré, driver: $DRIVER)"
            else
                WIFI_USB=$iface
                echo -e "      ${GREEN}$iface${NC} (USB, driver: $DRIVER)"
            fi
        fi
    done

    # Determine interface assignment
    if [ -n "$WIFI_USB" ] && [ -n "$WIFI_BUILTIN" ]; then
        # Both available: USB for AP (usually better), built-in for WAN
        WIFI_AP_INTERFACE=$WIFI_USB
        WIFI_WAN_INTERFACE=$WIFI_BUILTIN
        echo -e "   ${GREEN}✓ Configuration optimale: 2 interfaces WiFi${NC}"
        echo -e "      AP (Hotspot): $WIFI_AP_INTERFACE (USB)"
        echo -e "      WAN Client: $WIFI_WAN_INTERFACE (intégré)"
    elif [ -n "$WIFI_BUILTIN" ]; then
        # Only built-in: use for AP, WAN via Ethernet preferred
        WIFI_AP_INTERFACE=$WIFI_BUILTIN
        WIFI_WAN_INTERFACE=$WIFI_BUILTIN
        echo -e "   ${YELLOW}⚠️  Une seule interface WiFi - mode mixte AP+Client${NC}"
        echo -e "      AP (Hotspot): $WIFI_AP_INTERFACE"
        echo -e "      WAN WiFi: $WIFI_WAN_INTERFACE (si Ethernet indisponible)"
    elif [ -n "$WIFI_USB" ]; then
        # Only USB: use for AP
        WIFI_AP_INTERFACE=$WIFI_USB
        WIFI_WAN_INTERFACE=""
        echo -e "   ${YELLOW}⚠️  Uniquement WiFi USB détecté${NC}"
        echo -e "      AP (Hotspot): $WIFI_AP_INTERFACE"
    else
        echo -e "   ${RED}❌ Aucune interface WiFi détectée!${NC}"
        echo -e "   ${YELLOW}   Vérifiez que le WiFi n'est pas désactivé (rfkill)${NC}"
        # Check rfkill
        if command -v rfkill &> /dev/null; then
            rfkill list wifi
        fi
    fi
}

detect_wifi_capabilities() {
    echo -e "${CYAN}🔍 Détection des capacités WiFi...${NC}"

    if [ -n "$WIFI_AP_INTERFACE" ]; then
        # Check if 5GHz is supported
        WIFI_5GHZ_SUPPORT=false
        if iw list 2>/dev/null | grep -q "5[0-9][0-9][0-9] MHz"; then
            WIFI_5GHZ_SUPPORT=true
            echo -e "   ${GREEN}✓ Support 5GHz détecté${NC}"
        else
            echo -e "   ${YELLOW}⚠️  5GHz non supporté - 2.4GHz uniquement${NC}"
        fi

        # Check for 802.11ac support
        if iw list 2>/dev/null | grep -q "VHT"; then
            echo -e "   ${GREEN}✓ Support 802.11ac (WiFi 5) détecté${NC}"
        fi

        # Check for 802.11ax support (WiFi 6)
        if iw list 2>/dev/null | grep -q "HE"; then
            echo -e "   ${GREEN}✓ Support 802.11ax (WiFi 6) détecté${NC}"
        fi

        # Check AP mode support
        if iw list 2>/dev/null | grep -q "* AP"; then
            echo -e "   ${GREEN}✓ Mode Point d'Accès (AP) supporté${NC}"
        else
            echo -e "   ${RED}❌ Mode AP non supporté par cette interface!${NC}"
        fi
    fi
}

# ===== Main Detection =====

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Erreur: Ce script doit être exécuté en tant que root (sudo)${NC}"
    exit 1
fi

# Run hardware detection
detect_pi_model
detect_system_resources
detect_network_interfaces
detect_wifi_capabilities

echo ""

# Validate hardware
if [ "$PI_VERSION" = "unknown" ]; then
    echo -e "${YELLOW}⚠️  Attention: Ce système ne semble pas être une Raspberry Pi${NC}"
    read -p "Voulez-vous continuer quand même ? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Validate WiFi
if [ -z "$WIFI_AP_INTERFACE" ]; then
    echo -e "${RED}❌ Erreur: Aucune interface WiFi disponible pour le hotspot${NC}"
    echo -e "${YELLOW}   Solutions possibles:${NC}"
    echo -e "   1. Débloquer le WiFi: sudo rfkill unblock wifi"
    echo -e "   2. Connecter un dongle WiFi USB"
    echo -e "   3. Vérifier que le module WiFi est chargé"
    exit 1
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

# Generate interface configuration file for other services
echo -e "${GREEN}📝 Génération de la configuration des interfaces...${NC}"
cat > "$INSTALL_DIR/system/interfaces.conf" << EOF
# ROSE Link Interface Configuration
# Auto-generated by install.sh

# Detected interfaces
ETH_INTERFACE=$ETH_INTERFACE
WIFI_AP_INTERFACE=$WIFI_AP_INTERFACE
WIFI_WAN_INTERFACE=$WIFI_WAN_INTERFACE

# Pi model info
PI_MODEL="$PI_MODEL"
PI_VERSION=$PI_VERSION
EOF
chown "$USER:$GROUP" "$INSTALL_DIR/system/interfaces.conf"

# Configure hostapd with detected interface
echo -e "${GREEN}📶 Configuration du hotspot WiFi...${NC}"

# Determine WiFi mode based on capabilities
HOSTAPD_HW_MODE="g"
HOSTAPD_CHANNEL="6"
HOSTAPD_EXTRA=""

if [ "$WIFI_5GHZ_SUPPORT" = true ]; then
    echo -e "   ${GREEN}✓ Configuration 5GHz activée${NC}"
    HOSTAPD_HW_MODE="a"
    HOSTAPD_CHANNEL="36"
    HOSTAPD_EXTRA="
# 802.11ac (WiFi 5) support
ieee80211ac=1
vht_oper_chwidth=1
vht_oper_centr_freq_seg0_idx=42
vht_capab=[MAX-MPDU-11454][SHORT-GI-80][TX-STBC-2BY1][RX-STBC-1]"
else
    echo -e "   ${YELLOW}⚠️  Configuration 2.4GHz (5GHz non supporté)${NC}"
fi

# Generate hostapd.conf with detected interface
cat > /etc/hostapd/hostapd.conf << EOF
# ROSE Link Hotspot Configuration
# Auto-generated for: $PI_MODEL
# Interface: $WIFI_AP_INTERFACE

interface=$WIFI_AP_INTERFACE
driver=nl80211

# Network settings
ssid=ROSE-Link
hw_mode=$HOSTAPD_HW_MODE
channel=$HOSTAPD_CHANNEL
country_code=BE

# 802.11n support
ieee80211n=1
wmm_enabled=1
$HOSTAPD_EXTRA

# Security (WPA2 by default)
auth_algs=1
wpa=2
wpa_passphrase=RoseLink2024
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP

# Logging
logger_syslog=-1
logger_syslog_level=2
EOF

sed -i 's|#DAEMON_CONF=""|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd || true

# Configure dnsmasq with detected interface
echo -e "${GREEN}🌐 Configuration du serveur DHCP/DNS...${NC}"
mv /etc/dnsmasq.conf /etc/dnsmasq.conf.backup 2>/dev/null || true

cat > /etc/dnsmasq.conf << EOF
# ROSE Link DHCP/DNS Configuration
# Auto-generated for interface: $WIFI_AP_INTERFACE

# Interface binding
interface=$WIFI_AP_INTERFACE
bind-interfaces

# DHCP configuration
dhcp-range=192.168.50.10,192.168.50.250,255.255.255.0,24h
dhcp-option=option:router,192.168.50.1
dhcp-option=option:dns-server,192.168.50.1

# DNS configuration
server=1.1.1.1
server=8.8.8.8

# Domain
domain=roselink.local
local=/roselink.local/

# Performance
cache-size=1000
EOF

# Configure dhcpcd for static IP on AP interface
echo -e "${GREEN}🔧 Configuration de l'IP statique pour le hotspot...${NC}"
if ! grep -q "interface $WIFI_AP_INTERFACE" /etc/dhcpcd.conf; then
    cat >> /etc/dhcpcd.conf << EOF

# ROSE Link AP Configuration
interface $WIFI_AP_INTERFACE
    static ip_address=192.168.50.1/24
    nohook wpa_supplicant
EOF
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

# Configure iptables rules with detected interfaces
echo -e "${GREEN}🔥 Configuration des règles iptables...${NC}"
echo -e "   Interface AP: $WIFI_AP_INTERFACE"
echo -e "   Interface Ethernet: ${ETH_INTERFACE:-non détectée}"
echo -e "   Interface WiFi WAN: ${WIFI_WAN_INTERFACE:-non détectée}"

iptables -t nat -F
iptables -F FORWARD

# NAT for VPN (wg0 -> Internet)
iptables -t nat -A POSTROUTING -o wg0 -j MASQUERADE

# Allow forwarding from AP to VPN (wg0)
iptables -A FORWARD -i $WIFI_AP_INTERFACE -o wg0 -j ACCEPT
iptables -A FORWARD -i wg0 -o $WIFI_AP_INTERFACE -m state --state RELATED,ESTABLISHED -j ACCEPT

# Kill-switch: block forwarding from AP if wg0 is down
iptables -A FORWARD -i $WIFI_AP_INTERFACE ! -o wg0 -j REJECT

# Allow forwarding from WAN interfaces to VPN (for accessing remote LAN)
if [ -n "$ETH_INTERFACE" ]; then
    iptables -A FORWARD -i $ETH_INTERFACE -o wg0 -j ACCEPT
    echo -e "   ${GREEN}✓ Règle ajoutée pour $ETH_INTERFACE -> wg0${NC}"
fi

if [ -n "$WIFI_WAN_INTERFACE" ] && [ "$WIFI_WAN_INTERFACE" != "$WIFI_AP_INTERFACE" ]; then
    iptables -A FORWARD -i $WIFI_WAN_INTERFACE -o wg0 -j ACCEPT
    echo -e "   ${GREEN}✓ Règle ajoutée pour $WIFI_WAN_INTERFACE -> wg0${NC}"
fi

iptables -A FORWARD -i wg0 -m state --state RELATED,ESTABLISHED -j ACCEPT

# Save iptables rules
iptables-save > /etc/iptables/rules.v4
echo -e "   ${GREEN}✓ Règles iptables sauvegardées${NC}"

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
echo -e "${RED}"
cat << 'ROSE_SUCCESS'
               #********#
              ***#    #***
     *************    #******#*****
     *** #     #********#     # ***
     ***     ***************    ***    ****   ***  **** *****  **** #****   *****
     ***     **   #***#  ***    ***    ****  #***  *** *******  *** **** #*****
     ***     **          ***    ***    ***#   *** *** ***  #*** *** ***  ***#
     ***     **          ***    ***    ***   ******* ***    *** *** ***   ****
     #***    **          ***   ****    **** *** #*** ***    *** *** ***    #***
       ****  #***      #***  ****      **#****   *** ***   **** *** ***     ***
          *#***** **** ****#*#         #****#    *** *********# *** ***  *****
               #********#               ***     ***  #*******   *** ***  ****
ROSE_SUCCESS
echo -e "${NC}"
echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                              ROSE Link is Ready!                                              ║${NC}"
echo -e "${GREEN}║                           Installation Complete!                                              ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════════════════════════════════╝${NC}"
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
