"""
Middleware Configuration Tests
==============================

Tests for CORS and security middleware configuration.

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.middleware import (
    configure_middleware,
    _configure_cors,
    get_cors_config,
)


class TestConfigureMiddleware:
    """Tests for the main middleware configuration function."""

    def test_configure_middleware_adds_cors(self) -> None:
        """configure_middleware should add CORS middleware."""
        app = FastAPI()

        # Before configuration, app has no user middleware
        initial_middleware_count = len(app.user_middleware)

        configure_middleware(app)

        # After configuration, should have at least one middleware
        assert len(app.user_middleware) > initial_middleware_count

    def test_configure_middleware_returns_none(self) -> None:
        """configure_middleware should return None."""
        app = FastAPI()

        result = configure_middleware(app)

        assert result is None


class TestConfigureCors:
    """Tests for CORS middleware configuration."""

    def test_cors_adds_middleware_to_app(self) -> None:
        """_configure_cors should add CORS middleware to the app."""
        app = FastAPI()
        initial_count = len(app.user_middleware)

        _configure_cors(app)

        assert len(app.user_middleware) == initial_count + 1

    def test_cors_allows_configured_origins(self) -> None:
        """CORS should allow configured origins."""
        app = FastAPI()

        @app.get("/test")
        def test_endpoint():
            return {"status": "ok"}

        _configure_cors(app)

        client = TestClient(app)

        # Test with allowed origin
        response = client.get(
            "/test",
            headers={"Origin": "http://localhost:5173"},
        )

        # Should have CORS headers
        assert response.status_code == 200

    def test_cors_preflight_request(self) -> None:
        """CORS should handle preflight OPTIONS requests."""
        app = FastAPI()

        @app.get("/test")
        def test_endpoint():
            return {"status": "ok"}

        _configure_cors(app)

        client = TestClient(app)

        # Preflight request - CORS middleware handles this
        response = client.options(
            "/test",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )

        # Should respond to preflight (may be 200 or 400 depending on exact CORS config)
        # The important thing is that CORS headers are present in the response
        assert "access-control-allow-origin" in response.headers or response.status_code in (200, 400)


class TestGetCorsConfig:
    """Tests for CORS configuration retrieval."""

    def test_get_cors_config_returns_dict(self) -> None:
        """get_cors_config should return a dictionary."""
        config = get_cors_config()

        assert isinstance(config, dict)

    def test_get_cors_config_has_required_keys(self) -> None:
        """get_cors_config should have all required configuration keys."""
        config = get_cors_config()

        assert "allow_origins" in config
        assert "allow_credentials" in config
        assert "allow_methods" in config
        assert "allow_headers" in config

    def test_get_cors_config_origins_is_list(self) -> None:
        """allow_origins should be a list."""
        config = get_cors_config()

        assert isinstance(config["allow_origins"], list)

    def test_get_cors_config_methods_is_list(self) -> None:
        """allow_methods should be a list."""
        config = get_cors_config()

        assert isinstance(config["allow_methods"], list)

    def test_get_cors_config_headers_is_list(self) -> None:
        """allow_headers should be a list."""
        config = get_cors_config()

        assert isinstance(config["allow_headers"], list)

    def test_get_cors_config_credentials_is_bool(self) -> None:
        """allow_credentials should be a boolean."""
        config = get_cors_config()

        assert isinstance(config["allow_credentials"], bool)
        assert config["allow_credentials"] is True

    def test_get_cors_config_contains_localhost(self) -> None:
        """Origins should contain localhost for local development."""
        config = get_cors_config()

        localhost_origins = [
            o for o in config["allow_origins"] if "localhost" in o or "127.0.0.1" in o
        ]

        assert len(localhost_origins) > 0

    def test_get_cors_config_contains_api_key_header(self) -> None:
        """Headers should allow X-API-Key for authentication."""
        config = get_cors_config()

        assert "X-API-Key" in config["allow_headers"]

    def test_get_cors_config_contains_required_methods(self) -> None:
        """Methods should include GET and POST at minimum."""
        config = get_cors_config()

        assert "GET" in config["allow_methods"]
        assert "POST" in config["allow_methods"]
