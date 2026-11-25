"""Capture learner-flagged content corrections and native-check provenance.

Revision ID: 20261125_0016
Revises: 20261123_0015
Create Date: 2026-11-25

One new table plus two nullable-friendly item columns. The item columns use
plain ``ADD COLUMN`` because SQLite cannot rebuild ``item`` while review cards
and logs reference it with foreign keys on.
"""

import sqlalchemy as sa
from alembic import op

revision = "20261125_0016"
down_revision = "20261123_0015"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "content_report",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("language_id", sa.Integer(), nullable=True),
        sa.Column("item_id", sa.Integer(), nullable=True),
        sa.Column("phrase_id", sa.Integer(), nullable=True),
        sa.Column("scene_slug", sa.String(length=80), nullable=True),
        sa.Column("step_index", sa.Integer(), nullable=True),
        sa.Column("surface", sa.String(length=24), nullable=False),
        sa.Column("snapshot_text", sa.Text(), nullable=True),
        sa.Column("kind", sa.String(length=24), nullable=False),
        sa.Column("suggested_text", sa.String(length=300), nullable=True),
        sa.Column("context", sa.String(length=200), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default="open",
        ),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["language_id"], ["language.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["item_id"], ["item.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["phrase_id"], ["phrase.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_content_report_status_created",
        "content_report",
        ["status", "created_at"],
    )
    op.create_index(
        "ix_content_report_user_created",
        "content_report",
        ["user_id", "created_at"],
    )

    op.add_column(
        "item",
        sa.Column(
            "review_status",
            sa.String(length=16),
            nullable=False,
            server_default="unchecked",
        ),
    )
    op.add_column(
        "item",
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade():
    op.drop_column("item", "reviewed_at")
    op.drop_column("item", "review_status")
    op.drop_index(
        "ix_content_report_user_created", table_name="content_report"
    )
    op.drop_index(
        "ix_content_report_status_created", table_name="content_report"
    )
    op.drop_table("content_report")
