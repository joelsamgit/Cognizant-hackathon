"""add users, sessions, and resource ownership

Revision ID: 20260825_0004
Revises: 20260825_0003
Create Date: 2026-08-25 23:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260825_0004"
down_revision: str | None = "20260825_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("place", sa.String(length=160), nullable=False),
        sa.Column("pets", sa.JSON(), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
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
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    users = sa.table(
        "users",
        sa.column("id", sa.Integer()),
        sa.column("email", sa.String()),
        sa.column("password_hash", sa.String()),
        sa.column("full_name", sa.String()),
        sa.column("place", sa.String()),
        sa.column("pets", sa.JSON()),
        sa.column("timezone", sa.String()),
        sa.column("is_active", sa.Boolean()),
    )
    legacy_user_id = op.get_bind().execute(
        users.insert()
        .values(
            email="legacy-garden@plantguardian.local",
            password_hash="!disabled",
            full_name="Legacy Garden",
            place="Local installation",
            pets=["No pets"],
            timezone="UTC",
            is_active=False,
        )
        .returning(users.c.id)
    ).scalar_one()

    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_user_sessions_expires_at"),
        "user_sessions",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_sessions_token_hash"),
        "user_sessions",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        op.f("ix_user_sessions_user_id"),
        "user_sessions",
        ["user_id"],
        unique=False,
    )

    op.add_column("plants", sa.Column("user_id", sa.Integer(), nullable=True))
    op.execute(sa.update(sa.table("plants", sa.column("user_id"))).values(user_id=legacy_user_id))
    op.alter_column("plants", "user_id", nullable=False)
    op.create_foreign_key(
        "fk_plants_user_id_users",
        "plants",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(op.f("ix_plants_user_id"), "plants", ["user_id"], unique=False)

    op.add_column("push_subscriptions", sa.Column("user_id", sa.Integer(), nullable=True))
    op.execute(
        sa.update(sa.table("push_subscriptions", sa.column("user_id"))).values(
            user_id=legacy_user_id
        )
    )
    op.alter_column("push_subscriptions", "user_id", nullable=False)
    op.create_foreign_key(
        "fk_push_subscriptions_user_id_users",
        "push_subscriptions",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        op.f("ix_push_subscriptions_user_id"),
        "push_subscriptions",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_push_subscriptions_user_id"), table_name="push_subscriptions")
    op.drop_constraint(
        "fk_push_subscriptions_user_id_users",
        "push_subscriptions",
        type_="foreignkey",
    )
    op.drop_column("push_subscriptions", "user_id")
    op.drop_index(op.f("ix_plants_user_id"), table_name="plants")
    op.drop_constraint("fk_plants_user_id_users", "plants", type_="foreignkey")
    op.drop_column("plants", "user_id")
    op.drop_index(op.f("ix_user_sessions_user_id"), table_name="user_sessions")
    op.drop_index(op.f("ix_user_sessions_token_hash"), table_name="user_sessions")
    op.drop_index(op.f("ix_user_sessions_expires_at"), table_name="user_sessions")
    op.drop_table("user_sessions")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
