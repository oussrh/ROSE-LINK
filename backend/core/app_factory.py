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

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

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

    # Register routes
    _register_routes(app)

    # Mount static files (production only)
    if include_static:
        _mount_static_files(app)

    logger.debug(f"Created {APP_NAME} application")
    return app


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
    Mount static file serving for the web UI.

    The static file mount must be last to not override API routes.
    Uses HTML mode for SPA (Single Page Application) support.
    """
    try:
        if Paths.WEB_DIR.exists():
            app.mount(
                "/",
                StaticFiles(directory=str(Paths.WEB_DIR), html=True),
                name="static",
            )
            logger.debug(f"Static files mounted from {Paths.WEB_DIR}")
        else:
            logger.warning(f"Web directory not found: {Paths.WEB_DIR}")
    except Exception as e:
        logger.error(f"Failed to mount static files: {e}")
