"""Add real-time teacher sessions, turns, drills, and attempts.

Revision ID: 20261123_0013
Revises: 20261123_0012
Create Date: 2026-11-23
"""

import sqlalchemy as sa
from alembic import op

revision = "20261123_0013"
down_revision = "20261123_0012"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "teacher_session",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("language_id", sa.Integer(), nullable=True),
        sa.Column(
            "mode", sa.String(length=16), nullable=False, server_default="voice"
        ),
        sa.Column(
            "plan_slug",
            sa.String(length=40),
            nullable=False,
            server_default="free_talk",
        ),
        sa.Column(
            "plan_title",
            sa.String(length=200),
            nullable=False,
            server_default="Free talk",
        ),
        sa.Column(
            "provider",
            sa.String(length=40),
            nullable=False,
            server_default="openai_realtime",
        ),
        sa.Column("provider_session_id", sa.String(length=120), nullable=True),
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("turn_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "learner_turn_count", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("summary_text", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["language_id"], ["language.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid"),
    )
    op.create_index("ix_teacher_session_status", "teacher_session", ["status"])
    op.create_index("ix_teacher_session_started_at", "teacher_session", ["started_at"])
    op.create_index(
        "ix_teacher_session_user_started", "teacher_session", ["user_id", "started_at"]
    )

    op.create_table(
        "teacher_turn",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("turn_index", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("tool_name", sa.String(length=60), nullable=True),
        sa.Column("tool_args", sa.Text(), nullable=True),
        sa.Column("tool_result", sa.Text(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["session_id"], ["teacher_session.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "session_id", "turn_index", name="uq_teacher_turn_session_index"
        ),
    )

    op.create_table(
        "drill",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("language_id", sa.Integer(), nullable=True),
        sa.Column("item_id", sa.Integer(), nullable=True),
        sa.Column(
            "source", sa.String(length=16), nullable=False, server_default="teacher"
        ),
        sa.Column(
            "drill_type",
            sa.String(length=32),
            nullable=False,
            server_default="translate_to_target",
        ),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("expected", sa.Text(), nullable=False),
        sa.Column("payload", sa.Text(), nullable=True),
        sa.Column(
            "validated", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["session_id"], ["teacher_session.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["language_id"], ["language.id"]),
        sa.ForeignKeyConstraint(["item_id"], ["item.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid"),
    )
    op.create_index("ix_drill_user_created", "drill", ["user_id", "created_at"])

    op.create_table(
        "drill_attempt",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("drill_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("response", sa.Text(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column(
            "acceptable", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("client_attempt_id", sa.String(length=64), nullable=False),
        sa.Column("review_card_id", sa.Integer(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["drill_id"], ["drill.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["review_card_id"], ["review_card.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "drill_id", "client_attempt_id", name="uq_drill_attempt_client"
        ),
    )
    op.create_index(
        "ix_drill_attempt_user_created", "drill_attempt", ["user_id", "created_at"]
    )


def downgrade():
    op.drop_index("ix_drill_attempt_user_created", table_name="drill_attempt")
    op.drop_table("drill_attempt")
    op.drop_index("ix_drill_user_created", table_name="drill")
    op.drop_table("drill")
    op.drop_table("teacher_turn")
    op.drop_index("ix_teacher_session_user_started", table_name="teacher_session")
    op.drop_index("ix_teacher_session_started_at", table_name="teacher_session")
    op.drop_index("ix_teacher_session_status", table_name="teacher_session")
    op.drop_table("teacher_session")
