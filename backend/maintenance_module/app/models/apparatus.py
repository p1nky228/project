import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm.decl_api import DeclarativeMeta

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.technician import Technician
    from app.models.to_task import TOTask


class ApparatusStatus(PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class Apparatus(Base):
    __tablename__ = "apparatuses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    to_interval_days: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    last_to_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    technician_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("technicians.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[ApparatusStatus] = mapped_column(
        Enum(ApparatusStatus, name="apparatus_status_enum", create_constraint=True),
        default=ApparatusStatus.ACTIVE,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    technician: Mapped["Technician"] = relationship(
        "Technician",
        back_populates="assigned_apparatuses",
        foreign_keys=[technician_id],
    )
    to_tasks: Mapped[List["TOTask"]] = relationship(
        "TOTask",
        back_populates="apparatus",
        foreign_keys="TOTask.apparatus_id",
    )

    # Indexes
    __table_args__ = (
        Index("idx_apparatus_technician", "technician_id"),
        Index("idx_apparatus_status", "status"),
        Index("idx_apparatus_last_to", "last_to_date"),
    )

    def __repr__(self) -> str:
        return f"<Apparatus(id={self.id}, address={self.address}, status={self.status.value})>"