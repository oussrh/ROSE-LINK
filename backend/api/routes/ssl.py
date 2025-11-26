"""
SSL Certificate Routes
======================

SSL certificate management endpoints.

Endpoints:
- GET /ssl/status - Get current certificate status
- POST /ssl/request - Request Let's Encrypt certificate
- POST /ssl/renew - Renew certificates
- POST /ssl/self-signed - Generate self-signed certificate

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, EmailStr

from api.dependencies import require_auth
from services.ssl_service import SSLService

logger = logging.getLogger("rose-link.ssl-routes")

router = APIRouter()


class CertificateRequest(BaseModel):
    """Request model for certificate operations."""
    domain: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Domain name for the certificate",
        examples=["roselink.local", "example.com"]
    )
    email: EmailStr = Field(
        ...,
        description="Email for Let's Encrypt notifications"
    )
    dry_run: bool = Field(
        False,
        description="Test the process without making changes"
    )


class RenewRequest(BaseModel):
    """Request model for certificate renewal."""
    dry_run: bool = Field(
        False,
        description="Test the renewal without making changes"
    )


class SelfSignedRequest(BaseModel):
    """Request model for self-signed certificate generation."""
    domain: str = Field(
        "roselink.local",
        min_length=1,
        max_length=255,
        description="Domain name for the certificate"
    )


@router.get("/ssl/status")
async def get_ssl_status() -> Dict[str, Any]:
    """
    Get current SSL certificate status.

    Returns:
        Certificate information and status
    """
    cert_info = SSLService.get_certificate_info()
    certbot_installed = SSLService.check_certbot_installed()

    return {
        "certificate": cert_info.to_dict(),
        "certbot_installed": certbot_installed,
        "can_use_letsencrypt": certbot_installed,
    }


@router.post("/ssl/request", dependencies=[Depends(require_auth)])
async def request_certificate(request: CertificateRequest) -> Dict[str, Any]:
    """
    Request a new Let's Encrypt certificate.

    This requires:
    - Domain pointing to this server
    - Port 80 accessible from the internet
    - certbot installed

    Args:
        request: Certificate request parameters

    Returns:
        Certificate request result
    """
    if not SSLService.check_certbot_installed():
        raise HTTPException(
            status_code=503,
            detail="certbot is not installed. Install with: sudo apt install certbot python3-certbot-nginx"
        )

    try:
        result = SSLService.request_certificate(
            domain=request.domain,
            email=request.email,
            dry_run=request.dry_run,
        )

        if result["success"] and not request.dry_run:
            # Reload nginx to apply new certificate
            SSLService.reload_nginx()

        return result

    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Certificate request failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Certificate request failed: {e}"
        )


@router.post("/ssl/renew", dependencies=[Depends(require_auth)])
async def renew_certificates(request: RenewRequest) -> Dict[str, Any]:
    """
    Renew all Let's Encrypt certificates.

    Args:
        request: Renewal parameters

    Returns:
        Renewal result
    """
    if not SSLService.check_certbot_installed():
        raise HTTPException(
            status_code=503,
            detail="certbot is not installed"
        )

    try:
        result = SSLService.renew_certificates(dry_run=request.dry_run)

        if result["success"] and not request.dry_run:
            # Reload nginx to apply renewed certificate
            SSLService.reload_nginx()

        return result

    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Certificate renewal failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Certificate renewal failed: {e}"
        )


@router.post("/ssl/self-signed", dependencies=[Depends(require_auth)])
async def generate_self_signed(request: SelfSignedRequest) -> Dict[str, Any]:
    """
    Generate a new self-signed certificate.

    Use this when Let's Encrypt is not available or for local-only access.

    Args:
        request: Self-signed certificate parameters

    Returns:
        Generation result
    """
    try:
        result = SSLService.generate_self_signed(domain=request.domain)

        if result["success"]:
            # Reload nginx to apply new certificate
            SSLService.reload_nginx()

        return result

    except Exception as e:
        logger.error(f"Self-signed certificate generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Certificate generation failed: {e}"
        )
