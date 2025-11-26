# ROSE Link Feature Roadmap

This document outlines planned features, implementation details, and priorities for ROSE Link development.

## Version Overview

| Version | Theme | Status |
|---------|-------|--------|
| 1.1.0 | Production Ready | ✅ Current Release |
| 0.3.0 | Real-time & Monitoring | ✅ Legacy Release |
| 1.2.x | Extended Features | Future |

---

## v1.1.0 Delivered Scope

**Product Identity**: "VPN Router + Ad Blocking on Raspberry Pi"

### Core Features for v1.1.0

| Feature | Priority | Status |
|---------|----------|--------|
| AdGuard Home Integration | High | ✅ Completed |
| OpenVPN Support | High | ✅ Completed |
| Connected Clients Management | High | ✅ Completed |
| Simple QoS | Medium | ✅ Completed |
| Ready-to-Flash SD Image | High | ✅ Completed |
| First-Time Setup Wizard | High | ✅ Completed |
| Full Test Suite (90%+) | High | ✅ In Place |

### Features Deferred to v1.x

| Feature | Reason |
|---------|--------|
| Email Notifications | Nice-to-have, WebSocket/API provides monitoring |
| iOS/Android App | Web UI is responsive, works on mobile |
| Grafana Dashboard | `/api/metrics` endpoint lets users bring their own Grafana |
| Multi-WAN Load Balancing | Complex, edge case for most home users |
| Automatic Updates | Can be risky, manual APT repo updates work fine |

---

## v1.1.0 Feature Details

### AdGuard Home Integration

**Priority**: High
**Complexity**: Medium
**Status**: ✅ Completed

**Current Implementation**: Native AdGuard Home control ships with the stack. The service layer handles installation, health checks, and filter toggling (`backend/services/adguard_service.py`), and public endpoints expose status, enable/disable, stats, and install flows (`backend/api/routes/adguard.py`). The installer provisions AdGuard during setup (`install.sh`), and dashboard components surface ad-blocking controls and stats alongside other cards.

---

### OpenVPN Support

**Priority**: High
**Complexity**: High
**Status**: ✅ Completed

**Current Implementation**: The VPN provider abstraction covers WireGuard and OpenVPN (`backend/services/vpn/base.py`, `backend/services/vpn/openvpn.py`, `backend/services/vpn/wireguard.py`) with provider-aware upload and status handling in the API (`backend/api/routes/vpn.py`). Systemd units for OpenVPN are packaged under `system/rose-openvpn@.service`, and kill-switch handling is unified across providers via the existing firewall logic.

---

### Connected Clients Management

**Priority**: High
**Complexity**: Low-Medium
**Status**: ✅ Completed

**Current Implementation**: Persistent client tracking, device naming, and control flows are live via `backend/services/clients_service.py` and the associated API routes (`backend/api/routes/clients.py`). Historical and connected-client data is surfaced in the UI alongside block/unblock and kick actions, with backend support for MAC filtering and traffic metadata.

---

### Simple QoS (Traffic Prioritization)

**Priority**: Medium
**Complexity**: Medium-High
**Status**: ✅ Completed

**Description**: A simple "prioritize VPN traffic" toggle is implemented using tc-based shaping with firewall marks. API routes expose enable/disable/status operations (`backend/api/routes/qos.py`), and the service layer encapsulates queue setup/teardown (`backend/services/qos_service.py`). UI controls ship with the dashboard to switch prioritization on demand. Future profiles remain a post-1.1 enhancement.

---

### Ready-to-Flash SD Card Image

**Priority**: High
**Complexity**: High
**Status**: ✅ Completed

**Description**: Critical for ease of use - biggest barrier to adoption is installation complexity.

**Current Implementation**: SD card image generation is scripted via `scripts/build-image.sh`, targeting Raspberry Pi OS Lite with built-in ROSE Link services and setup automation. The script handles download, customization, compression, and checksum steps to produce ready-to-flash artifacts for releases.

---

### First-Time Setup Wizard

**Priority**: High
**Complexity**: Medium
**Status**: ✅ Completed

**Current Implementation**: First-run detection and wizard orchestration live in `backend/services/setup_service.py` with dedicated API routes (`backend/api/routes/setup.py`). Frontend setup flows and localization are bundled with the web assets and corresponding tests (`web/__tests__/setup.js`), providing guided WAN, VPN, hotspot, security, and AdGuard configuration on initial boot.

---

### Full Test Suite (90%+ Coverage)

**Priority**: High
**Complexity**: Medium
**Status**: ✅ In Place

**Current Implementation**: Backend and frontend suites cover the shipping features, including AdGuard, OpenVPN, clients, QoS, setup, hotspot, WAN, and system services (`backend/tests/*`, `web/__tests__`). Coverage thresholds are enforced in web tests (90% global targets in `web/package.json`), and API/service behavior is validated across dedicated test modules.

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

## Contributing to v1.2.x

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

**v1.2.x Target**: Extended feature polish beyond the current production release

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

