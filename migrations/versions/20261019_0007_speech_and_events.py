"""Add speech attempts and product events.

Revision ID: 20261019_0007
Revises: 20261019_0006
Create Date: 2026-10-19
"""

import sqlalchemy as sa
from alembic import op

revision = "20261019_0007"
down_revision = "20261019_0006"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "speech_attempt",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=True),
        sa.Column("target_text", sa.String(length=300), nullable=False),
        sa.Column("transcript", sa.String(length=500), nullable=False),
        sa.Column("match_score", sa.Float(), nullable=False),
        sa.Column("acceptable", sa.Boolean(), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("model", sa.String(length=60), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["item.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_speech_attempt_user_date",
        "speech_attempt",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_speech_attempt_created_at", "speech_attempt", ["created_at"]
    )

    op.create_table(
        "event",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=60), nullable=False),
        sa.Column("props", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_event_name", "event", ["name"])
    op.create_index("ix_event_created_at", "event", ["created_at"])
    op.create_index(
        "ix_event_user_name_date",
        "event",
        ["user_id", "name", "created_at"],
    )


def downgrade():
    op.drop_index("ix_event_user_name_date", table_name="event")
    op.drop_index("ix_event_created_at", table_name="event")
    op.drop_index("ix_event_name", table_name="event")
    op.drop_table("event")
    op.drop_index("ix_speech_attempt_created_at", table_name="speech_attempt")
    op.drop_index("ix_speech_attempt_user_date", table_name="speech_attempt")
    op.drop_table("speech_attempt")
