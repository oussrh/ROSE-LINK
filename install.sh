#!/bin/bash
#
# ROSE Link Installation Script v2.0
# Installs and configures ROSE Link VPN router on Raspberry Pi
# Supports: Raspberry Pi 3, 4, 5, Zero 2W
# Compatible: Debian 11 (Bullseye), Debian 12 (Bookworm), Raspberry Pi OS
#

# Strict error handling
set -euo pipefail
trap 'handle_error $? $LINENO' ERR

# ===== Configuration =====
# Version is fetched from VERSION file or GitHub, with fallback
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$SCRIPT_DIR/VERSION" ]]; then
    VERSION=$(cat "$SCRIPT_DIR/VERSION" | tr -d '[:space:]')
elif [[ -f "/opt/rose-link/VERSION" ]]; then
    VERSION=$(cat "/opt/rose-link/VERSION" | tr -d '[:space:]')
else
    # Fetch from GitHub if running remotely
    VERSION=$(curl -fsSL https://raw.githubusercontent.com/oussrh/ROSE-LINK/main/VERSION 2>/dev/null | tr -d '[:space:]' || echo "1.3.6")
fi
readonly VERSION
readonly INSTALL_DIR="/opt/rose-link"
readonly USER="rose"
readonly GROUP="rose"
readonly LOG_FILE="/var/log/rose-link-install.log"
readonly MIN_RAM_MB=512
readonly MIN_DISK_MB=300
readonly RECOMMENDED_RAM_MB=1024
readonly RECOMMENDED_DISK_MB=500

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
# shellcheck disable=SC2034  # MAGENTA may be used in future
readonly MAGENTA='\033[0;35m'
readonly BOLD='\033[1m'
readonly DIM='\033[2m'
readonly NC='\033[0m' # No Color

# Progress tracking
CURRENT_STEP=0
TOTAL_STEPS=13
INSTALL_START_TIME=""

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
WIFI_5GHZ_SUPPORT=false
DEBIAN_VERSION=""
DEBIAN_CODENAME=""

# Installation options (can be overridden via environment or flags)
INTERACTIVE=${INTERACTIVE:-true}
SKIP_HARDWARE_CHECK=${SKIP_HARDWARE_CHECK:-false}
FORCE_INSTALL=${FORCE_INSTALL:-false}
CUSTOM_SSID=${CUSTOM_SSID:-"ROSE-Link"}
CUSTOM_PASSWORD=${CUSTOM_PASSWORD:-""}
COUNTRY_CODE=${COUNTRY_CODE:-"BE"}

# ===== Utility Functions =====

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

handle_error() {
    local exit_code=$1
    local line_number=$2
    log "ERROR" "Installation failed at line $line_number with exit code $exit_code"
    echo -e "\n${RED}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ❌ Installation Error                                         ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo -e "${RED}Error at line $line_number (exit code: $exit_code)${NC}"
    echo -e "${YELLOW}Check the log file for details: $LOG_FILE${NC}"
    echo -e "${YELLOW}You can retry the installation after fixing the issue.${NC}"
    exit "$exit_code"
}

print_banner() {
    clear
    echo -e "${RED}"
    cat << 'ROSE_LOGO'

                      ####
                    ########
                   ###########
                 #####    #####
        ############        ############
      ##############         #############
      ####      #######  #######      ####
      #### ##      #########       ## ####
      #### ###### #######      ###### ####     #############        ###########       ###########   ##############
      ####    #######       #######   ####     ###############    ###############   ##############  ##############
      ####     ########  #########    ####     #####      ##### #######     ######  #####      ##   #####
      ####     ###  ######### ####    ####     #####      ##### #####         ##### ########        #####
      ####     ###     ##     ####    ####     #####     #####  #####         #####   ###########   #############
      ####     ###            ####    ####     ##############   #####         #####       ########  #############
      ####     ###            ####    ####     #############    ######       #####  ##       #####  #####
      ####     ###            ####    ####     #####    #####    ################  ###############  ##############
      #####    ###            ####   #####     #####     #####     #############    #############   ##############
        #####  #####        #####  #####                               ####              ####
          #####  #####    #####  #####                        ##
            ########################           #####        ######                  #####
              ####################             #####         ####                   #####
      ####            ####             ###     #####         ####   ##### #####     #####    #####
      ########        ####        ########     #####        ######  #############   #####  ######
      ### ########    ####     ####### ###     #####        ######  ####### ######  ##### #####
      ###     ######  ####  ######     ###     #####        ######  #####    #####  ##########
      ####       #### #### ####        ###     #####        ######  #####    #####  ###########
       ####       ############       #####     #####        ######  #####    #####  ############
        ##### #### ##########  #########       ###################  #####    #####  #####   #####
          ########  ########  ########         ############# ####   #####    #####  #####    #####
            ######### ##############
                  ############
                    ########
                      ####
                      ####
                      ####
                      ####
                      ####
                      ####

ROSE_LOGO
    echo -e "${NC}"
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║               ${BOLD}ROSE Link${NC}${BLUE} - Home VPN Router for Raspberry Pi - Version ${VERSION}                            ║${NC}"
    echo -e "${BLUE}║                              Supports: Pi 3, 4, 5, Zero 2W | Debian 11/12                                  ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

progress_bar() {
    local percent=$1
    local width=50
    local filled=$((percent * width / 100))
    local empty=$((width - filled))

    printf "\r${CYAN}["
    printf "%${filled}s" | tr ' ' '█'
    printf "%${empty}s" | tr ' ' '░'
    printf "] ${percent}%%${NC}"
}

step_start() {
    local step_name="$1"
    ((CURRENT_STEP++))
    local percent=$((CURRENT_STEP * 100 / TOTAL_STEPS))

    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}[${CURRENT_STEP}/${TOTAL_STEPS}]${NC} ${CYAN}$step_name${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    progress_bar "$percent"
    echo ""

    log "INFO" "Step $CURRENT_STEP/$TOTAL_STEPS: $step_name"
}

step_done() {
    echo -e "   ${GREEN}✓ Done${NC}"
}

step_warning() {
    local message="$1"
    echo -e "   ${YELLOW}⚠ $message${NC}"
    log "WARN" "$message"
}

step_error() {
    local message="$1"
    echo -e "   ${RED}✗ $message${NC}"
    log "ERROR" "$message"
}

step_info() {
    local message="$1"
    echo -e "   ${DIM}→ $message${NC}"
}

prompt_yes_no() {
    local prompt="$1"
    local default="${2:-n}"

    if [[ "$INTERACTIVE" != "true" ]]; then
        [[ "$default" =~ ^[Yy]$ ]] && return 0 || return 1
    fi

    local yn_prompt
    if [[ "$default" =~ ^[Yy]$ ]]; then
        yn_prompt="[Y/n]"
    else
        yn_prompt="[y/N]"
    fi

    read -p "   $prompt $yn_prompt " -n 1 -r
    echo

    if [[ -z "$REPLY" ]]; then
        [[ "$default" =~ ^[Yy]$ ]] && return 0 || return 1
    fi

    [[ $REPLY =~ ^[Yy]$ ]]
}

prompt_input() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"

    if [[ "$INTERACTIVE" != "true" ]]; then
        eval "$var_name=\"$default\""
        return
    fi

    read -p "   $prompt [$default]: " input
    if [[ -z "$input" ]]; then
        eval "$var_name=\"$default\""
    else
        eval "$var_name=\"$input\""
    fi
}

spinner() {
    local pid=$1
    local message="${2:-Processing}"
    local spin='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    local i=0

    while kill -0 "$pid" 2>/dev/null; do
        printf "\r   ${CYAN}${spin:i++%${#spin}:1}${NC} $message..."
        sleep 0.1
    done
    printf "\r   ${GREEN}✓${NC} $message...done\n"
}

# ===== Detection Functions =====

detect_debian_version() {
    step_info "Detecting Debian/Raspberry Pi OS version..."

    if [[ -f /etc/os-release ]]; then
        source /etc/os-release
        DEBIAN_VERSION="${VERSION_ID:-unknown}"
        DEBIAN_CODENAME="${VERSION_CODENAME:-unknown}"

        step_info "OS: $PRETTY_NAME"
        step_info "Version: $DEBIAN_VERSION ($DEBIAN_CODENAME)"

        # Check for supported versions
        case "$DEBIAN_CODENAME" in
            bullseye|bookworm|trixie)
                step_info "Debian version supported: $DEBIAN_CODENAME"
                ;;
            *)
                step_warning "Untested Debian version: $DEBIAN_CODENAME"
                ;;
        esac
    else
        step_warning "Could not detect OS version"
    fi
}

detect_pi_model() {
    step_info "Detecting Raspberry Pi model..."

    if [[ -f /proc/device-tree/model ]]; then
        PI_MODEL=$(tr -d '\0' < /proc/device-tree/model)
        step_info "Model: $PI_MODEL"

        case "$PI_MODEL" in
            *"Raspberry Pi 5"*)
                PI_VERSION=5
                step_info "${GREEN}Raspberry Pi 5 - Full support (5GHz, WiFi 6)${NC}"
                ;;
            *"Raspberry Pi 4"*)
                PI_VERSION=4
                step_info "${GREEN}Raspberry Pi 4 - Full support (5GHz, WiFi 5)${NC}"
                ;;
            *"Raspberry Pi 3"*)
                PI_VERSION=3
                step_info "${YELLOW}Raspberry Pi 3 - Limited support (2.4GHz only)${NC}"
                ;;
            *"Raspberry Pi Zero 2"*)
                PI_VERSION="zero2"
                step_info "${YELLOW}Raspberry Pi Zero 2 W - Basic support (limited resources)${NC}"
                ;;
            *"Raspberry Pi"*)
                PI_VERSION="other"
                step_warning "Untested Pi model - installation may work"
                ;;
            *)
                PI_VERSION="unknown"
                step_warning "Not a Raspberry Pi - limited hardware detection"
                ;;
        esac
    else
        PI_VERSION="unknown"
        step_warning "Could not detect hardware model"
    fi

    PI_ARCH=$(uname -m)
    step_info "Architecture: $PI_ARCH"
}

detect_system_resources() {
    step_info "Checking system resources..."

    # RAM check
    PI_RAM_MB=$(free -m | awk '/^Mem:/{print $2}')
    step_info "RAM: ${PI_RAM_MB} MB"

    if [[ "$PI_RAM_MB" -lt "$MIN_RAM_MB" ]]; then
        step_error "Insufficient RAM: ${PI_RAM_MB}MB < ${MIN_RAM_MB}MB minimum"
        return 1
    elif [[ "$PI_RAM_MB" -lt "$RECOMMENDED_RAM_MB" ]]; then
        step_warning "RAM below recommended: ${PI_RAM_MB}MB < ${RECOMMENDED_RAM_MB}MB"
    else
        step_info "RAM: OK (${PI_RAM_MB}MB)"
    fi

    # Disk space check
    local disk_free_mb
    disk_free_mb=$(df -m /opt 2>/dev/null | tail -1 | awk '{print $4}' || df -m / | tail -1 | awk '{print $4}')
    step_info "Free disk space: ${disk_free_mb} MB"

    if [[ "$disk_free_mb" -lt "$MIN_DISK_MB" ]]; then
        step_error "Insufficient disk space: ${disk_free_mb}MB < ${MIN_DISK_MB}MB minimum"
        return 1
    elif [[ "$disk_free_mb" -lt "$RECOMMENDED_DISK_MB" ]]; then
        step_warning "Disk space below recommended: ${disk_free_mb}MB < ${RECOMMENDED_DISK_MB}MB"
    else
        step_info "Disk space: OK (${disk_free_mb}MB)"
    fi

    # CPU temperature (if available)
    if [[ -f /sys/class/thermal/thermal_zone0/temp ]]; then
        local cpu_temp
        cpu_temp=$(($(cat /sys/class/thermal/thermal_zone0/temp) / 1000))
        step_info "CPU Temperature: ${cpu_temp}°C"

        if [[ "$cpu_temp" -gt 80 ]]; then
            step_warning "High CPU temperature! Consider adding cooling"
        elif [[ "$cpu_temp" -gt 70 ]]; then
            step_warning "CPU temperature elevated - monitor during operation"
        fi
    fi

    return 0
}

detect_network_interfaces() {
    step_info "Detecting network interfaces..."

    # Detect Ethernet
    for iface in eth0 end0 enp1s0 enp0s3; do
        if [[ -d "/sys/class/net/$iface" ]]; then
            ETH_INTERFACE=$iface
            local eth_state
            eth_state=$(cat "/sys/class/net/$iface/operstate" 2>/dev/null || echo "unknown")
            step_info "Ethernet: $ETH_INTERFACE (state: $eth_state)"
            break
        fi
    done

    [[ -z "$ETH_INTERFACE" ]] && step_warning "No Ethernet interface detected"

    # Detect WiFi interfaces
    step_info "Scanning WiFi interfaces..."

    for iface in /sys/class/net/*; do
        iface=$(basename "$iface")
        if [[ -d "/sys/class/net/$iface/wireless" ]]; then
            local device_path driver
            device_path=$(readlink -f "/sys/class/net/$iface/device" 2>/dev/null || echo "")
            driver=$(basename "$(readlink "/sys/class/net/$iface/device/driver" 2>/dev/null)" 2>/dev/null || echo "unknown")

            if [[ "$device_path" == *"mmc"* ]] || [[ "$device_path" == *"soc"* ]]; then
                WIFI_BUILTIN=$iface
                step_info "WiFi (built-in): $iface (driver: $driver)"
            else
                WIFI_USB=$iface
                step_info "WiFi (USB): $iface (driver: $driver)"
            fi
        fi
    done

    # Determine interface assignment strategy
    if [[ -n "$WIFI_USB" ]] && [[ -n "$WIFI_BUILTIN" ]]; then
        WIFI_AP_INTERFACE=$WIFI_USB
        WIFI_WAN_INTERFACE=$WIFI_BUILTIN
        step_info "${GREEN}Optimal configuration: Dual WiFi interfaces${NC}"
        step_info "  Access Point: $WIFI_AP_INTERFACE (USB)"
        step_info "  WAN Client: $WIFI_WAN_INTERFACE (built-in)"
    elif [[ -n "$WIFI_BUILTIN" ]]; then
        WIFI_AP_INTERFACE=$WIFI_BUILTIN
        WIFI_WAN_INTERFACE=$WIFI_BUILTIN
        step_info "Single WiFi interface: $WIFI_AP_INTERFACE"
        step_info "  Will operate in AP mode (Ethernet preferred for WAN)"
    elif [[ -n "$WIFI_USB" ]]; then
        WIFI_AP_INTERFACE=$WIFI_USB
        WIFI_WAN_INTERFACE=""
        step_info "USB WiFi only: $WIFI_AP_INTERFACE"
    else
        step_error "No WiFi interfaces detected!"
        step_info "Checking rfkill status..."
        if command -v rfkill &>/dev/null; then
            rfkill list wifi 2>/dev/null || true
        fi
        step_info "Try: sudo rfkill unblock wifi"
        return 1
    fi

    return 0
}

detect_wifi_capabilities() {
    step_info "Detecting WiFi capabilities..."

    if [[ -z "$WIFI_AP_INTERFACE" ]]; then
        step_warning "No WiFi interface to check"
        return 0
    fi

    # Check 5GHz support
    if iw list 2>/dev/null | grep -q "5[0-9][0-9][0-9] MHz"; then
        WIFI_5GHZ_SUPPORT=true
        step_info "${GREEN}5GHz band: Supported${NC}"
    else
        step_info "5GHz band: Not supported (2.4GHz only)"
    fi

    # Check WiFi standards
    if iw list 2>/dev/null | grep -q "VHT"; then
        step_info "${GREEN}802.11ac (WiFi 5): Supported${NC}"
    fi

    if iw list 2>/dev/null | grep -q "HE"; then
        step_info "${GREEN}802.11ax (WiFi 6): Supported${NC}"
    fi

    # Check AP mode support
    if iw list 2>/dev/null | grep -q "\* AP"; then
        step_info "${GREEN}Access Point mode: Supported${NC}"
    else
        step_error "Access Point mode: NOT SUPPORTED!"
        step_info "Your WiFi adapter cannot create a hotspot"
        return 1
    fi

    return 0
}

# ===== Installation Functions =====

install_dependencies() {
    step_info "Updating package lists..."

    # Update with retry logic
    local retries=3
    for ((i=1; i<=retries; i++)); do
        if apt-get update -qq 2>&1; then
            break
        fi
        step_warning "Package update failed, attempt $i/$retries"
        sleep 2
    done

    step_info "Installing system packages..."

    # Core packages
    local packages=(
        # Python runtime
        python3
        python3-pip
        python3-venv
        python3-dev

        # Web server
        nginx

        # WiFi Access Point
        hostapd
        dnsmasq

        # VPN
        wireguard
        wireguard-tools

        # Networking
        iptables
        iptables-persistent
        network-manager
        iw
        rfkill

        # Security
        openssl
        ca-certificates

        # Utilities
        curl
        procps
    )

    # Install packages non-interactively
    DEBIAN_FRONTEND=noninteractive apt-get install -y -q "${packages[@]}" 2>&1 | while read -r line; do
        if [[ "$line" == *"Setting up"* ]] || [[ "$line" == *"Processing"* ]]; then
            printf "\r   → Installing: %-40s" "${line:0:40}"
        fi
    done
    echo ""

    step_info "All dependencies installed"
}

create_user() {
    step_info "Creating service user '$USER'..."

    if id -u "$USER" &>/dev/null; then
        step_info "User '$USER' already exists"
    else
        useradd -r -s /usr/sbin/nologin -d "$INSTALL_DIR" -c "ROSE Link Service Account" "$USER"
        step_info "User '$USER' created"
    fi

    # Ensure group exists
    if ! getent group "$GROUP" &>/dev/null; then
        groupadd -r "$GROUP"
    fi

    # Add user to required groups for hardware access
    usermod -a -G netdev "$USER" 2>/dev/null || true
}

install_files() {
    step_info "Creating installation directory structure..."

    # Create directories with proper permissions
    mkdir -p "$INSTALL_DIR"/{backend,web,system,logs}
    mkdir -p /etc/wireguard/profiles
    mkdir -p /etc/nginx/ssl
    mkdir -p /var/log/rose-link

    # Set restrictive permissions on WireGuard directory
    chmod 700 /etc/wireguard
    chmod 700 /etc/wireguard/profiles

    step_info "Copying application files..."

    # Copy application files
    if [[ -d "backend" ]]; then
        cp -r backend/* "$INSTALL_DIR/backend/"
    fi

    if [[ -d "web" ]]; then
        cp -r web/* "$INSTALL_DIR/web/"
    fi

    if [[ -d "system" ]]; then
        cp -r system/* "$INSTALL_DIR/system/"
    fi

    # Set ownership
    chown -R "$USER:$GROUP" "$INSTALL_DIR"
    chown -R "$USER:$GROUP" /var/log/rose-link

    # Set executable permissions
    chmod +x "$INSTALL_DIR/system/rose-watchdog.sh" 2>/dev/null || true

    step_info "Files installed to $INSTALL_DIR"
}

setup_python_env() {
    step_info "Creating Python virtual environment..."

    # Remove existing venv if corrupted
    if [[ -d "$INSTALL_DIR/venv" ]] && [[ ! -x "$INSTALL_DIR/venv/bin/python" ]]; then
        rm -rf "$INSTALL_DIR/venv"
    fi

    # Create new venv
    python3 -m venv "$INSTALL_DIR/venv"

    step_info "Upgrading pip..."
    "$INSTALL_DIR/venv/bin/pip" install --upgrade pip -q

    step_info "Installing Python dependencies..."
    if [[ -f "$INSTALL_DIR/backend/requirements.txt" ]]; then
        "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/backend/requirements.txt" -q
    fi

    # Set ownership
    chown -R "$USER:$GROUP" "$INSTALL_DIR/venv"

    step_info "Python environment ready"
}

generate_interface_config() {
    step_info "Generating interface configuration..."

    cat > "$INSTALL_DIR/system/interfaces.conf" << EOF
# ROSE Link Interface Configuration
# Auto-generated by install.sh on $(date)
# DO NOT EDIT - This file is overwritten on reinstall

# Detected Interfaces
ETH_INTERFACE=${ETH_INTERFACE:-}
WIFI_AP_INTERFACE=${WIFI_AP_INTERFACE:-wlan0}
WIFI_WAN_INTERFACE=${WIFI_WAN_INTERFACE:-}

# Hardware Information
PI_MODEL="${PI_MODEL:-Unknown}"
PI_VERSION=${PI_VERSION:-unknown}
PI_ARCH=${PI_ARCH:-$(uname -m)}

# WiFi Capabilities
WIFI_5GHZ_SUPPORT=${WIFI_5GHZ_SUPPORT:-false}

# Installation Info
INSTALL_DATE=$(date -Iseconds)
INSTALLER_VERSION=${VERSION}
EOF

    chown "$USER:$GROUP" "$INSTALL_DIR/system/interfaces.conf"
    chmod 644 "$INSTALL_DIR/system/interfaces.conf"
}

configure_hostapd() {
    step_info "Configuring WiFi Access Point (hostapd)..."

    # Determine WiFi mode based on capabilities
    local hw_mode="g"
    local channel="6"
    local extra_config=""

    if [[ "$WIFI_5GHZ_SUPPORT" == "true" ]]; then
        hw_mode="a"
        channel="36"
        extra_config="
# 802.11ac (WiFi 5) support
ieee80211ac=1
vht_oper_chwidth=1
vht_oper_centr_freq_seg0_idx=42
vht_capab=[MAX-MPDU-11454][SHORT-GI-80][TX-STBC-2BY1][RX-STBC-1]"
        step_info "5GHz mode enabled (channel $channel)"
    else
        step_info "2.4GHz mode (channel $channel)"
    fi

    # Generate secure password if not provided
    local wifi_password="$CUSTOM_PASSWORD"
    if [[ -z "$wifi_password" ]]; then
        # Generate a random 12-character password
        wifi_password=$(openssl rand -base64 12 | tr -dc 'a-zA-Z0-9' | head -c 12)
        step_info "Generated secure WiFi password"
    fi

    # Create hostapd configuration
    cat > /etc/hostapd/hostapd.conf << EOF
# ROSE Link Hotspot Configuration
# Auto-generated for: ${PI_MODEL:-Unknown}
# Interface: ${WIFI_AP_INTERFACE:-wlan0}
# Generated: $(date)

# Interface settings
interface=${WIFI_AP_INTERFACE:-wlan0}
driver=nl80211

# Network settings
ssid=${CUSTOM_SSID}
hw_mode=${hw_mode}
channel=${channel}
country_code=${COUNTRY_CODE}

# 802.11n support (HT mode)
ieee80211n=1
wmm_enabled=1
ht_capab=[HT40][SHORT-GI-20][SHORT-GI-40][DSSS_CCK-40]
${extra_config}

# Security - WPA2 with strong settings
auth_algs=1
wpa=2
wpa_passphrase=${wifi_password}
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
wpa_pairwise=CCMP

# Performance settings
max_num_sta=20
beacon_int=100
dtim_period=2

# Logging
logger_syslog=-1
logger_syslog_level=2
logger_stdout=-1
logger_stdout_level=2
EOF

    # Set secure permissions
    chmod 600 /etc/hostapd/hostapd.conf

    # Configure hostapd to use our config
    if [[ -f /etc/default/hostapd ]]; then
        sed -i 's|#DAEMON_CONF=""|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd
        sed -i 's|DAEMON_CONF=".*"|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd
    fi

    # Save password info for user
    echo "$wifi_password" > "$INSTALL_DIR/.wifi_password"
    chmod 600 "$INSTALL_DIR/.wifi_password"
    chown "$USER:$GROUP" "$INSTALL_DIR/.wifi_password"

    step_info "Hotspot configured: SSID='${CUSTOM_SSID}'"
}

configure_dnsmasq() {
    step_info "Configuring DHCP/DNS server (dnsmasq)..."

    # Backup original config
    if [[ -f /etc/dnsmasq.conf ]] && [[ ! -f /etc/dnsmasq.conf.rose-backup ]]; then
        mv /etc/dnsmasq.conf /etc/dnsmasq.conf.rose-backup
    fi

    cat > /etc/dnsmasq.conf << EOF
# ROSE Link DHCP/DNS Configuration
# Auto-generated: $(date)

# Interface binding - only listen on AP interface
interface=${WIFI_AP_INTERFACE:-wlan0}
bind-interfaces
except-interface=lo

# DHCP configuration
dhcp-range=192.168.50.10,192.168.50.250,255.255.255.0,24h
dhcp-option=option:router,192.168.50.1
dhcp-option=option:dns-server,192.168.50.1,1.1.1.1
dhcp-option=option:netmask,255.255.255.0

# DNS configuration
server=1.1.1.1
server=8.8.8.8
server=9.9.9.9

# Domain settings
domain=roselink.local
local=/roselink.local/
expand-hosts

# Security settings
domain-needed
bogus-priv
no-resolv
stop-dns-rebind
rebind-localhost-ok

# Performance
cache-size=1000
dns-forward-max=150

# Logging (comment out for production)
# log-queries
log-dhcp
log-facility=/var/log/rose-link/dnsmasq.log
EOF

    step_info "DHCP range: 192.168.50.10-250"
}

configure_dhcpcd() {
    step_info "Configuring static IP for Access Point..."

    local dhcpcd_config
    dhcpcd_config="
# ROSE Link AP Configuration - Added $(date)
interface ${WIFI_AP_INTERFACE:-wlan0}
    static ip_address=192.168.50.1/24
    nohook wpa_supplicant
"

    # Check if configuration already exists
    if ! grep -q "# ROSE Link AP Configuration" /etc/dhcpcd.conf 2>/dev/null; then
        echo "$dhcpcd_config" >> /etc/dhcpcd.conf
        step_info "Static IP configured: 192.168.50.1/24"
    else
        step_info "Static IP configuration already present"
    fi
}

configure_sudoers() {
    step_info "Configuring sudo permissions..."

    cat > /etc/sudoers.d/rose << 'EOF'
# ROSE Link sudo rules
# Minimal permissions for network and VPN management

# Network management
rose ALL=(ALL) NOPASSWD: /usr/bin/nmcli *
rose ALL=(ALL) NOPASSWD: /usr/bin/iw *
rose ALL=(ALL) NOPASSWD: /usr/sbin/ip *
rose ALL=(ALL) NOPASSWD: /usr/sbin/rfkill *

# WireGuard VPN
rose ALL=(ALL) NOPASSWD: /usr/bin/wg show
rose ALL=(ALL) NOPASSWD: /usr/bin/wg-quick up *
rose ALL=(ALL) NOPASSWD: /usr/bin/wg-quick down *

# Service management (specific services only)
rose ALL=(ALL) NOPASSWD: /usr/bin/systemctl start wg-quick@*
rose ALL=(ALL) NOPASSWD: /usr/bin/systemctl stop wg-quick@*
rose ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart wg-quick@*
rose ALL=(ALL) NOPASSWD: /usr/bin/systemctl status wg-quick@*
rose ALL=(ALL) NOPASSWD: /usr/bin/systemctl start hostapd
rose ALL=(ALL) NOPASSWD: /usr/bin/systemctl stop hostapd
rose ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart hostapd
rose ALL=(ALL) NOPASSWD: /usr/bin/systemctl status hostapd
rose ALL=(ALL) NOPASSWD: /usr/bin/systemctl start dnsmasq
rose ALL=(ALL) NOPASSWD: /usr/bin/systemctl stop dnsmasq
rose ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart dnsmasq
rose ALL=(ALL) NOPASSWD: /usr/bin/systemctl status dnsmasq

# Log viewing
rose ALL=(ALL) NOPASSWD: /usr/bin/journalctl -u wg-quick@* *
rose ALL=(ALL) NOPASSWD: /usr/bin/journalctl -u hostapd *
rose ALL=(ALL) NOPASSWD: /usr/bin/journalctl -u rose-backend *

# System control (limited)
rose ALL=(ALL) NOPASSWD: /usr/sbin/reboot
EOF

    chmod 440 /etc/sudoers.d/rose

    # Validate sudoers file
    if visudo -c -f /etc/sudoers.d/rose &>/dev/null; then
        step_info "Sudo permissions configured"
    else
        step_error "Invalid sudoers configuration!"
        rm -f /etc/sudoers.d/rose
        return 1
    fi
}

configure_ssl() {
    step_info "Configuring SSL/TLS certificates..."

    local ssl_dir="/etc/nginx/ssl"
    local cert_file="$ssl_dir/roselink.crt"
    local key_file="$ssl_dir/roselink.key"

    mkdir -p "$ssl_dir"

    # Check if certificate exists and is valid
    local regenerate=false
    if [[ -f "$cert_file" ]] && [[ -f "$key_file" ]]; then
        # Check certificate expiration
        local expiry
        expiry=$(openssl x509 -enddate -noout -in "$cert_file" 2>/dev/null | cut -d= -f2)
        if [[ -n "$expiry" ]]; then
            local expiry_epoch
            expiry_epoch=$(date -d "$expiry" +%s 2>/dev/null || echo 0)
            local now_epoch
            now_epoch=$(date +%s)
            local days_left=$(( (expiry_epoch - now_epoch) / 86400 ))

            if [[ "$days_left" -lt 30 ]]; then
                step_warning "Certificate expires in $days_left days - regenerating"
                regenerate=true
            else
                step_info "Existing certificate valid ($days_left days remaining)"
            fi
        fi
    else
        regenerate=true
    fi

    if [[ "$regenerate" == "true" ]]; then
        step_info "Generating new SSL certificate..."

        # Generate certificate with SANs for local access
        openssl req -x509 -nodes -days 3650 -newkey rsa:4096 \
            -keyout "$key_file" \
            -out "$cert_file" \
            -subj "/C=${COUNTRY_CODE}/ST=Local/L=Local/O=ROSE Link/OU=VPN Router/CN=roselink.local" \
            -addext "subjectAltName=DNS:roselink.local,DNS:localhost,IP:192.168.50.1,IP:127.0.0.1" \
            2>/dev/null

        step_info "Certificate generated (valid for 10 years)"
    fi

    # Set secure permissions
    chmod 600 "$key_file"
    chmod 644 "$cert_file"
}

configure_nginx() {
    step_info "Configuring Nginx web server..."

    # Install Nginx configuration
    if [[ -f "$INSTALL_DIR/system/nginx/roselink" ]]; then
        cp "$INSTALL_DIR/system/nginx/roselink" /etc/nginx/sites-available/roselink
    else
        # Create default configuration
        cat > /etc/nginx/sites-available/roselink << 'EOF'
# ROSE Link Nginx Configuration

# Redirect HTTP to HTTPS
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    return 301 https://$host$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2 default_server;
    listen [::]:443 ssl http2 default_server;
    server_name roselink.local localhost 192.168.50.1;

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/roselink.crt;
    ssl_certificate_key /etc/nginx/ssl/roselink.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Root directory
    root /opt/rose-link/web;
    index index.html;

    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 75s;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;

        # WebSocket support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Static files
    location / {
        try_files $uri $uri/ /index.html;
        expires 1h;
        add_header Cache-Control "public, immutable";
    }

    # Service worker and manifest
    location ~* (service-worker\.js|manifest\.json)$ {
        expires -1;
        add_header Cache-Control "no-store, no-cache, must-revalidate";
    }

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    gzip_min_length 1000;
}
EOF
    fi

    # Enable site
    ln -sf /etc/nginx/sites-available/roselink /etc/nginx/sites-enabled/roselink

    # Disable default site
    rm -f /etc/nginx/sites-enabled/default

    # Test configuration
    if nginx -t 2>&1 | grep -q "successful"; then
        step_info "Nginx configuration validated"
    else
        step_error "Nginx configuration error!"
        nginx -t
        return 1
    fi
}

configure_firewall() {
    step_info "Configuring firewall (iptables)..."

    # Enable IP forwarding
    echo "net.ipv4.ip_forward=1" > /etc/sysctl.d/99-rose-link.conf
    sysctl -w net.ipv4.ip_forward=1 >/dev/null
    step_info "IP forwarding enabled"

    # Flush existing rules
    iptables -t nat -F
    iptables -F FORWARD

    # NAT for VPN traffic
    iptables -t nat -A POSTROUTING -o wg0 -j MASQUERADE
    step_info "NAT rule added for VPN (wg0)"

    # Allow forwarding from AP to VPN
    iptables -A FORWARD -i "${WIFI_AP_INTERFACE:-wlan0}" -o wg0 -j ACCEPT
    iptables -A FORWARD -i wg0 -o "${WIFI_AP_INTERFACE:-wlan0}" -m state --state RELATED,ESTABLISHED -j ACCEPT

    # Kill-switch: block forwarding if VPN is down
    iptables -A FORWARD -i "${WIFI_AP_INTERFACE:-wlan0}" ! -o wg0 -j REJECT --reject-with icmp-net-unreachable
    step_info "Kill-switch enabled (traffic blocked if VPN down)"

    # Allow forwarding from Ethernet to VPN
    if [[ -n "$ETH_INTERFACE" ]]; then
        iptables -A FORWARD -i "$ETH_INTERFACE" -o wg0 -j ACCEPT
        step_info "Forwarding enabled: $ETH_INTERFACE -> wg0"
    fi

    # Allow established connections back through VPN
    iptables -A FORWARD -i wg0 -m state --state RELATED,ESTABLISHED -j ACCEPT

    # Save rules
    iptables-save > /etc/iptables/rules.v4 2>/dev/null || true
    step_info "Firewall rules saved"
}

install_systemd_services() {
    step_info "Installing systemd services..."

    # Backend service
    cat > /etc/systemd/system/rose-backend.service << EOF
[Unit]
Description=ROSE Link Backend API
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=${USER}
Group=${GROUP}
WorkingDirectory=${INSTALL_DIR}/backend
Environment="PATH=${INSTALL_DIR}/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=${INSTALL_DIR}/venv/bin/python ${INSTALL_DIR}/backend/main.py
Restart=always
RestartSec=10

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${INSTALL_DIR} /etc/wireguard /var/log/rose-link

# Resource limits
MemoryMax=256M
CPUQuota=80%

[Install]
WantedBy=multi-user.target
EOF

    # Watchdog service
    cat > /etc/systemd/system/rose-watchdog.service << EOF
[Unit]
Description=ROSE Link VPN Watchdog
After=network.target wg-quick@wg0.service
Wants=wg-quick@wg0.service

[Service]
Type=simple
ExecStart=${INSTALL_DIR}/system/rose-watchdog.sh
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd
    systemctl daemon-reload
    step_info "Systemd services installed"
}

install_monitoring_command() {
    step_info "Installing monitoring management command..."

    # Install rose-monitoring command
    if [[ -f "system/rose-monitoring" ]]; then
        cp system/rose-monitoring /usr/local/bin/rose-monitoring
        chmod +x /usr/local/bin/rose-monitoring
        step_info "rose-monitoring command installed"
    elif [[ -f "$INSTALL_DIR/system/rose-monitoring" ]]; then
        cp "$INSTALL_DIR/system/rose-monitoring" /usr/local/bin/rose-monitoring
        chmod +x /usr/local/bin/rose-monitoring
        step_info "rose-monitoring command installed"
    fi

    # Create monitoring config directory
    mkdir -p "$INSTALL_DIR/monitoring/prometheus"
    mkdir -p "$INSTALL_DIR/monitoring/grafana/dashboards"

    # Copy monitoring configs
    if [[ -d "system/monitoring" ]]; then
        cp -r system/monitoring/* "$INSTALL_DIR/monitoring/" 2>/dev/null || true
    elif [[ -d "$INSTALL_DIR/system/monitoring" ]]; then
        cp -r "$INSTALL_DIR/system/monitoring/"* "$INSTALL_DIR/monitoring/" 2>/dev/null || true
    fi

    chown -R "$USER:$GROUP" "$INSTALL_DIR/monitoring"
    step_info "Monitoring configuration ready"
}

install_adguard_home() {
    step_info "Installing AdGuard Home DNS ad blocker..."

    local adguard_dir="/opt/AdGuardHome"
    local adguard_binary="$adguard_dir/AdGuardHome"

    # Check if already installed
    if [[ -f "$adguard_binary" ]]; then
        step_info "AdGuard Home already installed"
        return 0
    fi

    # Determine architecture
    local arch
    case "$(uname -m)" in
        aarch64|arm64) arch="arm64" ;;
        armv7l|armv6l) arch="armv7" ;;
        x86_64) arch="amd64" ;;
        *)
            step_warning "Unsupported architecture for AdGuard Home: $(uname -m)"
            return 1
            ;;
    esac

    step_info "Downloading AdGuard Home for $arch..."

    # Create installation directory
    mkdir -p "$adguard_dir"

    # Download latest AdGuard Home
    local download_url="https://static.adguard.com/adguardhome/release/AdGuardHome_linux_${arch}.tar.gz"
    local temp_file="/tmp/adguardhome.tar.gz"

    if curl -fsSL "$download_url" -o "$temp_file"; then
        step_info "Extracting AdGuard Home..."
        tar -xzf "$temp_file" -C /opt/
        rm -f "$temp_file"
    else
        step_warning "Failed to download AdGuard Home - skipping"
        return 1
    fi

    # Create initial configuration
    step_info "Configuring AdGuard Home..."
    cat > "$adguard_dir/AdGuardHome.yaml" << 'EOF'
bind_host: 0.0.0.0
bind_port: 3000
users: []
auth_attempts: 5
block_auth_min: 15
http_proxy: ""
language: ""
theme: auto
dns:
  bind_hosts:
    - 0.0.0.0
  port: 53
  anonymize_client_ip: false
  protection_enabled: true
  blocking_mode: default
  blocking_ipv4: ""
  blocking_ipv6: ""
  blocked_response_ttl: 10
  protection_disabled_until: null
  parental_block_host: family-block.dns.adguard.com
  safebrowsing_block_host: standard-block.dns.adguard.com
  ratelimit: 20
  ratelimit_whitelist: []
  refuse_any: true
  upstream_dns:
    - https://dns.cloudflare.com/dns-query
    - https://dns.google/dns-query
  upstream_dns_file: ""
  bootstrap_dns:
    - 1.1.1.1
    - 8.8.8.8
  fallback_dns: []
  all_servers: false
  fastest_addr: false
  fastest_timeout: 1s
  allowed_clients: []
  disallowed_clients: []
  blocked_hosts:
    - version.bind
    - id.server
    - hostname.bind
  trusted_proxies:
    - 127.0.0.0/8
    - ::1/128
  cache_size: 4194304
  cache_ttl_min: 0
  cache_ttl_max: 0
  cache_optimistic: false
  bogus_nxdomain: []
  aaaa_disabled: false
  enable_dnssec: true
  edns_client_subnet:
    custom_ip: ""
    enabled: false
    use_custom: false
  max_goroutines: 300
  handle_ddr: true
  ipset: []
  ipset_file: ""
  bootstrap_prefer_ipv6: false
  filtering_enabled: true
  filters_update_interval: 24
  parental_enabled: false
  safesearch_enabled: false
  safebrowsing_enabled: false
  safebrowsing_cache_size: 1048576
  safesearch_cache_size: 1048576
  parental_cache_size: 1048576
  cache_time: 30
  filters:
    - enabled: true
      url: https://adguardteam.github.io/HostlistsRegistry/assets/filter_1.txt
      name: AdGuard DNS filter
      id: 1
    - enabled: true
      url: https://adguardteam.github.io/HostlistsRegistry/assets/filter_2.txt
      name: AdAway Default Blocklist
      id: 2
  whitelist_filters: []
  user_rules: []
  dhcp:
    enabled: false
  clients:
    runtime_sources:
      whois: true
      arp: true
      rdns: true
      dhcp: true
      hosts: true
    persistent: []
  log_file: ""
  log_max_backups: 0
  log_max_size: 100
  log_max_age: 3
  log_compress: false
  log_localtime: false
  verbose: false
  os:
    group: ""
    user: ""
    rlimit_nofile: 0
  schema_version: 20
EOF

    # Install as systemd service
    step_info "Installing AdGuard Home service..."
    "$adguard_binary" -s install 2>/dev/null || true

    # Enable and start service
    systemctl enable AdGuardHome 2>/dev/null || true
    systemctl start AdGuardHome 2>/dev/null || true

    # Update dnsmasq to not conflict with AdGuard
    if [[ -f /etc/dnsmasq.conf ]]; then
        # Tell dnsmasq to use AdGuard as upstream
        if ! grep -q "server=127.0.0.1#5353" /etc/dnsmasq.conf; then
            sed -i 's/^server=1.1.1.1$/server=127.0.0.1#53/' /etc/dnsmasq.conf
            sed -i 's/^server=8.8.8.8$/# server=8.8.8.8 # Using AdGuard Home/' /etc/dnsmasq.conf
            sed -i 's/^server=9.9.9.9$/# server=9.9.9.9 # Using AdGuard Home/' /etc/dnsmasq.conf
        fi
    fi

    step_info "AdGuard Home installed and configured"
    step_info "Access AdGuard admin at: http://192.168.50.1:3000"
}

cleanup_wifi_client() {
    step_info "Cleaning up WiFi client connections for AP mode..."

    local ap_interface="${WIFI_AP_INTERFACE:-wlan0}"

    # Check if eth0 has a link (Ethernet connected)
    if ip link show eth0 2>/dev/null | grep -q "state UP"; then
        step_info "Ethernet connected - ensuring $ap_interface is in AP mode"

        # Remove any WiFi client connections on the AP interface
        local wifi_connections
        wifi_connections=$(nmcli -t -f NAME,DEVICE connection show 2>/dev/null | grep ":${ap_interface}$" | cut -d: -f1 || true)

        if [[ -n "$wifi_connections" ]]; then
            while IFS= read -r conn; do
                if [[ -n "$conn" ]]; then
                    step_info "Removing WiFi client connection: $conn"
                    nmcli connection delete "$conn" 2>/dev/null || true
                fi
            done <<< "$wifi_connections"
        fi

        # Disconnect the interface from any WiFi network
        nmcli device disconnect "$ap_interface" 2>/dev/null || true

        # Flush any DHCP-assigned IP and set static IP for AP
        ip addr flush dev "$ap_interface" 2>/dev/null || true
        ip addr add 192.168.50.1/24 dev "$ap_interface" 2>/dev/null || true

        step_info "WiFi interface prepared for AP mode"
    else
        step_warning "No Ethernet connection detected - WiFi may be needed for WAN"
        step_warning "Connect Ethernet cable for full hotspot functionality"
    fi
}

enable_services() {
    step_info "Enabling and starting services..."

    # Clean up any WiFi client connections before starting hotspot
    cleanup_wifi_client

    # Enable services
    local services=(rose-backend rose-watchdog hostapd dnsmasq nginx)

    for service in "${services[@]}"; do
        if systemctl enable "$service" 2>/dev/null; then
            step_info "Enabled: $service"
        else
            step_warning "Could not enable: $service"
        fi
    done

    # Start services (order matters)
    step_info "Starting services..."

    systemctl restart dhcpcd 2>/dev/null || true
    sleep 2

    systemctl restart dnsmasq 2>/dev/null || step_warning "dnsmasq start failed"
    systemctl restart hostapd 2>/dev/null || step_warning "hostapd start failed"
    systemctl restart nginx 2>/dev/null || step_warning "nginx start failed"
    systemctl restart rose-backend 2>/dev/null || step_warning "rose-backend start failed"

    step_info "Services started"
}

# ===== Main Installation Flow =====

print_summary() {
    local wifi_password
    wifi_password=$(cat "$INSTALL_DIR/.wifi_password" 2>/dev/null || echo "RoseLink2024")

    local elapsed=$((SECONDS - INSTALL_START_TIME))
    local minutes=$((elapsed / 60))
    local seconds=$((elapsed % 60))

    echo ""
    echo -e "${GREEN}"
    cat << 'ROSE_SUCCESS'

                      ####
                    ########
                 #####    #####
        ############        ############
      ####      #######  #######      ####
      ####     ########  #########    ####     #####      ##### #######     ######
      ####     ###  ######### ####    ####     #####      ##### #####         #####
      ####     ###     ##     ####    ####     #####     #####  #####         #####
      ####     ###            ####    ####     ##############   #####         #####
      #####    ###            ####   #####     #####     #####     #############
        #####  #####        #####  #####
            ########################           #####        ######
      ####            ####             ###     #####         ####   ##### #####
      ### ########    ####     ####### ###     #####        ######  ####### ######
       ####       ############       #####     #####        ######  #####    #####
          ########  ########  ########         ############# ####   #####    #####
                      ####
                      ####

ROSE_SUCCESS
    echo -e "${NC}"

    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                              🎉 ROSE Link Installation Complete! 🎉                                        ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}Installation completed in ${minutes}m ${seconds}s${NC}"
    echo ""
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}📶 WiFi Hotspot Credentials${NC}"
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "   SSID:     ${GREEN}${CUSTOM_SSID}${NC}"
    echo -e "   Password: ${GREEN}${wifi_password}${NC}"
    echo ""
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}🌐 Web Interface${NC}"
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "   ${CYAN}https://roselink.local${NC}"
    echo -e "   ${CYAN}https://192.168.50.1${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  Note: Accept the self-signed certificate warning in your browser${NC}"
    echo ""
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}🔐 Next Steps${NC}"
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "   1. Connect to the ${GREEN}${CUSTOM_SSID}${NC} WiFi network"
    echo -e "   2. Open ${CYAN}https://roselink.local${NC} in your browser"
    echo -e "   3. Go to the VPN tab and import your WireGuard .conf file"
    echo -e "   4. The VPN will connect automatically"
    echo ""
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}📈 Monitoring Dashboard (Optional)${NC}"
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "   Enable:  ${GREEN}sudo rose-monitoring enable${NC}"
    echo -e "   Status:  rose-monitoring status"
    echo -e "   Access:  https://roselink.local/grafana/"
    echo ""
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}📊 Service Status${NC}"
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    for service in rose-backend hostapd dnsmasq nginx AdGuardHome; do
        if systemctl is-active --quiet "$service" 2>/dev/null; then
            echo -e "   ${GREEN}●${NC} $service: ${GREEN}running${NC}"
        else
            echo -e "   ${RED}●${NC} $service: ${RED}stopped${NC}"
        fi
    done

    echo ""
    echo -e "${GREEN}🎉 Enjoy secure VPN access from anywhere!${NC}"
    echo ""
}

show_help() {
    echo "ROSE Link Installer v${VERSION}"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -y, --yes               Non-interactive mode (accept all defaults)"
    echo "  -f, --force             Force installation (skip hardware checks)"
    echo "  --ssid NAME             Set custom WiFi SSID (default: ROSE-Link)"
    echo "  --password PASS         Set custom WiFi password (min 8 chars)"
    echo "  --country CODE          Set country code (default: BE)"
    echo ""
    echo "Environment variables:"
    echo "  INTERACTIVE=false       Same as --yes"
    echo "  SKIP_HARDWARE_CHECK=true Same as --force"
    echo "  CUSTOM_SSID=name        Same as --ssid"
    echo "  CUSTOM_PASSWORD=pass    Same as --password"
    echo "  COUNTRY_CODE=XX         Same as --country"
    echo ""
    echo "Examples:"
    echo "  sudo $0                           # Interactive installation"
    echo "  sudo $0 -y                        # Non-interactive with defaults"
    echo "  sudo $0 --ssid MyRouter --country FR"
    echo ""
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                show_help
                exit 0
                ;;
            -y|--yes)
                INTERACTIVE=false
                shift
                ;;
            -f|--force)
                FORCE_INSTALL=true
                SKIP_HARDWARE_CHECK=true
                shift
                ;;
            --ssid)
                CUSTOM_SSID="$2"
                shift 2
                ;;
            --password)
                CUSTOM_PASSWORD="$2"
                if [[ ${#CUSTOM_PASSWORD} -lt 8 ]]; then
                    echo "Error: WiFi password must be at least 8 characters"
                    exit 1
                fi
                shift 2
                ;;
            --country)
                COUNTRY_CODE="$2"
                shift 2
                ;;
            *)
                echo "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

main() {
    parse_args "$@"

    # Initialize logging
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "=== ROSE Link Installation Started $(date) ===" > "$LOG_FILE"
    log "INFO" "Version: $VERSION"
    log "INFO" "Interactive: $INTERACTIVE"

    INSTALL_START_TIME=$SECONDS

    print_banner

    # Root check
    if [[ "$EUID" -ne 0 ]]; then
        echo -e "${RED}❌ Error: This script must be run as root (sudo)${NC}"
        echo -e "${YELLOW}   Run: sudo bash $0${NC}"
        exit 1
    fi

    # Step 1: Detect OS
    step_start "Detecting Operating System"
    detect_debian_version
    step_done

    # Step 2: Detect Hardware
    step_start "Detecting Hardware"
    detect_pi_model

    if [[ "$PI_VERSION" == "unknown" ]] && [[ "$SKIP_HARDWARE_CHECK" != "true" ]]; then
        echo ""
        step_warning "This doesn't appear to be a Raspberry Pi"
        if [[ "$INTERACTIVE" == "true" ]]; then
            if ! prompt_yes_no "Continue anyway?"; then
                echo "Installation cancelled."
                exit 0
            fi
        fi
    fi
    step_done

    # Step 3: Check Resources
    step_start "Checking System Resources"
    if ! detect_system_resources; then
        if [[ "$FORCE_INSTALL" != "true" ]]; then
            exit 1
        fi
        step_warning "Continuing despite resource warnings (--force)"
    fi
    step_done

    # Step 4: Detect Network
    step_start "Detecting Network Interfaces"
    if ! detect_network_interfaces; then
        exit 1
    fi
    step_done

    # Step 5: Detect WiFi Capabilities
    step_start "Detecting WiFi Capabilities"
    detect_wifi_capabilities || true
    step_done

    # Step 6: Install Dependencies
    step_start "Installing System Dependencies"
    install_dependencies
    step_done

    # Step 7: Create User
    step_start "Creating Service User"
    create_user
    step_done

    # Step 8: Install Files
    step_start "Installing Application Files"
    install_files
    setup_python_env
    generate_interface_config
    step_done

    # Step 9: Configure Services
    step_start "Configuring Network Services"
    configure_hostapd
    configure_dnsmasq
    configure_dhcpcd
    step_done

    # Step 10: Configure Security
    step_start "Configuring Security"
    configure_sudoers
    configure_ssl
    configure_nginx
    step_done

    # Step 11: Configure Firewall
    step_start "Configuring Firewall"
    configure_firewall
    step_done

    # Step 12: Install AdGuard Home
    step_start "Installing AdGuard Home DNS Blocker"
    install_adguard_home || step_warning "AdGuard Home installation failed - continuing"
    step_done

    # Step 13: Enable Services
    step_start "Enabling Services"
    install_systemd_services
    install_monitoring_command
    enable_services
    step_done

    # Show summary
    print_summary

    log "INFO" "Installation completed successfully"
}

# Run main function
main "$@"
