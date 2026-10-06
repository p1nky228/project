"""
API package for Maintenance Module.
"""

from app.api.admin_routes import router as admin_router

__all__ = ["admin_router"]