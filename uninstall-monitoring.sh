#!/bin/bash
#
# ROSE Link Monitoring Stack Uninstall Script
# Removes Prometheus, Node Exporter, and Grafana
#

set -euo pipefail

readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m'

echo -e "${YELLOW}ROSE Link Monitoring Stack Uninstaller${NC}"
echo ""

# Check root
if [[ "$EUID" -ne 0 ]]; then
    echo -e "${RED}Error: This script must be run as root (sudo)${NC}"
    exit 1
fi

read -p "This will remove Prometheus, Node Exporter, and Grafana. Continue? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo -e "\n${YELLOW}Stopping services...${NC}"
systemctl stop prometheus 2>/dev/null || true
systemctl stop node_exporter 2>/dev/null || true
systemctl stop grafana-server 2>/dev/null || true

echo -e "${YELLOW}Disabling services...${NC}"
systemctl disable prometheus 2>/dev/null || true
systemctl disable node_exporter 2>/dev/null || true
systemctl disable grafana-server 2>/dev/null || true

echo -e "${YELLOW}Removing systemd services...${NC}"
rm -f /etc/systemd/system/prometheus.service
rm -f /etc/systemd/system/node_exporter.service
systemctl daemon-reload

echo -e "${YELLOW}Removing Prometheus...${NC}"
rm -f /usr/local/bin/prometheus
rm -f /usr/local/bin/promtool
rm -rf /etc/prometheus
rm -rf /var/lib/prometheus

echo -e "${YELLOW}Removing Node Exporter...${NC}"
rm -f /usr/local/bin/node_exporter

echo -e "${YELLOW}Removing Grafana...${NC}"
apt-get remove -y grafana 2>/dev/null || true
apt-get autoremove -y 2>/dev/null || true
rm -rf /etc/grafana
rm -rf /var/lib/grafana

echo -e "${YELLOW}Removing prometheus user...${NC}"
userdel prometheus 2>/dev/null || true

echo -e "${YELLOW}Removing Grafana repository...${NC}"
rm -f /etc/apt/sources.list.d/grafana.list
rm -f /usr/share/keyrings/grafana.key

echo -e "${YELLOW}Cleaning up Nginx configuration...${NC}"
if [[ -f /etc/nginx/sites-available/roselink ]]; then
    # Remove Grafana location block
    sed -i '/# Grafana Dashboard/,/^    }/d' /etc/nginx/sites-available/roselink
    nginx -t 2>/dev/null && systemctl reload nginx 2>/dev/null || true
fi

echo ""
echo -e "${GREEN}Monitoring stack removed successfully!${NC}"
echo -e "${YELLOW}Note: The ROSE Link core installation remains intact.${NC}"
