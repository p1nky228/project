import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.apparatus import Apparatus
    from app.models.technician import Technician
    from app.models.to_photo import TOPhoto


class TOTaskStatus(PyEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    OVERDUE = "overdue"


class TOTask(Base):
    __tablename__ = "to_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    apparatus_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("apparatuses.id", ondelete="CASCADE"),
        nullable=False,
    )
    technician_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("technicians.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[TOTaskStatus] = mapped_column(
        Enum(TOTaskStatus, name="to_task_status_enum", create_constraint=True),
        default=TOTaskStatus.PENDING,
        nullable=False,
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    photos_json: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    meter_readings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    cash_amount: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    apparatus: Mapped["Apparatus"] = relationship(
        "Apparatus",
        back_populates="to_tasks",
        foreign_keys=[apparatus_id],
    )
    technician: Mapped["Technician"] = relationship(
        "Technician",
        back_populates="to_tasks",
        foreign_keys=[technician_id],
    )
    photos: Mapped[List["TOPhoto"]] = relationship(
        "TOPhoto",
        back_populates="task",
        foreign_keys="TOPhoto.task_id",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        Index("idx_to_task_apparatus", "apparatus_id"),
        Index("idx_to_task_technician", "technician_id"),
        Index("idx_to_task_status", "status"),
        Index("idx_to_task_scheduled", "scheduled_at"),
    )

    def __repr__(self) -> str:
        return f"<TOTask(id={self.id}, apparatus_id={self.apparatus_id}, technician_id={self.technician_id}, status={self.status.value})>"