"""Add onboarding and goal fields to users.

Revision ID: 20261019_0006
Revises: 20261019_0005
Create Date: 2026-10-19
"""

import sqlalchemy as sa
from alembic import op

revision = "20261019_0006"
down_revision = "20261019_0005"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user",
        sa.Column(
            "goal", sa.String(length=30), nullable=False, server_default="everyday"
        ),
    )
    op.add_column(
        "user",
        sa.Column(
            "daily_minutes", sa.Integer(), nullable=False, server_default="10"
        ),
    )
    op.add_column(
        "user",
        sa.Column(
            "experience", sa.String(length=20), nullable=False, server_default="new"
        ),
    )
    op.add_column(
        "user",
        sa.Column(
            "timezone", sa.String(length=64), nullable=False, server_default="UTC"
        ),
    )
    op.add_column(
        "user",
        sa.Column(
            "onboarding_complete",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade():
    for column in (
        "onboarding_complete",
        "timezone",
        "experience",
        "daily_minutes",
        "goal",
    ):
        op.drop_column("user", column)
