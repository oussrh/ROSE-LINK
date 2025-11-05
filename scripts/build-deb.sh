#!/bin/bash
#
# Build ROSE Link Debian package
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DEB_DIR="$PROJECT_DIR/debian"

echo "🌹 Building ROSE Link Debian package..."

# Clean previous build
rm -rf "$DEB_DIR/opt" "$DEB_DIR/etc"

# Create directory structure
mkdir -p "$DEB_DIR/opt/rose-link"/{backend,web,system}
mkdir -p "$DEB_DIR/etc/systemd/system"
mkdir -p "$DEB_DIR/etc/nginx/sites-available"
mkdir -p "$DEB_DIR/etc/sudoers.d"

# Copy files
echo "📦 Copying files..."
cp -r "$PROJECT_DIR/backend"/* "$DEB_DIR/opt/rose-link/backend/"
cp -r "$PROJECT_DIR/web"/* "$DEB_DIR/opt/rose-link/web/"
cp -r "$PROJECT_DIR/system"/* "$DEB_DIR/opt/rose-link/system/"

# Copy systemd services
cp "$PROJECT_DIR/system/rose-backend.service" "$DEB_DIR/etc/systemd/system/"
cp "$PROJECT_DIR/system/rose-watchdog.service" "$DEB_DIR/etc/systemd/system/"

# Copy Nginx config
cp "$PROJECT_DIR/system/nginx/roselink" "$DEB_DIR/etc/nginx/sites-available/"

# Copy sudoers
cp "$PROJECT_DIR/system/rose-sudoers" "$DEB_DIR/etc/sudoers.d/rose"

# Set permissions on control scripts
chmod 755 "$DEB_DIR/DEBIAN/postinst"
chmod 755 "$DEB_DIR/DEBIAN/prerm"

# Build package
echo "🔨 Building package..."
cd "$PROJECT_DIR"
dpkg-deb --build debian

# Rename package
mv debian.deb rose-link-pro_0.1.0-1_all.deb

echo "✅ Package built: rose-link-pro_0.1.0-1_all.deb"
echo ""
echo "📦 Install with:"
echo "   sudo apt-get install ./rose-link-pro_0.1.0-1_all.deb"
