"""
API Contract Tests
==================

Tests to verify API response schemas match their contracts.
These tests ensure API responses have consistent structure.

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from typing import Any

from main import app


class TestHealthAPIContract:
    """Test health endpoint response contracts."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_health_endpoint_contract(self):
        """Test GET /api/health response schema."""
        response = self.client.get("/api/health")
        assert response.status_code == 200

        data = response.json()

        # Required fields
        assert "status" in data
        assert isinstance(data["status"], str)
        assert data["status"] in ["ok", "healthy", "unhealthy", "degraded"]

        # Optional but expected fields
        if "version" in data:
            assert isinstance(data["version"], str)

        if "timestamp" in data:
            assert isinstance(data["timestamp"], str)

    def test_status_endpoint_contract(self):
        """Test GET /api/status response schema."""
        response = self.client.get("/api/status")
        assert response.status_code == 200

        data = response.json()

        # Required top-level fields
        assert "wan" in data
        assert "vpn" in data
        assert "ap" in data

        # WAN status contract
        wan = data["wan"]
        assert isinstance(wan, dict)
        # WAN status uses ethernet/wifi structure, not active flag
        assert "ethernet" in wan or "wifi" in wan or "connected" in wan

        # VPN status contract
        vpn = data["vpn"]
        assert isinstance(vpn, dict)
        assert "active" in vpn
        assert isinstance(vpn["active"], bool)

        # AP status contract
        ap = data["ap"]
        assert isinstance(ap, dict)
        assert "active" in ap
        assert isinstance(ap["active"], bool)


class TestVPNAPIContract:
    """Test VPN endpoint response contracts."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_vpn_status_contract(self):
        """Test GET /api/vpn/status response schema."""
        response = self.client.get("/api/vpn/status")
        assert response.status_code == 200

        data = response.json()

        # Required fields
        assert "active" in data
        assert isinstance(data["active"], bool)

        # Optional fields when active
        if data["active"]:
            # These should be present when VPN is active
            if "endpoint" in data:
                assert isinstance(data["endpoint"], (str, type(None)))
            if "transfer" in data:
                transfer = data["transfer"]
                assert isinstance(transfer, dict)
                if "received" in transfer:
                    assert isinstance(transfer["received"], str)
                if "sent" in transfer:
                    assert isinstance(transfer["sent"], str)

    def test_vpn_profiles_contract(self):
        """Test GET /api/vpn/profiles response schema (requires auth)."""
        # This endpoint requires auth, so we test with auth header
        response = self.client.get(
            "/api/vpn/profiles",
            headers={"X-API-Key": "test-key"}  # Will fail auth but tests schema
        )

        # Should return 401 without valid auth
        assert response.status_code in [200, 401]

        if response.status_code == 200:
            data = response.json()
            assert "profiles" in data
            assert isinstance(data["profiles"], list)

            for profile in data["profiles"]:
                assert "name" in profile
                assert "active" in profile
                assert isinstance(profile["name"], str)
                assert isinstance(profile["active"], bool)


class TestWiFiAPIContract:
    """Test WiFi endpoint response contracts."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)


class TestHotspotAPIContract:
    """Test Hotspot endpoint response contracts."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_hotspot_status_contract(self):
        """Test GET /api/hotspot/status response schema."""
        response = self.client.get("/api/hotspot/status")
        assert response.status_code == 200

        data = response.json()

        # Required fields
        assert "active" in data
        assert isinstance(data["active"], bool)

        # Optional fields when active
        if data["active"]:
            if "ssid" in data:
                assert isinstance(data["ssid"], str)
            if "channel" in data:
                assert isinstance(data["channel"], int)
            if "clients_count" in data:
                assert isinstance(data["clients_count"], int)


class TestSystemAPIContract:
    """Test System endpoint response contracts."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_system_info_contract(self):
        """Test GET /api/system/info response schema."""
        response = self.client.get("/api/system/info")
        assert response.status_code == 200

        data = response.json()

        # Expected fields (may be None on non-Pi systems)
        expected_fields = [
            "model",
            "ram_mb",
            "disk_total_gb",
            "cpu_temp_c",
        ]

        for field in expected_fields:
            # Field should exist in response
            assert field in data, f"Missing field: {field}"

    def test_system_interfaces_contract(self):
        """Test GET /api/system/interfaces response schema."""
        response = self.client.get("/api/system/interfaces")
        assert response.status_code == 200

        data = response.json()

        # Should have interface categories
        assert isinstance(data, dict)

        # Each category should be a list
        for category, interfaces in data.items():
            assert isinstance(interfaces, list)


class TestMetricsAPIContract:
    """Test Metrics endpoint response contracts."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_prometheus_metrics_contract(self):
        """Test GET /api/metrics response format."""
        response = self.client.get("/api/metrics")
        assert response.status_code == 200

        # Should return plain text
        assert response.headers["content-type"].startswith("text/plain")

        content = response.text

        # Should contain Prometheus format metrics
        assert "# TYPE" in content or "# HELP" in content

        # Should have our custom metrics
        assert "rose_link" in content

    def test_performance_metrics_contract(self):
        """Test GET /api/metrics/performance response schema."""
        response = self.client.get("/api/metrics/performance")
        assert response.status_code == 200

        data = response.json()

        # Required fields
        assert "total_requests" in data
        assert "total_errors" in data
        assert "error_rate" in data
        assert "latency_ms" in data

        # Type checks
        assert isinstance(data["total_requests"], int)
        assert isinstance(data["total_errors"], int)
        assert isinstance(data["error_rate"], float)
        assert isinstance(data["latency_ms"], dict)

        # Latency structure
        latency = data["latency_ms"]
        assert "avg" in latency
        assert "min" in latency
        assert "max" in latency
        assert "p50" in latency
        assert "p95" in latency
        assert "p99" in latency


class TestAuthAPIContract:
    """Test Authentication endpoint response contracts."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_auth_check_contract(self):
        """Test GET /api/auth/check response schema."""
        response = self.client.get("/api/auth/check")
        assert response.status_code == 200

        data = response.json()

        # Required fields
        assert "authenticated" in data
        assert "message" in data

        assert isinstance(data["authenticated"], bool)
        assert isinstance(data["message"], str)

    def test_login_error_contract(self):
        """Test POST /api/auth/login error response schema."""
        response = self.client.post(
            "/api/auth/login",
            json={"api_key": "invalid-key"}
        )

        # Should fail with invalid key (401) or validation error (422)
        assert response.status_code in [401, 422]

        data = response.json()
        assert "detail" in data

    def test_logout_contract(self):
        """Test POST /api/auth/logout response schema."""
        response = self.client.post("/api/auth/logout")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert data["status"] == "logged_out"


class TestErrorResponseContract:
    """Test error response contracts."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_404_error_contract(self):
        """Test 404 error response schema."""
        response = self.client.get("/api/nonexistent-endpoint")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data

    def test_401_error_contract(self):
        """Test 401 error response schema."""
        # Access protected endpoint without auth
        response = self.client.get("/api/system/logs")
        assert response.status_code == 401

        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_422_validation_error_contract(self):
        """Test 422 validation error response schema."""
        # Send invalid data to endpoint expecting specific schema
        response = self.client.post(
            "/api/auth/login",
            json={}  # Missing required fields
        )

        assert response.status_code == 422

        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)

        # Each validation error should have loc and msg
        for error in data["detail"]:
            assert "loc" in error
            assert "msg" in error
