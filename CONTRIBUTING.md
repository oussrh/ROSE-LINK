# Contributing to ROSE Link

Thank you for considering contributing to ROSE Link! 🌹

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

### Pull Requests

1. **Fork** the repository
2. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**:
   - Follow existing code style
   - Add comments for complex logic
   - Test your changes on actual hardware if possible
4. **Commit** with clear messages:
   ```bash
   git commit -m "Add: description of feature"
   git commit -m "Fix: description of bug fix"
   ```
5. **Push** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
6. **Open a Pull Request** with:
   - Clear description of changes
   - Reference to related issues
   - Screenshots/logs if applicable

## Development Setup

### Prerequisites

- Raspberry Pi 4 (for full testing) or any Debian-based Linux (for development)
- Python 3.9+
- Git

### Local Development

```bash
# Clone the repository
git clone https://github.com/USERNAME/ROSE-LINK.git
cd ROSE-LINK

# Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run backend (development)
python main.py
```

### Testing

Before submitting a PR, please test:

1. **Backend API**: Ensure all endpoints work
2. **Web UI**: Test in different browsers
3. **Installation**: Test install.sh on clean Raspberry Pi OS
4. **Services**: Verify systemd services start correctly
5. **VPN**: Test with actual WireGuard configuration
6. **Hotspot**: Test WiFi AP functionality

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
