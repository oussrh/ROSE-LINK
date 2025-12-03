#!/bin/bash
#
# ROSE Link Debian Package Builder
# Creates a proper .deb package for distribution
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
# shellcheck disable=SC2034  # YELLOW may be used in future
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DEB_DIR="$PROJECT_DIR/debian"
BUILD_DIR="$PROJECT_DIR/build"

# Read version from VERSION file (single source of truth)
if [[ -f "$PROJECT_DIR/VERSION" ]]; then
    APP_VERSION=$(cat "$PROJECT_DIR/VERSION" | tr -d '[:space:]')
else
    error "VERSION file not found at $PROJECT_DIR/VERSION"
fi

# Debian package version format: X.Y.Z-R (R = release number)
DEB_VERSION="${APP_VERSION}-1"
PACKAGE_NAME="rose-link_${DEB_VERSION}_all"

info() {
    echo -e "${CYAN}→${NC} $1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
    exit 1
}

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           🌹 ROSE Link Debian Package Builder                  ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Version: ${CYAN}${APP_VERSION}${NC} (deb: ${DEB_VERSION})"
echo ""

# Check for dpkg-deb
if ! command -v dpkg-deb &>/dev/null; then
    error "dpkg-deb not found. Install with: apt install dpkg"
fi

# Clean previous build
info "Cleaning previous build..."
rm -rf "${DEB_DIR:?}/opt" "${DEB_DIR:?}/etc" "${DEB_DIR:?}/var"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
success "Clean complete"

# Inject version into debian control file
info "Injecting version into control file..."
sed -i "s/^Version:.*/Version: ${DEB_VERSION}/" "$DEB_DIR/DEBIAN/control"
success "Control file updated to version ${DEB_VERSION}"

# Inject version into preinst script
info "Injecting version into preinst script..."
sed -i "s/__VERSION__/${APP_VERSION}/g" "$DEB_DIR/DEBIAN/preinst"
success "Preinst script updated to version ${APP_VERSION}"

# Create directory structure
info "Creating directory structure..."
mkdir -p "$DEB_DIR/opt/rose-link"/{backend,web,system/nginx}
mkdir -p "$DEB_DIR/etc/systemd/system"
mkdir -p "$DEB_DIR/etc/nginx/sites-available"
mkdir -p "$DEB_DIR/etc/sudoers.d"
mkdir -p "$DEB_DIR/var/log/rose-link"
success "Directory structure created"

# Copy application files
info "Copying application files..."

# Copy VERSION file to package root
cp "$PROJECT_DIR/VERSION" "$DEB_DIR/opt/rose-link/"
success "VERSION file copied"

# Backend
if [ -d "$PROJECT_DIR/backend" ]; then
    # Copy Python files and requirements
    cp "$PROJECT_DIR/backend"/*.py "$DEB_DIR/opt/rose-link/backend/" 2>/dev/null || true
    cp "$PROJECT_DIR/backend"/requirements*.txt "$DEB_DIR/opt/rose-link/backend/" 2>/dev/null || true

    # Copy subdirectories
    for subdir in api core services utils; do
        if [ -d "$PROJECT_DIR/backend/$subdir" ]; then
            cp -r "$PROJECT_DIR/backend/$subdir" "$DEB_DIR/opt/rose-link/backend/"
        fi
    done
    success "Backend files copied"
else
    error "Backend directory not found"
fi

# Web frontend
if [ -d "$PROJECT_DIR/web" ]; then
    # Copy HTML files
    cp "$PROJECT_DIR/web"/*.html "$DEB_DIR/opt/rose-link/web/" 2>/dev/null || true

    # Copy service worker and manifest
    cp "$PROJECT_DIR/web"/sw.js "$DEB_DIR/opt/rose-link/web/" 2>/dev/null || true
    cp "$PROJECT_DIR/web"/site.webmanifest "$DEB_DIR/opt/rose-link/web/" 2>/dev/null || true

    # Copy images (logos, icons, favicons)
    cp "$PROJECT_DIR/web"/*.webp "$DEB_DIR/opt/rose-link/web/" 2>/dev/null || true
    cp "$PROJECT_DIR/web"/*.png "$DEB_DIR/opt/rose-link/web/" 2>/dev/null || true
    cp "$PROJECT_DIR/web"/*.ico "$DEB_DIR/opt/rose-link/web/" 2>/dev/null || true

    # Copy subdirectories (css, js, icons, images, locales, vendor)
    for subdir in css js icons images locales vendor; do
        if [ -d "$PROJECT_DIR/web/$subdir" ]; then
            cp -r "$PROJECT_DIR/web/$subdir" "$DEB_DIR/opt/rose-link/web/"
        fi
    done
    success "Web frontend files copied"
else
    error "Web directory not found"
fi

# System configuration
if [ -d "$PROJECT_DIR/system" ]; then
    # Copy system scripts and configs
    cp "$PROJECT_DIR/system"/*.sh "$DEB_DIR/opt/rose-link/system/" 2>/dev/null || true
    cp "$PROJECT_DIR/system"/*.conf "$DEB_DIR/opt/rose-link/system/" 2>/dev/null || true
    cp "$PROJECT_DIR/system"/*.append "$DEB_DIR/opt/rose-link/system/" 2>/dev/null || true
    cp "$PROJECT_DIR/system/rose-sudoers" "$DEB_DIR/opt/rose-link/system/" 2>/dev/null || true
    cp "$PROJECT_DIR/system/rose-monitoring" "$DEB_DIR/opt/rose-link/system/" 2>/dev/null || true

    # Copy service files
    cp "$PROJECT_DIR/system"/*.service "$DEB_DIR/opt/rose-link/system/" 2>/dev/null || true

    # Copy Nginx config
    if [ -d "$PROJECT_DIR/system/nginx" ]; then
        cp "$PROJECT_DIR/system/nginx"/* "$DEB_DIR/opt/rose-link/system/nginx/" 2>/dev/null || true
    fi
    success "System configuration files copied"
else
    error "System directory not found"
fi

# Copy systemd services to /etc/systemd/system
info "Installing systemd services..."
cp "$PROJECT_DIR/system/rose-backend.service" "$DEB_DIR/etc/systemd/system/"
cp "$PROJECT_DIR/system/rose-watchdog.service" "$DEB_DIR/etc/systemd/system/"
success "Systemd services installed"

# Copy Nginx config
info "Installing Nginx configuration..."
if [ -f "$PROJECT_DIR/system/nginx/roselink" ]; then
    cp "$PROJECT_DIR/system/nginx/roselink" "$DEB_DIR/etc/nginx/sites-available/"
fi
success "Nginx configuration installed"

# Copy sudoers file
info "Installing sudoers configuration..."
cp "$PROJECT_DIR/system/rose-sudoers" "$DEB_DIR/etc/sudoers.d/rose"
success "Sudoers configuration installed"

# Set permissions on control scripts
info "Setting permissions..."
chmod 755 "$DEB_DIR/DEBIAN/preinst" 2>/dev/null || true
chmod 755 "$DEB_DIR/DEBIAN/postinst"
chmod 755 "$DEB_DIR/DEBIAN/prerm"
chmod 755 "$DEB_DIR/DEBIAN/postrm" 2>/dev/null || true
chmod 644 "$DEB_DIR/DEBIAN/conffiles" 2>/dev/null || true
chmod 644 "$DEB_DIR/DEBIAN/control"

# Set permissions on installed files
chmod 755 "$DEB_DIR/opt/rose-link/system"/*.sh 2>/dev/null || true
chmod 644 "$DEB_DIR/opt/rose-link/system"/*.service 2>/dev/null || true
chmod 644 "$DEB_DIR/opt/rose-link/system"/*.conf 2>/dev/null || true
chmod 440 "$DEB_DIR/etc/sudoers.d/rose"
success "Permissions set"

# Calculate installed size
info "Calculating package size..."
INSTALLED_SIZE=$(du -sk "$DEB_DIR" | cut -f1)
sed -i "s/^Installed-Size:.*/Installed-Size: $INSTALLED_SIZE/" "$DEB_DIR/DEBIAN/control"
success "Installed size: ${INSTALLED_SIZE}KB"

# Validate control file
info "Validating control file..."
if ! grep -q "^Package:" "$DEB_DIR/DEBIAN/control"; then
    error "Invalid control file: missing Package field"
fi
if ! grep -q "^Version:" "$DEB_DIR/DEBIAN/control"; then
    error "Invalid control file: missing Version field"
fi
success "Control file validated"

# Build package
info "Building Debian package..."
cd "$PROJECT_DIR"

# Use fakeroot if available for proper ownership
if command -v fakeroot &>/dev/null; then
    fakeroot dpkg-deb --build debian "$BUILD_DIR/${PACKAGE_NAME}.deb"
else
    dpkg-deb --build debian "$BUILD_DIR/${PACKAGE_NAME}.deb"
fi

# Move to project root
mv "$BUILD_DIR/${PACKAGE_NAME}.deb" "$PROJECT_DIR/"
success "Package built: ${PACKAGE_NAME}.deb"

# Verify package
info "Verifying package..."
if command -v lintian &>/dev/null; then
    echo ""
    echo -e "${CYAN}Lintian check:${NC}"
    lintian --no-tag-display-limit "$PROJECT_DIR/${PACKAGE_NAME}.deb" 2>&1 | head -20 || true
    echo ""
fi

# Show package info
info "Package information:"
dpkg-deb --info "$PROJECT_DIR/${PACKAGE_NAME}.deb" 2>/dev/null | head -15

# Cleanup build directory
rm -rf "$BUILD_DIR"
rm -rf "${DEB_DIR:?}/opt" "${DEB_DIR:?}/etc" "${DEB_DIR:?}/var"

# Restore preinst template placeholder for next build
sed -i "s/VERSION=\"${APP_VERSION}\"/VERSION=\"__VERSION__\"/g" "$DEB_DIR/DEBIAN/preinst"

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           🎉 Package Build Complete!                           ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Package: ${CYAN}${PACKAGE_NAME}.deb${NC}"
echo -e "Size: ${CYAN}$(du -h "$PROJECT_DIR/${PACKAGE_NAME}.deb" | cut -f1)${NC}"
echo ""
echo -e "Install with:"
echo -e "  ${CYAN}sudo apt install ./${PACKAGE_NAME}.deb${NC}"
echo ""
echo -e "Or for remote installation:"
echo -e "  ${CYAN}scp ${PACKAGE_NAME}.deb pi@raspberrypi.local:~/${NC}"
echo -e "  ${CYAN}ssh pi@raspberrypi.local 'sudo apt install ~/${PACKAGE_NAME}.deb'${NC}"
echo ""
