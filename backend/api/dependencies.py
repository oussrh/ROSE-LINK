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

import ipaddress
import logging
from typing import Optional

from fastapi import Header, HTTPException, Request

from services.auth_service import AuthService

logger = logging.getLogger("rose-link.api")

# Trusted local networks - requests from these are auto-authenticated
TRUSTED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),      # Localhost
    ipaddress.ip_network("192.168.50.0/24"),  # ROSE Link hotspot network
    ipaddress.ip_network("192.168.0.0/16"),   # Common home networks
    ipaddress.ip_network("10.0.0.0/8"),       # Private network
    ipaddress.ip_network("172.16.0.0/12"),    # Private network
]


def _is_local_request(request: Request) -> bool:
    """
    Check if request comes from a trusted local network.

    Args:
        request: FastAPI request object

    Returns:
        True if request is from local/trusted network
    """
    # Get client IP from X-Real-IP header (set by nginx) or fall back to client.host
    client_ip = request.headers.get("X-Real-IP") or request.headers.get(
        "X-Forwarded-For", ""
    ).split(",")[0].strip()

    if not client_ip and request.client:
        client_ip = request.client.host

    if not client_ip:
        return False

    try:
        ip = ipaddress.ip_address(client_ip)
        for network in TRUSTED_NETWORKS:
            if ip in network:
                logger.debug(f"Auto-authenticated local request from {client_ip}")
                return True
    except ValueError:
        logger.warning(f"Invalid IP address: {client_ip}")

    return False


async def require_auth(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None),
) -> bool:
    """
    Dependency that requires authentication.

    Checks for valid authentication via:
    1. Local network requests (auto-authenticated)
    2. X-API-Key header with API key
    3. Authorization: Bearer <session_token> header

    Args:
        request: FastAPI request object
        x_api_key: API key from X-API-Key header
        authorization: Bearer token from Authorization header

    Returns:
        True if authenticated

    Raises:
        HTTPException 401: If authentication fails
    """
    # Auto-authenticate local network requests
    if _is_local_request(request):
        return True

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
