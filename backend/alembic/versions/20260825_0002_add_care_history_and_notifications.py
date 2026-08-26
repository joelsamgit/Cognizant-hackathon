"""add care history and push notifications

Revision ID: 20260825_0002
Revises: 20260825_0001
Create Date: 2026-08-25 19:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260825_0002"
down_revision: str | None = "20260825_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "care_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plant_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=24), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("amount_ml", sa.Integer(), nullable=True),
        sa.Column("result", sa.String(length=24), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "action IN ('water', 'check', 'fertilize', 'mist', 'prune', 'repot')",
            name="ck_care_events_action_valid",
        ),
        sa.CheckConstraint(
            "result IN ('watered', 'still_damp', 'completed', 'skipped')",
            name="ck_care_events_result_valid",
        ),
        sa.CheckConstraint(
            "amount_ml IS NULL OR (amount_ml >= 0 AND amount_ml <= 10000)",
            name="ck_care_events_amount_valid",
        ),
        sa.ForeignKeyConstraint(["plant_id"], ["plants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_care_events_action", "care_events", ["action"], unique=False)
    op.create_index("ix_care_events_occurred_at", "care_events", ["occurred_at"], unique=False)
    op.create_index("ix_care_events_plant_id", "care_events", ["plant_id"], unique=False)

    op.execute(
        sa.text(
            """
            INSERT INTO care_events (plant_id, action, occurred_at, result, notes, created_at)
            SELECT id, 'water', last_watered, 'watered', 'Imported from existing watering record', CURRENT_TIMESTAMP
            FROM plants
            """
        )
    )

    op.create_table(
        "push_subscriptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("endpoint", sa.Text(), nullable=False),
        sa.Column("p256dh", sa.String(length=512), nullable=False),
        sa.Column("auth", sa.String(length=256), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("reminder_time", sa.String(length=5), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("failure_count", sa.Integer(), nullable=False),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("endpoint"),
    )

    op.create_table(
        "notification_deliveries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("subscription_id", sa.Integer(), nullable=False),
        sa.Column("plant_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=24), nullable=False),
        sa.Column("care_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["plant_id"], ["plants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["push_subscriptions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "subscription_id",
            "plant_id",
            "kind",
            "care_date",
            name="uq_notification_delivery_daily",
        ),
    )
    op.create_index(
        "ix_notification_deliveries_plant_id",
        "notification_deliveries",
        ["plant_id"],
        unique=False,
    )
    op.create_index(
        "ix_notification_deliveries_subscription_id",
        "notification_deliveries",
        ["subscription_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_notification_deliveries_subscription_id",
        table_name="notification_deliveries",
    )
    op.drop_index(
        "ix_notification_deliveries_plant_id",
        table_name="notification_deliveries",
    )
    op.drop_table("notification_deliveries")
    op.drop_table("push_subscriptions")
    op.drop_index("ix_care_events_plant_id", table_name="care_events")
    op.drop_index("ix_care_events_occurred_at", table_name="care_events")
    op.drop_index("ix_care_events_action", table_name="care_events")
    op.drop_table("care_events")
