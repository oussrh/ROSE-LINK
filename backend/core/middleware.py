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

from config import Security

logger = logging.getLogger("rose-link.middleware")


def configure_middleware(app: FastAPI) -> None:
    """
    Configure all middleware for the application.

    Middleware configured:
    - CORS: Restricted to local network only for security

    Args:
        app: The FastAPI application to configure
    """
    _configure_cors(app)
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
