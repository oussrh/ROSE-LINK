#!/bin/bash
# Script to update APT repository with new packages
# Run this on a Linux machine with dpkg-scanpackages

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
GPG_KEY="ROSE Link"

echo "Updating APT repository..."

# Generate Packages files for each architecture
for arch in arm64 armhf; do
    echo "Generating Packages for $arch..."

    PACKAGES_DIR="$REPO_DIR/dists/stable/main/binary-$arch"
    mkdir -p "$PACKAGES_DIR"

    # Scan packages
    cd "$REPO_DIR"
    dpkg-scanpackages --arch "$arch" pool/ > "$PACKAGES_DIR/Packages"
    gzip -9c "$PACKAGES_DIR/Packages" > "$PACKAGES_DIR/Packages.gz"

    echo "  Created $PACKAGES_DIR/Packages"
done

# Generate Release file with checksums
echo "Generating Release file..."

cd "$REPO_DIR/dists/stable"

# Create Release file
cat > Release << EOF
Origin: ROSE Link
Label: ROSE Link APT Repository
Suite: stable
Codename: stable
Architectures: arm64 armhf
Components: main
Description: Official APT repository for ROSE Link - Raspberry Pi VPN Router
Date: $(date -Ru)
EOF

# Add checksums
echo "MD5Sum:" >> Release
for file in main/binary-*/Packages main/binary-*/Packages.gz; do
    if [ -f "$file" ]; then
        echo " $(md5sum "$file" | cut -d' ' -f1) $(wc -c < "$file") $file" >> Release
    fi
done

echo "SHA256:" >> Release
for file in main/binary-*/Packages main/binary-*/Packages.gz; do
    if [ -f "$file" ]; then
        echo " $(sha256sum "$file" | cut -d' ' -f1) $(wc -c < "$file") $file" >> Release
    fi
done

# Sign Release file
echo "Signing Release file..."
gpg --default-key "$GPG_KEY" -abs -o Release.gpg Release
gpg --default-key "$GPG_KEY" --clearsign -o InRelease Release

echo ""
echo "Repository updated successfully!"
echo ""
echo "Files to commit:"
find "$REPO_DIR" -name "Packages*" -o -name "Release*" -o -name "InRelease" | head -20
