#!/bin/bash
#
# Setup APT repository structure for ROSE Link
# This creates a local APT repo that can be published to GitHub Pages
#

set -e

REPO_DIR="roselink-repo"
DIST="bookworm"
COMPONENT="main"
# shellcheck disable=SC2034  # ARCH may be used for multi-arch support in future
ARCH="armhf arm64 all"

echo "🌹 Setting up ROSE Link APT repository..."

# Create directory structure
mkdir -p "$REPO_DIR/dists/$DIST/$COMPONENT/binary-armhf"
mkdir -p "$REPO_DIR/dists/$DIST/$COMPONENT/binary-arm64"
mkdir -p "$REPO_DIR/dists/$DIST/$COMPONENT/binary-all"
mkdir -p "$REPO_DIR/pool/$COMPONENT"

echo "✅ Repository structure created in $REPO_DIR/"
echo ""
echo "Next steps:"
echo "  1. Run ./add_package.sh <path-to-deb> to add packages"
echo "  2. Run ./publish_to_github.sh to publish to GitHub Pages"
