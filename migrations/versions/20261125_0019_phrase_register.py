"""Record the formality register of a saved phrase.

Revision ID: 20261125_0019
Revises: 20261125_0018
Create Date: 2026-11-25
"""

import sqlalchemy as sa
from alembic import op

revision = "20261125_0019"
down_revision = "20261125_0018"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "phrase",
        sa.Column("register", sa.String(length=12), nullable=True),
    )


def downgrade():
    op.drop_column("phrase", "register")
