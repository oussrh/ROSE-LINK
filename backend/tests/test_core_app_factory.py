"""
Application Factory Tests
=========================

Tests for the FastAPI application factory pattern.

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator
from unittest.mock import patch, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.app_factory import create_app, _register_routes, _mount_static_files


class TestCreateApp:
    """Tests for application factory function."""

    def test_create_app_returns_fastapi_instance(self) -> None:
        """create_app should return a FastAPI application."""
        # Use a no-op lifespan to avoid startup tasks
        @asynccontextmanager
        async def noop_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
            yield

        app = create_app(include_static=False, lifespan=noop_lifespan)

        assert isinstance(app, FastAPI)

    def test_create_app_sets_title(self) -> None:
        """create_app should set the application title."""
        @asynccontextmanager
        async def noop_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
            yield

        app = create_app(include_static=False, lifespan=noop_lifespan)

        assert "ROSE Link" in app.title

    def test_create_app_sets_version(self) -> None:
        """create_app should set the application version."""
        @asynccontextmanager
        async def noop_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
            yield

        app = create_app(include_static=False, lifespan=noop_lifespan)

        assert app.version is not None
        assert len(app.version) > 0

    def test_create_app_sets_docs_url(self) -> None:
        """create_app should set the docs URL to /api/docs."""
        @asynccontextmanager
        async def noop_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
            yield

        app = create_app(include_static=False, lifespan=noop_lifespan)

        assert app.docs_url == "/api/docs"

    def test_create_app_sets_redoc_url(self) -> None:
        """create_app should set the redoc URL to /api/redoc."""
        @asynccontextmanager
        async def noop_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
            yield

        app = create_app(include_static=False, lifespan=noop_lifespan)

        assert app.redoc_url == "/api/redoc"

    def test_create_app_without_static_files(self) -> None:
        """create_app with include_static=False should not mount static files."""
        @asynccontextmanager
        async def noop_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
            yield

        app = create_app(include_static=False, lifespan=noop_lifespan)

        # Check that no routes are mounted at "/"
        static_routes = [r for r in app.routes if getattr(r, "name", None) == "static"]
        assert len(static_routes) == 0

    def test_create_app_registers_routes(self) -> None:
        """create_app should register API routes."""
        @asynccontextmanager
        async def noop_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
            yield

        app = create_app(include_static=False, lifespan=noop_lifespan)

        # Should have routes
        assert len(app.routes) > 0

    def test_create_app_skip_middleware(self) -> None:
        """create_app with skip_middleware=True should not add middleware."""
        @asynccontextmanager
        async def noop_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
            yield

        app = create_app(
            include_static=False, lifespan=noop_lifespan, skip_middleware=True
        )

        # Should not have user-added middleware (only default FastAPI middleware)
        assert len(app.user_middleware) == 0


class TestRegisterRoutes:
    """Tests for route registration."""

    def test_register_routes_includes_api_router(self) -> None:
        """_register_routes should include the main API router."""
        app = FastAPI()

        _register_routes(app)

        # Check for API routes
        route_paths = [getattr(r, "path", "") for r in app.routes]
        api_routes = [p for p in route_paths if p.startswith("/api")]
        assert len(api_routes) > 0

    def test_register_routes_includes_health_endpoint(self) -> None:
        """_register_routes should include health endpoint."""
        app = FastAPI()

        _register_routes(app)

        client = TestClient(app)
        response = client.get("/api/health")

        assert response.status_code == 200


class TestMountStaticFiles:
    """Tests for static file mounting."""

    def test_mount_static_files_when_dir_exists(self, temp_dir: Path) -> None:
        """_mount_static_files should mount when web directory exists."""
        web_dir = temp_dir / "web"
        web_dir.mkdir()
        (web_dir / "index.html").write_text("<html></html>")

        app = FastAPI()

        with patch("core.app_factory.Paths") as mock_paths:
            mock_paths.WEB_DIR = web_dir

            _mount_static_files(app)

        # Should have a static mount
        static_routes = [r for r in app.routes if getattr(r, "name", None) == "static"]
        assert len(static_routes) == 1

    def test_mount_static_files_when_dir_not_exists(
        self, temp_dir: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """_mount_static_files should warn when directory doesn't exist."""
        nonexistent_dir = temp_dir / "nonexistent"

        app = FastAPI()

        with patch("core.app_factory.Paths") as mock_paths:
            mock_paths.WEB_DIR = nonexistent_dir

            import logging

            with caplog.at_level(logging.WARNING, logger="rose-link.factory"):
                _mount_static_files(app)

        # Should not have a static mount
        static_routes = [r for r in app.routes if getattr(r, "name", None) == "static"]
        assert len(static_routes) == 0


class TestAppFactoryIntegration:
    """Integration tests for the application factory."""

    def test_health_endpoint_accessible(self) -> None:
        """Health endpoint should be accessible through factory-created app."""
        @asynccontextmanager
        async def noop_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
            yield

        app = create_app(include_static=False, lifespan=noop_lifespan)
        client = TestClient(app)

        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_docs_accessible(self) -> None:
        """API docs should be accessible."""
        @asynccontextmanager
        async def noop_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
            yield

        app = create_app(include_static=False, lifespan=noop_lifespan)
        client = TestClient(app)

        response = client.get("/api/docs")

        assert response.status_code == 200

    def test_custom_lifespan_used(self) -> None:
        """Factory should use provided custom lifespan."""
        lifespan_started = False

        @asynccontextmanager
        async def custom_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
            nonlocal lifespan_started
            lifespan_started = True
            yield

        app = create_app(include_static=False, lifespan=custom_lifespan)

        with TestClient(app):
            pass

        assert lifespan_started is True
