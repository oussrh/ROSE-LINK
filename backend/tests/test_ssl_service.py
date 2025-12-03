"""
SSL Service Tests
=================

Unit tests for the SSL certificate service with mocked command execution.

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from services.ssl_service import SSLService, CertificateInfo
from tests.conftest import MockCommandExecutor


class TestCertificateInfo:
    """Tests for CertificateInfo dataclass."""

    def test_to_dict_basic(self) -> None:
        """Should convert CertificateInfo to dictionary."""
        info = CertificateInfo(
            domain="example.com",
            valid=True,
            issuer="Let's Encrypt",
            not_before="Jan 1 00:00:00 2024 GMT",
            not_after="Apr 1 00:00:00 2024 GMT",
            days_until_expiry=90,
            is_self_signed=False,
            cert_path="/etc/letsencrypt/live/example.com/fullchain.pem",
            key_path="/etc/letsencrypt/live/example.com/privkey.pem",
        )
        result = info.to_dict()

        assert result["domain"] == "example.com"
        assert result["valid"] is True
        assert result["issuer"] == "Let's Encrypt"
        assert result["days_until_expiry"] == 90
        assert result["is_self_signed"] is False

    def test_to_dict_includes_expires_soon(self) -> None:
        """Should include expires_soon flag."""
        # Certificate expiring soon (< 30 days)
        info = CertificateInfo(
            domain="example.com",
            valid=True,
            days_until_expiry=15,
        )
        result = info.to_dict()
        assert result["expires_soon"] is True

        # Certificate not expiring soon
        info = CertificateInfo(
            domain="example.com",
            valid=True,
            days_until_expiry=60,
        )
        result = info.to_dict()
        assert result["expires_soon"] is False


class TestSSLServiceGetCertificateInfo:
    """Tests for get_certificate_info method."""

    def test_returns_letsencrypt_cert_info(
        self, temp_dir: Path, mock_executor: MockCommandExecutor
    ) -> None:
        """Should return info for Let's Encrypt certificate."""
        # Create mock certificate paths
        cert_dir = temp_dir / "letsencrypt" / "live" / "example.com"
        cert_dir.mkdir(parents=True)
        (cert_dir / "fullchain.pem").write_text("cert content")
        (cert_dir / "privkey.pem").write_text("key content")

        openssl_output = """
subject=CN = example.com
issuer=O = Let's Encrypt, CN = R3
notBefore=Jan  1 00:00:00 2024 GMT
notAfter=Apr  1 00:00:00 2024 GMT
"""
        mock_executor.set_response(
            "openssl x509",
            return_code=0,
            stdout=openssl_output
        )

        with patch.object(SSLService, "CERT_DIR", temp_dir / "letsencrypt" / "live"):
            result = SSLService.get_certificate_info("example.com")

        assert result.valid is True
        assert result.is_self_signed is False
        assert "Let's Encrypt" in result.issuer

    def test_returns_self_signed_cert_info(
        self, temp_dir: Path, mock_executor: MockCommandExecutor
    ) -> None:
        """Should return info for self-signed certificate."""
        # Create mock self-signed certificate
        ssl_dir = temp_dir / "nginx" / "ssl"
        ssl_dir.mkdir(parents=True)
        cert_file = ssl_dir / "rose-link.crt"
        key_file = ssl_dir / "rose-link.key"
        cert_file.write_text("cert content")
        key_file.write_text("key content")

        openssl_output = """
subject=CN = roselink.local
issuer=CN = roselink.local, O = ROSE Link
notBefore=Jan  1 00:00:00 2024 GMT
notAfter=Jan  1 00:00:00 2025 GMT
"""
        mock_executor.set_response(
            "openssl x509",
            return_code=0,
            stdout=openssl_output
        )

        with patch.object(SSLService, "CERT_DIR", temp_dir / "nonexistent"):
            with patch.object(SSLService, "SELF_SIGNED_CERT", cert_file):
                with patch.object(SSLService, "SELF_SIGNED_KEY", key_file):
                    result = SSLService.get_certificate_info()

        assert result.valid is True
        assert result.is_self_signed is True

    def test_returns_invalid_when_no_cert(self, temp_dir: Path) -> None:
        """Should return invalid when no certificate exists."""
        with patch.object(SSLService, "CERT_DIR", temp_dir / "nonexistent"):
            with patch.object(
                SSLService, "SELF_SIGNED_CERT", temp_dir / "missing.crt"
            ):
                result = SSLService.get_certificate_info()

        assert result.valid is False


class TestSSLServiceParseCertificate:
    """Tests for _parse_certificate method."""

    def test_parses_certificate_details(
        self, temp_dir: Path, mock_executor: MockCommandExecutor
    ) -> None:
        """Should parse certificate details from openssl output."""
        cert_file = temp_dir / "cert.pem"
        key_file = temp_dir / "key.pem"
        cert_file.write_text("cert")
        key_file.write_text("key")

        openssl_output = """
subject=CN = example.com
issuer=O = Test CA, CN = Test
notBefore=Jan  1 00:00:00 2024 GMT
notAfter=Dec 31 23:59:59 2024 GMT
"""
        mock_executor.set_response(
            "openssl x509",
            return_code=0,
            stdout=openssl_output
        )

        result = SSLService._parse_certificate(cert_file, key_file, "example.com")

        assert result.valid is True
        assert result.domain == "example.com"
        assert "Test CA" in result.issuer

    def test_returns_invalid_on_openssl_error(
        self, temp_dir: Path, mock_executor: MockCommandExecutor
    ) -> None:
        """Should return invalid when openssl fails."""
        cert_file = temp_dir / "cert.pem"
        key_file = temp_dir / "key.pem"
        cert_file.write_text("cert")
        key_file.write_text("key")

        mock_executor.set_response(
            "openssl x509",
            return_code=1,
            stderr="Error"
        )

        result = SSLService._parse_certificate(cert_file, key_file, "example.com")

        assert result.valid is False


class TestSSLServiceCheckCertbotInstalled:
    """Tests for check_certbot_installed method."""

    def test_returns_true_when_installed(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should return True when certbot is installed."""
        mock_executor.set_response("which certbot", return_code=0)

        result = SSLService.check_certbot_installed()

        assert result is True

    def test_returns_false_when_not_installed(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should return False when certbot is not installed."""
        mock_executor.set_response("which certbot", return_code=1)

        result = SSLService.check_certbot_installed()

        assert result is False


class TestSSLServiceRequestCertificate:
    """Tests for request_certificate method."""

    def test_requests_certificate_successfully(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should request certificate and return success."""
        mock_executor.set_response("which certbot", return_code=0)
        mock_executor.set_response("sudo certbot certonly", return_code=0)

        result = SSLService.request_certificate(
            domain="example.com",
            email="admin@example.com"
        )

        assert result["success"] is True
        assert "example.com" in result["domain"]

    def test_raises_error_when_certbot_not_installed(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should raise RuntimeError when certbot not installed."""
        mock_executor.set_response("which certbot", return_code=1)

        with pytest.raises(RuntimeError, match="not installed"):
            SSLService.request_certificate(
                domain="example.com",
                email="admin@example.com"
            )

    def test_returns_failure_on_certbot_error(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should return failure when certbot fails."""
        mock_executor.set_response("which certbot", return_code=0)
        mock_executor.set_response(
            "sudo certbot certonly",
            return_code=1,
            stderr="Certificate request failed"
        )

        result = SSLService.request_certificate(
            domain="example.com",
            email="admin@example.com"
        )

        assert result["success"] is False
        assert "failed" in result["message"].lower()

    def test_dry_run_mode(self, mock_executor: MockCommandExecutor) -> None:
        """Should run in dry-run mode when requested."""
        mock_executor.set_response("which certbot", return_code=0)
        mock_executor.set_response("sudo certbot certonly", return_code=0)

        result = SSLService.request_certificate(
            domain="example.com",
            email="admin@example.com",
            dry_run=True
        )

        assert result["success"] is True
        assert "dry run" in result["message"].lower()

        # Verify --dry-run was in command
        calls = mock_executor.calls
        certbot_call = [c for c in calls if "certbot" in " ".join(c[0])]
        assert len(certbot_call) > 0


class TestSSLServiceRenewCertificates:
    """Tests for renew_certificates method."""

    def test_renews_certificates_successfully(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should renew certificates and return success."""
        mock_executor.set_response("which certbot", return_code=0)
        mock_executor.set_response("sudo certbot renew", return_code=0)

        result = SSLService.renew_certificates()

        assert result["success"] is True

    def test_raises_error_when_certbot_not_installed(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should raise RuntimeError when certbot not installed."""
        mock_executor.set_response("which certbot", return_code=1)

        with pytest.raises(RuntimeError, match="not installed"):
            SSLService.renew_certificates()

    def test_returns_failure_on_renew_error(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should return failure when renewal fails."""
        mock_executor.set_response("which certbot", return_code=0)
        mock_executor.set_response(
            "sudo certbot renew",
            return_code=1,
            stderr="Renewal failed"
        )

        result = SSLService.renew_certificates()

        assert result["success"] is False

    def test_dry_run_mode(self, mock_executor: MockCommandExecutor) -> None:
        """Should run in dry-run mode when requested."""
        mock_executor.set_response("which certbot", return_code=0)
        mock_executor.set_response("sudo certbot renew", return_code=0)

        result = SSLService.renew_certificates(dry_run=True)

        assert result["success"] is True
        assert "dry run" in result["message"].lower()


class TestSSLServiceGenerateSelfSigned:
    """Tests for generate_self_signed method."""

    def test_generates_certificate_successfully(
        self, temp_dir: Path, mock_executor: MockCommandExecutor
    ) -> None:
        """Should generate self-signed certificate."""
        cert_file = temp_dir / "cert.crt"
        key_file = temp_dir / "cert.key"

        mock_executor.set_response("sudo mkdir", return_code=0)
        mock_executor.set_response("sudo openssl req", return_code=0)

        with patch.object(SSLService, "SELF_SIGNED_CERT", cert_file):
            with patch.object(SSLService, "SELF_SIGNED_KEY", key_file):
                result = SSLService.generate_self_signed()

        assert result["success"] is True

    def test_returns_failure_on_openssl_error(
        self, temp_dir: Path, mock_executor: MockCommandExecutor
    ) -> None:
        """Should return failure when openssl fails."""
        cert_file = temp_dir / "cert.crt"
        key_file = temp_dir / "cert.key"

        mock_executor.set_response("sudo mkdir", return_code=0)
        mock_executor.set_response(
            "sudo openssl req",
            return_code=1,
            stderr="OpenSSL error"
        )

        with patch.object(SSLService, "SELF_SIGNED_CERT", cert_file):
            with patch.object(SSLService, "SELF_SIGNED_KEY", key_file):
                result = SSLService.generate_self_signed()

        assert result["success"] is False

    def test_uses_custom_domain(
        self, temp_dir: Path, mock_executor: MockCommandExecutor
    ) -> None:
        """Should use custom domain in certificate."""
        cert_file = temp_dir / "cert.crt"
        key_file = temp_dir / "cert.key"

        mock_executor.set_response("sudo mkdir", return_code=0)
        mock_executor.set_response("sudo openssl req", return_code=0)

        with patch.object(SSLService, "SELF_SIGNED_CERT", cert_file):
            with patch.object(SSLService, "SELF_SIGNED_KEY", key_file):
                result = SSLService.generate_self_signed(domain="custom.local")

        assert result["success"] is True


class TestSSLServiceReloadNginx:
    """Tests for reload_nginx method."""

    def test_reloads_nginx_successfully(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should reload nginx and return True."""
        mock_executor.set_response("sudo systemctl reload nginx", return_code=0)

        result = SSLService.reload_nginx()

        assert result is True

    def test_returns_false_on_failure(
        self, mock_executor: MockCommandExecutor
    ) -> None:
        """Should return False when reload fails."""
        mock_executor.set_response("sudo systemctl reload nginx", return_code=1)

        result = SSLService.reload_nginx()

        assert result is False
