"""add gamification waterings and xp

Revision ID: 20260827_0003
Revises: 20260825_0004
Create Date: 2026-08-27 00:03:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260827_0003"
down_revision: str | None = "20260825_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "plants",
        sa.Column("xp", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_table(
        "waterings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plant_id", sa.Integer(), nullable=False),
        sa.Column("watered_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["plant_id"], ["plants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_waterings_plant_id_watered_at",
        "waterings",
        ["plant_id", sa.text("watered_at DESC")],
        unique=False,
    )
    op.execute(
        sa.text(
            "INSERT INTO waterings (plant_id, watered_at) "
            "SELECT id, last_watered FROM plants"
        )
    )


def downgrade() -> None:
    op.drop_index("ix_waterings_plant_id_watered_at", table_name="waterings")
    op.drop_table("waterings")
    op.drop_column("plants", "xp")
