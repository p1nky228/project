"""add accepted_at and rejected_at to to_tasks

Revision ID: 002_add_accepted_rejected_at
Revises: 001_add_to_module_models
Create Date: 2026-10-06

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_accepted_rejected_at'
down_revision = '001_add_to_module_models'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add accepted_at and rejected_at columns to to_tasks table
    op.add_column(
        'to_tasks',
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        'to_tasks',
        sa.Column('rejected_at', sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    # Remove the columns
    op.drop_column('to_tasks', 'accepted_at')
    op.drop_column('to_tasks', 'rejected_at')