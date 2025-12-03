#!/bin/bash
#
# Quick install script for ROSE Link from APT repository
# Usage: curl -fsSL https://raw.githubusercontent.com/oussrh/roselink-repo/main/install.sh | sudo bash
#

set -e

GITHUB_USER="oussrh"
REPO_URL="https://$GITHUB_USER.github.io/ROSE-LINK"

echo "🌹 ROSE Link Quick Installer"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Check if Raspberry Pi
if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo "⚠️  Warning: Not a Raspberry Pi. Continue anyway? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "📦 Adding ROSE Link repository..."

# Install prerequisites
apt-get update
apt-get install -y curl gnupg

# Add GPG key
curl -fsSL "$REPO_URL/gpg.key" \
  | gpg --dearmor -o /etc/apt/trusted.gpg.d/roselink.gpg

# Add repository
echo "deb [arch=arm64,armhf signed-by=/etc/apt/trusted.gpg.d/roselink.gpg] $REPO_URL stable main" \
  | tee /etc/apt/sources.list.d/roselink.list

# Install ROSE Link
echo "📦 Installing ROSE Link Pro..."
apt-get update
apt-get install -y rose-link-pro

echo ""
echo "✅ ROSE Link installed successfully!"
echo ""
echo "📱 Access: https://roselink.local"
echo "📶 Default hotspot: ROSE-Link / RoseLink2024"
echo ""
