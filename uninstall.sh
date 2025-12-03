#!/bin/bash
#
# ROSE Link Uninstallation Script
# Safely removes ROSE Link VPN router from Raspberry Pi
# Supports both direct installation and Debian package
#

set -e

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly BOLD='\033[1m'
readonly DIM='\033[2m'
readonly NC='\033[0m'

# Configuration
readonly INSTALL_DIR="/opt/rose-link"
readonly USER="rose"
readonly GROUP="rose"
readonly LOG_FILE="/var/log/rose-link-uninstall.log"

# Progress tracking
CURRENT_STEP=0
TOTAL_STEPS=12

# Options
INTERACTIVE=true
FULL_CLEANUP=false
KEEP_PROFILES=true
KEEP_USER=true

# Logging
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE" 2>/dev/null || true
}

print_step() {
    CURRENT_STEP=$((CURRENT_STEP + 1))
    echo ""
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}  Step $CURRENT_STEP/$TOTAL_STEPS: $1${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    log "INFO" "Step $CURRENT_STEP: $1"
}

info() {
    echo -e "  ${CYAN}▸${NC} $1"
    log "INFO" "$1"
}

success() {
    echo -e "  ${GREEN}✓${NC} $1"
    log "INFO" "$1"
}

warning() {
    echo -e "  ${YELLOW}⚠${NC} $1"
    log "WARN" "$1"
}

error() {
    echo -e "  ${RED}✗${NC} $1"
    log "ERROR" "$1"
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

    read -p "    $prompt $yn_prompt " -n 1 -r
    echo

    if [[ -z "$REPLY" ]]; then
        [[ "$default" =~ ^[Yy]$ ]] && return 0 || return 1
    fi

    [[ $REPLY =~ ^[Yy]$ ]]
}

show_banner() {
    clear
    echo -e "${RED}"
    cat << 'ROSE_LOGO'

                      ####
                    ########
                 #####    #####
        ############        ############
      ####      #######  #######      ####
      ####     ########  #########    ####
      ####     ###  ######### ####    ####
      ####     ###     ##     ####    ####
      #####    ###            ####   #####
        #####  #####        #####  #####
            ########################
      ####            ####             ###
       ####       ############       #####
          ########  ########  ########
                      ####

ROSE_LOGO
    echo -e "${NC}"
    echo -e "${RED}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║${NC}          ${BOLD}ROSE Link Uninstaller${NC}                                            ${RED}║${NC}"
    echo -e "${RED}║${NC}          ${DIM}Safely remove ROSE Link from your Raspberry Pi${NC}                   ${RED}║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

show_help() {
    echo "ROSE Link Uninstaller"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help           Show this help message"
    echo "  -y, --yes            Non-interactive mode (accept all defaults)"
    echo "  -f, --full           Full cleanup (remove all data and configs)"
    echo "  --remove-profiles    Remove VPN profiles"
    echo "  --remove-user        Remove the 'rose' system user"
    echo ""
    echo "Examples:"
    echo "  sudo $0              # Interactive uninstallation"
    echo "  sudo $0 -y           # Quick uninstall keeping data"
    echo "  sudo $0 -y -f        # Complete removal"
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
            -f|--full)
                FULL_CLEANUP=true
                KEEP_PROFILES=false
                KEEP_USER=false
                shift
                ;;
            --remove-profiles)
                KEEP_PROFILES=false
                shift
                ;;
            --remove-user)
                KEEP_USER=false
                shift
                ;;
            *)
                echo "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

check_root() {
    if [[ "$EUID" -ne 0 ]]; then
        error "This script must be run as root (sudo)"
        echo -e "${YELLOW}   Run: sudo $0${NC}"
        exit 1
    fi
}

check_package_installed() {
    if dpkg -l rose-link-pro 2>/dev/null | grep -q "^ii"; then
        return 0
    fi
    return 1
}

show_warning() {
    echo -e "${YELLOW}⚠️  Warning: This will remove the following ROSE Link components:${NC}"
    echo ""
    echo "   • ROSE Link backend service"
    echo "   • ROSE Link watchdog service"
    echo "   • Hostapd configuration"
    echo "   • dnsmasq configuration"
    echo "   • Nginx ROSE Link site"
    echo "   • SSL certificates"
    echo "   • Firewall (iptables) rules"
    echo "   • Installation directory ($INSTALL_DIR)"

    if [[ "$KEEP_PROFILES" != "true" ]]; then
        echo "   • WireGuard VPN profiles"
    fi

    if [[ "$KEEP_USER" != "true" ]]; then
        echo "   • System user '$USER'"
    fi

    echo ""

    if [[ "$INTERACTIVE" == "true" ]]; then
        echo -e "${YELLOW}Type 'yes' to confirm uninstallation:${NC}"
        read -p "   > " confirm
        if [[ "$confirm" != "yes" ]]; then
            echo ""
            info "Uninstallation cancelled."
            exit 0
        fi
    fi
}

stop_services() {
    print_step "Stopping services"

    local services=(rose-backend rose-watchdog wg-quick@wg0)

    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service" 2>/dev/null; then
            systemctl stop "$service" 2>/dev/null || warning "Could not stop $service"
            success "Stopped $service"
        else
            info "$service not running"
        fi
    done
}

disable_services() {
    print_step "Disabling services"

    local services=(rose-backend rose-watchdog wg-quick@wg0)

    for service in "${services[@]}"; do
        if systemctl is-enabled --quiet "$service" 2>/dev/null; then
            systemctl disable "$service" 2>/dev/null || true
            success "Disabled $service"
        fi
    done
}

remove_systemd_services() {
    print_step "Removing systemd services"

    rm -f /etc/systemd/system/rose-backend.service
    rm -f /etc/systemd/system/rose-watchdog.service
    systemctl daemon-reload

    success "Systemd service files removed"
}

remove_sudoers() {
    print_step "Removing sudoers configuration"

    if [[ -f /etc/sudoers.d/rose ]]; then
        rm -f /etc/sudoers.d/rose
        success "Sudoers configuration removed"
    else
        info "Sudoers configuration not found"
    fi
}

remove_nginx_config() {
    print_step "Removing Nginx configuration"

    rm -f /etc/nginx/sites-enabled/roselink
    rm -f /etc/nginx/sites-available/roselink

    # Restore default site
    if [[ -f /etc/nginx/sites-available/default ]]; then
        ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default 2>/dev/null || true
        info "Default Nginx site restored"
    fi

    systemctl restart nginx 2>/dev/null || true
    success "Nginx configuration removed"
}

remove_ssl_certificates() {
    print_step "Removing SSL certificates"

    if [[ -f /etc/nginx/ssl/roselink.key ]] || [[ -f /etc/nginx/ssl/roselink.crt ]]; then
        rm -f /etc/nginx/ssl/roselink.key
        rm -f /etc/nginx/ssl/roselink.crt
        rmdir /etc/nginx/ssl 2>/dev/null || true
        success "SSL certificates removed"
    else
        info "SSL certificates not found"
    fi
}

remove_hostapd_config() {
    print_step "Removing hostapd configuration"

    rm -f /etc/hostapd/hostapd.conf

    # Restore default hostapd config
    if [[ -f /etc/default/hostapd ]]; then
        sed -i 's|DAEMON_CONF="/etc/hostapd/hostapd.conf"|#DAEMON_CONF=""|' /etc/default/hostapd 2>/dev/null || true
    fi

    systemctl stop hostapd 2>/dev/null || true
    systemctl disable hostapd 2>/dev/null || true

    success "Hostapd configuration removed"
}

restore_dnsmasq_config() {
    print_step "Restoring dnsmasq configuration"

    if [[ -f /etc/dnsmasq.conf.rose-backup ]]; then
        mv /etc/dnsmasq.conf.rose-backup /etc/dnsmasq.conf
        success "Original dnsmasq.conf restored from backup"
    elif [[ -f /etc/dnsmasq.conf.backup ]]; then
        mv /etc/dnsmasq.conf.backup /etc/dnsmasq.conf
        success "Original dnsmasq.conf restored from backup"
    else
        rm -f /etc/dnsmasq.conf
        warning "No backup found, dnsmasq.conf removed"
    fi

    systemctl stop dnsmasq 2>/dev/null || true
    systemctl disable dnsmasq 2>/dev/null || true
}

clean_dhcpcd_config() {
    print_step "Cleaning network configuration"

    if grep -q "# ROSE Link AP Configuration" /etc/dhcpcd.conf 2>/dev/null; then
        cp /etc/dhcpcd.conf /etc/dhcpcd.conf.rose-uninstall-backup
        sed -i '/# ROSE Link AP Configuration/,/^$/d' /etc/dhcpcd.conf
        success "dhcpcd.conf cleaned"
    else
        info "dhcpcd.conf already clean"
    fi
}

clean_iptables() {
    print_step "Cleaning firewall rules"

    # Flush NAT and FORWARD chains
    iptables -t nat -F 2>/dev/null || true
    iptables -F FORWARD 2>/dev/null || true

    # Save clean rules
    iptables-save > /etc/iptables/rules.v4 2>/dev/null || true

    # Remove sysctl config
    rm -f /etc/sysctl.d/99-rose-link.conf

    success "Iptables rules cleared"
    success "IP forwarding config removed"
}

remove_wireguard_profiles() {
    print_step "Handling VPN profiles"

    if [[ "$KEEP_PROFILES" == "true" ]]; then
        if [[ "$INTERACTIVE" == "true" ]]; then
            if prompt_yes_no "Remove WireGuard VPN profiles?"; then
                KEEP_PROFILES=false
            fi
        fi
    fi

    if [[ "$KEEP_PROFILES" != "true" ]]; then
        rm -rf /etc/wireguard/profiles
        rm -f /etc/wireguard/wg0.conf
        success "WireGuard profiles removed"
    else
        warning "WireGuard profiles preserved at /etc/wireguard/profiles"
    fi
}

remove_installation_directory() {
    print_step "Removing installation files"

    if [[ -d "$INSTALL_DIR" ]]; then
        rm -rf "$INSTALL_DIR"
        success "$INSTALL_DIR removed"
    else
        info "Installation directory already removed"
    fi

    # Remove logs
    rm -rf /var/log/rose-link
    rm -f /var/log/rose-link-*.log
    success "Log files removed"
}

remove_user() {
    print_step "Handling system user"

    if [[ "$KEEP_USER" == "true" ]]; then
        if [[ "$INTERACTIVE" == "true" ]]; then
            if prompt_yes_no "Remove the '$USER' system user?"; then
                KEEP_USER=false
            fi
        fi
    fi

    if [[ "$KEEP_USER" != "true" ]]; then
        if id -u "$USER" &>/dev/null; then
            userdel -r "$USER" 2>/dev/null || userdel "$USER" 2>/dev/null || warning "Could not remove user"
            success "User '$USER' removed"
        else
            info "User '$USER' already removed"
        fi
    else
        warning "System user '$USER' preserved"
    fi
}

offer_package_cleanup() {
    if [[ "$INTERACTIVE" != "true" ]] && [[ "$FULL_CLEANUP" != "true" ]]; then
        return
    fi

    echo ""
    echo -e "${YELLOW}The following packages were installed by ROSE Link:${NC}"
    echo "   hostapd, dnsmasq, wireguard, wireguard-tools"
    echo "   iptables-persistent, network-manager"
    echo ""

    if [[ "$INTERACTIVE" == "true" ]]; then
        if prompt_yes_no "Remove these packages? (NOT recommended if used by other services)"; then
            info "Removing ROSE Link packages..."
            apt-get remove -y hostapd dnsmasq iptables-persistent 2>/dev/null || true
            success "Selected packages removed"
            warning "WireGuard and NetworkManager were kept for safety"
        else
            success "Packages preserved"
        fi
    elif [[ "$FULL_CLEANUP" == "true" ]]; then
        info "Removing ROSE Link packages..."
        apt-get remove -y hostapd dnsmasq iptables-persistent 2>/dev/null || true
        success "Selected packages removed"
    fi
}

offer_reboot() {
    echo ""
    echo -e "${YELLOW}A reboot is recommended for all changes to take effect.${NC}"

    if [[ "$INTERACTIVE" == "true" ]]; then
        if prompt_yes_no "Reboot now?"; then
            info "Rebooting..."
            reboot
        fi
    fi
}

show_completion() {
    echo ""
    echo -e "${GREEN}"
    cat << 'COMPLETE_LOGO'

         ✓ ✓ ✓     UNINSTALLATION COMPLETE     ✓ ✓ ✓

COMPLETE_LOGO
    echo -e "${NC}"
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${NC}                   ${BOLD}ROSE Link Successfully Removed${NC}                         ${GREEN}║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}  Summary${NC}"
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "  ${GREEN}✓${NC} Services stopped and disabled"
    echo -e "  ${GREEN}✓${NC} Systemd service files removed"
    echo -e "  ${GREEN}✓${NC} Nginx configuration removed"
    echo -e "  ${GREEN}✓${NC} SSL certificates removed"
    echo -e "  ${GREEN}✓${NC} Hostapd configuration removed"
    echo -e "  ${GREEN}✓${NC} dnsmasq configuration restored"
    echo -e "  ${GREEN}✓${NC} Firewall rules cleared"
    echo -e "  ${GREEN}✓${NC} Installation directory removed"

    if [[ "$KEEP_PROFILES" == "true" ]]; then
        echo -e "  ${YELLOW}⚠${NC} WireGuard profiles preserved at /etc/wireguard/profiles"
    else
        echo -e "  ${GREEN}✓${NC} WireGuard profiles removed"
    fi

    if [[ "$KEEP_USER" == "true" ]]; then
        echo -e "  ${YELLOW}⚠${NC} System user '$USER' preserved"
    else
        echo -e "  ${GREEN}✓${NC} System user removed"
    fi

    echo ""
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}  Reinstall${NC}"
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "  To reinstall ROSE Link, run:"
    echo -e "  ${CYAN}curl -fsSL https://get.roselink.dev | sudo bash${NC}"
    echo ""

    log "INFO" "Uninstallation completed successfully"
}

main() {
    parse_args "$@"

    # Initialize logging
    mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true
    log "INFO" "=== ROSE Link Uninstallation Started ==="

    show_banner
    check_root

    # Check if installed via dpkg
    if check_package_installed; then
        echo -e "${CYAN}ROSE Link was installed via Debian package.${NC}"
        echo ""
        echo "To remove, use:"
        echo -e "  ${CYAN}sudo apt remove rose-link-pro${NC}       (keep config)"
        echo -e "  ${CYAN}sudo apt purge rose-link-pro${NC}        (remove all)"
        echo ""

        if [[ "$INTERACTIVE" == "true" ]]; then
            if prompt_yes_no "Continue with manual uninstallation anyway?"; then
                :  # Continue
            else
                exit 0
            fi
        fi
    fi

    show_warning

    echo ""
    echo -e "${BOLD}Starting uninstallation...${NC}"
    echo ""

    stop_services
    disable_services
    remove_systemd_services
    remove_sudoers
    remove_nginx_config
    remove_ssl_certificates
    remove_hostapd_config
    restore_dnsmasq_config
    clean_dhcpcd_config
    clean_iptables
    remove_wireguard_profiles
    remove_installation_directory
    remove_user
    offer_package_cleanup

    show_completion
    offer_reboot
}

main "$@"
