# Changelog

All notable changes to ROSE Link will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-11-05

### Added
- 🎉 Initial release of ROSE Link Pro
- 📡 WAN connectivity with Ethernet (priority) and WiFi client (fallback)
- 🔐 WireGuard VPN client with multi-profile support
- 📶 WiFi hotspot/AP with configurable SSID, password, country, channel
- 🛡️ Kill-switch iptables rules (no traffic if VPN down)
- 👁️ VPN watchdog with automatic reconnection
- 🎨 Modern dark-themed Web UI with Tailwind CSS and htmx
- 🔒 HTTPS with self-signed certificate via Nginx
- 🐍 FastAPI REST API for all operations
- 📦 Three installation methods: archive (.tar.gz), Debian package (.deb), APT repository
- 📚 Complete documentation and README
- 🔧 Systemd services for all components
- 🚀 One-command installation script

### Features
- Auto-failover between Ethernet and WiFi WAN
- Import WireGuard .conf files from web interface
- Real-time status monitoring (WAN, VPN, AP)
- WiFi network scanner for WAN configuration
- Configurable hotspot with WPA2/WPA3 support
- Sudoers configuration for secure privilege escalation
- IP forwarding and NAT configuration
- DHCP/DNS server for hotspot clients (dnsmasq)
- Persistent iptables rules

### Security
- Backend API isolated on 127.0.0.1
- HTTPS-only access via Nginx reverse proxy
- Restricted sudoers for rose user
- Kill-switch protection against VPN leaks
- VPN config files protected (mode 600)
- No root execution of services

### Documentation
- Complete README with installation guides
- API endpoint documentation
- Troubleshooting guide
- Architecture documentation
- Contributing guidelines
- MIT License

### Known Limitations
- WPA3 support depends on hardware/driver
- Self-signed SSL certificate requires manual acceptance
- Simultaneous WiFi WAN + AP on single radio may reduce throughput
- Fritz!Box-specific VPN endpoint (configurable)

## [0.2.0] - 2025-11-26

### Added
- Complete i18n support (English & French) with localStorage persistence
- Mobile-first responsive design for all screen sizes
- Toast notification system for user feedback
- Tab state persistence across page reloads
- Loading spinner indicators for async operations
- Accessibility improvements (ARIA labels, roles, semantic HTML)
- CORS middleware for external API access
- API documentation endpoints (/api/docs, /api/redoc)

### Changed
- **Backend**: Complete code refactoring with comprehensive docstrings
- **Backend**: Fixed hardcoded `wlan0` interface - now uses dynamic interface detection
- **Backend**: Updated deprecated `model.dict()` to `model_dump()` (Pydantic v2)
- **Backend**: Added command timeout and improved error handling
- **Backend**: Enhanced input validation with Pydantic Field constraints
- **Frontend**: Upgraded htmx from 1.9.10 to 2.0.3 (latest stable)
- **Frontend**: All text now uses i18n system (no more hardcoded French text)
- **Frontend**: Improved touch targets for mobile devices (touch-manipulation)
- **Frontend**: Sticky header for better mobile navigation
- **Frontend**: Optimized status cards for 3-column mobile layout
- **Dependencies**: Updated to cutting-edge package versions:
  - FastAPI >= 0.115.0 (was 0.109.0)
  - Uvicorn >= 0.32.0 (was 0.27.0)
  - Pydantic >= 2.10.0 (was 2.5.3)
  - python-multipart >= 0.0.17 (was 0.0.6)

### Fixed
- WiFi disconnect endpoint now uses configured interface instead of hardcoded `wlan0`
- VPN transfer stats parsing for edge cases
- Symlink handling for VPN profile activation
- Error handling for missing configuration files

### Improved
- Code organization with clear section separators
- Type hints throughout the codebase
- Error messages with more context
- UI/UX with consistent spacing and responsive breakpoints
- Performance with optimized re-renders and lazy loading

## [0.2.1] - 2025-11-26

### Added
- Product features documentation (PRODUCT_FEATURES.md)
- Frontend tests execution in CI pipeline

### Changed
- **CI/CD**: Made mypy type checking blocking (was non-blocking with `|| true`)
- **CI/CD**: Made frontend linting blocking (removed `continue-on-error`)
- **CI/CD**: Made ShellCheck linting blocking (was non-blocking with `|| true`)
- **CI/CD**: Made Bandit security scan blocking (was non-blocking with `|| true`)
- **CI/CD**: Increased JavaScript test coverage threshold from 50% to 70%
- **CI/CD**: Build job now depends on both backend and frontend tests

### Improved
- Updated DEVELOPMENT.md with comprehensive CI check documentation
- All quality gates in CI pipeline are now strictly enforced

## [0.3.0] - 2025-11-26

### Added
- **WebSocket Real-time Updates**: Replace polling with WebSocket for live status updates
  - Backend WebSocket manager with connection handling
  - Frontend WebSocket utility with auto-reconnection
  - Real-time status broadcasting every 2 seconds
  - Support for on-demand status and bandwidth requests

- **Configuration Backup/Restore**: Complete backup and restore functionality
  - Backup VPN profiles, hotspot config, and system settings
  - Download backups as .tar.gz files
  - Upload and import backup files
  - Selective component restore
  - Backup metadata with timestamps

- **Bandwidth Statistics**: Real-time network bandwidth monitoring
  - Per-interface statistics (bytes, packets, errors)
  - Bandwidth rate calculation
  - Historical data tracking
  - Formatted human-readable values

- **Prometheus Metrics Endpoint**: `/api/metrics` for monitoring
  - VPN, WAN, and Hotspot status metrics
  - System metrics (CPU, memory, disk, temperature)
  - Network bandwidth counters per interface
  - Uptime and connection metrics

- **Speed Test Integration**: Internet speed testing
  - Support for speedtest-cli and Ookla speedtest
  - Async test execution
  - Test history storage
  - Fallback to basic ping test

- **Let's Encrypt SSL Certificates**: Automated SSL management
  - Request certificates via certbot
  - Renew existing certificates
  - Generate self-signed certificates
  - Certificate status and expiry monitoring

### API Endpoints Added
- `WS /api/ws` - WebSocket for real-time updates
- `GET /api/ws/status` - WebSocket connection status
- `GET /api/backup/list` - List available backups
- `POST /api/backup/create` - Create new backup
- `POST /api/backup/restore/{filename}` - Restore from backup
- `GET /api/backup/download/{filename}` - Download backup
- `POST /api/backup/upload` - Upload backup file
- `DELETE /api/backup/{filename}` - Delete backup
- `GET /api/metrics` - Prometheus metrics
- `GET /api/speedtest/status` - Speed test status
- `POST /api/speedtest/run` - Start speed test
- `GET /api/speedtest/history` - Test history
- `GET /api/ssl/status` - SSL certificate status
- `POST /api/ssl/request` - Request Let's Encrypt certificate
- `POST /api/ssl/renew` - Renew certificates
- `POST /api/ssl/self-signed` - Generate self-signed certificate

### Services Added
- `BandwidthService` - Network bandwidth monitoring
- `BackupService` - Configuration backup/restore
- `SpeedTestService` - Internet speed testing
- `SSLService` - SSL certificate management
- `ConnectionManager` - WebSocket connection management

### Changed
- Frontend now uses WebSocket for real-time status updates
- Reduced polling frequency (WebSocket provides instant updates)
- Improved status card rendering performance

### Planned for 0.4.0
- [ ] Email notifications for VPN failures
- [ ] QoS (Quality of Service) traffic prioritization
- [ ] AdGuard Home integration (DNS filtering + ad blocking)
- [ ] OpenVPN support (in addition to WireGuard)
- [ ] Grafana metrics dashboard
- [ ] Connected clients management

## [1.0.0] - 2025-11-26

### Added
- **AdGuard Home Integration**: DNS-level ad blocking built-in
  - Full AdGuard Home management API
  - Blocking statistics and query log
  - Enable/disable filtering from web interface
  - Automatic DNS configuration

- **OpenVPN Support**: Multi-protocol VPN support
  - Upload and manage .ovpn configuration files
  - Support for embedded certificates
  - Username/password authentication support
  - VPN provider abstraction layer for future protocols

- **Connected Clients Management**: Complete device tracking
  - Real-time and historical client tracking
  - MAC-based device type detection (Apple, Samsung, etc.)
  - Custom device naming
  - Block/unblock/kick clients
  - Per-client traffic statistics

- **QoS Traffic Prioritization**: Simple traffic management
  - "Prioritize VPN Traffic" toggle
  - Configurable bandwidth allocation
  - Uses Linux tc with HTB queueing
  - iptables packet marking

- **First-Time Setup Wizard**: Guided initial configuration
  - Multi-step wizard (Network, VPN, Hotspot, Security, AdGuard)
  - First-run detection
  - Skip option for advanced users
  - Language selection (EN/FR)

- **Ready-to-Flash SD Card Image**: Simplified installation
  - Pre-configured Raspberry Pi OS image
  - First-boot auto-configuration
  - Setup WiFi hotspot for initial configuration
  - GitHub Actions workflow for automated builds

- **Comprehensive Test Suite**: 90%+ code coverage
  - Tests for all new services
  - Integration tests for API routes
  - Frontend tests for new components

### API Endpoints Added
- `GET/POST /api/adguard/*` - AdGuard Home management
- `GET/PUT/POST /api/clients/*` - Connected clients management
- `GET/POST/PUT /api/qos/*` - QoS traffic prioritization
- `GET/POST /api/setup/*` - First-time setup wizard

### Services Added
- `AdGuardService` - AdGuard Home integration
- `ClientsService` - Connected clients management
- `QoSService` - Traffic prioritization
- `SetupService` - Setup wizard state management
- `VPNManager` - Unified VPN provider management
- `WireGuardProvider` - WireGuard VPN provider
- `OpenVPNProvider` - OpenVPN VPN provider

### Changed
- Refactored VPN service to support multiple providers
- Updated ROADMAP.md with v1.0.0 focused scope
- Improved documentation with new features

### Security
- MAC-based client blocking via iptables
- Secure credential storage for OpenVPN auth

---

## [1.1.0] - 2025-11-26

### Added
- **Performance Metrics Endpoint**: `/api/metrics/performance` for application monitoring
  - Request latency statistics (avg, min, max, p50, p95, p99)
  - Total request and error counts
  - Error rate calculation
  - Per-endpoint request tracking

- **Request Timing Middleware**: Automatic latency tracking for all requests
  - Thread-safe metrics collection
  - Rolling sample window for percentile calculations
  - X-Response-Time header on all responses

- **Rate Limiting**: Protection against API abuse
  - VPN upload: 10 requests/minute
  - WiFi/Hotspot configuration: 5 requests/minute
  - System reboot: 2 requests/minute
  - Per-IP throttling using slowapi

- **Comprehensive E2E Test Suite**: Playwright tests for critical user flows
  - VPN management tests (profile upload, activation, status)
  - WiFi WAN tests (scanning, connection, status display)
  - Hotspot tests (configuration, channel selection, clients)
  - Accessibility tests (keyboard navigation, ARIA labels)

- **API Contract Tests**: Schema validation for API responses
  - Health endpoint contracts
  - VPN, WiFi, Hotspot endpoint contracts
  - System and metrics endpoint contracts
  - Error response format validation

- **HTTP/2 Server Push**: Nginx configured for critical asset preloading
  - Push CSS, JavaScript, and images on page load
  - Improved First Contentful Paint (FCP)

### Changed
- **Authentication**: Added `require_auth` to sensitive endpoints
  - `/api/vpn/profiles` - now requires authentication
  - `/api/wifi/scan`, `/api/wifi/connect` - now require authentication
  - `/api/hotspot/clients`, `/api/hotspot/apply` - now require authentication
  - `/api/system/logs`, `/api/system/reboot` - now require authentication
  - `/api/settings/vpn` - now requires authentication

- **Frontend Error Handling**: Complete rewrite of `api.js`
  - New `ApiError` class with status and detail
  - `apiAction()` utility for consistent error handling
  - Request timeout support via AbortController (30s default)
  - Eliminates duplicate error handling code

- **ESLint Configuration**: Migrated to ESLint v9+ flat config
  - New `eslint.config.js` with modern format
  - Updated dependencies (@eslint/js, globals)

- **Test Coverage Threshold**: Increased from 70% to 90%
  - Backend pytest coverage: 90% minimum
  - Frontend Jest coverage: 90% minimum (branches, functions, lines, statements)

### Improved
- Documentation with authentication annotations on all endpoints
- French README (README.fr.md) aligned with English version
- DEVELOPMENT.md updated with new coverage requirements

---

## [1.2.0] - 2025-11-28

### Added
- **Grafana Monitoring Dashboard**: Complete monitoring stack with Docker Compose
  - Grafana + Prometheus + Node Exporter containerized setup
  - Comprehensive ROSE-LINK dashboard with:
    - Status overview (VPN, WAN, Hotspot, Clients, Uptime, Temperature)
    - System resources gauges and time series (CPU, Memory, Disk)
    - Network traffic graphs (throughput, packets, total traffic)
    - VPN & connectivity status history
    - CPU temperature and disk usage over time
  - Template variables for interface filtering (multi-select) and instance selection
  - Link capacity variable (10/100/1000/2500/10000 Mbps) for bandwidth calculations
  - Bandwidth utilization panel showing percentage of capacity used
  - Pre-configured Prometheus scraping of ROSE-LINK metrics endpoint

- **Prometheus Alert Rules**: Production-ready alerting configuration
  - VPNDisconnected: VPN down for >1 minute (Critical)
  - WANDisconnected: WAN down for >2 minutes (Critical)
  - HighCPUTemperature: CPU temp >70°C for >5 minutes (Warning)
  - CriticalCPUTemperature: CPU temp >80°C for >1 minute (Critical)
  - HighCPUUsage: CPU usage >90% for >5 minutes (Warning)
  - HighMemoryUsage: Memory usage >85% for >5 minutes (Warning)
  - CriticalMemoryUsage: Memory usage >95% for >2 minutes (Critical)
  - LowDiskSpace: Disk usage >80% for >10 minutes (Warning)
  - CriticalDiskSpace: Disk usage >95% for >5 minutes (Critical)
  - HotspotDown: Hotspot inactive for >2 minutes (Warning)
  - RoseLinkDown: Backend not responding for >1 minute (Critical)

- **E2E Test Coverage Improvements**: Comprehensive Playwright tests
  - Grafana dashboard E2E tests with dedicated test project
  - E2E coverage quality assessment and improvements
  - Tests for VPN, WiFi, Hotspot, Accessibility flows

- **Accessibility Enhancements**: Improved keyboard navigation and ARIA support
  - Type checking configuration for frontend
  - Performance benchmarks

### Changed
- Frontend test branch coverage increased to 90%+ threshold
- Enhanced Grafana dashboard panels with min/max aggregations
- Alert annotations added to Grafana panels for operational visibility

### Files Added
- `monitoring/docker-compose.yml` - Container orchestration
- `monitoring/README.md` - Monitoring stack documentation
- `monitoring/prometheus/prometheus.yml` - Prometheus configuration
- `monitoring/prometheus/alerts.yml` - Alert rules
- `monitoring/grafana/dashboards/rose-link-dashboard.json` - Main dashboard
- `monitoring/grafana/provisioning/datasources/datasources.yml` - Datasource config
- `monitoring/grafana/provisioning/dashboards/dashboards.yml` - Dashboard provisioning
- `e2e/tests/grafana.spec.js` - Grafana E2E tests

---

## [Unreleased]

### Planned for 1.x
- Email notifications for VPN failures
- Full QoS profiles (Gaming, Streaming, Work)
- Multi-WAN load balancing
- Automatic updates

---

[1.2.0]: https://github.com/oussrh/ROSE-LINK/releases/tag/v1.2.0
[1.1.0]: https://github.com/oussrh/ROSE-LINK/releases/tag/v1.1.0
[1.0.0]: https://github.com/oussrh/ROSE-LINK/releases/tag/v1.0.0
[0.3.0]: https://github.com/oussrh/ROSE-LINK/releases/tag/v0.3.0
[0.2.1]: https://github.com/oussrh/ROSE-LINK/releases/tag/v0.2.1
[0.2.0]: https://github.com/oussrh/ROSE-LINK/releases/tag/v0.2.0
[0.1.0]: https://github.com/oussrh/ROSE-LINK/releases/tag/v0.1.0
