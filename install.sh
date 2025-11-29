#!/bin/bash
# ROSE Link APT Repository Setup Script

set -e

REPO_URL="https://oussrh.github.io/ROSE-LINK"
KEYRING_PATH="/usr/share/keyrings/rose-link.gpg"
SOURCES_PATH="/etc/apt/sources.list.d/rose-link.list"

echo "==================================="
echo "  ROSE Link APT Repository Setup"
echo "==================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: Please run as root (use sudo)"
    exit 1
fi

# Check architecture
ARCH=$(dpkg --print-architecture)
if [[ "$ARCH" != "arm64" && "$ARCH" != "armhf" ]]; then
    echo "Warning: This package is designed for Raspberry Pi (arm64/armhf)"
    echo "Detected architecture: $ARCH"
    echo ""
    read -p "Continue anyway? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "[1/4] Adding GPG key..."
curl -fsSL "$REPO_URL/gpg.key" | gpg --dearmor -o "$KEYRING_PATH"
chmod 644 "$KEYRING_PATH"
echo "      Done"

echo ""
echo "[2/4] Adding repository..."
echo "deb [arch=arm64,armhf signed-by=$KEYRING_PATH] $REPO_URL stable main" > "$SOURCES_PATH"
echo "      Done"

echo ""
echo "[3/4] Updating package lists..."
apt-get update -qq
echo "      Done"

echo ""
echo "[4/4] Repository added successfully!"
echo ""
echo "You can now install ROSE Link with:"
echo ""
echo "  sudo apt install rose-link"
echo ""
