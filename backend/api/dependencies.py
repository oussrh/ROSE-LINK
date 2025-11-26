"""
API Dependencies
================

FastAPI dependency injection functions for authentication and
other cross-cutting concerns.

Dependencies:
- require_auth: Raises 401 if not authenticated
- optional_auth: Returns auth status without raising

Usage:
    @router.get("/protected")
    async def protected_endpoint(auth: bool = Depends(require_auth)):
        ...

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import Header, HTTPException

from services.auth_service import AuthService

logger = logging.getLogger("rose-link.api")


async def require_auth(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None),
) -> bool:
    """
    Dependency that requires authentication.

    Checks for valid authentication via either:
    - X-API-Key header with API key
    - Authorization: Bearer <session_token> header

    Args:
        x_api_key: API key from X-API-Key header
        authorization: Bearer token from Authorization header

    Returns:
        True if authenticated

    Raises:
        HTTPException 401: If authentication fails
    """
    # Check API key
    if x_api_key and AuthService.verify_api_key(x_api_key):
        logger.debug("Authenticated via API key")
        return True

    # Check session token
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        if AuthService.verify_session(token):
            logger.debug("Authenticated via session token")
            return True

    # Authentication failed
    logger.warning("Authentication failed")
    raise HTTPException(
        status_code=401,
        detail="Authentication required. Provide X-API-Key header or valid session token.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def optional_auth(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None),
) -> bool:
    """
    Dependency for optional authentication.

    Checks authentication but doesn't raise exception on failure.
    Useful for endpoints that behave differently based on auth status.

    Args:
        x_api_key: API key from X-API-Key header
        authorization: Bearer token from Authorization header

    Returns:
        True if authenticated, False otherwise
    """
    # Check API key
    if x_api_key and AuthService.verify_api_key(x_api_key):
        return True

    # Check session token
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        if AuthService.verify_session(token):
            return True

    return False
