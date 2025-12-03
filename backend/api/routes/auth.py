"""
Authentication API Routes
=========================

Endpoints for user authentication and session management.

Endpoints:
- POST /api/auth/login: Authenticate and get session token
- POST /api/auth/logout: Invalidate session token
- GET /api/auth/check: Check authentication status

Rate Limiting:
- Login endpoint: 5 requests per minute per IP
- Logout endpoint: 10 requests per minute per IP
- Check endpoint: 30 requests per minute per IP

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from models import LoginRequest, LoginResponse, AuthStatus
from services.auth_service import AuthService
from api.dependencies import optional_auth

logger = logging.getLogger("rose-link.api.auth")

# Rate limiter instance
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
async def login(request: Request, login_data: LoginRequest = Body(...)) -> LoginResponse:
    """
    Authenticate with API key and receive a session token.

    The session token can be used for subsequent requests via
    the Authorization: Bearer <token> header.

    Rate limited to 5 requests per minute per IP to prevent brute force attacks.

    Args:
        request: FastAPI request object (for rate limiting)
        login_data: Login credentials with API key

    Returns:
        Session token and expiration info

    Raises:
        HTTPException 401: If API key is invalid
        HTTPException 429: If rate limit exceeded
    """
    if not AuthService.verify_api_key(login_data.api_key):
        logger.warning("Login attempt with invalid API key")
        raise HTTPException(status_code=401, detail="Invalid API key")

    token = AuthService.create_session()
    logger.info("User authenticated successfully")

    return LoginResponse(
        token=token,
        expires_in=AuthService.get_session_expiry(),
        message="Authentication successful",
    )


@router.post("/logout")
@limiter.limit("10/minute")
async def logout(
    request: Request,
    authorization: Optional[str] = Header(None),
) -> dict[str, str]:
    """
    Invalidate the current session token.

    Rate limited to 10 requests per minute per IP.

    Args:
        request: FastAPI request object (for rate limiting)
        authorization: Bearer token header

    Returns:
        Logout confirmation
    """
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        AuthService.invalidate_session(token)

    return {"status": "logged_out"}


@router.get("/check")
@limiter.limit("30/minute")
async def check_auth(
    request: Request,
    authenticated: bool = Depends(optional_auth),
) -> dict[str, Any]:
    """
    Check if current request is authenticated.

    This endpoint can be used to verify authentication status
    without performing any other action.

    Rate limited to 30 requests per minute per IP.

    Args:
        request: FastAPI request object (for rate limiting)
        authenticated: Whether the request is authenticated

    Returns:
        Authentication status and message
    """
    return {
        "authenticated": authenticated,
        "message": "Authenticated" if authenticated else "Not authenticated",
    }


def get_limiter() -> Limiter:
    """Get the rate limiter instance for app configuration."""
    return limiter
