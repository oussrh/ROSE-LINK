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
import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock
from typing import TYPE_CHECKING, Dict, List

if TYPE_CHECKING:
    from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from config import Security

logger = logging.getLogger("rose-link.middleware")


@dataclass
class RequestMetrics:
    """Container for request performance metrics."""
    total_requests: int = 0
    total_errors: int = 0
    total_latency_ms: float = 0.0
    latency_samples: List[float] = field(default_factory=list)
    requests_by_path: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    latency_by_path: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))
    max_samples: int = 1000  # Keep last N samples for percentile calculation


# Global metrics instance with thread-safe access
_metrics = RequestMetrics()
_metrics_lock = Lock()


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to measure and track request latency.

    Tracks:
    - Total request count
    - Error count (5xx responses)
    - Request latency (min, max, avg, p50, p95, p99)
    - Per-endpoint metrics
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()

        response = await call_next(request)

        # Calculate latency
        latency_ms = (time.perf_counter() - start_time) * 1000
        path = request.url.path

        # Update metrics thread-safely
        with _metrics_lock:
            _metrics.total_requests += 1
            _metrics.total_latency_ms += latency_ms

            # Track errors
            if response.status_code >= 500:
                _metrics.total_errors += 1

            # Track latency samples (limited to prevent memory growth)
            if len(_metrics.latency_samples) >= _metrics.max_samples:
                _metrics.latency_samples.pop(0)
            _metrics.latency_samples.append(latency_ms)

            # Track per-path metrics
            _metrics.requests_by_path[path] += 1
            if len(_metrics.latency_by_path[path]) >= 100:
                _metrics.latency_by_path[path].pop(0)
            _metrics.latency_by_path[path].append(latency_ms)

        # Add timing header for debugging
        response.headers["X-Response-Time"] = f"{latency_ms:.2f}ms"

        return response


def get_request_metrics() -> dict:
    """
    Get current request performance metrics.

    Returns:
        Dictionary containing performance metrics
    """
    with _metrics_lock:
        samples = sorted(_metrics.latency_samples) if _metrics.latency_samples else [0]

        def percentile(p: float) -> float:
            if not samples:
                return 0.0
            k = (len(samples) - 1) * p / 100
            f = int(k)
            c = f + 1 if f + 1 < len(samples) else f
            return samples[f] + (k - f) * (samples[c] - samples[f])

        return {
            "total_requests": _metrics.total_requests,
            "total_errors": _metrics.total_errors,
            "error_rate": _metrics.total_errors / max(_metrics.total_requests, 1),
            "latency_ms": {
                "avg": _metrics.total_latency_ms / max(_metrics.total_requests, 1),
                "min": min(samples) if samples else 0,
                "max": max(samples) if samples else 0,
                "p50": percentile(50),
                "p95": percentile(95),
                "p99": percentile(99),
            },
            "requests_by_path": dict(_metrics.requests_by_path),
        }


def reset_request_metrics() -> None:
    """Reset all request metrics. Useful for testing."""
    global _metrics
    with _metrics_lock:
        _metrics = RequestMetrics()


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
    - Request Timing: Track request latency and performance
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
    _configure_request_timing(app)
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


def _configure_request_timing(app: FastAPI) -> None:
    """
    Configure request timing middleware.

    Tracks request latency and performance metrics for monitoring.
    Metrics can be retrieved via get_request_metrics().
    """
    app.add_middleware(RequestTimingMiddleware)
    logger.debug("Request timing middleware enabled")


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
