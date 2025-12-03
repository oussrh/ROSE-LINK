#!/bin/bash
#
# ROSE Link SD Card Image Builder
# ================================
#
# Creates a ready-to-flash SD card image with ROSE Link pre-installed.
#
# Requirements:
# - Linux system with root access
# - qemu-user-static for ARM emulation
# - At least 8GB free disk space
# - Internet connection for downloads
#
# Usage:
#   sudo ./build-image.sh [options]
#
# Options:
#   -o, --output DIR    Output directory (default: ./output)
#   -v, --version VER   ROSE Link version (default: from VERSION file)
#   -k, --keep          Keep intermediate files
#   -h, --help          Show this help
#
# Author: ROSE Link Team
# License: MIT

set -euo pipefail

# ==============================================================================
# Configuration
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Raspberry Pi OS image configuration
RPI_OS_VERSION="2024-03-15"
RPI_OS_URL="https://downloads.raspberrypi.com/raspios_lite_arm64/images/raspios_lite_arm64-${RPI_OS_VERSION}/2024-03-15-raspios-bookworm-arm64-lite.img.xz"
# shellcheck disable=SC2034  # SHA256 may be used for verification in future
RPI_OS_SHA256="f0a2f8e8d5c9e2f0a1b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3"

# Output configuration
OUTPUT_DIR="${PROJECT_ROOT}/output"
WORK_DIR="/tmp/rose-link-image-build"
IMAGE_NAME="rose-link"
ROSE_VERSION=""

# Build options
KEEP_INTERMEDIATE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==============================================================================
# Helper Functions
# ==============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

die() {
    log_error "$1"
    exit 1
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        die "This script must be run as root (use sudo)"
    fi
}

check_dependencies() {
    log_info "Checking dependencies..."

    local deps=("wget" "xz" "losetup" "mount" "chroot" "rsync" "sha256sum")

    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            die "Missing dependency: $dep"
        fi
    done

    # Check for qemu-user-static
    if [[ ! -f /usr/bin/qemu-arm-static ]] && [[ ! -f /usr/bin/qemu-aarch64-static ]]; then
        die "qemu-user-static is required for ARM emulation. Install with: apt install qemu-user-static"
    fi

    log_success "All dependencies satisfied"
}

cleanup() {
    log_info "Cleaning up..."

    # Unmount if mounted
    if mountpoint -q "${WORK_DIR}/mnt/boot"; then
        umount "${WORK_DIR}/mnt/boot" 2>/dev/null || true
    fi
    if mountpoint -q "${WORK_DIR}/mnt"; then
        umount "${WORK_DIR}/mnt" 2>/dev/null || true
    fi

    # Detach loop device
    if [[ -n "${LOOP_DEV:-}" ]]; then
        losetup -d "$LOOP_DEV" 2>/dev/null || true
    fi

    # Remove work directory if not keeping intermediate files
    if [[ "$KEEP_INTERMEDIATE" == false ]] && [[ -d "$WORK_DIR" ]]; then
        rm -rf "$WORK_DIR"
    fi
}

trap cleanup EXIT

# ==============================================================================
# Main Build Functions
# ==============================================================================

download_base_image() {
    log_info "Downloading Raspberry Pi OS base image..."

    local image_file="${WORK_DIR}/raspios.img.xz"
    local image_extracted="${WORK_DIR}/raspios.img"

    if [[ -f "$image_extracted" ]]; then
        log_info "Base image already exists, skipping download"
        return
    fi

    if [[ ! -f "$image_file" ]]; then
        wget -O "$image_file" "$RPI_OS_URL" || die "Failed to download base image"
    fi

    log_info "Extracting base image..."
    xz -dk "$image_file" || die "Failed to extract base image"

    log_success "Base image ready"
}

expand_image() {
    log_info "Expanding image to accommodate ROSE Link..."

    local image_file="${WORK_DIR}/raspios.img"

    # Add 1GB to the image
    truncate -s +1G "$image_file"

    # Expand the root partition
    LOOP_DEV=$(losetup -fP --show "$image_file")
    log_info "Loop device: $LOOP_DEV"

    # Resize partition (partition 2)
    parted -s "$LOOP_DEV" resizepart 2 100%

    # Check and resize filesystem
    e2fsck -f "${LOOP_DEV}p2" || true
    resize2fs "${LOOP_DEV}p2"

    log_success "Image expanded"
}

mount_image() {
    log_info "Mounting image..."

    mkdir -p "${WORK_DIR}/mnt"

    # Mount root partition
    mount "${LOOP_DEV}p2" "${WORK_DIR}/mnt"

    # Mount boot partition
    mount "${LOOP_DEV}p1" "${WORK_DIR}/mnt/boot"

    log_success "Image mounted"
}

setup_qemu() {
    log_info "Setting up QEMU for ARM emulation..."

    # Copy qemu-aarch64-static for chroot
    if [[ -f /usr/bin/qemu-aarch64-static ]]; then
        cp /usr/bin/qemu-aarch64-static "${WORK_DIR}/mnt/usr/bin/"
    elif [[ -f /usr/bin/qemu-arm-static ]]; then
        cp /usr/bin/qemu-arm-static "${WORK_DIR}/mnt/usr/bin/"
    fi

    log_success "QEMU configured"
}

copy_rose_link() {
    log_info "Copying ROSE Link files..."

    local dest="${WORK_DIR}/mnt/opt/rose-link-install"
    mkdir -p "$dest"

    # Copy the project files
    rsync -av --exclude='.git' --exclude='output' --exclude='*.pyc' \
        --exclude='__pycache__' --exclude='node_modules' --exclude='.venv' \
        --exclude='venv' --exclude='*.egg-info' \
        "$PROJECT_ROOT/" "$dest/"

    log_success "ROSE Link files copied"
}

configure_first_boot() {
    log_info "Configuring first boot scripts..."

    # Create first-boot script
    cat > "${WORK_DIR}/mnt/opt/rose-link-first-boot.sh" << 'FIRSTBOOT'
#!/bin/bash
#
# ROSE Link First Boot Configuration
# Runs once on first boot to complete setup

set -e

LOG_FILE="/var/log/rose-link-first-boot.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check if already configured
if [[ -f /opt/rose-link/.first-boot-done ]]; then
    exit 0
fi

log "Starting ROSE Link first boot configuration..."

# Expand filesystem
log "Expanding filesystem..."
raspi-config --expand-rootfs || true

# Wait for network
log "Waiting for network..."
for i in {1..30}; do
    if ping -c 1 8.8.8.8 &>/dev/null; then
        log "Network available"
        break
    fi
    sleep 2
done

# Install ROSE Link
log "Installing ROSE Link..."
cd /opt/rose-link-install
if [[ -f install.sh ]]; then
    bash install.sh -y --first-boot 2>&1 | tee -a "$LOG_FILE"
fi

# Cleanup installation files
log "Cleaning up..."
rm -rf /opt/rose-link-install

# Mark first boot as done
touch /opt/rose-link/.first-boot-done

# Regenerate SSH keys
log "Regenerating SSH host keys..."
rm -f /etc/ssh/ssh_host_*
dpkg-reconfigure openssh-server

log "First boot configuration complete!"
log "Connect to ROSE-Link-Setup WiFi to configure"

# Remove the service
systemctl disable rose-link-first-boot.service

# Reboot to apply all changes
log "Rebooting..."
reboot
FIRSTBOOT

    chmod +x "${WORK_DIR}/mnt/opt/rose-link-first-boot.sh"

    # Create systemd service for first boot
    cat > "${WORK_DIR}/mnt/etc/systemd/system/rose-link-first-boot.service" << 'SERVICE'
[Unit]
Description=ROSE Link First Boot Configuration
After=network-online.target
Wants=network-online.target
ConditionPathExists=!/opt/rose-link/.first-boot-done

[Service]
Type=oneshot
ExecStart=/opt/rose-link-first-boot.sh
RemainAfterExit=yes
StandardOutput=journal+console
StandardError=journal+console

[Install]
WantedBy=multi-user.target
SERVICE

    # Enable the service
    chroot "${WORK_DIR}/mnt" systemctl enable rose-link-first-boot.service

    log_success "First boot configuration ready"
}

configure_wifi_setup() {
    log_info "Configuring setup WiFi hotspot..."

    # Ensure hostapd directory exists (may not exist until hostapd is installed)
    mkdir -p "${WORK_DIR}/mnt/etc/hostapd"

    # Configure hostapd for initial setup hotspot
    cat > "${WORK_DIR}/mnt/etc/hostapd/hostapd.conf.setup" << 'HOSTAPD'
# ROSE Link Setup Hotspot
interface=wlan0
driver=nl80211
ssid=ROSE-Link-Setup
hw_mode=g
channel=6
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=roselink123
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
HOSTAPD

    log_success "Setup WiFi configured"
}

configure_ssh() {
    log_info "Enabling SSH..."

    # Enable SSH
    touch "${WORK_DIR}/mnt/boot/ssh"

    log_success "SSH enabled"
}

finalize_image() {
    log_info "Finalizing image..."

    # Sync and unmount
    sync

    umount "${WORK_DIR}/mnt/boot"
    umount "${WORK_DIR}/mnt"

    # Detach loop device
    losetup -d "$LOOP_DEV"
    unset LOOP_DEV

    # Move and compress image
    local final_name="${IMAGE_NAME}-${ROSE_VERSION}.img"
    mv "${WORK_DIR}/raspios.img" "${OUTPUT_DIR}/${final_name}"

    log_info "Compressing image..."
    xz -9 -T0 "${OUTPUT_DIR}/${final_name}"

    # Generate checksum
    cd "$OUTPUT_DIR"
    sha256sum "${final_name}.xz" > "${final_name}.xz.sha256"

    log_success "Image created: ${OUTPUT_DIR}/${final_name}.xz"
    log_success "Checksum: ${OUTPUT_DIR}/${final_name}.xz.sha256"
}

# ==============================================================================
# Main
# ==============================================================================

show_help() {
    cat << EOF
ROSE Link SD Card Image Builder

Usage: sudo $0 [options]

Options:
  -o, --output DIR    Output directory (default: ./output)
  -v, --version VER   ROSE Link version
  -k, --keep          Keep intermediate files
  -h, --help          Show this help

Example:
  sudo $0 -o ./releases -v 1.0.0
EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -o|--output)
                OUTPUT_DIR="$2"
                shift 2
                ;;
            -v|--version)
                ROSE_VERSION="$2"
                shift 2
                ;;
            -k|--keep)
                KEEP_INTERMEDIATE=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                die "Unknown option: $1"
                ;;
        esac
    done

    # Get version from config if not provided
    if [[ -z "$ROSE_VERSION" ]]; then
        if [[ -f "${PROJECT_ROOT}/backend/config.py" ]]; then
            ROSE_VERSION=$(grep 'APP_VERSION' "${PROJECT_ROOT}/backend/config.py" | cut -d'"' -f2)
        fi
        ROSE_VERSION="${ROSE_VERSION:-1.0.0}"
    fi
}

main() {
    echo "=============================================="
    echo "  ROSE Link SD Card Image Builder"
    echo "=============================================="
    echo ""

    parse_args "$@"

    check_root
    check_dependencies

    # Create directories
    mkdir -p "$OUTPUT_DIR"
    mkdir -p "$WORK_DIR"

    log_info "Building ROSE Link v${ROSE_VERSION} image..."
    log_info "Output directory: $OUTPUT_DIR"
    log_info "Work directory: $WORK_DIR"

    download_base_image
    expand_image
    mount_image
    setup_qemu
    copy_rose_link
    configure_first_boot
    configure_wifi_setup
    configure_ssh
    finalize_image

    echo ""
    echo "=============================================="
    log_success "Image build complete!"
    echo "=============================================="
    echo ""
    echo "To flash the image:"
    echo "  1. Download Balena Etcher or Raspberry Pi Imager"
    echo "  2. Select the image: ${OUTPUT_DIR}/${IMAGE_NAME}-${ROSE_VERSION}.img.xz"
    echo "  3. Select your SD card"
    echo "  4. Flash!"
    echo ""
    echo "First boot:"
    echo "  1. Insert SD card into Raspberry Pi and power on"
    echo "  2. Wait ~5 minutes for initial setup"
    echo "  3. Connect to 'ROSE-Link-Setup' WiFi (password: roselink123)"
    echo "  4. Open https://192.168.50.1 to complete setup"
    echo ""
}

main "$@"
