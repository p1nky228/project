"""
Database models for the Maintenance Module.
"""

from app.models.apparatus import Apparatus, ApparatusStatus
from app.models.technician import Technician, TechnicianRole, apparatus_technician
from app.models.to_task import TOTask, TOTaskStatus
from app.models.to_photo import TOPhoto

__all__ = [
    "Apparatus",
    "ApparatusStatus",
    "Technician",
    "TechnicianRole",
    "apparatus_technician",
    "TOTask",
    "TOTaskStatus",
    "TOPhoto",
]