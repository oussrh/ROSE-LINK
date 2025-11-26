# Contributing to ROSE Link

Thank you for considering contributing to ROSE Link!

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected behavior vs actual behavior
- System information (Raspberry Pi model, OS version, etc.)
- Relevant logs

### Suggesting Features

Feature requests are welcome! Please create an issue with:
- Clear description of the feature
- Use case / motivation
- Possible implementation approach (if you have ideas)

See [ROADMAP.md](ROADMAP.md) for planned features.

### Pull Requests

1. **Fork** the repository
2. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**:
   - Follow existing code style
   - Add comments for complex logic
   - Add tests for new functionality
   - Test your changes on actual hardware if possible
4. **Run the test suite**:
   ```bash
   make test
   make lint
   ```
5. **Commit** with clear messages:
   ```bash
   git commit -m "Add: description of feature"
   git commit -m "Fix: description of bug fix"
   ```
6. **Push** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Open a Pull Request** with:
   - Clear description of changes
   - Reference to related issues
   - Screenshots/logs if applicable

## Development Setup

For comprehensive development instructions, see [DEVELOPMENT.md](DEVELOPMENT.md).

### Quick Start

```bash
# Clone the repository
git clone https://github.com/oussrh/ROSE-LINK.git
cd ROSE-LINK

# Setup development environment (backend + dev tools)
make setup-dev

# Activate virtual environment
source backend/venv/bin/activate

# Run tests
make test

# Start development server
make dev
```

### Testing

Before submitting a PR:

```bash
# Run all tests with coverage
make test

# Run linting
make lint

# Run full CI locally
make ci
```

Ensure:
1. **All tests pass**: `make test` exits with code 0
2. **Coverage maintained**: Minimum 70% coverage
3. **Linting passes**: No errors from `make lint`
4. **Backend API**: Endpoints work correctly
5. **Web UI**: Test in different browsers
6. **Hardware** (if applicable): Test on Raspberry Pi

## Code Style

### Python
- Follow PEP 8
- Use type hints where appropriate
- Add docstrings for functions/classes
- Keep functions focused and small

### Shell Scripts
- Use `#!/bin/bash` shebang
- Set `set -e` for error handling
- Add comments for complex operations
- Quote variables: `"$VAR"`

### Web (HTML/JS)
- Use semantic HTML
- Follow existing Tailwind CSS patterns
- Keep JavaScript simple and readable
- Add comments for complex logic

## Project Structure

```
ROSE-LINK/
├── backend/          # FastAPI backend
├── web/             # Web UI (HTML/CSS/JS)
├── system/          # System configs (hostapd, dnsmasq, etc.)
├── scripts/         # Build and utility scripts
├── debian/          # Debian packaging files
└── docs/            # Additional documentation
```

## Commit Message Guidelines

Use conventional commits format:

- `Add: new feature`
- `Fix: bug description`
- `Update: component improvements`
- `Docs: documentation changes`
- `Refactor: code restructuring`
- `Test: add or update tests`
- `Chore: maintenance tasks`

Examples:
```
Add: multi-profile VPN support
Fix: hotspot not starting on boot
Update: improve VPN watchdog reliability
Docs: add troubleshooting section
```

## Questions?

Feel free to open an issue with the `question` label!

---

🌹 **Thank you for contributing to ROSE Link!**
