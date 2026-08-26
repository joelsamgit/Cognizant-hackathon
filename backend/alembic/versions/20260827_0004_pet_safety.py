"""add pet safety fields

Revision ID: 20260827_0004
Revises: 20260827_0003
Create Date: 2026-08-27 00:04:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260827_0004"
down_revision: str | None = "20260827_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("plants", sa.Column("pet_safety", sa.String(length=20), nullable=True))
    op.add_column("plants", sa.Column("pet_severity", sa.String(length=10), nullable=True))
    op.add_column("plants", sa.Column("toxic_cats", sa.Boolean(), nullable=True))
    op.add_column("plants", sa.Column("toxic_dogs", sa.Boolean(), nullable=True))
    op.add_column("plants", sa.Column("placement_tip", sa.String(length=300), nullable=True))


def downgrade() -> None:
    op.drop_column("plants", "placement_tip")
    op.drop_column("plants", "toxic_dogs")
    op.drop_column("plants", "toxic_cats")
    op.drop_column("plants", "pet_severity")
    op.drop_column("plants", "pet_safety")
