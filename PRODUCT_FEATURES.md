- **Status tracking**: Monitor connection state and signal strength

### Hotspot Configuration

#### WiFi Access Point
- **Custom SSID**: Configure your network name
- **Security options**: WPA2/WPA3 (WPA3 enabled when hardware supports it)
- **Regulatory compliance**: Country-specific channel and power settings
- **Channel selection**: Optimize for 2.4GHz (channels 1, 6, 11) or 5GHz bands
- **Client monitoring**: Real-time connected device count

### User Interface

#### Responsive Web Design
- **Dark mode**: Elegant, eye-friendly interface
- **Cross-device support**: Optimized for desktop, tablet, and mobile
- **Real-time updates**: Automatic status refresh
- **Bilingual**: English and French language support

#### Modern Technologies
- **htmx**: Dynamic HTML interactions without full page reloads
- **Tailwind CSS**: Utility-first responsive styling
- **Lucide Icons**: Consistent iconography
- **Toast notifications**: User feedback for actions
- **Loading spinners**: Visual feedback during operations
- **Accessibility baseline**: Keyboard navigation and semantic structure respected across views

#### Device Management
- **Profile presets**: Pre-defined VPN, WAN, and hotspot defaults for quick onboarding
- **Config export/import**: Backup or restore device settings through the UI
- **Session-safe edits**: Pending changes staged until explicitly applied

---

## Security Architecture

### Backend Isolation
- **Nginx reverse proxy**: API accessible only through Nginx, not directly exposed
- **HTTPS by default**: Self-signed certificate for encrypted connections
- **CORS configuration**: Controlled cross-origin access

### System Security
- **Restricted sudoers**: Minimal sudo permissions for required system commands only
- **Protected configurations**: VPN files stored with mode 600 (owner read/write only)
- **iptables kill-switch**: Firewall rules prevent traffic leaks when VPN is down

### Input Validation
- **Pydantic models**: Type-safe request/response validation
- **Input sanitization**: Security sanitizers for user-provided data
- **Command abstraction**: System calls isolated through CommandRunner class

---

## Backend Architecture

### Application Structure
@@ -94,50 +100,51 @@ backend/
│   ├── wan.py           # WAN connectivity
│   ├── hotspot.py       # WiFi access point
│   ├── system.py        # System monitoring
│   └── interface.py     # Network interface detection
├── utils/               # Shared utilities
│   ├── command_runner.py  # System command execution
│   ├── validators.py    # Input validation helpers
│   └── sanitizers.py    # Security sanitization
├── tests/               # Test suite
├── config.py            # Configuration management
├── models.py            # Pydantic data models
└── main.py              # Application entry point
```

### Design Principles

1. **Application Factory Pattern**: `create_app()` function enables test isolation and configuration flexibility
2. **Service Layer Separation**: Business logic in `services/`, HTTP routes handle only request/response
3. **Dependency Injection**: FastAPI's `Depends()` for authentication, configuration, and services
4. **Command Abstraction**: `CommandRunner` class isolates system calls for testability and security

### Key Technologies
- **FastAPI 0.115+**: High-performance async Python framework
- **Pydantic 2.10+**: Data validation and serialization
- **Uvicorn**: ASGI server for production deployment
- **Redis**: Caching layer for connection metrics and UI presence indicators

---

## Developer Experience

### Makefile Automation

| Target | Purpose |
|--------|---------|
| `setup-dev` | Initialize development environment (venv, dependencies) |
| `dev` | Run backend in development mode with auto-reload |
| `test` | Execute test suite |
| `test-cov` | Run tests with coverage report generation |
| `lint` | Check code style with Ruff |
| `lint-fix` | Auto-fix linting issues |
| `typecheck` | Run mypy type checking |
| `security` | Execute Bandit security scan |
| `archive` | Build tar.gz distribution |
| `deb` | Build Debian package |
| `clean` | Remove build artifacts and caches |

### Local CI Simulation
```bash
# Run full CI pipeline locally
make ci
@@ -157,50 +164,64 @@ make ci
| Python type checking | mypy | Yes | Zero errors |
| Backend tests | pytest | Yes | 70% coverage |
| Frontend linting | ESLint | Yes | Zero errors |
| Frontend tests | Jest | Yes | 70% coverage |
| Shell scripts | ShellCheck | Yes | Zero warnings |
| Security scan | Bandit | Yes | Zero high/medium issues |

### Workflow Structure

```yaml
# .github/workflows/ci.yml
jobs:
  test-backend:     # Python tests, linting, types, coverage
  test-frontend:    # JavaScript tests, linting, coverage
  lint-shell:       # Shell script validation
  security-scan:    # Bandit security analysis
  build-test:       # Artifact creation verification
```

### Coverage Requirements
- **Backend (Python)**: Minimum 70% coverage, target 80%+ for new code
- **Frontend (JavaScript)**: Minimum 70% coverage across branches, functions, lines, statements

---

## Observability & Maintenance

### System Insights
- **Live metrics**: CPU, RAM, disk, and temperature surfaced in the UI
- **Network telemetry**: WAN uptime, VPN handshake stats, and hotspot client counts
- **Log streaming**: Tail recent backend logs for support diagnostics

### Backup & Updates
- **Configuration backups**: Downloadable tarball containing VPN profiles and network settings
- **Offline update flow**: Upload signed bundle to upgrade without internet connectivity
- **Safety nets**: Update pre-checks verify disk space, signatures, and version compatibility

---

## API Documentation

### Interactive Documentation
- **Swagger UI**: Available at `/api/docs`
- **ReDoc**: Available at `/api/redoc`
- **OpenAPI spec**: Auto-generated from code annotations

### Endpoint Categories
- **Health/Status**: System health checks and global status
- **WiFi WAN**: Network scanning and connection management
- **VPN**: Profile management, connection control, status monitoring
- **Hotspot**: Access point configuration and control
- **Settings**: Watchdog and system configuration
- **System**: Hardware info, interfaces, logs, reboot

---

## Hardware Support

### Raspberry Pi Compatibility

| Model | Support Level | WiFi Bands | Notes |
|-------|--------------|------------|-------|
| Raspberry Pi 5 | Full | 2.4GHz + 5GHz | Optimal performance |
| Raspberry Pi 4 | Full | 2.4GHz + 5GHz | Recommended |
