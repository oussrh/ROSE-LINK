# ROSE-LINK Monitoring Stack

This directory contains the Grafana + Prometheus monitoring stack for ROSE-LINK.

## Components

- **Prometheus**: Metrics collection and storage (port 9090)
- **Grafana**: Dashboard visualization (port 3000)
- **Node Exporter**: Optional system metrics exporter (port 9100)

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- ROSE-LINK backend running on port 8000

### Starting the Monitoring Stack

```bash
cd monitoring
docker-compose up -d
```

### Accessing Services

- **Grafana Dashboard**: http://localhost:3000
  - Default credentials: `admin` / `roselink`
  - Anonymous access is enabled for read-only viewing
  - ROSE-LINK dashboard is set as the default home

- **Prometheus**: http://localhost:9090
  - Query metrics directly
  - View alert rules
  - Check target health

### Stopping the Stack

```bash
docker-compose down
```

To remove all data volumes:
```bash
docker-compose down -v
```

## Dashboard Features

The ROSE-LINK Dashboard includes:

### Status Overview
- VPN Connection Status (Connected/Disconnected)
- WAN Connection Status
- Hotspot Status (Active/Inactive)
- Connected Clients Count
- System Uptime
- CPU Temperature

### System Resources
- CPU Usage Gauge & History
- Memory Usage Gauge & History
- Disk Usage Gauge
- CPU Temperature Gauge

### Network Traffic
- Network Throughput (bytes/sec per interface)
- Network Packets (packets/sec per interface)
- Total Network Traffic

### VPN & Connectivity History
- VPN Status Timeline
- WAN Status Timeline
- Hotspot Status Timeline
- Connected Clients Over Time

### System Information
- CPU Temperature Over Time (with threshold alerts)
- Disk Usage Over Time

## Prometheus Metrics

The ROSE-LINK backend exposes the following metrics at `/api/metrics`:

| Metric | Type | Description |
|--------|------|-------------|
| `rose_link_info` | Gauge | Application version info |
| `rose_link_vpn_status` | Gauge | VPN connection status (1=connected, 0=disconnected) |
| `rose_link_wan_status` | Gauge | WAN connection status |
| `rose_link_hotspot_status` | Gauge | Hotspot active status |
| `rose_link_hotspot_clients` | Gauge | Number of connected clients |
| `rose_link_cpu_temperature_celsius` | Gauge | CPU temperature in Celsius |
| `rose_link_cpu_usage_percent` | Gauge | CPU usage percentage |
| `rose_link_memory_used_bytes` | Gauge | Used memory in bytes |
| `rose_link_memory_total_bytes` | Gauge | Total memory in bytes |
| `rose_link_disk_used_bytes` | Gauge | Used disk space in bytes |
| `rose_link_disk_total_bytes` | Gauge | Total disk space in bytes |
| `rose_link_network_rx_bytes_total` | Counter | Received bytes per interface |
| `rose_link_network_tx_bytes_total` | Counter | Transmitted bytes per interface |
| `rose_link_network_rx_packets_total` | Counter | Received packets per interface |
| `rose_link_network_tx_packets_total` | Counter | Transmitted packets per interface |
| `rose_link_uptime_seconds` | Gauge | System uptime in seconds |

## Alert Rules

Pre-configured alerts in `prometheus/alerts.yml`:

| Alert | Severity | Condition |
|-------|----------|-----------|
| VPNDisconnected | Critical | VPN down for >1 minute |
| WANDisconnected | Critical | WAN down for >2 minutes |
| HighCPUTemperature | Warning | CPU temp >70°C for >5 minutes |
| CriticalCPUTemperature | Critical | CPU temp >80°C for >1 minute |
| HighCPUUsage | Warning | CPU usage >90% for >5 minutes |
| HighMemoryUsage | Warning | Memory usage >85% for >5 minutes |
| CriticalMemoryUsage | Critical | Memory usage >95% for >2 minutes |
| LowDiskSpace | Warning | Disk usage >80% for >10 minutes |
| CriticalDiskSpace | Critical | Disk usage >95% for >5 minutes |
| HotspotDown | Warning | Hotspot inactive for >2 minutes |
| RoseLinkDown | Critical | Backend not responding for >1 minute |

## E2E Testing

Run Grafana dashboard E2E tests with Playwright:

```bash
cd ../e2e

# Run only Grafana tests
npx playwright test --project=grafana

# Run Grafana tests on Firefox
npx playwright test --project=grafana-firefox

# Run with custom Grafana URL
GRAFANA_URL=http://custom-host:3000 npx playwright test --project=grafana

# Run all E2E tests including Grafana
npx playwright test
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GF_SECURITY_ADMIN_USER` | admin | Grafana admin username |
| `GF_SECURITY_ADMIN_PASSWORD` | roselink | Grafana admin password |
| `GF_AUTH_ANONYMOUS_ENABLED` | true | Enable anonymous access |
| `GF_AUTH_ANONYMOUS_ORG_ROLE` | Viewer | Role for anonymous users |

### Customizing Prometheus

Edit `prometheus/prometheus.yml` to:
- Change scrape intervals
- Add additional targets
- Modify alert configurations

### Customizing Grafana

- Dashboards: Add JSON files to `grafana/dashboards/`
- Datasources: Edit `grafana/provisioning/datasources/datasources.yml`
- Dashboard provisioning: Edit `grafana/provisioning/dashboards/dashboards.yml`

## Troubleshooting

### No data in dashboard

1. Check ROSE-LINK backend is running:
   ```bash
   curl http://localhost:8000/api/metrics
   ```

2. Check Prometheus targets:
   - Visit http://localhost:9090/targets
   - Ensure "rose-link" target is UP

3. Check Prometheus can reach the backend:
   ```bash
   docker exec rose-link-prometheus wget -qO- http://host.docker.internal:8000/api/metrics
   ```

### Grafana login issues

1. Default credentials: `admin` / `roselink`
2. Reset password:
   ```bash
   docker exec rose-link-grafana grafana-cli admin reset-admin-password newpassword
   ```

### Container networking issues

If Prometheus can't reach the backend:

1. On Linux, check `host.docker.internal` is available:
   ```bash
   docker exec rose-link-prometheus cat /etc/hosts
   ```

2. Alternative: Use host network mode or specify the host IP directly in `prometheus.yml`

## File Structure

```
monitoring/
├── docker-compose.yml          # Container orchestration
├── README.md                   # This file
├── prometheus/
│   ├── prometheus.yml          # Prometheus configuration
│   └── alerts.yml              # Alert rules
└── grafana/
    ├── provisioning/
    │   ├── datasources/
    │   │   └── datasources.yml # Datasource configuration
    │   └── dashboards/
    │       └── dashboards.yml  # Dashboard provisioning
    └── dashboards/
        └── rose-link-dashboard.json  # Main dashboard
```
