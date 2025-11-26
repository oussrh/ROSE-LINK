"""
Core Module - Application Factory and Infrastructure
=====================================================

This module provides the core infrastructure for the ROSE Link backend:
- Application factory pattern for testable app creation
- Lifespan management for startup/shutdown events
- Middleware configuration for security and CORS

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

from core.app_factory import create_app
from core.lifespan import lifespan_handler
from core.middleware import configure_middleware

__all__ = [
    "create_app",
    "lifespan_handler",
    "configure_middleware",
]
