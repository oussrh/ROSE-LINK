"""
Authentication Service Tests
=============================

Unit tests for the authentication service.

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest


class TestAuthServiceAPIKey:
    """Tests for API key management."""

    def test_get_or_create_api_key_creates_new_key(self, temp_dir: Path) -> None:
        """get_or_create_api_key should create a new key if none exists."""
        # Set up temp paths
        api_key_file = temp_dir / ".api_key"
        api_key_hash_file = temp_dir / ".api_key_hash"

        with patch("services.auth_service.Paths") as mock_paths:
            mock_paths.API_KEY_FILE = api_key_file
            mock_paths.API_KEY_HASH_FILE = api_key_hash_file

            from services.auth_service import AuthService

            # Clear any cached state
            AuthService._sessions.clear()

            key = AuthService.get_or_create_api_key()

            assert key is not None
            assert len(key) > 0
            assert api_key_file.exists()
            assert api_key_hash_file.exists()

    def test_get_or_create_api_key_returns_existing_key(self, temp_dir: Path) -> None:
        """get_or_create_api_key should return existing key if present."""
        api_key_file = temp_dir / ".api_key"
        api_key_hash_file = temp_dir / ".api_key_hash"

        existing_key = "existing-test-key-12345"
        api_key_file.write_text(existing_key)

        with patch("services.auth_service.Paths") as mock_paths:
            mock_paths.API_KEY_FILE = api_key_file
            mock_paths.API_KEY_HASH_FILE = api_key_hash_file

            from services.auth_service import AuthService

            key = AuthService.get_or_create_api_key()

            assert key == existing_key

    def test_verify_api_key_valid_key(self, temp_dir: Path) -> None:
        """verify_api_key should return True for valid key."""
        api_key_file = temp_dir / ".api_key"
        api_key_hash_file = temp_dir / ".api_key_hash"

        test_key = "test-api-key-for-verification"
        key_hash = hashlib.sha256(test_key.encode()).hexdigest()

        api_key_file.write_text(test_key)
        api_key_hash_file.write_text(key_hash)

        with patch("services.auth_service.Paths") as mock_paths:
            mock_paths.API_KEY_FILE = api_key_file
            mock_paths.API_KEY_HASH_FILE = api_key_hash_file

            from services.auth_service import AuthService

            assert AuthService.verify_api_key(test_key) is True

    def test_verify_api_key_invalid_key(self, temp_dir: Path) -> None:
        """verify_api_key should return False for invalid key."""
        api_key_file = temp_dir / ".api_key"
        api_key_hash_file = temp_dir / ".api_key_hash"

        correct_key = "correct-key"
        key_hash = hashlib.sha256(correct_key.encode()).hexdigest()

        api_key_file.write_text(correct_key)
        api_key_hash_file.write_text(key_hash)

        with patch("services.auth_service.Paths") as mock_paths:
            mock_paths.API_KEY_FILE = api_key_file
            mock_paths.API_KEY_HASH_FILE = api_key_hash_file

            from services.auth_service import AuthService

            assert AuthService.verify_api_key("wrong-key") is False

    def test_verify_api_key_empty_key(self) -> None:
        """verify_api_key should return False for empty key."""
        from services.auth_service import AuthService

        assert AuthService.verify_api_key("") is False
        assert AuthService.verify_api_key(None) is False  # type: ignore


class TestAuthServiceSession:
    """Tests for session management."""

    def test_create_session_returns_token(self) -> None:
        """create_session should return a secure token."""
        from services.auth_service import AuthService

        token = AuthService.create_session()

        assert token is not None
        assert len(token) > 0
        assert isinstance(token, str)

    def test_create_session_stores_expiration(self) -> None:
        """create_session should store token with expiration."""
        from services.auth_service import AuthService

        AuthService._sessions.clear()
        token = AuthService.create_session()

        assert token in AuthService._sessions
        assert AuthService._sessions[token] > datetime.now()

    def test_verify_session_valid_token(self) -> None:
        """verify_session should return True for valid token."""
        from services.auth_service import AuthService

        AuthService._sessions.clear()
        token = AuthService.create_session()

        assert AuthService.verify_session(token) is True

    def test_verify_session_invalid_token(self) -> None:
        """verify_session should return False for unknown token."""
        from services.auth_service import AuthService

        assert AuthService.verify_session("nonexistent-token") is False

    def test_verify_session_expired_token(self) -> None:
        """verify_session should return False for expired token."""
        from services.auth_service import AuthService

        AuthService._sessions.clear()
        token = AuthService.create_session()

        # Set expiration in the past
        AuthService._sessions[token] = datetime.now() - timedelta(hours=1)

        assert AuthService.verify_session(token) is False
        # Token should be removed
        assert token not in AuthService._sessions

    def test_invalidate_session_removes_token(self) -> None:
        """invalidate_session should remove the token."""
        from services.auth_service import AuthService

        AuthService._sessions.clear()
        token = AuthService.create_session()

        result = AuthService.invalidate_session(token)

        assert result is True
        assert token not in AuthService._sessions

    def test_invalidate_session_unknown_token(self) -> None:
        """invalidate_session should return False for unknown token."""
        from services.auth_service import AuthService

        result = AuthService.invalidate_session("unknown-token")

        assert result is False

    def test_get_session_expiry_returns_seconds(self) -> None:
        """get_session_expiry should return duration in seconds."""
        from services.auth_service import AuthService

        expiry = AuthService.get_session_expiry()

        assert isinstance(expiry, int)
        assert expiry > 0
        # Default is 24 hours
        assert expiry == 86400

    def test_cleanup_expired_sessions(self) -> None:
        """_cleanup_expired_sessions should remove expired tokens."""
        from services.auth_service import AuthService

        AuthService._sessions.clear()

        # Create some sessions
        valid_token = AuthService.create_session()
        expired_token = "expired-token"
        AuthService._sessions[expired_token] = datetime.now() - timedelta(hours=1)

        count = AuthService._cleanup_expired_sessions()

        assert count == 1
        assert valid_token in AuthService._sessions
        assert expired_token not in AuthService._sessions

    def test_get_active_session_count(self) -> None:
        """get_active_session_count should return count of active sessions."""
        from services.auth_service import AuthService

        AuthService._sessions.clear()
        AuthService.create_session()
        AuthService.create_session()

        count = AuthService.get_active_session_count()

        assert count == 2


class TestAuthServiceAuthenticate:
    """Tests for the authenticate convenience method."""

    def test_authenticate_with_valid_api_key(self, temp_dir: Path) -> None:
        """authenticate should succeed with valid API key."""
        api_key_file = temp_dir / ".api_key"
        api_key_hash_file = temp_dir / ".api_key_hash"

        test_key = "valid-api-key"
        key_hash = hashlib.sha256(test_key.encode()).hexdigest()

        api_key_file.write_text(test_key)
        api_key_hash_file.write_text(key_hash)

        with patch("services.auth_service.Paths") as mock_paths:
            mock_paths.API_KEY_FILE = api_key_file
            mock_paths.API_KEY_HASH_FILE = api_key_hash_file

            from services.auth_service import AuthService

            result = AuthService.authenticate(api_key=test_key)

            assert result is True

    def test_authenticate_with_valid_session(self) -> None:
        """authenticate should succeed with valid session token."""
        from services.auth_service import AuthService

        AuthService._sessions.clear()
        token = AuthService.create_session()

        result = AuthService.authenticate(bearer_token=token)

        assert result is True

    def test_authenticate_with_no_credentials(self) -> None:
        """authenticate should fail with no credentials."""
        from services.auth_service import AuthService

        result = AuthService.authenticate()

        assert result is False

    def test_authenticate_with_invalid_credentials(self) -> None:
        """authenticate should fail with invalid credentials."""
        from services.auth_service import AuthService

        result = AuthService.authenticate(
            api_key="invalid-key",
            bearer_token="invalid-token",
        )

        assert result is False
