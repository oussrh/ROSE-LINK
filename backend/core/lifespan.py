"""
Lifespan Management
===================

Handles application startup and shutdown events.

Responsibilities:
- Create required directories with proper permissions
- Initialize or retrieve API key for authentication
- Clean up resources on shutdown

This module isolates lifecycle concerns from the main application,
improving testability and maintainability.

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncGenerator

if TYPE_CHECKING:
    from fastapi import FastAPI

from config import APP_NAME, APP_VERSION, Paths
from services.auth_service import AuthService
from core.websocket import manager as ws_manager

logger = logging.getLogger("rose-link.lifespan")


async def startup_tasks() -> None:
    """
    Execute all startup tasks.

    Tasks:
    1. Create required directories (WireGuard profiles, etc.)
    2. Initialize or retrieve the API key
    3. Start WebSocket broadcast loop

    Each task handles its own errors gracefully to allow partial
    functionality even if some initialization fails.
    """
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")

    # Create required directories
    await _ensure_directories()

    # Initialize authentication
    await _initialize_auth()

    # Start WebSocket broadcast loop for real-time updates
    await _start_websocket_broadcast()

    logger.info("Startup complete")


async def shutdown_tasks() -> None:
    """
    Execute all shutdown tasks.

    Tasks:
    1. Close all WebSocket connections
    2. Log shutdown event
    """
    logger.info(f"Shutting down {APP_NAME}")

    # Close all WebSocket connections gracefully
    await ws_manager.close_all()
    logger.info("All WebSocket connections closed")


async def _ensure_directories() -> None:
    """
    Create required directories with proper permissions.

    Directories created:
    - WireGuard profiles directory

    Errors are logged but don't prevent startup, allowing
    the application to run with limited functionality.
    """
    try:
        Paths.WG_PROFILES_DIR.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured WireGuard profiles directory exists: {Paths.WG_PROFILES_DIR}")
    except PermissionError as e:
        logger.error(f"Permission denied creating directory {Paths.WG_PROFILES_DIR}: {e}")
        logger.warning("Application may have limited functionality without write access")
    except OSError as e:
        logger.error(f"Failed to create directory {Paths.WG_PROFILES_DIR}: {e}")


async def _initialize_auth() -> None:
    """
    Initialize API key authentication.

    Retrieves existing API key or creates a new one.
    Errors are logged but don't prevent startup.
    """
    try:
        api_key = AuthService.get_or_create_api_key()
        if api_key:
            logger.info(f"API key available at {Paths.API_KEY_FILE}")
        else:
            logger.warning("API key initialization returned empty key")
    except PermissionError as e:
        logger.error(f"Permission denied accessing API key files: {e}")
        logger.warning("Authentication may not work correctly")
    except OSError as e:
        logger.error(f"Failed to initialize API key: {e}")


async def _start_websocket_broadcast() -> None:
    """
    Start the WebSocket broadcast loop.

    The broadcast loop sends periodic status updates to all
    connected WebSocket clients. It runs as a background task.
    """
    try:
        # Start the broadcast loop as a background task
        asyncio.create_task(ws_manager.start_broadcast_loop(interval=2.0))
        logger.info("WebSocket broadcast loop started")
    except Exception as e:
        logger.error(f"Failed to start WebSocket broadcast loop: {e}")


@asynccontextmanager
async def lifespan_handler(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.

    This is the main entry point for FastAPI's lifespan handling.
    It delegates to startup_tasks and shutdown_tasks for the actual work.

    Args:
        app: The FastAPI application instance

    Yields:
        None - control returns to the application during its lifetime
    """
    # Startup
    await startup_tasks()

    yield  # Application runs here

    # Shutdown
    await shutdown_tasks()
