"""Label pre-formality Amharic phrases with their everyday register.

Before formality existed, the Amharic translation prompt used the everyday
second person (አንተ/አንቺ). Those saved rows have no register, so label them
`casual` rather than showing them as an unrecorded or formal phrase.

Revision ID: 20261126_0020
Revises: 20261125_0019
Create Date: 2026-11-26
"""

from alembic import op

revision = "20261126_0020"
down_revision = "20261125_0019"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        UPDATE phrase
        SET register = 'casual'
        WHERE register IS NULL
          AND target_text IS NOT NULL
          AND target_language_id IN (
              SELECT id FROM language WHERE code = 'am'
          )
        """
    )


def downgrade():
    # Intentionally not reversed: nulling every 'casual' row would also erase
    # registers the learner chose explicitly after this migration.
    pass
