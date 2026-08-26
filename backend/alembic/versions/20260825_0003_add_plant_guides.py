"""add structured plant details and care guides

Revision ID: 20260825_0003
Revises: 20260825_0002
Create Date: 2026-08-25 22:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260825_0003"
down_revision: str | None = "20260825_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("plants", sa.Column("catalog_key", sa.String(length=100), nullable=True))
    op.add_column("plants", sa.Column("details", sa.JSON(), nullable=True))
    op.add_column("plants", sa.Column("care_guide", sa.JSON(), nullable=True))
    op.create_index(op.f("ix_plants_catalog_key"), "plants", ["catalog_key"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_plants_catalog_key"), table_name="plants")
    op.drop_column("plants", "care_guide")
    op.drop_column("plants", "details")
    op.drop_column("plants", "catalog_key")
