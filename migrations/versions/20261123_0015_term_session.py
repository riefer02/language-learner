"""Link teacher-saved terms to the session that produced them.

Revision ID: 20261123_0015
Revises: 20261123_0014
Create Date: 2026-11-23
"""

import sqlalchemy as sa
from alembic import op

revision = "20261123_0015"
down_revision = "20261123_0014"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("term_card") as batch:
        batch.add_column(sa.Column("session_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_term_card_session",
            "teacher_session",
            ["session_id"],
            ["id"],
            ondelete="SET NULL",
        )
    op.create_index("ix_term_card_session_id", "term_card", ["session_id"])


def downgrade():
    op.drop_index("ix_term_card_session_id", table_name="term_card")
    with op.batch_alter_table("term_card") as batch:
        batch.drop_constraint("fk_term_card_session", type_="foreignkey")
        batch.drop_column("session_id")
