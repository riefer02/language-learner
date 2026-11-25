"""Record who a saved phrase is addressed to.

Revision ID: 20261125_0018
Revises: 20261125_0017
Create Date: 2026-11-25
"""

import sqlalchemy as sa
from alembic import op

revision = "20261125_0018"
down_revision = "20261125_0017"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "phrase",
        sa.Column("addressee", sa.String(length=12), nullable=True),
    )


def downgrade():
    op.drop_column("phrase", "addressee")
