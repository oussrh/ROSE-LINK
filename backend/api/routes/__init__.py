"""
API Routes Package
==================

Contains all API endpoint modules organized by domain.

Author: ROSE Link Team
License: MIT
"""

from . import auth, wifi, vpn, hotspot, system

__all__ = ["auth", "wifi", "vpn", "hotspot", "system"]
