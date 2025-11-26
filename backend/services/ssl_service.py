"""
SSL Certificate Service
=======================

Handles Let's Encrypt SSL certificate management.

Features:
- Request new certificates via certbot
- Renew existing certificates
- Check certificate status and expiry
- Configure nginx for SSL

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from config import Paths
from utils.command_runner import run_command, CommandRunner

logger = logging.getLogger("rose-link.ssl")


@dataclass
class CertificateInfo:
    """Information about an SSL certificate."""
    domain: str
    valid: bool
    issuer: str = ""
    not_before: Optional[str] = None
    not_after: Optional[str] = None
    days_until_expiry: int = 0
    is_self_signed: bool = True
    cert_path: str = ""
    key_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "domain": self.domain,
            "valid": self.valid,
            "issuer": self.issuer,
            "not_before": self.not_before,
            "not_after": self.not_after,
            "days_until_expiry": self.days_until_expiry,
            "is_self_signed": self.is_self_signed,
            "cert_path": self.cert_path,
            "key_path": self.key_path,
            "expires_soon": self.days_until_expiry < 30,
        }


class SSLService:
    """
    Service for SSL certificate management.

    This service handles Let's Encrypt certificate operations
    using certbot.
    """

    # Certificate paths
    LETSENCRYPT_DIR = Path("/etc/letsencrypt")
    CERT_DIR = LETSENCRYPT_DIR / "live"

    # Self-signed certificate paths
    SELF_SIGNED_CERT = Path("/etc/nginx/ssl/rose-link.crt")
    SELF_SIGNED_KEY = Path("/etc/nginx/ssl/rose-link.key")

    @classmethod
    def get_certificate_info(cls, domain: str = "roselink.local") -> CertificateInfo:
        """
        Get information about the current SSL certificate.

        Args:
            domain: Domain name to check

        Returns:
            CertificateInfo with certificate details
        """
        # Check for Let's Encrypt certificate first
        le_cert = cls.CERT_DIR / domain / "fullchain.pem"
        le_key = cls.CERT_DIR / domain / "privkey.pem"

        if le_cert.exists() and le_key.exists():
            return cls._parse_certificate(le_cert, le_key, domain)

        # Fall back to self-signed certificate
        if cls.SELF_SIGNED_CERT.exists():
            return cls._parse_certificate(
                cls.SELF_SIGNED_CERT,
                cls.SELF_SIGNED_KEY,
                domain
            )

        return CertificateInfo(
            domain=domain,
            valid=False,
            is_self_signed=True,
        )

    @classmethod
    def _parse_certificate(
        cls,
        cert_path: Path,
        key_path: Path,
        domain: str
    ) -> CertificateInfo:
        """
        Parse certificate information using openssl.

        Args:
            cert_path: Path to certificate file
            key_path: Path to private key file
            domain: Domain name

        Returns:
            CertificateInfo with parsed details
        """
        info = CertificateInfo(
            domain=domain,
            valid=True,
            cert_path=str(cert_path),
            key_path=str(key_path),
        )

        # Use openssl to get certificate details
        ret, out, _ = run_command([
            "openssl", "x509", "-in", str(cert_path),
            "-noout", "-subject", "-issuer", "-dates"
        ], check=False)

        if ret != 0:
            info.valid = False
            return info

        # Parse issuer
        issuer_match = re.search(r"issuer=(.+)", out)
        if issuer_match:
            issuer = issuer_match.group(1).strip()
            info.issuer = issuer
            # Check if self-signed
            info.is_self_signed = "Let's Encrypt" not in issuer

        # Parse dates
        not_before_match = re.search(r"notBefore=(.+)", out)
        if not_before_match:
            info.not_before = not_before_match.group(1).strip()

        not_after_match = re.search(r"notAfter=(.+)", out)
        if not_after_match:
            not_after_str = not_after_match.group(1).strip()
            info.not_after = not_after_str

            # Parse expiry date and calculate days remaining
            try:
                # Format: "Nov 26 12:00:00 2025 GMT"
                expiry = datetime.strptime(
                    not_after_str.replace(" GMT", ""),
                    "%b %d %H:%M:%S %Y"
                )
                delta = expiry - datetime.now()
                info.days_until_expiry = max(0, delta.days)
            except ValueError:
                pass

        return info

    @classmethod
    def check_certbot_installed(cls) -> bool:
        """
        Check if certbot is installed.

        Returns:
            True if certbot is available
        """
        ret, _, _ = run_command(["which", "certbot"], check=False)
        return ret == 0

    @classmethod
    def request_certificate(
        cls,
        domain: str,
        email: str,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Request a new Let's Encrypt certificate.

        Args:
            domain: Domain name for the certificate
            email: Email for Let's Encrypt notifications
            dry_run: If True, only test the process

        Returns:
            Dictionary with result status

        Raises:
            RuntimeError: If certbot is not installed
        """
        if not cls.check_certbot_installed():
            raise RuntimeError("certbot is not installed")

        # Build certbot command
        cmd = [
            "sudo", "certbot", "certonly",
            "--nginx",
            "-d", domain,
            "--email", email,
            "--agree-tos",
            "--non-interactive",
        ]

        if dry_run:
            cmd.append("--dry-run")

        logger.info(f"Requesting certificate for {domain}")
        ret, out, err = run_command(cmd, timeout=120)

        if ret == 0:
            logger.info(f"Certificate {'test' if dry_run else 'request'} successful")
            return {
                "success": True,
                "message": "Certificate obtained successfully" if not dry_run else "Dry run successful",
                "domain": domain,
                "output": out,
            }
        else:
            logger.error(f"Certificate request failed: {err}")
            return {
                "success": False,
                "message": "Certificate request failed",
                "error": err,
                "output": out,
            }

    @classmethod
    def renew_certificates(cls, dry_run: bool = False) -> Dict[str, Any]:
        """
        Renew all Let's Encrypt certificates.

        Args:
            dry_run: If True, only test the renewal

        Returns:
            Dictionary with renewal status
        """
        if not cls.check_certbot_installed():
            raise RuntimeError("certbot is not installed")

        cmd = ["sudo", "certbot", "renew"]

        if dry_run:
            cmd.append("--dry-run")

        logger.info("Renewing certificates")
        ret, out, err = run_command(cmd, timeout=120)

        if ret == 0:
            logger.info("Certificate renewal successful")
            return {
                "success": True,
                "message": "Renewal successful" if not dry_run else "Dry run successful",
                "output": out,
            }
        else:
            logger.error(f"Renewal failed: {err}")
            return {
                "success": False,
                "message": "Renewal failed",
                "error": err,
                "output": out,
            }

    @classmethod
    def generate_self_signed(cls, domain: str = "roselink.local") -> Dict[str, Any]:
        """
        Generate a new self-signed certificate.

        Args:
            domain: Domain name for the certificate

        Returns:
            Dictionary with result status
        """
        # Ensure directory exists
        ssl_dir = cls.SELF_SIGNED_CERT.parent
        ret, _, err = run_command([
            "sudo", "mkdir", "-p", str(ssl_dir)
        ], check=False)

        # Generate self-signed certificate
        cmd = [
            "sudo", "openssl", "req", "-x509",
            "-nodes",
            "-days", "365",
            "-newkey", "rsa:2048",
            "-keyout", str(cls.SELF_SIGNED_KEY),
            "-out", str(cls.SELF_SIGNED_CERT),
            "-subj", f"/CN={domain}/O=ROSE Link/C=US"
        ]

        logger.info(f"Generating self-signed certificate for {domain}")
        ret, out, err = run_command(cmd, timeout=60)

        if ret == 0:
            logger.info("Self-signed certificate generated")
            return {
                "success": True,
                "message": "Self-signed certificate generated",
                "cert_path": str(cls.SELF_SIGNED_CERT),
                "key_path": str(cls.SELF_SIGNED_KEY),
            }
        else:
            logger.error(f"Certificate generation failed: {err}")
            return {
                "success": False,
                "message": "Certificate generation failed",
                "error": err,
            }

    @classmethod
    def reload_nginx(cls) -> bool:
        """
        Reload nginx to apply certificate changes.

        Returns:
            True if reload successful
        """
        ret, _, _ = run_command(["sudo", "systemctl", "reload", "nginx"], check=False)
        return ret == 0
