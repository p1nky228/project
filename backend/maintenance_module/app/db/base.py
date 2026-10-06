"""
Database base configuration for SQLAlchemy 2.0 async.
"""

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    """
    Base class for all database models.
    Uses SQLAlchemy 2.0 async style with AsyncAttrs.
    """
    pass