"""Guarantee a single local development user.

Revision ID: 20261019_0004
Revises: 20261019_0003
Create Date: 2026-10-19
"""

import sqlalchemy as sa
from alembic import op

revision = "20261019_0004"
down_revision = "20261019_0003"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "uq_user_single_local",
        "user",
        ["is_local"],
        unique=True,
        sqlite_where=sa.text("is_local = 1"),
        postgresql_where=sa.text("is_local = 1"),
    )


def downgrade():
    op.drop_index("uq_user_single_local", table_name="user")
