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

## [Unreleased]

### Planned for 0.2.0
- [ ] Next.js SPA web interface with animations
- [ ] WebSocket real-time status updates
- [ ] i18n support (FR, EN, NL, AR)
- [ ] Configuration backup/restore
- [ ] Let's Encrypt SSL certificate option
- [ ] Speed test integration
- [ ] Email notifications for VPN failures

### Planned for 0.3.0
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

[0.1.0]: https://github.com/oussrh/ROSE-LINK/releases/tag/v0.1.0
