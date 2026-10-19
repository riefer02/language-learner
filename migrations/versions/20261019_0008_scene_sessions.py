"""Add scene progress sessions.

Revision ID: 20261019_0008
Revises: 20261019_0007
Create Date: 2026-10-19
"""

import sqlalchemy as sa
from alembic import op

revision = "20261019_0008"
down_revision = "20261019_0007"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "scene_session",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("scene_slug", sa.String(length=60), nullable=False),
        sa.Column("step_index", sa.Integer(), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "scene_slug", name="uq_scene_session_user_scene"
        ),
    )
    op.create_index(
        "ix_scene_session_user",
        "scene_session",
        ["user_id", "completed"],
    )


def downgrade():
    op.drop_index("ix_scene_session_user", table_name="scene_session")
    op.drop_table("scene_session")
