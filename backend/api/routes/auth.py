"""
Authentication API Routes
=========================

Endpoints for user authentication and session management.

Endpoints:
- POST /api/auth/login: Authenticate and get session token
- POST /api/auth/logout: Invalidate session token
- GET /api/auth/check: Check authentication status

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException

from models import LoginRequest, LoginResponse, AuthStatus
from services.auth_service import AuthService
from api.dependencies import optional_auth

logger = logging.getLogger("rose-link.api.auth")

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    """
    Authenticate with API key and receive a session token.

    The session token can be used for subsequent requests via
    the Authorization: Bearer <token> header.

    Args:
        request: Login credentials with API key

    Returns:
        Session token and expiration info

    Raises:
        HTTPException 401: If API key is invalid
    """
    if not AuthService.verify_api_key(request.api_key):
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
async def logout(
    authorization: Optional[str] = Header(None),
) -> dict[str, str]:
    """
    Invalidate the current session token.

    Args:
        authorization: Bearer token header

    Returns:
        Logout confirmation
    """
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        AuthService.invalidate_session(token)

    return {"status": "logged_out"}


@router.get("/check")
async def check_auth(authenticated: bool = Depends(optional_auth)) -> dict[str, Any]:
    """
    Check if current request is authenticated.

    This endpoint can be used to verify authentication status
    without performing any other action.

    Returns:
        Authentication status and message
    """
    return {
        "authenticated": authenticated,
        "message": "Authenticated" if authenticated else "Not authenticated",
    }
