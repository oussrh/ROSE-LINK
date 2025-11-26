# ROSE Link Feature Roadmap

This document outlines planned features, implementation details, and priorities for ROSE Link development.

## Version Overview

| Version | Theme | Status |
|---------|-------|--------|
| 0.2.x | Stability & Polish | Current |
| 0.3.0 | Real-time & Monitoring | Planned |
| 0.4.0 | Extended VPN & DNS | Planned |
| 1.0.0 | Production Ready | Future |

---

## Version 0.3.0 - Real-time & Monitoring

### WebSocket Real-time Updates

**Priority**: High
**Complexity**: Medium
**Dependencies**: None (websockets already in uvicorn[standard])

**Current State**: Frontend polls `/api/status` periodically via htmx.

**Implementation Plan**:

1. **Backend WebSocket Endpoint** (`backend/api/routes/websocket.py`)
   ```python
   @router.websocket("/ws/status")
   async def websocket_status(websocket: WebSocket):
       await websocket.accept()
       while True:
           status = await get_combined_status()
           await websocket.send_json(status)
           await asyncio.sleep(2)
   ```

2. **Connection Manager** (`backend/core/websocket.py`)
   - Track active connections
   - Broadcast to all clients on state changes
   - Handle reconnection gracefully

3. **Frontend Integration** (`web/js/utils/websocket.js`)
   - WebSocket client with auto-reconnect
   - Fall back to polling if WebSocket fails
   - Update UI components on message receive

4. **Events to Broadcast**:
   - VPN status changes (connect/disconnect)
   - WAN connectivity changes
   - Hotspot client join/leave
   - System metrics (every 5s)

**Files to Create/Modify**:
- `backend/api/routes/websocket.py` (new)
- `backend/core/websocket.py` (new)
- `backend/core/lifespan.py` (add connection manager)
- `web/js/utils/websocket.js` (new)
- `web/js/app.js` (integrate WebSocket)

---

### Configuration Backup/Restore

**Priority**: High
**Complexity**: Low
**Dependencies**: None

**Current State**: No backup functionality exists.

**Implementation Plan**:

1. **Backup Endpoint** (`GET /api/backup`)
   - Collect all configuration:
     - VPN profiles (`/etc/wireguard/profiles/*.conf`)
     - Hotspot config (`/etc/hostapd/hostapd.conf`)
     - Watchdog settings (JSON config)
     - API key hash (optional)
   - Create encrypted ZIP archive
   - Return as downloadable file

2. **Restore Endpoint** (`POST /api/restore`)
   - Accept uploaded backup archive
   - Validate archive structure
   - Verify checksums
   - Restore files to correct locations
   - Restart affected services

3. **Backup Format**:
   ```
   rose-link-backup-YYYYMMDD.zip
   ├── manifest.json          # Version, timestamp, checksum
   ├── vpn/
   │   └── *.conf             # VPN profiles
   ├── hotspot/
   │   └── hostapd.conf       # Hotspot config
   └── settings/
       └── watchdog.json      # Watchdog settings
   ```

**Files to Create/Modify**:
- `backend/api/routes/backup.py` (new)
- `backend/services/backup.py` (new)
- `web/js/components/backup.js` (new)
- `web/index.html` (add backup/restore UI)

---

### Bandwidth Statistics

**Priority**: Medium
**Complexity**: Medium
**Dependencies**: None

**Current State**: Real-time VPN transfer stats only, no history.

**Implementation Plan**:

1. **Data Collection**:
   - Read from `/sys/class/net/<iface>/statistics/`
   - Collect every minute: rx_bytes, tx_bytes per interface
   - Store in SQLite database (optional) or JSON log

2. **API Endpoints**:
   - `GET /api/stats/bandwidth?period=24h` - Historical data
   - `GET /api/stats/current` - Current rates

3. **Storage** (lightweight, no external DB):
   ```python
   # /opt/rose-link/data/bandwidth.json
   {
       "2024-11-26T10:00:00Z": {
           "wg0": {"rx": 1234567, "tx": 987654},
           "eth0": {"rx": 5678901, "tx": 2345678}
       }
   }
   ```

4. **Data Retention**:
   - Keep 1-minute resolution for 24h
   - Aggregate to 1-hour resolution for 7 days
   - Aggregate to daily for 30 days

5. **Frontend Visualization**:
   - Line chart using lightweight library (Chart.js or similar)
   - Interface selector
   - Time period selector

**Files to Create/Modify**:
- `backend/api/routes/stats.py` (new)
- `backend/services/stats.py` (new)
- `backend/utils/bandwidth_collector.py` (new)
- `web/js/components/stats.js` (new)
- `web/vendor/chart.min.js` (new, ~200KB)

---

### Let's Encrypt SSL Certificates

**Priority**: Medium
**Complexity**: Medium
**Dependencies**: Port 80 accessible, domain name

**Current State**: Self-signed certificates via Nginx.

**Implementation Plan**:

1. **Certificate Management Service**:
   - Use `certbot` or `acme.sh` for certificate issuance
   - Support both DNS and HTTP validation
   - Auto-renewal via systemd timer

2. **API Endpoints**:
   - `POST /api/ssl/request` - Request new certificate
   - `GET /api/ssl/status` - Certificate status and expiry
   - `POST /api/ssl/renew` - Force renewal

3. **Configuration**:
   ```yaml
   ssl:
     mode: "self-signed" | "letsencrypt"
     domain: "rose.example.com"
     email: "admin@example.com"
   ```

4. **Nginx Integration**:
   - Update ssl_certificate paths
   - Reload after certificate renewal

**Files to Create/Modify**:
- `backend/api/routes/ssl.py` (new)
- `backend/services/ssl.py` (new)
- `system/rose-ssl-renew.service` (new)
- `system/rose-ssl-renew.timer` (new)
- `system/nginx/rose-link-ssl.conf` (modify)

---

### Speed Test Integration

**Priority**: Low
**Complexity**: Low
**Dependencies**: `speedtest-cli` package

**Implementation Plan**:

1. **API Endpoint**:
   - `POST /api/speedtest/run` - Start speed test (async)
   - `GET /api/speedtest/result` - Get latest result

2. **Implementation**:
   ```python
   async def run_speedtest():
       result = await run_command("speedtest-cli --json")
       return json.loads(result)
   ```

3. **Frontend**:
   - "Run Speed Test" button
   - Progress indicator (tests take 30-60s)
   - Display: Download, Upload, Ping, Server

**Files to Create/Modify**:
- `backend/api/routes/speedtest.py` (new)
- `web/js/components/speedtest.js` (new)

---

### Prometheus Metrics Endpoint

**Priority**: Medium
**Complexity**: Low
**Dependencies**: None (optional prometheus_client)

**Implementation Plan**:

1. **Metrics Endpoint** (`GET /metrics`):
   ```prometheus
   # HELP rose_vpn_connected VPN connection status
   # TYPE rose_vpn_connected gauge
   rose_vpn_connected 1

   # HELP rose_vpn_bytes_received Total bytes received via VPN
   # TYPE rose_vpn_bytes_received counter
   rose_vpn_bytes_received 1234567

   # HELP rose_hotspot_clients Number of connected hotspot clients
   # TYPE rose_hotspot_clients gauge
   rose_hotspot_clients 3

   # HELP rose_system_cpu_temp CPU temperature in Celsius
   # TYPE rose_system_cpu_temp gauge
   rose_system_cpu_temp 52.5
   ```

2. **Grafana Dashboard** (JSON template):
   - Pre-built dashboard for common metrics
   - Documentation for Grafana setup

**Files to Create/Modify**:
- `backend/api/routes/metrics.py` (new)
- `docs/grafana-dashboard.json` (new)
- `docs/MONITORING.md` (new)

---

## Version 0.4.0 - Extended VPN & DNS

### OpenVPN Support

**Priority**: Medium
**Complexity**: High
**Dependencies**: `openvpn` package

**Current State**: WireGuard only.

**Implementation Plan**:

1. **Profile Detection**:
   - Detect `.ovpn` files vs `.conf` files
   - Parse OpenVPN configuration format

2. **Service Abstraction**:
   - Create `VPNProvider` interface
   - `WireGuardProvider` and `OpenVPNProvider` implementations
   - Factory to select provider based on profile type

3. **API Changes**:
   - `/api/vpn/upload` accepts both formats
   - `/api/vpn/status` returns provider-agnostic status

4. **Challenges**:
   - OpenVPN requires username/password for some configs
   - Certificate handling differs
   - Status parsing is different

**Files to Create/Modify**:
- `backend/services/vpn/base.py` (new, interface)
- `backend/services/vpn/wireguard.py` (refactor from vpn.py)
- `backend/services/vpn/openvpn.py` (new)
- `backend/services/vpn/factory.py` (new)

---

### AdGuard Home Integration

**Priority**: Medium
**Complexity**: Medium
**Dependencies**: AdGuard Home installation

**Implementation Plan**:

1. **Integration Options**:
   - Option A: Replace dnsmasq with AdGuard Home
   - Option B: Run alongside, AdGuard as upstream DNS

2. **API Endpoints**:
   - `GET /api/adguard/status` - AdGuard status
   - `POST /api/adguard/enable` - Enable/disable
   - `GET /api/adguard/stats` - Blocking statistics

3. **Installation**:
   - Optional during ROSE Link install
   - Download and configure AdGuard Home
   - Update dnsmasq to forward to AdGuard

4. **Frontend**:
   - AdGuard status card
   - Link to AdGuard web UI (port 3000)
   - Basic stats display

**Files to Create/Modify**:
- `backend/api/routes/adguard.py` (new)
- `backend/services/adguard.py` (new)
- `install.sh` (add optional AdGuard installation)
- `web/js/components/adguard.js` (new)

---

### QoS Traffic Prioritization

**Priority**: Low
**Complexity**: High
**Dependencies**: tc, iptables knowledge

**Implementation Plan**:

1. **Traffic Classes**:
   - High Priority: VoIP, Video conferencing
   - Normal: Web browsing, General
   - Low Priority: Downloads, Torrents

2. **Implementation**:
   - Use `tc` (traffic control) for queuing
   - `iptables` for packet marking
   - Pre-defined profiles (Gaming, Streaming, Work)

3. **API Endpoints**:
   - `GET /api/qos/status` - Current QoS settings
   - `POST /api/qos/profile` - Apply QoS profile
   - `POST /api/qos/custom` - Custom rules

4. **Challenges**:
   - Complex tc syntax
   - Testing difficult without traffic
   - May impact overall throughput

**Files to Create/Modify**:
- `backend/api/routes/qos.py` (new)
- `backend/services/qos.py` (new)
- `system/qos-profiles/` (new directory with tc scripts)

---

## Version 1.0.0 - Production Ready

### Flashable SD Card Image

**Priority**: High (for 1.0)
**Complexity**: High
**Dependencies**: Build infrastructure

**Implementation Plan**:

1. **Image Creation**:
   - Base: Raspberry Pi OS Lite (64-bit)
   - Pre-installed: ROSE Link + all dependencies
   - First-boot configuration script

2. **Build Process**:
   - GitHub Actions workflow
   - Use `pi-gen` or custom script
   - Compress with xz

3. **Distribution**:
   - GitHub Releases
   - Separate download page
   - Checksum verification

---

### First-Run Setup Wizard

**Priority**: High (for 1.0)
**Complexity**: Medium
**Dependencies**: None

**Implementation Plan**:

1. **Wizard Flow**:
   - Welcome screen
   - Network configuration (Ethernet/WiFi WAN)
   - VPN profile import
   - Hotspot configuration
   - Admin password setup
   - Summary and apply

2. **Detection**:
   - Check if first run (`/opt/rose-link/.initialized`)
   - Redirect to wizard if not initialized

3. **Implementation**:
   - Dedicated wizard routes
   - Step-by-step frontend
   - Validation at each step

---

### Multi-WAN Load Balancing

**Priority**: Low
**Complexity**: Very High
**Dependencies**: Multiple network interfaces

**Implementation Plan**:

1. **Modes**:
   - Failover (current behavior, enhanced)
   - Load Balancing (round-robin)
   - Weighted (bandwidth-based)

2. **Technical Approach**:
   - Multiple default routes with different metrics
   - Connection tracking for session persistence
   - Health checks for failover

3. **Challenges**:
   - Complex routing rules
   - Source NAT considerations
   - VPN tunnel over specific WAN

---

### Mobile Applications

**Priority**: Low
**Complexity**: Very High
**Dependencies**: Mobile development resources

**Options**:

1. **Progressive Web App (PWA)**:
   - Lower complexity
   - Works on both platforms
   - Limited native features

2. **React Native / Flutter**:
   - Better native experience
   - Requires mobile dev expertise
   - Separate codebase to maintain

**Recommendation**: Start with PWA, evaluate native later.

---

### Automatic Updates

**Priority**: Medium
**Complexity**: Medium
**Dependencies**: APT repository

**Implementation Plan**:

1. **Update Check**:
   - Daily check against APT repository
   - Compare installed vs available version

2. **Update Process**:
   - Notification in UI
   - One-click update button
   - Automatic backup before update
   - Service restart after update

3. **Rollback**:
   - Keep previous version
   - Rollback option if update fails

---

## Test Suite Completion

### Current Coverage

| Component | Coverage | Status |
|-----------|----------|--------|
| Services | ~75% | Good |
| API Routes | ~70% | Good |
| Core | ~65% | Needs work |
| Frontend | 0% | Not started |

### Targets

| Version | Backend | Frontend | Integration |
|---------|---------|----------|-------------|
| 0.3.0 | 80% | 30% | Basic |
| 0.4.0 | 85% | 50% | Expanded |
| 1.0.0 | 90% | 70% | Full |

### Test Infrastructure Improvements

1. **Code Coverage Reporting**:
   - pytest-cov integration (done)
   - Codecov badge in README
   - Coverage reports in CI

2. **Frontend Testing**:
   - Jest/Vitest for JavaScript
   - Component unit tests
   - E2E tests with Playwright (future)

3. **Integration Testing**:
   - Docker-based test environment
   - Mock hardware interfaces
   - API contract testing

4. **Performance Testing**:
   - Load testing for API
   - Memory leak detection
   - Long-running stability tests

---

## Contributing to Roadmap Features

### Claiming a Feature

1. Check if feature has an open issue
2. Comment on issue to claim
3. Create feature branch: `feature/<feature-name>`
4. Submit PR when ready

### Feature Development Checklist

- [ ] API design documented
- [ ] Backend implementation
- [ ] Frontend integration
- [ ] Unit tests (min 80% coverage)
- [ ] Integration tests
- [ ] Documentation updated
- [ ] CHANGELOG entry

### Priority Legend

| Priority | Meaning |
|----------|---------|
| High | Core functionality, blocks other features |
| Medium | Important but not blocking |
| Low | Nice to have, can be deferred |

---

## Feedback

Have feature requests or suggestions? Open an issue with:
- Clear use case description
- Expected behavior
- Any technical considerations
