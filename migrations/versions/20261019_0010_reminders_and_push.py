"""Add reminder preferences and push subscriptions.

Revision ID: 20261019_0010
Revises: 20261019_0009
Create Date: 2026-10-19
"""

import sqlalchemy as sa
from alembic import op

revision = "20261019_0010"
down_revision = "20261019_0009"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user",
        sa.Column(
            "reminder_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "user",
        sa.Column(
            "reminder_time",
            sa.String(length=5),
            nullable=False,
            server_default="19:00",
        ),
    )

    op.create_table(
        "push_subscription",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("endpoint", sa.Text(), nullable=False),
        sa.Column("p256dh", sa.String(length=300), nullable=False),
        sa.Column("auth", sa.String(length=120), nullable=False),
        sa.Column("user_agent", sa.String(length=300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_count", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("endpoint"),
    )
    op.create_index(
        "ix_push_subscription_user", "push_subscription", ["user_id"]
    )


def downgrade():
    op.drop_index("ix_push_subscription_user", table_name="push_subscription")
    op.drop_table("push_subscription")
    op.drop_column("user", "reminder_time")
    op.drop_column("user", "reminder_enabled")
