"""Add TO module models: Apparatus, Technician, TOTask, TOPhoto

Revision ID: 001
Revises:
Create Date: 2024-01-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    apparatus_status_enum = postgresql.ENUM(
        'active', 'inactive', 'maintenance',
        name='apparatus_status_enum',
        create_type=True
    )
    apparatus_status_enum.create(op.get_bind(), checkfirst=True)

    technician_role_enum = postgresql.ENUM(
        'technician', 'admin', 'dispatcher', 'manager',
        name='technician_role_enum',
        create_type=True
    )
    technician_role_enum.create(op.get_bind(), checkfirst=True)

    to_task_status_enum = postgresql.ENUM(
        'pending', 'in_progress', 'completed', 'rejected', 'overdue',
        name='to_task_status_enum',
        create_type=True
    )
    to_task_status_enum.create(op.get_bind(), checkfirst=True)

    # Create technicians table
    op.create_table(
        'technicians',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('full_name', sa.String(length=200), nullable=False),
        sa.Column('role', technician_role_enum, nullable=False, server_default='technician'),
        sa.Column('rating', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_id')
    )
    op.create_index('idx_technician_telegram_id', 'technicians', ['telegram_id'], unique=False)
    op.create_index('idx_technician_role', 'technicians', ['role'], unique=False)

    # Create apparatuses table
    op.create_table(
        'apparatuses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('address', sa.String(length=500), nullable=False),
        sa.Column('lat', sa.Float(), nullable=False),
        sa.Column('lon', sa.Float(), nullable=False),
        sa.Column('to_interval_days', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('last_to_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('technician_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', apparatus_status_enum, nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['technician_id'], ['technicians.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_apparatus_technician', 'apparatuses', ['technician_id'], unique=False)
    op.create_index('idx_apparatus_status', 'apparatuses', ['status'], unique=False)
    op.create_index('idx_apparatus_last_to', 'apparatuses', ['last_to_date'], unique=False)

    # Create apparatus_technician association table (M2M)
    op.create_table(
        'apparatus_technician',
        sa.Column('apparatus_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('technician_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['apparatus_id'], ['apparatuses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['technician_id'], ['technicians.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('apparatus_id', 'technician_id')
    )

    # Create to_tasks table
    op.create_table(
        'to_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('apparatus_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('technician_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', to_task_status_enum, nullable=False, server_default='pending'),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('photos_json', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('meter_readings', postgresql.JSONB(), nullable=True),
        sa.Column('cash_amount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['apparatus_id'], ['apparatuses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['technician_id'], ['technicians.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_to_task_apparatus', 'to_tasks', ['apparatus_id'], unique=False)
    op.create_index('idx_to_task_technician', 'to_tasks', ['technician_id'], unique=False)
    op.create_index('idx_to_task_status', 'to_tasks', ['status'], unique=False)
    op.create_index('idx_to_task_scheduled', 'to_tasks', ['scheduled_at'], unique=False)

    # Create to_photos table
    op.create_table(
        'to_photos',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('step_number', sa.Integer(), nullable=False),
        sa.Column('s3_key', sa.String(length=500), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['to_tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_to_photo_task', 'to_photos', ['task_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('idx_to_photo_task', table_name='to_photos')
    op.drop_table('to_photos')

    op.drop_index('idx_to_task_scheduled', table_name='to_tasks')
    op.drop_index('idx_to_task_status', table_name='to_tasks')
    op.drop_index('idx_to_task_technician', table_name='to_tasks')
    op.drop_index('idx_to_task_apparatus', table_name='to_tasks')
    op.drop_table('to_tasks')

    op.drop_table('apparatus_technician')

    op.drop_index('idx_apparatus_last_to', table_name='apparatuses')
    op.drop_index('idx_apparatus_status', table_name='apparatuses')
    op.drop_index('idx_apparatus_technician', table_name='apparatuses')
    op.drop_table('apparatuses')

    op.drop_index('idx_technician_role', table_name='technicians')
    op.drop_index('idx_technician_telegram_id', table_name='technicians')
    op.drop_table('technicians')

    # Drop enum types
    to_task_status_enum = postgresql.ENUM(
        'pending', 'in_progress', 'completed', 'rejected', 'overdue',
        name='to_task_status_enum'
    )
    to_task_status_enum.drop(op.get_bind(), checkfirst=True)

    technician_role_enum = postgresql.ENUM(
        'technician', 'admin', 'dispatcher', 'manager',
        name='technician_role_enum'
    )
    technician_role_enum.drop(op.get_bind(), checkfirst=True)

    apparatus_status_enum = postgresql.ENUM(
        'active', 'inactive', 'maintenance',
        name='apparatus_status_enum'
    )
    apparatus_status_enum.drop(op.get_bind(), checkfirst=True)