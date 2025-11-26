"""
ROSE Link Backend Test Suite
============================

This package contains automated tests for the ROSE Link backend.

Test Organization:
- conftest.py: Shared fixtures and test configuration
- test_command_runner.py: Command execution layer tests
- test_auth_service.py: Authentication service tests
- test_api_*.py: API endpoint tests

Running Tests:
    # Run all tests
    pytest

    # Run with coverage
    pytest --cov=. --cov-report=html

    # Run specific test file
    pytest tests/test_auth_service.py

    # Run with verbose output
    pytest -v
"""
