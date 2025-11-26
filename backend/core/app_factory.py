"""
Application Factory
===================

Factory pattern for creating FastAPI application instances.

Benefits:
- Testability: Create isolated app instances for testing
- Flexibility: Configure different setups (production, testing, etc.)
- Separation: Core app creation logic isolated from entry point

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import logging
from typing import Callable, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from config import (
    APP_NAME,
    APP_VERSION,
    APP_DESCRIPTION,
    Paths,
)
from core.lifespan import lifespan_handler
from core.middleware import configure_middleware
from api import api_router
from api.routes.health import health_router
from api.routes.auth import get_limiter

logger = logging.getLogger("rose-link.factory")


def create_app(
    *,
    include_static: bool = True,
    lifespan: Optional[Callable] = None,
    skip_middleware: bool = False,
) -> FastAPI:
    """
    Create and configure a FastAPI application instance.

    Args:
        include_static: Whether to mount static file serving (default: True)
                       Set to False for API-only testing
        lifespan: Custom lifespan handler (default: production handler)
                 Pass None to disable lifespan for isolated tests
        skip_middleware: Skip middleware configuration (for isolated testing)

    Returns:
        Configured FastAPI application instance

    Example:
        # Production
        app = create_app()

        # Testing (no static files, no lifespan)
        app = create_app(include_static=False, lifespan=None)
    """
    # Use provided lifespan or default to production handler
    effective_lifespan = lifespan if lifespan is not None else lifespan_handler

    # Create the application
    app = FastAPI(
        title=f"{APP_NAME} API",
        description=APP_DESCRIPTION,
        version=APP_VERSION,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=effective_lifespan,
    )

    # Configure middleware (unless skipped for testing)
    if not skip_middleware:
        configure_middleware(app)

    # Configure rate limiting
    _configure_rate_limiting(app)

    # Register routes
    _register_routes(app)

    # Mount static files (production only)
    if include_static:
        _mount_static_files(app)

    logger.debug(f"Created {APP_NAME} application")
    return app


def _configure_rate_limiting(app: FastAPI) -> None:
    """
    Configure rate limiting for the application.

    Rate limiting is applied to authentication endpoints to prevent
    brute force attacks:
    - Login: 5 requests/minute per IP
    - Logout: 10 requests/minute per IP
    - Check: 30 requests/minute per IP
    """
    limiter = get_limiter()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    logger.debug("Rate limiting configured")


def _register_routes(app: FastAPI) -> None:
    """
    Register all API routes.

    Route structure:
    - /api/* - Main API routes (auth, wifi, vpn, hotspot, system)
    - /api/health - Health check endpoint
    - /api/status - Combined status endpoint
    """
    # Mount main API router
    app.include_router(api_router, prefix="/api")

    # Mount health endpoints (at root API level)
    app.include_router(health_router, prefix="/api", tags=["Health"])

    logger.debug("Routes registered")


def _mount_static_files(app: FastAPI) -> None:
    """
    Mount static file serving for the web UI with cache headers.

    The static file mount must be last to not override API routes.
    Uses HTML mode for SPA (Single Page Application) support.

    Cache strategy:
    - HTML files: no-cache (always revalidate)
    - Static assets (JS, CSS, images): 1 year cache
    - Service worker: no-cache (ensure updates)
    """
    try:
        if Paths.WEB_DIR.exists():
            app.mount(
                "/",
                CacheControlStaticFiles(directory=str(Paths.WEB_DIR), html=True),
                name="static",
            )
            logger.debug(f"Static files mounted from {Paths.WEB_DIR}")
        else:
            logger.warning(f"Web directory not found: {Paths.WEB_DIR}")
    except Exception as e:
        logger.error(f"Failed to mount static files: {e}")


class CacheControlStaticFiles(StaticFiles):
    """
    StaticFiles with cache control headers for optimal caching.

    Cache policy:
    - HTML files: no-cache, must-revalidate (always check for updates)
    - Service worker (sw.js): no-cache (critical for PWA updates)
    - Static assets (JS, CSS, images, fonts): max-age=31536000 (1 year)
    - Default: max-age=3600 (1 hour)
    """

    async def get_response(self, path: str, scope) -> Response:
        response = await super().get_response(path, scope)

        # Determine cache policy based on file type
        if path.endswith(".html") or path == "" or path == "/":
            # HTML files - always revalidate
            response.headers["Cache-Control"] = "no-cache, must-revalidate"
        elif path == "sw.js" or path.endswith("sw.js"):
            # Service worker - never cache (critical for PWA updates)
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        elif any(path.endswith(ext) for ext in [".js", ".css", ".webp", ".png", ".ico", ".woff2", ".woff"]):
            # Static assets - cache for 1 year (immutable content)
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        elif path.endswith(".json"):
            # JSON files (locales, manifest) - cache for 1 day
            response.headers["Cache-Control"] = "public, max-age=86400"
        else:
            # Default - cache for 1 hour
            response.headers["Cache-Control"] = "public, max-age=3600"

        return response
