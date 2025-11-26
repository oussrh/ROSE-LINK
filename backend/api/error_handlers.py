"""
API Error Handlers
==================

Consolidated error handling utilities for API routes.

This module provides a centralized approach to error handling, reducing
code duplication across route handlers and ensuring consistent error responses.

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import logging
from functools import wraps
from typing import Any, Callable, Type, TypeVar

from fastapi import HTTPException

from exceptions import (
    RoseLinkError,
    ValidationError,
    FileTooLargeError,
    InvalidWireGuardConfigError,
    VPNProfileNotFoundError,
    VPNProfileActiveError,
    VPNConnectionError,
    HotspotConfigurationError,
    WifiConnectionError,
    WifiScanError,
    AuthenticationError,
    FileOperationError,
)

logger = logging.getLogger("rose-link.api.error_handlers")

# Type variable for return type preservation
T = TypeVar("T")


# Exception to HTTP status code mapping
EXCEPTION_STATUS_CODES: dict[Type[Exception], int] = {
    # 400 Bad Request - Client errors
    ValidationError: 400,
    FileTooLargeError: 400,
    InvalidWireGuardConfigError: 400,
    VPNProfileActiveError: 400,
    ValueError: 400,
    # 401 Unauthorized
    AuthenticationError: 401,
    # 404 Not Found
    VPNProfileNotFoundError: 404,
    FileNotFoundError: 404,
    # 500 Internal Server Error - Server errors
    VPNConnectionError: 500,
    HotspotConfigurationError: 500,
    WifiConnectionError: 500,
    WifiScanError: 500,
    FileOperationError: 500,
    OSError: 500,
}


def get_status_code(exception: Exception) -> int:
    """
    Get the appropriate HTTP status code for an exception.

    Args:
        exception: The exception to map

    Returns:
        HTTP status code (defaults to 500 for unknown exceptions)
    """
    for exc_type, status_code in EXCEPTION_STATUS_CODES.items():
        if isinstance(exception, exc_type):
            return status_code
    return 500


def exception_to_http_exception(
    exception: Exception,
    operation: str = "Operation",
    log_error: bool = True,
) -> HTTPException:
    """
    Convert an exception to an HTTPException with appropriate status code.

    Args:
        exception: The exception to convert
        operation: Description of the operation that failed (for logging)
        log_error: Whether to log the error (default True)

    Returns:
        HTTPException with appropriate status code and detail
    """
    status_code = get_status_code(exception)

    # Log server errors
    if log_error and status_code >= 500:
        logger.error(f"{operation} failed: {exception}")

    # Get error message
    if isinstance(exception, RoseLinkError):
        detail = str(exception)
    elif isinstance(exception, ValueError):
        detail = str(exception)
    elif isinstance(exception, FileNotFoundError):
        detail = "Resource not found"
    else:
        # Don't expose internal error details for unexpected exceptions
        detail = f"{operation} failed"

    return HTTPException(status_code=status_code, detail=detail)


def handle_route_errors(
    operation: str,
    expected_exceptions: tuple[Type[Exception], ...] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for consistent error handling in route handlers.

    This decorator catches exceptions and converts them to appropriate
    HTTPExceptions, reducing boilerplate in route handlers.

    Args:
        operation: Description of the operation (used in error messages)
        expected_exceptions: Tuple of exception types to handle gracefully.
                           If None, handles all RoseLinkError subclasses.

    Returns:
        Decorated function with error handling

    Example:
        @router.post("/upload")
        @handle_route_errors(
            operation="Upload profile",
            expected_exceptions=(FileTooLargeError, InvalidWireGuardConfigError)
        )
        async def upload_profile(file: UploadFile):
            # ... implementation
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                # Re-raise HTTPExceptions as-is
                raise
            except Exception as e:
                if expected_exceptions and isinstance(e, expected_exceptions):
                    raise exception_to_http_exception(e, operation, log_error=False)
                elif isinstance(e, RoseLinkError):
                    raise exception_to_http_exception(e, operation)
                elif isinstance(e, (ValueError, FileNotFoundError)):
                    raise exception_to_http_exception(e, operation, log_error=False)
                else:
                    # Unexpected exception - log and return generic error
                    logger.exception(f"Unexpected error in {operation}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"{operation} failed: {str(e)}"
                    )

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                if expected_exceptions and isinstance(e, expected_exceptions):
                    raise exception_to_http_exception(e, operation, log_error=False)
                elif isinstance(e, RoseLinkError):
                    raise exception_to_http_exception(e, operation)
                elif isinstance(e, (ValueError, FileNotFoundError)):
                    raise exception_to_http_exception(e, operation, log_error=False)
                else:
                    logger.exception(f"Unexpected error in {operation}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"{operation} failed: {str(e)}"
                    )

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator


# Pre-configured decorators for common operations
def vpn_error_handler(func: Callable[..., T]) -> Callable[..., T]:
    """Error handler for VPN operations."""
    return handle_route_errors(
        operation="VPN operation",
        expected_exceptions=(
            FileTooLargeError,
            InvalidWireGuardConfigError,
            VPNProfileNotFoundError,
            VPNProfileActiveError,
            VPNConnectionError,
            ValidationError,
        ),
    )(func)


def hotspot_error_handler(func: Callable[..., T]) -> Callable[..., T]:
    """Error handler for hotspot operations."""
    return handle_route_errors(
        operation="Hotspot operation",
        expected_exceptions=(
            HotspotConfigurationError,
            ValidationError,
        ),
    )(func)


def wifi_error_handler(func: Callable[..., T]) -> Callable[..., T]:
    """Error handler for WiFi operations."""
    return handle_route_errors(
        operation="WiFi operation",
        expected_exceptions=(
            WifiConnectionError,
            WifiScanError,
            ValidationError,
        ),
    )(func)


def backup_error_handler(func: Callable[..., T]) -> Callable[..., T]:
    """Error handler for backup operations."""
    return handle_route_errors(
        operation="Backup operation",
        expected_exceptions=(
            FileOperationError,
            ValidationError,
        ),
    )(func)
