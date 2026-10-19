"""Add can-do proof artifacts.

Revision ID: 20261019_0009
Revises: 20261019_0008
Create Date: 2026-10-19
"""

import sqlalchemy as sa
from alembic import op

revision = "20261019_0009"
down_revision = "20261019_0008"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "can_do_artifact",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("scene_slug", sa.String(length=60), nullable=False),
        sa.Column("label", sa.String(length=300), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "scene_slug", name="uq_can_do_user_scene"
        ),
    )
    op.create_index(
        "ix_can_do_user_date", "can_do_artifact", ["user_id", "created_at"]
    )
    op.create_index(
        "ix_can_do_artifact_created_at", "can_do_artifact", ["created_at"]
    )


def downgrade():
    op.drop_index(
        "ix_can_do_artifact_created_at", table_name="can_do_artifact"
    )
    op.drop_index("ix_can_do_user_date", table_name="can_do_artifact")
    op.drop_table("can_do_artifact")
