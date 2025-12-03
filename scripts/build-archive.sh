#!/bin/bash
#
# Build ROSE Link archive (tar.gz)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🌹 Building ROSE Link archive..."

# Create temporary directory
BUILD_DIR=$(mktemp -d)
ROSE_DIR="$BUILD_DIR/rose-link"

mkdir -p "$ROSE_DIR"

# Copy files
echo "📦 Copying files..."
cp -r "$PROJECT_DIR/backend" "$ROSE_DIR/"
cp -r "$PROJECT_DIR/web" "$ROSE_DIR/"
cp -r "$PROJECT_DIR/system" "$ROSE_DIR/"
cp "$PROJECT_DIR/install.sh" "$ROSE_DIR/"
cp "$PROJECT_DIR/README.md" "$ROSE_DIR/" 2>/dev/null || true

# Create archive
echo "🗜️  Creating archive..."
cd "$BUILD_DIR"
tar -czf "$PROJECT_DIR/rose-link-pro.tar.gz" rose-link/

# Cleanup
rm -rf "$BUILD_DIR"

echo "✅ Archive built: rose-link-pro.tar.gz"
echo ""
echo "📦 Install with:"
echo "   tar -xzf rose-link-pro.tar.gz"
echo "   cd rose-link"
echo "   sudo bash install.sh"
