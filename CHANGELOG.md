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

## [Unreleased]

### Planned for 0.3.0
- [ ] WebSocket real-time status updates
- [ ] Configuration backup/restore
- [ ] Let's Encrypt SSL certificate option
- [ ] Speed test integration
- [ ] Email notifications for VPN failures
- [ ] QoS (Quality of Service) traffic prioritization
- [ ] AdGuard Home integration (DNS filtering + ad blocking)
- [ ] OpenVPN support (in addition to WireGuard)
- [ ] Grafana metrics dashboard
- [ ] Bandwidth usage statistics
- [ ] Connected clients management

### Planned for 1.0.0
- [ ] Flashable SD card image (Raspberry Pi OS + ROSE Link)
- [ ] First-run setup wizard
- [ ] Multi-WAN load balancing
- [ ] iOS/Android companion app
- [ ] Automatic updates
- [ ] Full test suite

---

[0.2.1]: https://github.com/oussrh/ROSE-LINK/releases/tag/v0.2.1
[0.2.0]: https://github.com/oussrh/ROSE-LINK/releases/tag/v0.2.0
[0.1.0]: https://github.com/oussrh/ROSE-LINK/releases/tag/v0.1.0
