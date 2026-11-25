"""Store the learner-facing transliteration on saved phrases.

Revision ID: 20261125_0017
Revises: 20261125_0016
Create Date: 2026-11-25
"""

import sqlalchemy as sa
from alembic import op

revision = "20261125_0017"
down_revision = "20261125_0016"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "phrase",
        sa.Column("target_transliteration", sa.String(length=500), nullable=True),
    )


def downgrade():
    op.drop_column("phrase", "target_transliteration")
