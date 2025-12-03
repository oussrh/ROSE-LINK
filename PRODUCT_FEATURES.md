# ROSE Link - Product Features

> **Version 1.6.4** - VPN Router + Ad Blocking on Raspberry Pi

## Overview

ROSE Link transforms your Raspberry Pi into a professional VPN router and WiFi access point, providing secure remote access to your home network from anywhere in the world.

---

## Core Features

### WAN Connectivity

#### Ethernet (Priority)
- **Gigabit support**: Full speed on Pi 4/5
- **Auto-detection**: Plug and play configuration
- **DHCP client**: Automatic IP assignment

#### WiFi Client (Fallback)
- **Network scanning**: Discover available networks
- **Secure connection**: WPA2/WPA3 support
- **Auto-failover**: Seamless switch from Ethernet
- **Status tracking**: Monitor connection state and signal strength

### VPN Support

#### WireGuard
- **Multi-profile management**: Import and switch between configurations
- **Fritz!Box compatible**: Direct .conf file import
- **Kill-switch**: Block all traffic if VPN disconnects
- **Watchdog service**: Automatic reconnection on failure
- **Transfer statistics**: Real-time TX/RX monitoring

#### OpenVPN
- **Profile upload**: Import .ovpn configuration files
- **Embedded certificates**: Full certificate chain support
- **Username/password auth**: Interactive authentication support
- **Provider abstraction**: Unified API for both VPN types

### Hotspot Configuration

#### WiFi Access Point
- **Custom SSID**: Configure your network name
- **Security options**: WPA2/WPA3 (WPA3 enabled when hardware supports it)
- **Regulatory compliance**: Country-specific channel and power settings
- **Channel selection**: Optimize for 2.4GHz (channels 1, 6, 11) or 5GHz bands
- **Client monitoring**: Real-time connected device count

### AdGuard Home Integration

- **DNS-level ad blocking**: Network-wide protection
- **Statistics dashboard**: Blocked queries, top clients
- **Filter management**: Enable/disable from web UI
- **Automatic DNS configuration**: Seamless setup

### Connected Clients Management

- **Real-time tracking**: See all connected devices
- **Device identification**: MAC-based manufacturer detection
- **Custom naming**: Label devices for easy identification
- **Access control**: Block/unblock/kick clients
- **Traffic statistics**: Per-client bandwidth usage
- **Connection history**: Track device activity over time

### QoS (Quality of Service)

- **VPN traffic prioritization**: Ensure stable VPN performance
- **tc-based shaping**: Linux traffic control integration
- **Simple toggle**: Enable/disable from dashboard

---

## User Interface

### Responsive Web Design
- **Dark mode**: Elegant, eye-friendly interface
- **Cross-device support**: Optimized for desktop, tablet, and mobile
- **Real-time updates**: WebSocket-based status refresh
- **Bilingual**: English and French language support

### Modern Technologies
- **htmx 2.0**: Dynamic HTML interactions without full page reloads
- **Tailwind CSS**: Utility-first responsive styling
- **Lucide Icons**: Consistent iconography
- **Toast notifications**: User feedback for actions
- **Loading spinners**: Visual feedback during operations
- **Accessibility**: Keyboard navigation and semantic HTML

### First-Time Setup Wizard
- **Guided configuration**: Step-by-step network, VPN, hotspot setup
- **Language selection**: Choose EN or FR on first boot
- **Skip option**: For advanced users
- **First-run detection**: Automatic wizard trigger

---

## Security Architecture

### Backend Isolation
- **Nginx reverse proxy**: API accessible only through Nginx (127.0.0.1)
- **HTTPS by default**: Self-signed certificate with RSA 4096-bit
- **CORS configuration**: Controlled cross-origin access
- **Rate limiting**: Protection against API abuse

### System Security
- **Restricted sudoers**: Minimal sudo permissions for required commands
- **Protected configurations**: VPN files stored with mode 600
- **iptables kill-switch**: Firewall rules prevent traffic leaks
- **No root services**: All services run under dedicated `rose` user
- **systemd hardening**: ProtectSystem, PrivateTmp, NoNewPrivileges

### Input Validation
- **Pydantic models**: Type-safe request/response validation
- **Input sanitization**: Security sanitizers for user-provided data
- **Command abstraction**: System calls isolated through CommandRunner

---

## Backend Architecture

### Application Structure

```
backend/
├── api/                 # HTTP endpoint routes
│   └── routes/          # Feature-specific endpoints
├── core/                # Application infrastructure
│   ├── app_factory.py   # FastAPI app creation
│   ├── lifespan.py      # Startup/shutdown events
│   ├── middleware.py    # CORS, rate limiting, timing
│   └── websocket.py     # Real-time connection manager
├── services/            # Business logic layer
│   ├── vpn/             # VPN provider abstraction
│   ├── adguard_service.py
│   ├── clients_service.py
│   ├── hotspot_service.py
│   └── ...
├── utils/               # Shared utilities
│   ├── command_runner.py
│   ├── validators.py
│   └── sanitizers.py
├── tests/               # Test suite (80%+ coverage)
├── config.py            # Configuration management
├── models.py            # Pydantic data models
└── main.py              # Application entry point
```

### Design Principles

1. **Application Factory Pattern**: `create_app()` enables test isolation
2. **Service Layer Separation**: Business logic in `services/`, routes handle HTTP only
3. **Dependency Injection**: FastAPI's `Depends()` for auth, config, services
4. **Command Abstraction**: `CommandRunner` isolates system calls for testability

### Key Technologies
- **FastAPI 0.115+**: High-performance async Python framework
- **Pydantic 2.10+**: Data validation and serialization
- **Uvicorn**: ASGI server for production deployment
- **pytest**: Test framework with 80%+ coverage

---

## Monitoring & Observability

### System Insights
- **Live metrics**: CPU, RAM, disk, and temperature in UI
- **Network telemetry**: WAN uptime, VPN handshake stats, client counts
- **Log streaming**: Tail recent backend logs for diagnostics

### Prometheus Metrics
- **Endpoint**: `/api/metrics` in standard Prometheus format
- **VPN metrics**: Connection status, transfer bytes, handshake time
- **System metrics**: CPU usage, memory, disk, temperature
- **Hotspot metrics**: Connected clients, interface stats

### Speed Test Integration
- **Multiple backends**: speedtest-cli, Ookla, basic ping fallback
- **History tracking**: Store and compare results
- **Async execution**: Non-blocking tests

### Backup & Restore
- **Configuration backups**: VPN profiles, hotspot config, system settings
- **Download/Upload**: Manage backups through web UI
- **Selective restore**: Choose which components to restore

---

## API Documentation

### Interactive Documentation
- **Swagger UI**: Available at `/api/docs`
- **ReDoc**: Available at `/api/redoc`
- **OpenAPI spec**: Auto-generated from code annotations

### Endpoint Categories
- **Health/Status**: System health checks and global status
- **WiFi WAN**: Network scanning and connection management
- **VPN**: Profile management, connection control, status
- **Hotspot**: Access point configuration and control
- **AdGuard**: Ad blocking management
- **Clients**: Connected device management
- **QoS**: Traffic prioritization
- **Setup**: First-time configuration wizard
- **Backup**: Configuration backup/restore
- **SSL**: Certificate management
- **Speed Test**: Internet speed testing
- **Metrics**: Prometheus metrics and performance stats
- **System**: Hardware info, interfaces, logs, reboot

---

## Hardware Support

### Raspberry Pi Compatibility

| Model | WiFi Interfaces | Ethernet | WiFi WAN | Hotspot Band | Support Level |
|-------|----------------|----------|----------|--------------|---------------|
| **Raspberry Pi 5** | 1 (Dual-band) | Gigabit | Ethernet only | 5GHz / 2.4GHz | Full |
| **Raspberry Pi 4 Model B** | 1 (Dual-band) | Gigabit | Ethernet only | 5GHz / 2.4GHz | Full |
| **Raspberry Pi 4 + USB WiFi** | 2 | Gigabit | Yes | 5GHz / 2.4GHz | Full |
| **Raspberry Pi 3 Model B+** | 1 (2.4GHz) | 100Mbps | Ethernet only | 2.4GHz | Limited |
| **Raspberry Pi 3 Model B** | 1 (2.4GHz) | 100Mbps | Ethernet only | 2.4GHz | Limited |
| **Raspberry Pi Zero 2 W** | 1 (2.4GHz) | None | USB Ethernet req. | 2.4GHz | Basic |
| **Raspberry Pi 400** | 1 (Dual-band) | Gigabit | Ethernet only | 5GHz / 2.4GHz | Good |
| **Raspberry Pi CM4 + IO Board** | 1 (Dual-band) | Gigabit | Ethernet only | 5GHz / 2.4GHz | Full |

### Other ARM SBCs (Community Tested)

| Model | WiFi Interfaces | Ethernet | Support Level |
|-------|----------------|----------|---------------|
| **Orange Pi 5** | 1 (Dual-band) | Gigabit | Good* |
| **Banana Pi M5** | 1 (Dual-band) | Gigabit | Good* |
| **ODROID-C4** | None | Gigabit | Limited* |
| **Rock Pi 4** | 1 (Dual-band) | Gigabit | Good* |
| **NanoPi R4S** | None | Dual Gigabit | Good* |

> **\*** Community tested - may require manual configuration. Must run Debian-based Linux.

### Single vs Dual WiFi

Most Raspberry Pi models have only **one WiFi interface**:
- WiFi is **reserved for the hotspot** (Access Point mode)
- Internet connection **must come from Ethernet**
- WiFi WAN options are **automatically hidden** in the web interface

Adding a USB WiFi adapter enables:
- One WiFi for **WAN connection** (connects to existing WiFi)
- One WiFi for **Hotspot** (creates ROSE-Link network)

### Requirements
- **RAM**: 512MB minimum, 2GB+ recommended
- **Storage**: 8GB microSD minimum, 32GB Class A2 recommended
- **OS**: Raspberry Pi OS (Bullseye/Bookworm/Trixie) or Debian 11/12/13

### Hardware Detection
- **Auto-detection**: Model, interfaces, WiFi capabilities
- **Single WiFi detection**: Hides WiFi WAN options when only one interface
- **Dynamic configuration**: Adapts to available hardware
- **5GHz auto-enable**: When hardware supports it

---

## Installation Methods

### Method 1: One-Line Install
```bash
curl -fsSL https://raw.githubusercontent.com/oussrh/ROSE-LINK/main/install.sh | sudo bash
```

### Method 2: Download and Install
```bash
wget https://github.com/oussrh/ROSE-LINK/releases/latest/download/rose-link-pro.tar.gz
tar -xzf rose-link-pro.tar.gz && cd rose-link
sudo bash install.sh
```

### Method 3: APT Repository (Recommended)
```bash
curl -sSL https://oussrh.github.io/ROSE-LINK/install.sh | sudo bash
sudo apt install rose-link
```

### Method 4: Ready-to-Flash SD Image
- Pre-configured Raspberry Pi OS image
- First-boot auto-setup
- Setup WiFi hotspot for initial configuration

---

## Developer Experience

### Makefile Automation

| Target | Purpose |
|--------|---------|
| `setup-dev` | Initialize development environment |
| `dev` | Run backend with auto-reload |
| `test` | Execute test suite |
| `test-cov` | Run tests with coverage report |
| `lint` | Check code style with Ruff |
| `typecheck` | Run mypy type checking |
| `security` | Execute Bandit security scan |
| `archive` | Build tar.gz distribution |
| `deb` | Build Debian package |

### CI/CD Pipeline

| Check | Tool | Threshold |
|-------|------|-----------|
| Backend Tests | pytest | 80% coverage |
| Backend Linting | Ruff | Zero errors |
| Type Checking | mypy | Zero errors |
| Frontend Tests | Jest | 65-80% coverage |
| Frontend Linting | ESLint | Zero errors |
| Shell Scripts | ShellCheck | Zero warnings |
| Security Scan | Bandit | Zero high/medium |

---

## License

MIT License - See [LICENSE](LICENSE) for details.
