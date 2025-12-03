"""
Authentication Service
======================

Handles API key management and session token authentication.

Authentication Flow:
1. User provides API key via X-API-Key header or login endpoint
2. API key is verified against stored hash
3. Session token is issued for subsequent requests
4. Session tokens expire after 24 hours

Security Features:
- API keys stored as SHA-256 hashes
- Secure token generation using secrets module
- HMAC comparison to prevent timing attacks
- Automatic session cleanup

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

from config import Paths, Security

logger = logging.getLogger("rose-link.auth")


class AuthService:
    """
    Service for handling authentication operations.

    This class manages:
    - API key generation and verification
    - Session token creation and validation
    - Automatic cleanup of expired sessions

    The service uses in-memory session storage, which means sessions
    are lost on application restart. This is intentional for security.
    """

    # In-memory session storage
    # Key: token string, Value: expiration datetime
    _sessions: dict[str, datetime] = {}

    @classmethod
    def get_or_create_api_key(cls) -> str:
        """
        Get existing API key or create a new one.

        If an API key file exists, returns its contents.
        Otherwise, generates a new secure API key and stores it.

        Returns:
            The API key string

        Note:
            The API key is stored in plaintext for retrieval,
            while a hash is stored for verification. This allows
            administrators to view the key while maintaining security.
        """
        # Try to read existing key
        if Paths.API_KEY_FILE.exists():
            try:
                key = Paths.API_KEY_FILE.read_text().strip()
                if key:
                    return key
            except (IOError, OSError) as e:
                logger.warning(f"Could not read API key file: {e}")

        # Generate new API key
        api_key = secrets.token_urlsafe(Security.API_KEY_LENGTH)

        try:
            # Ensure directory exists
            Paths.API_KEY_FILE.parent.mkdir(parents=True, exist_ok=True)

            # Store the key (for admin access)
            Paths.API_KEY_FILE.write_text(api_key)
            os.chmod(Paths.API_KEY_FILE, Security.SECURE_FILE_MODE)

            # Store hash for verification
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            Paths.API_KEY_HASH_FILE.write_text(key_hash)
            os.chmod(Paths.API_KEY_HASH_FILE, Security.SECURE_FILE_MODE)

            logger.info("Generated new API key")

        except (IOError, OSError) as e:
            logger.warning(f"Could not persist API key: {e}")

        return api_key

    @classmethod
    def verify_api_key(cls, api_key: str) -> bool:
        """
        Verify an API key against the stored hash.

        Uses HMAC comparison to prevent timing attacks.

        Args:
            api_key: The API key to verify

        Returns:
            True if the key is valid, False otherwise
        """
        if not api_key:
            return False

        try:
            # Prefer hash-based verification
            if Paths.API_KEY_HASH_FILE.exists():
                stored_hash = Paths.API_KEY_HASH_FILE.read_text().strip()
                provided_hash = hashlib.sha256(api_key.encode()).hexdigest()
                return hmac.compare_digest(stored_hash, provided_hash)

            # Fallback to direct comparison (legacy)
            if Paths.API_KEY_FILE.exists():
                stored_key = Paths.API_KEY_FILE.read_text().strip()
                return hmac.compare_digest(stored_key, api_key)

        except (IOError, OSError) as e:
            logger.error(f"Error verifying API key: {e}")

        return False

    @classmethod
    def create_session(cls) -> str:
        """
        Create a new session token.

        Also performs cleanup of expired sessions.

        Returns:
            A secure session token string
        """
        # Generate secure token
        token = secrets.token_urlsafe(Security.API_KEY_LENGTH)

        # Set expiration
        cls._sessions[token] = datetime.now() + Security.SESSION_DURATION

        # Cleanup expired sessions
        cls._cleanup_expired_sessions()

        logger.debug("Created new session token")
        return token

    @classmethod
    def verify_session(cls, token: str) -> bool:
        """
        Verify a session token is valid and not expired.

        Args:
            token: The session token to verify

        Returns:
            True if the token is valid and not expired
        """
        if not token or token not in cls._sessions:
            return False

        expiration = cls._sessions[token]

        if expiration < datetime.now():
            # Token expired, remove it
            del cls._sessions[token]
            logger.debug("Session token expired")
            return False

        return True

    @classmethod
    def invalidate_session(cls, token: str) -> bool:
        """
        Invalidate (logout) a session token.

        Args:
            token: The session token to invalidate

        Returns:
            True if token was found and removed
        """
        if token in cls._sessions:
            del cls._sessions[token]
            logger.info("Session invalidated (logout)")
            return True
        return False

    @classmethod
    def get_session_expiry(cls) -> int:
        """
        Get session duration in seconds.

        Returns:
            Number of seconds until session expiration
        """
        return int(Security.SESSION_DURATION.total_seconds())

    @classmethod
    def _cleanup_expired_sessions(cls) -> int:
        """
        Remove all expired sessions from storage.

        Returns:
            Number of sessions removed
        """
        now = datetime.now()
        expired = [t for t, exp in cls._sessions.items() if exp < now]

        for token in expired:
            del cls._sessions[token]

        if expired:
            logger.debug(f"Cleaned up {len(expired)} expired sessions")

        return len(expired)

    @classmethod
    def authenticate(
        cls,
        api_key: Optional[str] = None,
        bearer_token: Optional[str] = None,
    ) -> bool:
        """
        Authenticate using either API key or bearer token.

        This is a convenience method that checks both authentication
        methods in order of preference.

        Args:
            api_key: API key from X-API-Key header
            bearer_token: Session token from Authorization header

        Returns:
            True if authentication succeeds
        """
        # Check API key first
        if api_key and cls.verify_api_key(api_key):
            logger.debug("Authenticated via API key")
            return True

        # Check session token
        if bearer_token and cls.verify_session(bearer_token):
            logger.debug("Authenticated via session token")
            return True

        return False

    @classmethod
    def get_active_session_count(cls) -> int:
        """
        Get the number of active (non-expired) sessions.

        Returns:
            Count of active sessions
        """
        cls._cleanup_expired_sessions()
        return len(cls._sessions)
