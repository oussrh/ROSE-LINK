#!/bin/bash
#
# ROSE Link Update Script
# Updates ROSE Link to the latest version while preserving configuration
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
readonly GITHUB_REPO="oussrh/ROSE-LINK"
readonly LOG_FILE="/var/log/rose-link-update.log"

# Progress tracking
CURRENT_STEP=0
TOTAL_STEPS=7

# Version info
CURRENT_VERSION=""
LATEST_VERSION=""

# ===== Utility Functions =====

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
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}  Step $CURRENT_STEP/$TOTAL_STEPS: $1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
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

show_banner() {
    clear
    echo -e "${CYAN}"
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
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}          ${BOLD}ROSE Link Updater${NC}                                                 ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}          ${DIM}Update to the latest version while keeping your config${NC}            ${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

show_help() {
    echo "ROSE Link Updater"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help      Show this help message"
    echo "  -y, --yes       Non-interactive mode (skip confirmation)"
    echo "  -f, --force     Force update even if already on latest version"
    echo "  -c, --check     Check for updates without installing"
    echo ""
    echo "Examples:"
    echo "  sudo $0              # Interactive update"
    echo "  sudo $0 -y           # Automatic update without prompts"
    echo "  sudo $0 --check      # Just check if updates are available"
    echo ""
}

check_root() {
    if [[ "$EUID" -ne 0 ]]; then
        error "This script must be run as root (sudo)"
        echo -e "  ${YELLOW}Run: sudo $0${NC}"
        exit 1
    fi
}

get_current_version() {
    if [[ -f "$INSTALL_DIR/VERSION" ]]; then
        CURRENT_VERSION=$(cat "$INSTALL_DIR/VERSION" | tr -d '[:space:]')
    elif [[ -f "/opt/rose-link/backend/config.py" ]]; then
        CURRENT_VERSION=$(grep -oP 'APP_VERSION.*?"[\d.]+"' /opt/rose-link/backend/config.py 2>/dev/null | grep -oP '[\d.]+' || echo "unknown")
    else
        CURRENT_VERSION="not installed"
    fi
}

get_latest_version() {
    LATEST_VERSION=$(curl -fsSL "https://raw.githubusercontent.com/${GITHUB_REPO}/main/VERSION" 2>/dev/null | tr -d '[:space:]')
    if [[ -z "$LATEST_VERSION" ]]; then
        # Fallback to GitHub API
        LATEST_VERSION=$(curl -fsSL "https://api.github.com/repos/${GITHUB_REPO}/releases/latest" 2>/dev/null | grep -oP '"tag_name": "v?\K[^"]+' || echo "")
    fi
}

compare_versions() {
    if [[ "$CURRENT_VERSION" == "$LATEST_VERSION" ]]; then
        return 1  # Same version
    fi
    return 0  # Different version (update available)
}

# ===== Update Steps =====

check_updates() {
    print_step "Checking for updates"

    get_current_version
    info "Current version: ${CURRENT_VERSION:-unknown}"

    get_latest_version
    if [[ -z "$LATEST_VERSION" ]]; then
        error "Could not fetch latest version from GitHub"
        exit 1
    fi
    info "Latest version: $LATEST_VERSION"

    if compare_versions; then
        echo ""
        echo -e "  ${GREEN}▸ Update available: $CURRENT_VERSION → $LATEST_VERSION${NC}"
        return 0
    else
        echo ""
        echo -e "  ${GREEN}✓ Already on the latest version ($CURRENT_VERSION)${NC}"
        return 1
    fi
}

backup_config() {
    print_step "Backing up configuration"

    local backup_dir="/tmp/rose-link-backup-$(date +%Y%m%d%H%M%S)"
    mkdir -p "$backup_dir"

    # Backup hostapd config
    if [[ -f /etc/hostapd/hostapd.conf ]]; then
        cp /etc/hostapd/hostapd.conf "$backup_dir/"
        success "Hotspot configuration backed up"
    fi

    # Backup WireGuard profiles
    if [[ -d /etc/wireguard/profiles ]]; then
        cp -r /etc/wireguard/profiles "$backup_dir/"
        success "VPN profiles backed up"
    fi

    # Backup VPN settings
    if [[ -f "$INSTALL_DIR/system/vpn-settings.conf" ]]; then
        cp "$INSTALL_DIR/system/vpn-settings.conf" "$backup_dir/"
        success "VPN settings backed up"
    fi

    echo "$backup_dir" > /tmp/rose-link-backup-path
    info "Backup saved to: $backup_dir"
}

stop_services() {
    print_step "Stopping services"

    local services=(rose-backend rose-watchdog)

    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service" 2>/dev/null; then
            systemctl stop "$service" 2>/dev/null || warning "Could not stop $service"
            success "Stopped $service"
        fi
    done
}

download_update() {
    print_step "Downloading latest version"

    local tmp_dir="/tmp/rose-link-update"
    rm -rf "$tmp_dir"
    mkdir -p "$tmp_dir"

    info "Downloading from GitHub..."

    if curl -fsSL "https://github.com/${GITHUB_REPO}/archive/refs/heads/main.tar.gz" -o "$tmp_dir/rose-link.tar.gz"; then
        success "Download complete"
    else
        error "Failed to download update"
        exit 1
    fi

    info "Extracting files..."
    tar -xzf "$tmp_dir/rose-link.tar.gz" -C "$tmp_dir" --strip-components=1
    success "Extraction complete"
}

install_update() {
    print_step "Installing update"

    local tmp_dir="/tmp/rose-link-update"

    # Update backend
    info "Updating backend..."
    rm -rf "$INSTALL_DIR/backend"
    cp -r "$tmp_dir/backend" "$INSTALL_DIR/"
    success "Backend updated"

    # Update web interface
    info "Updating web interface..."
    rm -rf "$INSTALL_DIR/web"
    cp -r "$tmp_dir/web" "$INSTALL_DIR/"
    success "Web interface updated"

    # Update system files
    info "Updating system files..."
    cp -r "$tmp_dir/system/"* "$INSTALL_DIR/system/" 2>/dev/null || true
    success "System files updated"

    # Update VERSION file
    cp "$tmp_dir/VERSION" "$INSTALL_DIR/VERSION"
    success "Version file updated"

    # Update Python dependencies
    info "Updating Python dependencies..."
    if [[ -f "$INSTALL_DIR/venv/bin/pip" ]]; then
        "$INSTALL_DIR/venv/bin/pip" install -q -r "$INSTALL_DIR/backend/requirements.txt" 2>/dev/null || warning "Some dependencies may not have updated"
        success "Dependencies updated"
    fi

    # Fix permissions
    chown -R rose:rose "$INSTALL_DIR" 2>/dev/null || true
}

restore_config() {
    print_step "Restoring configuration"

    local backup_dir
    backup_dir=$(cat /tmp/rose-link-backup-path 2>/dev/null)

    if [[ -z "$backup_dir" ]] || [[ ! -d "$backup_dir" ]]; then
        warning "No backup found to restore"
        return
    fi

    # Restore VPN settings
    if [[ -f "$backup_dir/vpn-settings.conf" ]]; then
        cp "$backup_dir/vpn-settings.conf" "$INSTALL_DIR/system/"
        success "VPN settings restored"
    fi

    info "Hotspot and VPN profiles preserved (not overwritten)"

    # Cleanup backup
    rm -f /tmp/rose-link-backup-path
}

start_services() {
    print_step "Starting services"

    systemctl daemon-reload

    local services=(rose-backend rose-watchdog)

    for service in "${services[@]}"; do
        if systemctl start "$service" 2>/dev/null; then
            success "Started $service"
        else
            warning "Could not start $service"
        fi
    done

    # Restart nginx to pick up any changes
    systemctl restart nginx 2>/dev/null || warning "Could not restart nginx"
}

show_completion() {
    get_current_version

    echo ""
    echo -e "${GREEN}"
    cat << 'COMPLETE_LOGO'

         ✓ ✓ ✓     UPDATE COMPLETE     ✓ ✓ ✓

COMPLETE_LOGO
    echo -e "${NC}"
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${NC}              ${BOLD}ROSE Link Updated Successfully!${NC}                             ${GREEN}║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}  Version Info${NC}"
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "  ${GREEN}✓${NC} Now running: ${GREEN}v$CURRENT_VERSION${NC}"
    echo ""

    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}  What's Preserved${NC}"
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "  ${GREEN}✓${NC} WiFi hotspot configuration (SSID, password)"
    echo -e "  ${GREEN}✓${NC} WireGuard VPN profiles"
    echo -e "  ${GREEN}✓${NC} VPN watchdog settings"
    echo -e "  ${GREEN}✓${NC} SSL certificates"
    echo ""

    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}  Access${NC}"
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "  ${CYAN}https://roselink.local${NC}"
    echo -e "  ${CYAN}https://192.168.50.1${NC}"
    echo ""

    log "INFO" "Update completed successfully to v$CURRENT_VERSION"
}

# ===== Main =====

main() {
    local interactive=true
    local force=false
    local check_only=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                show_help
                exit 0
                ;;
            -y|--yes)
                interactive=false
                shift
                ;;
            -f|--force)
                force=true
                shift
                ;;
            -c|--check)
                check_only=true
                shift
                ;;
            *)
                echo "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # Initialize logging
    mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true
    log "INFO" "=== ROSE Link Update Started ==="

    show_banner
    check_root

    # Check for updates
    if ! check_updates; then
        if [[ "$force" != "true" ]]; then
            echo ""
            if [[ "$check_only" == "true" ]]; then
                exit 0
            fi
            echo -e "  ${YELLOW}Use --force to reinstall the same version${NC}"
            exit 0
        fi
    fi

    if [[ "$check_only" == "true" ]]; then
        exit 0
    fi

    # Confirm update
    if [[ "$interactive" == "true" ]]; then
        echo ""
        read -p "  Proceed with update? [Y/n] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]?$ ]]; then
            info "Update cancelled"
            exit 0
        fi
    fi

    # Perform update
    backup_config
    stop_services
    download_update
    install_update
    restore_config
    start_services

    show_completion

    # Cleanup
    rm -rf /tmp/rose-link-update
}

main "$@"
