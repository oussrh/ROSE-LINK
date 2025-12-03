#!/bin/bash
#
# Add a package to the ROSE Link APT repository
#

set -e

if [ $# -lt 1 ]; then
    echo "Usage: $0 <path-to-deb-file>"
    exit 1
fi

DEB_FILE="$1"
REPO_DIR="roselink-repo"
DIST="bookworm"
COMPONENT="main"

if [ ! -f "$DEB_FILE" ]; then
    echo "❌ Error: File not found: $DEB_FILE"
    exit 1
fi

echo "🌹 Adding package to repository..."

# Check if dpkg-scanpackages is available
if ! command -v dpkg-scanpackages &>/dev/null; then
    echo "❌ dpkg-scanpackages not found. Installing dpkg-dev..."
    sudo apt-get install -y dpkg-dev
fi

# Copy package to pool
cp "$DEB_FILE" "$REPO_DIR/pool/$COMPONENT/"

# Generate Packages files
for arch in armhf arm64 all; do
    echo "📦 Generating Packages file for $arch..."
    cd "$REPO_DIR"

    dpkg-scanpackages --arch "$arch" "pool/$COMPONENT" > "dists/$DIST/$COMPONENT/binary-$arch/Packages"

    gzip -9fk "dists/$DIST/$COMPONENT/binary-$arch/Packages"

    cd - > /dev/null
done

# Generate Release file
echo "📝 Generating Release file..."
cd "$REPO_DIR/dists/$DIST"

cat > Release <<EOF
Origin: ROSE Link
Label: ROSE Link
Suite: $DIST
Codename: $DIST
Architectures: armhf arm64 all
Components: $COMPONENT
Description: ROSE Link VPN Router packages
Date: $(date -Ru)
EOF

# Add checksums
echo "MD5Sum:" >> Release
for file in $(find . -type f | grep -v Release); do
    md5sum "$file" | sed "s|./| |" >> Release
done

echo "SHA256:" >> Release
for file in $(find . -type f | grep -v Release); do
    sha256sum "$file" | sed "s|./| |" >> Release
done

cd - > /dev/null

# Sign Release file (if GPG key exists)
if command -v gpg &>/dev/null && gpg --list-secret-keys &>/dev/null; then
    echo "🔐 Signing Release file..."
    cd "$REPO_DIR/dists/$DIST"
    gpg --default-key "${GPG_KEY_ID:-$(gpg --list-secret-keys --keyid-format LONG | grep sec | awk '{print $2}' | cut -d'/' -f2 | head -1)}" -abs -o Release.gpg Release
    gpg --default-key "${GPG_KEY_ID:-$(gpg --list-secret-keys --keyid-format LONG | grep sec | awk '{print $2}' | cut -d'/' -f2 | head -1)}" --clearsign -o InRelease Release
    cd - > /dev/null
    echo "✅ Release file signed"
else
    echo "⚠️  GPG key not found. Repository will work but without signature verification."
    echo "   To create a GPG key: gpg --full-generate-key"
fi

echo "✅ Package added successfully!"
echo ""
echo "📦 Repository ready in $REPO_DIR/"
