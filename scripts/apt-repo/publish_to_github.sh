#!/bin/bash
#
# Publish ROSE Link APT repository to GitHub Pages
#

set -e

REPO_DIR="roselink-repo"
GITHUB_REPO=""  # Set this to your GitHub repo (e.g., "username/roselink-repo")

echo "🌹 Publishing ROSE Link APT repository to GitHub Pages..."

if [ -z "$GITHUB_REPO" ]; then
    echo ""
    echo "⚠️  Please set GITHUB_REPO variable in this script"
    echo "   Example: GITHUB_REPO='yourusername/roselink-repo'"
    echo ""
    read -p "Enter your GitHub username: " github_user
    read -p "Enter repository name (default: roselink-repo): " repo_name
    repo_name=${repo_name:-roselink-repo}
    GITHUB_REPO="$github_user/$repo_name"
fi

if [ ! -d "$REPO_DIR" ]; then
    echo "❌ Error: Repository directory not found: $REPO_DIR"
    echo "   Run ./setup_repo.sh first"
    exit 1
fi

# Create GitHub Pages structure
cd "$REPO_DIR"

# Export GPG public key
if command -v gpg &>/dev/null && gpg --list-secret-keys &>/dev/null; then
    echo "🔐 Exporting GPG public key..."
    gpg --armor --export > ROSELINK-REPO.gpg
fi

# Create README for GitHub Pages
cat > README.md <<'EOF'
# 🌹 ROSE Link APT Repository

Official APT repository for ROSE Link VPN Router.

## Installation

### Add the repository

```bash
# Add GPG key
curl -fsSL https://oussrh.github.io/roselink-repo/ROSELINK-REPO.gpg \
  | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/roselink.gpg

# Add repository
echo "deb [arch=armhf,arm64 signed-by=/etc/apt/trusted.gpg.d/roselink.gpg] https://oussrh.github.io/roselink-repo bookworm main" \
  | sudo tee /etc/apt/sources.list.d/roselink.list

# Update and install
sudo apt update
sudo apt install -y rose-link-pro
```

### Quick Install (one-liner)

```bash
curl -fsSL https://raw.githubusercontent.com/oussrh/roselink-repo/main/install.sh | sudo bash
```

## About ROSE Link

ROSE Link transforms your Raspberry Pi 4 into a VPN router that:
- Connects to internet via Ethernet or WiFi
- Establishes WireGuard VPN tunnel to your Fritz!Box
- Creates a WiFi hotspot for your devices
- Routes all traffic through Belgium
- Provides a modern web interface for configuration

## Features

✅ Auto-failover WAN (Ethernet → WiFi)
✅ Multi-profile WireGuard VPN
✅ Secure WiFi hotspot (WPA2/WPA3)
✅ Kill-switch (no traffic if VPN down)
✅ Auto-reconnect watchdog
✅ Modern dark UI (Tailwind + htmx)
✅ HTTPS web interface

## Access

After installation:
- Web UI: https://roselink.local or https://192.168.50.1
- Default hotspot: ROSE-Link / RoseLink2024

## Support

- Documentation: [GitHub Wiki](https://github.com/oussrh/roselink-repo/wiki)
- Issues: [GitHub Issues](https://github.com/oussrh/roselink-repo/issues)

---

🌹 **Made with love for secure remote access**
EOF

echo "✅ README created"

# Check if git repo exists
if [ ! -d .git ]; then
    echo "📦 Initializing Git repository..."
    git init
    git checkout -b main 2>/dev/null || git checkout main
fi

# Add all files
git add .
git commit -m "Update ROSE Link APT repository" || true

# Check if remote exists
if ! git remote | grep -q origin; then
    echo "🔗 Adding GitHub remote..."
    git remote add origin "https://github.com/$GITHUB_REPO.git"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Repository prepared!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📤 Next steps:"
echo ""
echo "  1. Create GitHub repository: https://github.com/new"
echo "     Repository name: roselink-repo"
echo "     Public repository"
echo ""
echo "  2. Push to GitHub:"
echo "     git push -u origin main"
echo ""
echo "  3. Enable GitHub Pages:"
echo "     - Go to repository Settings → Pages"
echo "     - Source: Deploy from a branch"
echo "     - Branch: main, folder: / (root)"
echo "     - Save"
echo ""
echo "  4. Wait a few minutes, then access:"
echo "     https://$GITHUB_REPO/roselink-repo"
echo ""
echo "  5. Update README.md with your actual GitHub username"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd - > /dev/null
