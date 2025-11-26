"""
Middleware Configuration
========================

Configures application middleware for security, CORS, and other concerns.

This module centralizes all middleware configuration, making it easy to:
- Test middleware settings in isolation
- Add/remove middleware without touching the main application
- Document security policies in one place

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from config import Security

logger = logging.getLogger("rose-link.middleware")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.

    Headers added:
    - X-Content-Type-Options: Prevent MIME type sniffing
    - X-Frame-Options: Prevent clickjacking
    - X-XSS-Protection: Enable browser XSS protection
    - Referrer-Policy: Control referrer information
    - Content-Security-Policy: Restrict resource loading
    - Strict-Transport-Security: Force HTTPS (when applicable)
    - Permissions-Policy: Restrict browser features
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Enable browser XSS filter
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy - Allow local resources and inline styles for Tailwind
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com",
            "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data:",
            "connect-src 'self' ws: wss:",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # HSTS - Only set for HTTPS requests
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        # Permissions Policy - Restrict browser features
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), interest-cohort=()"
        )

        return response


def configure_middleware(app: FastAPI) -> None:
    """
    Configure all middleware for the application.

    Middleware configured (in order of execution):
    - Security Headers: Add security headers to all responses
    - GZip: Compress responses for bandwidth savings (~70%)
    - CORS: Restricted to local network only for security

    Note: Middleware is executed in reverse order of addition,
    so we add them in the order we want them to wrap the request.

    Args:
        app: The FastAPI application to configure
    """
    _configure_cors(app)
    _configure_gzip(app)
    _configure_security_headers(app)
    logger.debug("Middleware configuration complete")


def _configure_cors(app: FastAPI) -> None:
    """
    Configure CORS middleware.

    Security considerations:
    - Origins restricted to local network addresses only
    - Credentials allowed for session-based auth
    - Methods limited to those actually used by the API
    - Headers restricted to those needed for authentication

    This prevents cross-origin attacks from external websites
    while allowing the local web UI to communicate with the API.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=Security.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=Security.ALLOWED_METHODS,
        allow_headers=Security.ALLOWED_HEADERS,
    )
    logger.debug(f"CORS configured with origins: {Security.ALLOWED_ORIGINS}")


def _configure_gzip(app: FastAPI) -> None:
    """
    Configure GZip compression middleware.

    Compresses responses larger than 1000 bytes, providing
    ~70% bandwidth savings for text-based content (HTML, JSON, JS, CSS).

    Note: Images (WebP, PNG) are already compressed and won't benefit.
    """
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    logger.debug("GZip compression enabled (minimum_size=1000)")


def _configure_security_headers(app: FastAPI) -> None:
    """
    Configure security headers middleware.

    Adds comprehensive security headers to protect against:
    - XSS attacks (CSP, X-XSS-Protection)
    - Clickjacking (X-Frame-Options, frame-ancestors)
    - MIME sniffing (X-Content-Type-Options)
    - Information leakage (Referrer-Policy)
    - Downgrade attacks (HSTS for HTTPS)
    """
    app.add_middleware(SecurityHeadersMiddleware)
    logger.debug("Security headers middleware enabled")


def get_cors_config() -> dict:
    """
    Get the current CORS configuration.

    Returns:
        Dictionary containing CORS settings for testing/inspection
    """
    return {
        "allow_origins": list(Security.ALLOWED_ORIGINS),
        "allow_credentials": True,
        "allow_methods": list(Security.ALLOWED_METHODS),
        "allow_headers": list(Security.ALLOWED_HEADERS),
    }


def get_security_headers() -> dict:
    """
    Get the security headers that will be added to responses.

    Returns:
        Dictionary of security headers for testing/inspection
    """
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=(), interest-cohort=()",
    }
