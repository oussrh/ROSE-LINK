# ROSE Link Feature Roadmap

This document outlines planned features, implementation details, and priorities for ROSE Link development.

## Version Overview

| Version | Theme | Status |
|---------|-------|--------|
| 0.3.0 | Real-time & Monitoring | ✅ Released |
| 1.0.0 | Production Ready | 🚧 In Development |
| 1.x | Extended Features | Future |

---

## v1.0.0 Target Scope

**Product Identity**: "VPN Router + Ad Blocking on Raspberry Pi"

### Core Features for v1.0.0

| Feature | Priority | Status |
|---------|----------|--------|
| AdGuard Home Integration | High | 🚧 In Progress |
| OpenVPN Support | High | 🚧 In Progress |
| Connected Clients Management | High | 🚧 In Progress |
| Simple QoS | Medium | 🚧 In Progress |
| Ready-to-Flash SD Image | High | 🚧 In Progress |
| First-Time Setup Wizard | High | 🚧 In Progress |
| Full Test Suite (90%+) | High | 🚧 In Progress |

### Features Deferred to v1.x

| Feature | Reason |
|---------|--------|
| Email Notifications | Nice-to-have, WebSocket/API provides monitoring |
| iOS/Android App | Web UI is responsive, works on mobile |
| Grafana Dashboard | `/api/metrics` endpoint lets users bring their own Grafana |
| Multi-WAN Load Balancing | Complex, edge case for most home users |
| Automatic Updates | Can be risky, manual APT repo updates work fine |

---

## v1.0.0 Feature Details

### AdGuard Home Integration

**Priority**: High
**Complexity**: Medium
**Status**: 🚧 In Progress

**Description**: Integrates AdGuard Home for DNS-level ad blocking, turning ROSE Link into a Pi-hole alternative with VPN routing.

**Implementation Plan**:

1. **AdGuard Home Service** (`backend/services/adguard_service.py`)
   - Install/manage AdGuard Home binary
   - Health check via AdGuard API
   - Enable/disable filtering
   - Get blocking statistics

2. **API Endpoints** (`backend/api/routes/adguard.py`)
   ```
   GET  /api/adguard/status     - AdGuard status and stats
   POST /api/adguard/enable     - Enable ad blocking
   POST /api/adguard/disable    - Disable ad blocking
   GET  /api/adguard/stats      - Blocking statistics (queries, blocked, etc.)
   POST /api/adguard/install    - Install AdGuard Home (first-time setup)
   ```

3. **DNS Configuration**:
   - Option A: AdGuard replaces dnsmasq for DNS (recommended)
   - Option B: dnsmasq forwards to AdGuard (fallback)
   - Automatic configuration during install

4. **Frontend Integration** (`web/js/components/adguard.js`)
   - Status card with blocking stats
   - Enable/disable toggle
   - Link to AdGuard web UI (port 3000)
   - Quick stats: queries today, blocked %, top blocked domains

**Files to Create/Modify**:
- `backend/api/routes/adguard.py` (new)
- `backend/services/adguard_service.py` (new)
- `web/js/components/adguard.js` (new)
- `install.sh` (add AdGuard installation)
- `web/index.html` (add AdGuard tab/section)

---

### OpenVPN Support

**Priority**: High
**Complexity**: High
**Status**: 🚧 In Progress

**Description**: Many VPN providers only offer OpenVPN configs. Adding OpenVPN support expands compatibility significantly.

**Implementation Plan**:

1. **VPN Provider Abstraction** (`backend/services/vpn/`)
   ```python
   # base.py - Interface
   class VPNProvider(ABC):
       async def connect() -> bool
       async def disconnect() -> bool
       async def get_status() -> VPNStatus
       async def import_config(file_path: Path) -> bool

   # wireguard.py - WireGuard implementation
   class WireGuardProvider(VPNProvider): ...

   # openvpn.py - OpenVPN implementation
   class OpenVPNProvider(VPNProvider): ...
   ```

2. **Profile Detection**:
   - `.conf` files → WireGuard
   - `.ovpn` files → OpenVPN
   - Auto-detect on upload

3. **OpenVPN Features**:
   - Support for `.ovpn` with embedded certificates
   - Support for separate cert/key files
   - Username/password authentication support
   - Connection status parsing from logs

4. **API Changes**:
   - `/api/vpn/upload` accepts both `.conf` and `.ovpn`
   - `/api/vpn/status` returns provider-agnostic status
   - New: `/api/vpn/providers` lists available providers

5. **Kill-Switch Adaptation**:
   - iptables rules work for both WireGuard and OpenVPN
   - Interface detection (`wg0` vs `tun0`)

**Files to Create/Modify**:
- `backend/services/vpn/base.py` (new - interface)
- `backend/services/vpn/wireguard.py` (refactor from vpn_service.py)
- `backend/services/vpn/openvpn.py` (new)
- `backend/services/vpn/__init__.py` (factory)
- `backend/api/routes/vpn.py` (modify)
- `system/rose-openvpn@.service` (new)

---

### Connected Clients Management

**Priority**: High
**Complexity**: Low-Medium
**Status**: 🚧 In Progress

**Description**: Essential router feature - users expect to see and manage devices connected to their hotspot.

**Current State**: Basic client list exists at `GET /api/hotspot/clients`

**Enhancements**:

1. **Persistent Client Tracking**:
   - Store client history in JSON file
   - Track: MAC, IP, hostname, first seen, last seen, total traffic

2. **Client Information**:
   - Device type detection (via MAC OUI lookup)
   - Custom device naming/labels
   - Connection history

3. **Client Management**:
   - Block/unblock clients (MAC filtering)
   - Per-client bandwidth stats
   - Kick client (force disconnect)

4. **API Endpoints**:
   ```
   GET  /api/clients              - List all clients (current + historical)
   GET  /api/clients/{mac}        - Get client details
   PUT  /api/clients/{mac}        - Update client (name, blocked status)
   POST /api/clients/{mac}/block  - Block client
   POST /api/clients/{mac}/unblock- Unblock client
   POST /api/clients/{mac}/kick   - Kick connected client
   ```

5. **Frontend**:
   - Clients tab with sortable table
   - Device icons by type
   - Quick actions (block, kick, rename)
   - Traffic graphs per client

**Files to Create/Modify**:
- `backend/api/routes/clients.py` (new)
- `backend/services/clients_service.py` (new)
- `web/js/components/clients.js` (new)
- `data/clients.json` (runtime data)

---

### Simple QoS (Traffic Prioritization)

**Priority**: Medium
**Complexity**: Medium-High
**Status**: 🚧 In Progress

**Description**: Simple "prioritize VPN traffic" toggle. Full QoS with port/app prioritization deferred to v1.1.

**Simplified Approach for v1.0**:

1. **Single Toggle**: "Prioritize VPN Traffic"
   - When enabled: VPN traffic gets priority over local traffic
   - Uses `tc` (traffic control) with simple HTB queueing

2. **Implementation**:
   ```bash
   # Enable QoS
   tc qdisc add dev eth0 root handle 1: htb default 20
   tc class add dev eth0 parent 1: classid 1:1 htb rate 100mbit
   tc class add dev eth0 parent 1:1 classid 1:10 htb rate 80mbit prio 1  # VPN
   tc class add dev eth0 parent 1:1 classid 1:20 htb rate 20mbit prio 2  # Other

   # Mark VPN packets
   iptables -t mangle -A OUTPUT -o wg0 -j MARK --set-mark 10
   tc filter add dev eth0 parent 1: prio 1 handle 10 fw flowid 1:10
   ```

3. **API Endpoints**:
   ```
   GET  /api/qos/status   - QoS enabled/disabled, current settings
   POST /api/qos/enable   - Enable VPN traffic prioritization
   POST /api/qos/disable  - Disable QoS (default behavior)
   ```

4. **Future (v1.1)**:
   - Pre-defined profiles (Gaming, Streaming, Work)
   - Port-based prioritization
   - Application detection

**Files to Create/Modify**:
- `backend/api/routes/qos.py` (new)
- `backend/services/qos_service.py` (new)
- `web/js/components/qos.js` (new)

---

### Ready-to-Flash SD Card Image

**Priority**: High
**Complexity**: High
**Status**: 🚧 In Progress

**Description**: Critical for ease of use - biggest barrier to adoption is installation complexity.

**Implementation Plan**:

1. **Image Contents**:
   - Base: Raspberry Pi OS Lite (64-bit, Bookworm)
   - Pre-installed: ROSE Link + all dependencies
   - First-boot: Expand filesystem, run setup wizard
   - Configured: SSH enabled, default credentials

2. **Build Process** (GitHub Actions):
   ```yaml
   - Download official Raspberry Pi OS image
   - Mount and customize with pi-gen or direct modification
   - Install ROSE Link packages
   - Configure first-boot scripts
   - Compress with xz for smaller download
   - Generate checksums (SHA256)
   ```

3. **Build Script** (`scripts/build-image.sh`):
   - Uses `qemu-user-static` for ARM emulation
   - Customization via chroot
   - Automated testing in emulated environment

4. **Distribution**:
   - GitHub Releases (compressed .img.xz)
   - Checksum file for verification
   - Clear flashing instructions (Balena Etcher, Raspberry Pi Imager)

5. **First Boot Experience**:
   - Auto-expand filesystem
   - Generate unique SSH keys
   - Start setup wizard
   - Connect to `ROSE-Link-Setup` hotspot for initial config

**Files to Create**:
- `scripts/build-image.sh` (main build script)
- `scripts/image/first-boot.sh` (first boot customization)
- `scripts/image/customize.sh` (image customization)
- `.github/workflows/build-image.yml` (CI/CD for image builds)

---

### First-Time Setup Wizard

**Priority**: High
**Complexity**: Medium
**Status**: 🚧 In Progress

**Description**: Essential UX - without it, v1.0 doesn't feel "production ready".

**Wizard Flow**:

```
Step 1: Welcome
  → Language selection (EN/FR)
  → Quick intro to ROSE Link

Step 2: Network (WAN)
  → Auto-detect Ethernet
  → Or scan and connect to WiFi
  → Connection test

Step 3: VPN Configuration
  → Upload WireGuard .conf or OpenVPN .ovpn
  → Or skip for later
  → Connection test (if configured)

Step 4: Hotspot Setup
  → SSID name
  → Password (with strength indicator)
  → Country (regulatory)
  → Channel selection

Step 5: Security
  → Set admin password
  → Optional: Enable 2FA (future)

Step 6: AdGuard Home (Optional)
  → Enable DNS ad blocking?
  → Basic filter selection

Step 7: Summary
  → Review all settings
  → Apply and restart services
  → Show connection instructions
```

**Implementation**:

1. **First-Run Detection**:
   ```python
   # Check if setup completed
   INITIALIZED_FILE = "/opt/rose-link/.initialized"

   def is_first_run() -> bool:
       return not Path(INITIALIZED_FILE).exists()
   ```

2. **API Endpoints**:
   ```
   GET  /api/setup/status        - Check if setup needed
   GET  /api/setup/step/{n}      - Get step data
   POST /api/setup/step/{n}      - Submit step data
   POST /api/setup/complete      - Finalize setup
   POST /api/setup/skip          - Skip setup (advanced users)
   ```

3. **Frontend**:
   - Dedicated `/setup` route
   - Step indicators (progress bar)
   - Validation at each step
   - Back/Next navigation
   - Skip option for advanced users

**Files to Create/Modify**:
- `backend/api/routes/setup.py` (new)
- `backend/services/setup_service.py` (new)
- `web/setup.html` (new - standalone wizard page)
- `web/js/setup.js` (new - wizard logic)
- `web/css/setup.css` (new - wizard styles)

---

### Full Test Suite (90%+ Coverage)

**Priority**: High
**Complexity**: Medium
**Status**: 🚧 In Progress

**Description**: Non-negotiable for a "1.0" release - stability matters.

**Current State**:
- Backend: ~75% coverage (10 test files, 2841 lines)
- Frontend: ~70% coverage (Jest tests)

**Target**: 90%+ line coverage for backend, 80%+ for frontend

**Test Additions Needed**:

1. **Backend Tests**:
   - `test_adguard_service.py` - AdGuard integration
   - `test_openvpn_service.py` - OpenVPN provider
   - `test_clients_service.py` - Client management
   - `test_qos_service.py` - QoS functionality
   - `test_setup_service.py` - Setup wizard
   - `test_backup_service.py` - Backup/restore (expand)
   - `test_api_routes_*.py` - Route-level tests for new endpoints

2. **Frontend Tests**:
   - Component tests for new features
   - Setup wizard flow tests
   - WebSocket integration tests

3. **Integration Tests**:
   - End-to-end API tests
   - Service interaction tests
   - Full wizard flow test

4. **Test Infrastructure**:
   - Coverage threshold enforcement in CI (fail if < 90%)
   - Coverage badges in README
   - Test reports as CI artifacts

**Files to Create**:
- `backend/tests/test_adguard_service.py`
- `backend/tests/test_openvpn_service.py`
- `backend/tests/test_clients_service.py`
- `backend/tests/test_qos_service.py`
- `backend/tests/test_setup_service.py`
- `web/__tests__/setup.test.js`
- `web/__tests__/adguard.test.js`
- `web/__tests__/clients.test.js`

---

## Completed Features (v0.3.0)

### ✅ WebSocket Real-time Updates
- Backend WebSocket endpoint (`/api/ws`)
- Connection manager for multiple clients
- Auto-reconnect with exponential backoff
- Real-time status broadcasting

### ✅ Configuration Backup/Restore
- Full backup API (create, restore, download, upload)
- Selective component backup
- ZIP format with manifest

### ✅ Prometheus Metrics Endpoint
- `/api/metrics` with standard Prometheus format
- VPN, WAN, Hotspot, System metrics

### ✅ Speed Test Integration
- Async speed test execution
- History tracking
- Support for speedtest-cli and Ookla

### ✅ SSL Certificate Management
- Self-signed certificate generation
- Let's Encrypt integration ready
- Certificate status monitoring

---

## Contributing to v1.0.0

### Claiming a Feature

1. Check if feature has an open issue
2. Comment on issue to claim
3. Create feature branch: `feature/<feature-name>`
4. Submit PR when ready

### Feature Development Checklist

- [ ] API design documented
- [ ] Backend implementation with type hints
- [ ] Service layer with business logic
- [ ] Unit tests (min 90% coverage)
- [ ] Frontend integration
- [ ] i18n strings (EN + FR)
- [ ] Documentation updated
- [ ] CHANGELOG entry

### Code Quality Requirements

- All code must pass CI checks:
  - `ruff` linting
  - `mypy` type checking
  - `bandit` security scan
  - `pytest` with 90%+ coverage
  - `eslint` for JavaScript
  - `jest` for frontend tests

---

## Release Timeline

**v1.0.0 Target**: Feature-complete, production-ready release

**Milestones**:
1. All core features implemented
2. Test coverage ≥ 90%
3. Documentation complete
4. SD card image builds successfully
5. Setup wizard functional
6. Beta testing period
7. Final release

---

## Post-1.0 Roadmap (v1.x)

Features deferred from v1.0.0 for future releases:

| Feature | Version | Notes |
|---------|---------|-------|
| Email Notifications | v1.1 | VPN failure alerts via SMTP |
| Full QoS Profiles | v1.1 | Gaming, Streaming, Work profiles |
| Grafana Dashboard | v1.1 | Pre-built dashboard JSON |
| Multi-WAN Load Balancing | v1.2 | Round-robin, weighted, failover |
| Automatic Updates | v1.2 | APT-based with rollback |
| iOS/Android App | v2.0 | Native mobile experience |

---

## Feedback

Have feature requests or suggestions? Open an issue with:
- Clear use case description
- Expected behavior
- Any technical considerations
