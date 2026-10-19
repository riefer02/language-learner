"""Add optimistic versioning to review cards.

Revision ID: 20261019_0005
Revises: 20261019_0004
Create Date: 2026-10-19
"""

import sqlalchemy as sa
from alembic import op

revision = "20261019_0005"
down_revision = "20261019_0004"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "review_card",
        sa.Column(
            "version", sa.Integer(), nullable=False, server_default="1"
        ),
    )


def downgrade():
    op.drop_column("review_card", "version")
