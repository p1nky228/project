import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, List

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Enum, ForeignKey, Index, Integer, String, Table, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm.decl_api import DeclarativeMeta

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.apparatus import Apparatus
    from app.models.to_task import TOTask


class TechnicianRole(PyEnum):
    TECHNICIAN = "technician"
    ADMIN = "admin"
    DISPATCHER = "dispatcher"
    MANAGER = "manager"


# Association table for M2M relationship between Technician and Apparatus
apparatus_technician = Table(
    "apparatus_technician",
    Base.metadata,
    Column(
        "apparatus_id",
        UUID(as_uuid=True),
        ForeignKey("apparatuses.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "technician_id",
        UUID(as_uuid=True),
        ForeignKey("technicians.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Technician(Base):
    __tablename__ = "technicians"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[TechnicianRole] = mapped_column(
        Enum(TechnicianRole, name="technician_role_enum", create_constraint=True),
        default=TechnicianRole.TECHNICIAN,
        nullable=False,
    )
    rating: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    assigned_apparatuses: Mapped[List["Apparatus"]] = relationship(
        "Apparatus",
        secondary=apparatus_technician,
        back_populates="technician",
    )
    to_tasks: Mapped[List["TOTask"]] = relationship(
        "TOTask",
        back_populates="technician",
        foreign_keys="TOTask.technician_id",
    )

    # Indexes
    __table_args__ = (
        Index("idx_technician_telegram_id", "telegram_id"),
        Index("idx_technician_role", "role"),
    )

    def __repr__(self) -> str:
        return f"<Technician(id={self.id}, telegram_id={self.telegram_id}, full_name={self.full_name}, role={self.role.value})>"