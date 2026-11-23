"""Rename legacy Korean-shaped columns to language-neutral names.

Revision ID: 20261123_0014
Revises: 20261123_0013
Create Date: 2026-11-23

Contract phase. The expand/backfill already copied data into language-neutral
tables; this migration makes the primary columns honest:

* ``item.korean``        -> ``item.target_text``
* ``item.english``       -> ``item.gloss``
* ``item.romanization``  -> ``item.transliteration``
* ``phrase.english_text`` -> dropped (``phrase.source_text`` is canonical)
* ``phrase.korean_text``  -> dropped (``phrase.target_text`` is canonical)

SQLite's native RENAME COLUMN is used instead of a batch table rebuild because
``item`` is referenced by review cards/logs, and rebuilding it with foreign keys
on fails on real databases.
"""

import sqlalchemy as sa
from alembic import op

revision = "20261123_0014"
down_revision = "20261123_0013"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE item RENAME COLUMN korean TO target_text")
    op.execute("ALTER TABLE item RENAME COLUMN english TO gloss")
    op.execute("ALTER TABLE item RENAME COLUMN romanization TO transliteration")
    op.create_index("ix_item_target_text", "item", ["target_text"])

    op.drop_index("ix_phrase_english_text", table_name="phrase")
    op.drop_column("phrase", "english_text")
    op.drop_column("phrase", "korean_text")
    op.create_index("ix_phrase_target_text", "phrase", ["target_text"])


def downgrade():
    op.drop_index("ix_phrase_target_text", table_name="phrase")
    op.add_column(
        "phrase",
        sa.Column(
            "english_text",
            sa.String(length=500),
            nullable=False,
            server_default="",
        ),
    )
    op.add_column(
        "phrase",
        sa.Column(
            "korean_text",
            sa.String(length=500),
            nullable=False,
            server_default="",
        ),
    )
    op.execute(
        "UPDATE phrase SET english_text = COALESCE(source_text, ''), "
        "korean_text = COALESCE(target_text, '')"
    )
    op.create_index("ix_phrase_english_text", "phrase", ["english_text"])

    op.drop_index("ix_item_target_text", table_name="item")
    op.execute("ALTER TABLE item RENAME COLUMN target_text TO korean")
    op.execute("ALTER TABLE item RENAME COLUMN gloss TO english")
    op.execute("ALTER TABLE item RENAME COLUMN transliteration TO romanization")
