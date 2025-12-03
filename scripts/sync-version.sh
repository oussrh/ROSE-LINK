#!/bin/bash
#
# ROSE Link Version Sync Script
# Synchronizes version across all components from the VERSION file
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

info() {
    echo -e "${CYAN}→${NC} $1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
    exit 1
}

# Read version from VERSION file
if [[ -f "$PROJECT_DIR/VERSION" ]]; then
    VERSION=$(cat "$PROJECT_DIR/VERSION" | tr -d '[:space:]')
else
    error "VERSION file not found at $PROJECT_DIR/VERSION"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           🌹 ROSE Link Version Sync                            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Syncing all components to version: ${CYAN}${VERSION}${NC}"
echo ""

# Update web/package.json
if [[ -f "$PROJECT_DIR/web/package.json" ]]; then
    info "Updating web/package.json..."
    # Use node/jq if available, otherwise sed
    if command -v node &>/dev/null; then
        node -e "
            const fs = require('fs');
            const pkg = JSON.parse(fs.readFileSync('$PROJECT_DIR/web/package.json'));
            pkg.version = '$VERSION';
            fs.writeFileSync('$PROJECT_DIR/web/package.json', JSON.stringify(pkg, null, 2) + '\n');
        "
    else
        sed -i "s/\"version\": \"[^\"]*\"/\"version\": \"$VERSION\"/" "$PROJECT_DIR/web/package.json"
    fi
    success "web/package.json updated"
fi

# Update e2e/package.json (if exists)
if [[ -f "$PROJECT_DIR/e2e/package.json" ]]; then
    info "Updating e2e/package.json..."
    if command -v node &>/dev/null; then
        node -e "
            const fs = require('fs');
            const pkg = JSON.parse(fs.readFileSync('$PROJECT_DIR/e2e/package.json'));
            pkg.version = '$VERSION';
            fs.writeFileSync('$PROJECT_DIR/e2e/package.json', JSON.stringify(pkg, null, 2) + '\n');
        "
    else
        sed -i "s/\"version\": \"[^\"]*\"/\"version\": \"$VERSION\"/" "$PROJECT_DIR/e2e/package.json"
    fi
    success "e2e/package.json updated"
fi

# Update debian/DEBIAN/control (for manual sync, build-deb.sh also does this)
if [[ -f "$PROJECT_DIR/debian/DEBIAN/control" ]]; then
    info "Updating debian/DEBIAN/control..."
    sed -i "s/^Version:.*/Version: ${VERSION}-1/" "$PROJECT_DIR/debian/DEBIAN/control"
    success "debian/DEBIAN/control updated"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           ✓ Version Sync Complete                              ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "All components synced to version ${CYAN}${VERSION}${NC}"
echo ""
echo -e "Files updated:"
echo -e "  - web/package.json"
echo -e "  - e2e/package.json (if exists)"
echo -e "  - debian/DEBIAN/control"
echo ""
echo -e "Note: The website (website/package.json) maintains its own version"
echo -e "      as it's a separate marketing site."
echo ""
