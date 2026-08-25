"""create plants table

Revision ID: 20260825_0001
Revises:
Create Date: 2026-08-25 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260825_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "plants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nickname", sa.String(length=100), nullable=False),
        sa.Column("species", sa.String(length=160), nullable=False),
        sa.Column("room", sa.String(length=100), nullable=False),
        sa.Column("sunlight", sa.String(length=40), nullable=False),
        sa.Column("watering_frequency", sa.Integer(), nullable=False),
        sa.Column("last_watered", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "sunlight IN ('Direct Sun', 'Indirect Light', 'Low Light')",
            name="ck_plants_sunlight_valid",
        ),
        sa.CheckConstraint(
            "watering_frequency > 0",
            name="ck_plants_watering_frequency_positive",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_plants_id"), "plants", ["id"], unique=False)
    op.create_index(op.f("ix_plants_nickname"), "plants", ["nickname"], unique=False)
    op.create_index(op.f("ix_plants_room"), "plants", ["room"], unique=False)
    op.create_index(op.f("ix_plants_species"), "plants", ["species"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_plants_species"), table_name="plants")
    op.drop_index(op.f("ix_plants_room"), table_name="plants")
    op.drop_index(op.f("ix_plants_nickname"), table_name="plants")
    op.drop_index(op.f("ix_plants_id"), table_name="plants")
    op.drop_table("plants")

