# Security Policy

## Supported Versions

We provide security updates for the actively maintained release lines listed below. Versions not marked as supported will only receive fixes through an upgrade to a supported branch.

| Version | Supported          |
| ------- | ------------------ |
| 1.1.x   | :white_check_mark: |
| 1.0.x   | :white_check_mark: |
| 0.3.x   | :x:                |
| < 0.3   | :x:                |

## Security Features

ROSE Link implements multiple layers of security:

- **Network Isolation**: Backend API accessible only via Nginx reverse proxy (127.0.0.1)
- **HTTPS by Default**: Self-signed certificates with RSA 4096-bit encryption
- **Kill-Switch**: iptables rules block all traffic if VPN disconnects
- **Restricted Sudo**: Minimal permissions for the `rose` service account
- **Protected Configs**: VPN files stored with mode 600 (owner read/write only)
- **Input Validation**: Pydantic models and security sanitizers for all user input
- **Rate Limiting**: API endpoints protected against abuse
- **No Root Services**: All services run under dedicated `rose` user

## Reporting a Vulnerability

Please report suspected vulnerabilities privately so we can investigate and release a fix before public disclosure.

* **Contact:** Send details to **security@rose.link** with a description of the issue, steps to reproduce, and any relevant logs or proofs of concept.
* **Acknowledgement:** We will confirm receipt within **3 business days** and provide status updates at least every **7 days** while the issue is under investigation.
* **Coordinated disclosure:** Once a fix or mitigation is available, we will coordinate release timing with you before announcing or merging changes publicly.

## Security Best Practices

When using ROSE Link:

1. **Change default passwords** immediately after installation
2. **Keep software updated** - run `sudo apt update && sudo apt upgrade` regularly
3. **Use strong WiFi passwords** (minimum 12 characters recommended)
4. **Consider Let's Encrypt** for production deployments with public domain
5. **Review connected clients** periodically and block unknown devices
6. **Enable AdGuard Home** for additional DNS-level protection
