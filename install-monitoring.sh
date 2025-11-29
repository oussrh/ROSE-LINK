#!/bin/bash
#
# ROSE Link Monitoring Stack Installation Script
# Installs Prometheus and Grafana natively on Raspberry Pi
# Compatible with: Raspberry Pi 4, 5 (1GB+ RAM recommended)
#

set -euo pipefail
trap 'handle_error $? $LINENO' ERR

# ===== Configuration =====
readonly VERSION="1.0.0"
readonly PROMETHEUS_VERSION="2.47.0"
readonly NODE_EXPORTER_VERSION="1.6.1"
readonly INSTALL_DIR="/opt/rose-link"
readonly MONITORING_DIR="/opt/rose-link/monitoring"
readonly PROMETHEUS_USER="prometheus"
readonly GRAFANA_PASSWORD="${GRAFANA_PASSWORD:-roselink}"
readonly LOG_FILE="/var/log/rose-link-monitoring-install.log"
readonly MIN_RAM_MB=1024

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly BOLD='\033[1m'
readonly NC='\033[0m'

# Architecture detection
ARCH=""
PROMETHEUS_ARCH=""

# ===== Utility Functions =====

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

handle_error() {
    local exit_code=$1
    local line_number=$2
    log "ERROR" "Installation failed at line $line_number with exit code $exit_code"
    echo -e "\n${RED}Installation Error at line $line_number (exit code: $exit_code)${NC}"
    echo -e "${YELLOW}Check the log file: $LOG_FILE${NC}"
    exit "$exit_code"
}

print_banner() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║         ROSE Link Monitoring Stack Installer v${VERSION}              ║"
    echo "║              Prometheus + Grafana for Raspberry Pi                ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

step_info() {
    echo -e "   ${CYAN}→${NC} $1"
}

step_done() {
    echo -e "   ${GREEN}✓${NC} Done"
}

step_warning() {
    echo -e "   ${YELLOW}⚠${NC} $1"
}

step_error() {
    echo -e "   ${RED}✗${NC} $1"
}

# ===== Pre-flight Checks =====

check_root() {
    if [[ "$EUID" -ne 0 ]]; then
        echo -e "${RED}Error: This script must be run as root (sudo)${NC}"
        exit 1
    fi
}

check_rose_link_installed() {
    if [[ ! -d "$INSTALL_DIR" ]]; then
        echo -e "${RED}Error: ROSE Link is not installed${NC}"
        echo -e "${YELLOW}Please install ROSE Link first: sudo bash install.sh${NC}"
        exit 1
    fi

    if ! systemctl is-active --quiet rose-backend 2>/dev/null; then
        step_warning "rose-backend service is not running"
        echo -e "${YELLOW}   Start it with: sudo systemctl start rose-backend${NC}"
    fi
}

check_resources() {
    local ram_mb
    ram_mb=$(free -m | awk '/^Mem:/{print $2}')

    if [[ "$ram_mb" -lt "$MIN_RAM_MB" ]]; then
        echo -e "${YELLOW}Warning: Low RAM detected (${ram_mb}MB)${NC}"
        echo -e "${YELLOW}Monitoring stack requires at least 1GB RAM for optimal performance${NC}"
        echo -e "${YELLOW}Consider using Raspberry Pi 4/5 with 2GB+ RAM${NC}"
        read -p "Continue anyway? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 0
        fi
    fi
}

detect_architecture() {
    ARCH=$(uname -m)
    case "$ARCH" in
        aarch64|arm64)
            PROMETHEUS_ARCH="arm64"
            ;;
        armv7l|armhf)
            PROMETHEUS_ARCH="armv7"
            ;;
        x86_64)
            PROMETHEUS_ARCH="amd64"
            ;;
        *)
            echo -e "${RED}Unsupported architecture: $ARCH${NC}"
            exit 1
            ;;
    esac
    step_info "Detected architecture: $ARCH (prometheus: $PROMETHEUS_ARCH)"
}

# ===== Installation Functions =====

install_prometheus() {
    echo -e "\n${BOLD}[1/5] Installing Prometheus${NC}"

    local prometheus_url="https://github.com/prometheus/prometheus/releases/download/v${PROMETHEUS_VERSION}/prometheus-${PROMETHEUS_VERSION}.linux-${PROMETHEUS_ARCH}.tar.gz"
    local tmp_dir="/tmp/prometheus_install"

    step_info "Creating prometheus user..."
    if ! id -u "$PROMETHEUS_USER" &>/dev/null; then
        useradd -r -s /usr/sbin/nologin -d /var/lib/prometheus -c "Prometheus" "$PROMETHEUS_USER"
    fi

    step_info "Creating directories..."
    mkdir -p /etc/prometheus
    mkdir -p /var/lib/prometheus
    mkdir -p "$tmp_dir"

    step_info "Downloading Prometheus v${PROMETHEUS_VERSION}..."
    curl -sL "$prometheus_url" -o "$tmp_dir/prometheus.tar.gz"

    step_info "Extracting..."
    tar -xzf "$tmp_dir/prometheus.tar.gz" -C "$tmp_dir"

    step_info "Installing binaries..."
    cp "$tmp_dir/prometheus-${PROMETHEUS_VERSION}.linux-${PROMETHEUS_ARCH}/prometheus" /usr/local/bin/
    cp "$tmp_dir/prometheus-${PROMETHEUS_VERSION}.linux-${PROMETHEUS_ARCH}/promtool" /usr/local/bin/
    chmod +x /usr/local/bin/prometheus /usr/local/bin/promtool

    step_info "Installing console templates..."
    cp -r "$tmp_dir/prometheus-${PROMETHEUS_VERSION}.linux-${PROMETHEUS_ARCH}/consoles" /etc/prometheus/
    cp -r "$tmp_dir/prometheus-${PROMETHEUS_VERSION}.linux-${PROMETHEUS_ARCH}/console_libraries" /etc/prometheus/

    # Set ownership
    chown -R "$PROMETHEUS_USER:$PROMETHEUS_USER" /etc/prometheus
    chown -R "$PROMETHEUS_USER:$PROMETHEUS_USER" /var/lib/prometheus

    # Cleanup
    rm -rf "$tmp_dir"

    step_done
}

install_node_exporter() {
    echo -e "\n${BOLD}[2/5] Installing Node Exporter${NC}"

    local node_exporter_url="https://github.com/prometheus/node_exporter/releases/download/v${NODE_EXPORTER_VERSION}/node_exporter-${NODE_EXPORTER_VERSION}.linux-${PROMETHEUS_ARCH}.tar.gz"
    local tmp_dir="/tmp/node_exporter_install"

    mkdir -p "$tmp_dir"

    step_info "Downloading Node Exporter v${NODE_EXPORTER_VERSION}..."
    curl -sL "$node_exporter_url" -o "$tmp_dir/node_exporter.tar.gz"

    step_info "Extracting..."
    tar -xzf "$tmp_dir/node_exporter.tar.gz" -C "$tmp_dir"

    step_info "Installing binary..."
    cp "$tmp_dir/node_exporter-${NODE_EXPORTER_VERSION}.linux-${PROMETHEUS_ARCH}/node_exporter" /usr/local/bin/
    chmod +x /usr/local/bin/node_exporter

    # Cleanup
    rm -rf "$tmp_dir"

    step_done
}

install_grafana() {
    echo -e "\n${BOLD}[3/5] Installing Grafana${NC}"

    step_info "Adding Grafana APT repository..."

    # Install prerequisites
    apt-get install -y -qq apt-transport-https software-properties-common wget gnupg2

    # Add Grafana GPG key
    wget -q -O /usr/share/keyrings/grafana.key https://apt.grafana.com/gpg.key

    # Add repository
    echo "deb [signed-by=/usr/share/keyrings/grafana.key] https://apt.grafana.com stable main" > /etc/apt/sources.list.d/grafana.list

    step_info "Updating package lists..."
    apt-get update -qq

    step_info "Installing Grafana..."
    apt-get install -y -qq grafana

    step_done
}

configure_prometheus() {
    echo -e "\n${BOLD}[4/5] Configuring Monitoring Stack${NC}"

    step_info "Creating Prometheus configuration..."

    cat > /etc/prometheus/prometheus.yml << 'EOF'
# ROSE-LINK Prometheus Configuration (Native Installation)
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'rose-link-monitor'

# Alerting rules
rule_files:
  - "alerts.yml"

# Scrape configuration
scrape_configs:
  # ROSE-LINK Backend Metrics
  - job_name: 'rose-link'
    metrics_path: '/api/metrics'
    scrape_interval: 10s
    scrape_timeout: 5s
    static_configs:
      - targets: ['localhost:8000']
        labels:
          instance: 'rose-link-backend'
          environment: 'production'
    honor_labels: true

  # Prometheus self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Node Exporter (system metrics)
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']
        labels:
          instance: 'rose-link-host'
EOF

    step_info "Creating alert rules..."

    cat > /etc/prometheus/alerts.yml << 'EOF'
# ROSE-LINK Alert Rules
groups:
  - name: rose-link-alerts
    rules:
      # VPN Connection Alerts
      - alert: VPNDisconnected
        expr: rose_link_vpn_status == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "VPN connection is down"
          description: "The VPN connection has been disconnected for more than 1 minute."

      # WAN Connection Alerts
      - alert: WANDisconnected
        expr: rose_link_wan_status == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "WAN connection is down"
          description: "The WAN connection has been disconnected for more than 2 minutes."

      # CPU Temperature Alerts
      - alert: HighCPUTemperature
        expr: rose_link_cpu_temperature_celsius > 70
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU temperature detected"
          description: "CPU temperature is {{ $value }}C, which exceeds the safe threshold."

      - alert: CriticalCPUTemperature
        expr: rose_link_cpu_temperature_celsius > 80
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Critical CPU temperature"
          description: "CPU temperature is {{ $value }}C. Immediate attention required."

      # CPU Usage Alerts
      - alert: HighCPUUsage
        expr: rose_link_cpu_usage_percent > 90
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage"
          description: "CPU usage has been above 90% for more than 5 minutes."

      # Memory Alerts
      - alert: HighMemoryUsage
        expr: (rose_link_memory_used_bytes / rose_link_memory_total_bytes) * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is above 85%."

      - alert: CriticalMemoryUsage
        expr: (rose_link_memory_used_bytes / rose_link_memory_total_bytes) * 100 > 95
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Critical memory usage"
          description: "Memory usage is above 95%. System may become unstable."

      # Disk Space Alerts
      - alert: LowDiskSpace
        expr: (rose_link_disk_used_bytes / rose_link_disk_total_bytes) * 100 > 80
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Low disk space"
          description: "Disk usage is above 80%."

      - alert: CriticalDiskSpace
        expr: (rose_link_disk_used_bytes / rose_link_disk_total_bytes) * 100 > 95
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Critical disk space"
          description: "Disk usage is above 95%. Immediate action required."

      # Hotspot Alerts
      - alert: HotspotDown
        expr: rose_link_hotspot_status == 0
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Hotspot is not active"
          description: "The WiFi hotspot has been inactive for more than 2 minutes."

      # Service Health
      - alert: RoseLinkDown
        expr: up{job="rose-link"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "ROSE-LINK backend is down"
          description: "The ROSE-LINK backend service is not responding."

      # Node Exporter Alerts (System Level)
      - alert: HostOutOfMemory
        expr: node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes * 100 < 10
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Host out of memory"
          description: "Node memory is filling up (< 10% left)"

      - alert: HostHighCpuLoad
        expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[2m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Host high CPU load"
          description: "CPU load is > 80%"
EOF

    chown -R "$PROMETHEUS_USER:$PROMETHEUS_USER" /etc/prometheus

    step_done
}

configure_grafana() {
    step_info "Configuring Grafana..."

    # Create provisioning directories
    mkdir -p /etc/grafana/provisioning/datasources
    mkdir -p /etc/grafana/provisioning/dashboards
    mkdir -p /var/lib/grafana/dashboards

    # Configure datasources
    cat > /etc/grafana/provisioning/datasources/datasources.yml << 'EOF'
# ROSE-LINK Grafana Datasources (Native Installation)
apiVersion: 1

datasources:
  # Prometheus - Primary metrics source
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://localhost:9090
    isDefault: true
    editable: false
    jsonData:
      timeInterval: "10s"
      httpMethod: POST
      manageAlerts: true
      prometheusType: Prometheus
      prometheusVersion: 2.47.0
EOF

    # Configure dashboard provisioning
    cat > /etc/grafana/provisioning/dashboards/dashboards.yml << 'EOF'
# ROSE-LINK Grafana Dashboard Provisioning
apiVersion: 1

providers:
  - name: 'ROSE-LINK Dashboards'
    orgId: 1
    folder: 'ROSE-LINK'
    folderUid: 'rose-link'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
      foldersFromFilesStructure: false
EOF

    # Copy dashboard if it exists in the monitoring folder
    if [[ -f "$INSTALL_DIR/monitoring/grafana/dashboards/rose-link-dashboard.json" ]]; then
        cp "$INSTALL_DIR/monitoring/grafana/dashboards/rose-link-dashboard.json" /var/lib/grafana/dashboards/
        step_info "Dashboard provisioned from existing configuration"
    elif [[ -f "monitoring/grafana/dashboards/rose-link-dashboard.json" ]]; then
        cp "monitoring/grafana/dashboards/rose-link-dashboard.json" /var/lib/grafana/dashboards/
        step_info "Dashboard provisioned from local files"
    else
        step_warning "Dashboard file not found - you'll need to import it manually"
    fi

    # Update Grafana configuration
    cat > /etc/grafana/grafana.ini << EOF
[server]
http_port = 3000
root_url = http://localhost:3000

[security]
admin_user = admin
admin_password = ${GRAFANA_PASSWORD}

[users]
allow_sign_up = false

[auth.anonymous]
enabled = true
org_role = Viewer

[dashboards]
default_home_dashboard_path = /var/lib/grafana/dashboards/rose-link-dashboard.json

[plugins]
allow_loading_unsigned_plugins = grafana-simple-json-datasource
EOF

    chown -R grafana:grafana /var/lib/grafana
    chown -R grafana:grafana /etc/grafana

    step_done
}

create_systemd_services() {
    echo -e "\n${BOLD}[5/5] Creating Systemd Services${NC}"

    step_info "Creating Prometheus service..."

    cat > /etc/systemd/system/prometheus.service << EOF
[Unit]
Description=Prometheus Monitoring System
Documentation=https://prometheus.io/docs/introduction/overview/
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${PROMETHEUS_USER}
Group=${PROMETHEUS_USER}
ExecReload=/bin/kill -HUP \$MAINPID
ExecStart=/usr/local/bin/prometheus \\
  --config.file=/etc/prometheus/prometheus.yml \\
  --storage.tsdb.path=/var/lib/prometheus \\
  --web.console.templates=/etc/prometheus/consoles \\
  --web.console.libraries=/etc/prometheus/console_libraries \\
  --storage.tsdb.retention.time=15d \\
  --web.enable-lifecycle \\
  --web.listen-address=0.0.0.0:9090

SyslogIdentifier=prometheus
Restart=always
RestartSec=10

# Resource limits for Raspberry Pi
MemoryMax=256M
CPUQuota=50%

[Install]
WantedBy=multi-user.target
EOF

    step_info "Creating Node Exporter service..."

    cat > /etc/systemd/system/node_exporter.service << EOF
[Unit]
Description=Prometheus Node Exporter
Documentation=https://github.com/prometheus/node_exporter
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${PROMETHEUS_USER}
Group=${PROMETHEUS_USER}
ExecStart=/usr/local/bin/node_exporter \\
  --collector.filesystem.mount-points-exclude='^/(sys|proc|dev|host|etc)($$|/)' \\
  --web.listen-address=:9100

SyslogIdentifier=node_exporter
Restart=always
RestartSec=10

# Resource limits
MemoryMax=64M
CPUQuota=20%

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd
    systemctl daemon-reload

    step_done
}

enable_and_start_services() {
    step_info "Enabling services..."

    systemctl enable prometheus
    systemctl enable node_exporter
    systemctl enable grafana-server

    step_info "Starting services..."

    systemctl start prometheus
    sleep 2
    systemctl start node_exporter
    sleep 2
    systemctl start grafana-server

    step_done
}

configure_nginx_proxy() {
    step_info "Configuring Nginx proxy for Grafana..."

    # Check if nginx config exists
    if [[ -f /etc/nginx/sites-available/roselink ]]; then
        # Add Grafana location block if not already present
        if ! grep -q "location /grafana" /etc/nginx/sites-available/roselink; then
            # Insert before the last closing brace
            sed -i '/^}$/i\
    # Grafana Dashboard\
    location /grafana/ {\
        proxy_pass http://127.0.0.1:3000/;\
        proxy_http_version 1.1;\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
        proxy_set_header Upgrade $http_upgrade;\
        proxy_set_header Connection "upgrade";\
    }' /etc/nginx/sites-available/roselink

            # Update Grafana root_url
            sed -i 's|root_url = http://localhost:3000|root_url = %(protocol)s://%(domain)s/grafana/|' /etc/grafana/grafana.ini
            echo "serve_from_sub_path = true" >> /etc/grafana/grafana.ini

            # Test and reload nginx
            if nginx -t 2>&1 | grep -q "successful"; then
                systemctl reload nginx
                step_info "Grafana available at https://roselink.local/grafana/"
            else
                step_warning "Nginx configuration error - Grafana accessible on port 3000 only"
            fi
        else
            step_info "Grafana proxy already configured"
        fi
    else
        step_warning "Nginx not configured - Grafana accessible on port 3000 directly"
    fi
}

print_summary() {
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║            Monitoring Stack Installation Complete!                ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BOLD}Services Status:${NC}"

    for service in prometheus node_exporter grafana-server; do
        if systemctl is-active --quiet "$service" 2>/dev/null; then
            echo -e "   ${GREEN}●${NC} $service: ${GREEN}running${NC}"
        else
            echo -e "   ${RED}●${NC} $service: ${RED}stopped${NC}"
        fi
    done

    echo ""
    echo -e "${BOLD}Access URLs:${NC}"
    echo -e "   Grafana:    ${CYAN}https://roselink.local/grafana/${NC}"
    echo -e "               ${CYAN}http://192.168.50.1:3000${NC}"
    echo -e "   Prometheus: ${CYAN}http://192.168.50.1:9090${NC}"
    echo ""
    echo -e "${BOLD}Grafana Credentials:${NC}"
    echo -e "   Username: ${GREEN}admin${NC}"
    echo -e "   Password: ${GREEN}${GRAFANA_PASSWORD}${NC}"
    echo ""
    echo -e "${BOLD}Data Retention:${NC}"
    echo -e "   Prometheus: 15 days (to save disk space on Pi)"
    echo ""
    echo -e "${YELLOW}Note: Resource limits are applied to protect your Raspberry Pi${NC}"
    echo -e "${YELLOW}      Prometheus: max 256MB RAM, 50% CPU${NC}"
    echo -e "${YELLOW}      Node Exporter: max 64MB RAM, 20% CPU${NC}"
    echo ""
}

show_help() {
    echo "ROSE Link Monitoring Stack Installer v${VERSION}"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  --grafana-password PASS Set Grafana admin password (default: roselink)"
    echo ""
    echo "Environment variables:"
    echo "  GRAFANA_PASSWORD        Grafana admin password"
    echo ""
    echo "This script installs:"
    echo "  - Prometheus v${PROMETHEUS_VERSION} (metrics collection)"
    echo "  - Node Exporter v${NODE_EXPORTER_VERSION} (system metrics)"
    echo "  - Grafana (dashboard visualization)"
    echo ""
    echo "Requirements:"
    echo "  - ROSE Link must be installed first"
    echo "  - Raspberry Pi 4/5 with 1GB+ RAM recommended"
    echo "  - ~500MB disk space"
    echo ""
}

# ===== Main =====

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                show_help
                exit 0
                ;;
            --grafana-password)
                GRAFANA_PASSWORD="$2"
                shift 2
                ;;
            *)
                echo "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # Initialize logging
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "=== ROSE Link Monitoring Installation Started $(date) ===" > "$LOG_FILE"

    print_banner

    # Pre-flight checks
    check_root
    check_rose_link_installed
    check_resources
    detect_architecture

    # Installation
    install_prometheus
    install_node_exporter
    install_grafana
    configure_prometheus
    configure_grafana
    create_systemd_services
    enable_and_start_services
    configure_nginx_proxy

    # Summary
    print_summary

    log "INFO" "Monitoring stack installation completed successfully"
}

main "$@"
