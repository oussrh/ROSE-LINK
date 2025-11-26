# ROSE Link Development Guide

This document provides comprehensive guidance for contributors and developers working on ROSE Link.

## Table of Contents

- [Development Environment Setup](#development-environment-setup)
- [Project Architecture](#project-architecture)
- [Running Locally](#running-locally)
- [Frontend Development](#frontend-development)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Building Artifacts](#building-artifacts)
- [CI/CD Pipeline](#cicd-pipeline)
- [Debugging](#debugging)
- [Common Tasks](#common-tasks)

---

## Development Environment Setup

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.9+ | Recommended: 3.11 |
| Node.js | 18+ | Required for frontend tooling |
| Git | 2.x | For version control |
| Make | 4.x | Build automation |
| curl, jq | Latest | API testing |

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/oussrh/ROSE-LINK.git
cd ROSE-LINK

# 2. Setup development environment (creates venv, installs all deps)
make setup-dev

# 3. Activate the virtual environment
source backend/venv/bin/activate

# 4. Run tests to verify setup
make test

# 5. Start development server
make dev
```

### Manual Setup

If you prefer manual setup:

```bash
# Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Verify installation
python -c "import fastapi; print(f'FastAPI {fastapi.__version__}')"
pytest --version
ruff --version
```

### IDE Configuration

#### VS Code

Recommended extensions:
- Python (Microsoft)
- Pylance
- Ruff
- Even Better TOML

Settings (`.vscode/settings.json`):
```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/backend/venv/bin/python",
    "python.linting.enabled": true,
    "editor.formatOnSave": true,
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff"
    }
}
```

#### PyCharm

1. Set Python interpreter to `backend/venv/bin/python`
2. Mark `backend/` as Sources Root
3. Enable pytest as default test runner

---

## Project Architecture

```
ROSE-LINK/
├── backend/                 # FastAPI REST API
│   ├── api/                # HTTP endpoint routes
│   │   ├── routes/         # Feature-specific routes
│   │   └── deps.py         # Dependency injection
│   ├── core/               # Application infrastructure
│   │   ├── app_factory.py  # FastAPI app creation
│   │   ├── lifespan.py     # Startup/shutdown events
│   │   └── middleware.py   # CORS, security
│   ├── services/           # Business logic layer
│   │   ├── auth.py         # Authentication
│   │   ├── vpn.py          # VPN management
│   │   ├── wan.py          # WAN connectivity
│   │   ├── hotspot.py      # WiFi AP
│   │   ├── system.py       # System monitoring
│   │   └── interface.py    # Network interfaces
│   ├── utils/              # Shared utilities
│   │   ├── command_runner.py  # System command execution
│   │   ├── validators.py   # Input validation
│   │   └── sanitizers.py   # Security sanitization
│   ├── tests/              # Test suite
│   ├── config.py           # Configuration management
│   ├── models.py           # Pydantic data models
│   ├── exceptions.py       # Custom exceptions
│   └── main.py             # Application entry point
│
├── web/                    # Frontend (Static HTML/JS)
│   ├── js/                 # JavaScript modules
│   │   ├── components/     # Feature components
│   │   ├── utils/          # API, DOM, toast utilities
│   │   └── i18n.js         # Internationalization
│   ├── css/                # Tailwind CSS
│   ├── locales/            # Translation files
│   ├── vendor/             # Third-party libraries
│   └── index.html          # Main SPA template
│
├── system/                 # System configuration
│   ├── nginx/              # Reverse proxy config
│   ├── *.service           # Systemd service files
│   └── *.conf              # Service configurations
│
├── scripts/                # Build and utility scripts
├── debian/                 # Debian packaging
├── .github/workflows/      # CI/CD pipelines
└── docs/                   # Additional documentation
```

### Key Design Patterns

1. **Service Layer**: All business logic in `services/`, HTTP routes only handle request/response
2. **Dependency Injection**: FastAPI's `Depends()` for auth, config, services
3. **Command Abstraction**: `CommandRunner` class isolates system calls for testability
4. **Factory Pattern**: `create_app()` enables test isolation

---

## Running Locally

### Backend Only

```bash
# Development server with auto-reload
make dev

# Or manually:
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API is available at:
- http://localhost:8000/api/health
- http://localhost:8000/api/docs (Swagger UI)
- http://localhost:8000/api/redoc (ReDoc)

### Full Stack (with Nginx)

For production-like testing:

```bash
# 1. Install on a Raspberry Pi or VM
sudo bash install.sh

# 2. Access via HTTPS
https://<device-ip>/
```

### Mock Mode

The backend can run without actual hardware by mocking system commands:

```python
# In tests, commands are automatically mocked
# For development, set environment variable:
export ROSE_MOCK_COMMANDS=true
```

---

## Frontend Development

The frontend is a static site served by Nginx. Local tooling uses Node.js for linting, testing, and type checking.

### Setup

```bash
cd web
npm install
```

### Useful Commands

```bash
# Lint JavaScript
npm run lint

# Fix lint issues where possible
npm run lint:fix

# Run Jest tests
npm test

# Collect coverage reports
npm run test:coverage

# Type-check TypeScript-aware JSDoc/definitions
npm run typecheck
```

Tests and linting rely on the Jest configuration and ESLint rules defined in `web/package.json` and `web/eslint.config.js`. Coverage output is written to `web/coverage/`.

---

## Testing

### Running Tests

```bash
# All tests with coverage
make test

# Fast tests (no coverage)
make test-fast

# With coverage report
make test-cov
# Opens: backend/coverage_html/index.html

# Specific test file
cd backend
pytest tests/test_vpn_service.py -v

# Specific test
pytest tests/test_vpn_service.py::test_get_vpn_status -v

# Run only marked tests
pytest -m "not slow"
pytest -m "integration"
```

### Test Organization

| File | Purpose |
|------|---------|
| `conftest.py` | Fixtures, mock executor, test client |
| `test_*_service.py` | Service layer unit tests |
| `test_api_*.py` | API endpoint tests |
| `test_core_*.py` | Application infrastructure tests |

### Writing Tests

```python
# tests/test_example.py
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_service(mock_executor):
    """Create service with mocked command execution."""
    from services.vpn import VPNService
    return VPNService(executor=mock_executor)

def test_vpn_status_connected(mock_service, mock_executor):
    """Test VPN status when connected."""
    # Arrange
    mock_executor.add_response("wg show wg0", "interface: wg0\n...")

    # Act
    status = mock_service.get_status()

    # Assert
    assert status.connected is True
    mock_executor.assert_called_with("wg show wg0")
```

### Coverage Requirements

- **Backend (Python)**: 80% minimum coverage
- **Frontend (JavaScript)**: 65-80% minimum across metrics (branches 65%, functions 80%, lines 70%, statements 70%)
- CI fails if coverage drops below threshold

---

## Code Quality

### Linting

```bash
# Check for issues
make lint

# Auto-fix issues
make lint-fix

# Manual ruff commands
cd backend
ruff check .           # Lint
ruff check . --fix     # Auto-fix
ruff format .          # Format
```

### Type Checking

```bash
make typecheck

# Or manually
cd backend
mypy . --ignore-missing-imports
```

### Security Scanning

```bash
make security

# Or manually
cd backend
bandit -r . -ll --exclude ./tests
```

### Pre-commit Hooks (Optional)

```bash
# Install hooks
cd backend
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## Building Artifacts

### Development Build

```bash
# Test archive creation
make archive
# Creates: rose-link-X.X.X.tar.gz

# Test Debian package
make deb
# Creates: rose-link_X.X.X_all.deb

# Build both
make all
```

### Clean Build

```bash
# Remove all build artifacts and caches
make clean
```

### Version Bump

1. Update version in:
   - `backend/config.py`: `VERSION = "X.X.X"`
   - `CHANGELOG.md`: Add new version section
   - `Makefile`: Update version target

2. Create git tag:
```bash
git tag -a vX.X.X -m "Release vX.X.X"
git push origin vX.X.X
```

---

## CI/CD Pipeline

### Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | Push, PR | Tests, linting, security |
| `release.yml` | Tag push | Build and publish releases |

### Running CI Locally

```bash
# Full CI simulation
make ci

# This runs:
# 1. make lint
# 2. make test-cov
# 3. make security
```

### CI Checks

All checks are blocking - the CI pipeline fails if any check does not pass.

| Check | Tool | Threshold |
|-------|------|-----------|
| Backend Tests | pytest | 80% coverage minimum |
| Backend Linting | Ruff | Zero errors |
| Backend Type Checking | mypy | Zero type errors |
| Frontend Tests | Jest | 65-80% coverage minimum |
| Frontend Linting | ESLint | Zero errors |
| Shell Script Linting | ShellCheck | Zero warnings |
| Security Scan | Bandit | Zero high/medium issues |
| Build Verification | Archive creation | Must succeed |

---

## Debugging

### Backend Logs

```bash
# Development server logs (auto)
make dev

# Production logs
sudo journalctl -u rose-backend -f

# Enable debug logging
export LOG_LEVEL=DEBUG
uvicorn main:app --reload
```

### API Testing

```bash
# Health check
curl -s http://localhost:8000/api/health | jq

# Authenticated request
curl -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/status | jq

# POST request
curl -X POST \
     -H "Content-Type: application/json" \
     -d '{"ssid": "test", "password": "test123"}' \
     http://localhost:8000/api/wifi/connect
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Module not found | Activate venv: `source backend/venv/bin/activate` |
| Permission denied | Check file permissions, run as non-root |
| Tests fail on hardware | Run with `-m "not integration"` |
| Coverage too low | Add tests for uncovered code paths |

---

## Common Tasks

### Adding a New API Endpoint

1. Create route in `backend/api/routes/`
2. Add service method in `backend/services/`
3. Add Pydantic models if needed
4. Write tests in `backend/tests/`
5. Update API documentation

### Adding a New Service

1. Create `backend/services/new_service.py`
2. Add to `__init__.py` exports
3. Create fixture in `tests/conftest.py`
4. Write comprehensive tests

### Updating Dependencies

```bash
# Update requirements.txt
pip install --upgrade <package>
pip freeze | grep <package>  # Get exact version

# Update requirements-dev.txt for dev dependencies
```

### Running on Real Hardware

```bash
# 1. SSH to Raspberry Pi
ssh pi@<ip-address>

# 2. Clone and install
git clone https://github.com/oussrh/ROSE-LINK.git
cd ROSE-LINK
sudo bash install.sh

# 3. Test installation
curl -k https://localhost/api/health
```

---

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic v2 Docs](https://docs.pydantic.dev/)
- [pytest Documentation](https://docs.pytest.org/)
- [Ruff Linter](https://docs.astral.sh/ruff/)
- [WireGuard Documentation](https://www.wireguard.com/)

---

## Questions?

- Open an issue with the `question` label
- Check existing issues and discussions
- Review the [CONTRIBUTING.md](CONTRIBUTING.md) guide
