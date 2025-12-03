"""
API Health Endpoint Tests
=========================

Tests for the health check and status endpoints.

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.conftest import MockCommandExecutor


class TestHealthEndpoint:
    """Tests for the /api/health endpoint."""

    def test_health_returns_200(self, client: TestClient) -> None:
        """Health endpoint should return 200 OK."""
        response = client.get("/api/health")

        assert response.status_code == 200

    def test_health_returns_status_ok(self, client: TestClient) -> None:
        """Health endpoint should return status 'ok'."""
        response = client.get("/api/health")
        data = response.json()

        assert data["status"] == "ok"

    def test_health_returns_service_name(self, client: TestClient) -> None:
        """Health endpoint should return service name."""
        response = client.get("/api/health")
        data = response.json()

        assert "service" in data
        assert data["service"] == "ROSE Link"

    def test_health_returns_version(self, client: TestClient) -> None:
        """Health endpoint should return version."""
        response = client.get("/api/health")
        data = response.json()

        assert "version" in data
        assert len(data["version"]) > 0


class TestStatusEndpoint:
    """Tests for the /api/status endpoint."""

    def test_status_returns_200(
        self, client: TestClient, mock_executor: MockCommandExecutor
    ) -> None:
        """Status endpoint should return 200 OK."""
        # Mock the underlying commands
        mock_executor.set_response("ip addr show", return_code=0, stdout="")
        mock_executor.set_response("nmcli -t -f", return_code=0, stdout="")
        mock_executor.set_response("sudo wg show wg0", return_code=1, stdout="")
        mock_executor.set_response("systemctl is-active", return_code=0, stdout="active\n")

        response = client.get("/api/status")

        assert response.status_code == 200

    def test_status_returns_wan_info(
        self, client: TestClient, mock_executor: MockCommandExecutor
    ) -> None:
        """Status endpoint should return WAN information."""
        mock_executor.set_response("ip addr show", return_code=0, stdout="")
        mock_executor.set_response("nmcli -t -f", return_code=0, stdout="")
        mock_executor.set_response("sudo wg show wg0", return_code=1, stdout="")
        mock_executor.set_response("systemctl is-active", return_code=0, stdout="active\n")

        response = client.get("/api/status")
        data = response.json()

        assert "wan" in data

    def test_status_returns_vpn_info(
        self, client: TestClient, mock_executor: MockCommandExecutor
    ) -> None:
        """Status endpoint should return VPN information."""
        mock_executor.set_response("ip addr show", return_code=0, stdout="")
        mock_executor.set_response("nmcli -t -f", return_code=0, stdout="")
        mock_executor.set_response("sudo wg show wg0", return_code=1, stdout="")
        mock_executor.set_response("systemctl is-active", return_code=0, stdout="active\n")

        response = client.get("/api/status")
        data = response.json()

        assert "vpn" in data

    def test_status_returns_ap_info(
        self, client: TestClient, mock_executor: MockCommandExecutor
    ) -> None:
        """Status endpoint should return AP (hotspot) information."""
        mock_executor.set_response("ip addr show", return_code=0, stdout="")
        mock_executor.set_response("nmcli -t -f", return_code=0, stdout="")
        mock_executor.set_response("sudo wg show wg0", return_code=1, stdout="")
        mock_executor.set_response("systemctl is-active", return_code=0, stdout="active\n")

        response = client.get("/api/status")
        data = response.json()

        assert "ap" in data
