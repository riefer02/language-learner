"""Track whether a review introduced a new card.

Revision ID: 20261019_0003
Revises: 20261019_0002
Create Date: 2026-10-19
"""

import sqlalchemy as sa
from alembic import op

revision = "20261019_0003"
down_revision = "20261019_0002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "review_log",
        sa.Column(
            "was_new",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade():
    op.drop_column("review_log", "was_new")
