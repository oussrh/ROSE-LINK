#!/bin/bash
#
# ROSE Link Uninstallation Script v2.0
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
readonly NC='\033[0m'

# Configuration
readonly INSTALL_DIR="/opt/rose-link"
readonly USER="rose"
readonly GROUP="rose"
readonly LOG_FILE="/var/log/rose-link-uninstall.log"

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

info() {
    echo -e "${CYAN}→${NC} $1"
    log "INFO" "$1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
    log "INFO" "$1"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    log "WARN" "$1"
}

error() {
    echo -e "${RED}✗${NC} $1"
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

    read -p "   $prompt $yn_prompt " -n 1 -r
    echo

    if [[ -z "$REPLY" ]]; then
        [[ "$default" =~ ^[Yy]$ ]] && return 0 || return 1
    fi

    [[ $REPLY =~ ^[Yy]$ ]]
}

show_banner() {
    echo ""
    echo -e "${RED}╔════════════════════════════════════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                              🌹 ROSE Link Uninstallation                                                   ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════════════════════════════════════════════════════╝${NC}"
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
    info "Stopping ROSE Link services..."

    local services=(rose-backend rose-watchdog wg-quick@wg0)

    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service" 2>/dev/null; then
            systemctl stop "$service" 2>/dev/null || warning "Could not stop $service"
            success "Stopped $service"
        fi
    done

    success "Services stopped"
}

disable_services() {
    info "Disabling services..."

    local services=(rose-backend rose-watchdog wg-quick@wg0)

    for service in "${services[@]}"; do
        systemctl disable "$service" 2>/dev/null || true
    done

    success "Services disabled"
}

remove_systemd_services() {
    info "Removing systemd service files..."

    rm -f /etc/systemd/system/rose-backend.service
    rm -f /etc/systemd/system/rose-watchdog.service
    systemctl daemon-reload

    success "Systemd services removed"
}

remove_sudoers() {
    info "Removing sudoers configuration..."

    rm -f /etc/sudoers.d/rose

    success "Sudoers configuration removed"
}

remove_nginx_config() {
    info "Removing Nginx configuration..."

    rm -f /etc/nginx/sites-enabled/roselink
    rm -f /etc/nginx/sites-available/roselink

    # Restore default site
    if [[ -f /etc/nginx/sites-available/default ]]; then
        ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default 2>/dev/null || true
    fi

    systemctl restart nginx 2>/dev/null || true

    success "Nginx configuration removed"
}

remove_ssl_certificates() {
    info "Removing SSL certificates..."

    rm -f /etc/nginx/ssl/roselink.key
    rm -f /etc/nginx/ssl/roselink.crt
    rmdir /etc/nginx/ssl 2>/dev/null || true

    success "SSL certificates removed"
}

remove_hostapd_config() {
    info "Removing hostapd configuration..."

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
    info "Restoring dnsmasq configuration..."

    if [[ -f /etc/dnsmasq.conf.rose-backup ]]; then
        mv /etc/dnsmasq.conf.rose-backup /etc/dnsmasq.conf
        success "Original dnsmasq.conf restored"
    elif [[ -f /etc/dnsmasq.conf.backup ]]; then
        mv /etc/dnsmasq.conf.backup /etc/dnsmasq.conf
        success "Original dnsmasq.conf restored"
    else
        rm -f /etc/dnsmasq.conf
        warning "No backup found, dnsmasq.conf removed"
    fi

    systemctl stop dnsmasq 2>/dev/null || true
    systemctl disable dnsmasq 2>/dev/null || true

    success "dnsmasq configuration handled"
}

clean_dhcpcd_config() {
    info "Cleaning dhcpcd configuration..."

    if grep -q "# ROSE Link AP Configuration" /etc/dhcpcd.conf 2>/dev/null; then
        # Create backup
        cp /etc/dhcpcd.conf /etc/dhcpcd.conf.rose-uninstall-backup

        # Remove ROSE Link section
        sed -i '/# ROSE Link AP Configuration/,/^$/d' /etc/dhcpcd.conf
        success "dhcpcd.conf cleaned"
    else
        success "dhcpcd.conf already clean"
    fi
}

clean_iptables() {
    info "Cleaning iptables rules..."

    # Flush NAT and FORWARD chains
    iptables -t nat -F 2>/dev/null || true
    iptables -F FORWARD 2>/dev/null || true

    # Save clean rules
    iptables-save > /etc/iptables/rules.v4 2>/dev/null || true

    # Remove sysctl config
    rm -f /etc/sysctl.d/99-rose-link.conf

    success "Iptables rules cleared"
}

remove_wireguard_profiles() {
    if [[ "$KEEP_PROFILES" == "true" ]]; then
        if [[ "$INTERACTIVE" == "true" ]]; then
            if prompt_yes_no "Remove WireGuard VPN profiles?"; then
                KEEP_PROFILES=false
            fi
        fi
    fi

    if [[ "$KEEP_PROFILES" != "true" ]]; then
        info "Removing WireGuard profiles..."
        rm -rf /etc/wireguard/profiles
        rm -f /etc/wireguard/wg0.conf
        success "WireGuard profiles removed"
    else
        warning "WireGuard profiles preserved at /etc/wireguard/profiles"
    fi
}

remove_installation_directory() {
    info "Removing installation directory..."

    if [[ -d "$INSTALL_DIR" ]]; then
        rm -rf "$INSTALL_DIR"
        success "$INSTALL_DIR removed"
    else
        success "Installation directory already removed"
    fi

    # Remove logs
    rm -rf /var/log/rose-link
    rm -f /var/log/rose-link-*.log
}

remove_user() {
    if [[ "$KEEP_USER" == "true" ]]; then
        if [[ "$INTERACTIVE" == "true" ]]; then
            if prompt_yes_no "Remove the '$USER' system user?"; then
                KEEP_USER=false
            fi
        fi
    fi

    if [[ "$KEEP_USER" != "true" ]]; then
        info "Removing system user '$USER'..."
        if id -u "$USER" &>/dev/null; then
            userdel -r "$USER" 2>/dev/null || userdel "$USER" 2>/dev/null || warning "Could not remove user"
            success "User '$USER' removed"
        else
            success "User '$USER' already removed"
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
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                              🌹 ROSE Link Uninstallation Complete                                          ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    echo -e "${BOLD}Summary:${NC}"
    echo "   • Services stopped and disabled"
    echo "   • Configuration files removed"
    echo "   • Installation directory removed"

    if [[ "$KEEP_PROFILES" == "true" ]]; then
        echo -e "   • ${YELLOW}WireGuard profiles preserved${NC}"
    else
        echo "   • WireGuard profiles removed"
    fi

    if [[ "$KEEP_USER" == "true" ]]; then
        echo -e "   • ${YELLOW}System user '$USER' preserved${NC}"
    else
        echo "   • System user removed"
    fi

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
