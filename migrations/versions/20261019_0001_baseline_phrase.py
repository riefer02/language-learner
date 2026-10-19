"""Baseline the missing ``phrase`` table and add conversation indexes.

The original repository created ``phrase`` with ``db.create_all()`` while the
first Alembic migration created only the conversation tables. This migration
makes a fresh ``flask db upgrade`` work and is idempotent for existing
databases that already have the table.

Revision ID: 20261019_0001
Revises: afc06f678e70
Create Date: 2026-10-19
"""

import sqlalchemy as sa
from alembic import op

revision = "20261019_0001"
down_revision = "afc06f678e70"
branch_labels = None
depends_on = None


def _table_names(bind):
    return set(sa.inspect(bind).get_table_names())


def _index_names(bind, table):
    return {index["name"] for index in sa.inspect(bind).get_indexes(table)}


def upgrade():
    bind = op.get_bind()
    tables = _table_names(bind)

    if "phrase" not in tables:
        op.create_table(
            "phrase",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=True),
            sa.Column("english_text", sa.String(length=500), nullable=False),
            sa.Column("korean_text", sa.String(length=500), nullable=False),
            sa.Column("audio_path", sa.String(length=255), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
        )
        op.create_index(
            "ix_phrase_english_text", "phrase", ["english_text"], unique=False
        )
        op.create_index(
            "ix_phrase_created_at", "phrase", ["created_at"], unique=False
        )
        op.create_index(
            "ix_phrase_created_id", "phrase", ["created_at", "id"], unique=False
        )

    phrase_indexes = _index_names(bind, "phrase")
    for name, columns in (
        ("ix_phrase_english_text", ["english_text"]),
        ("ix_phrase_created_at", ["created_at"]),
        ("ix_phrase_created_id", ["created_at", "id"]),
    ):
        if name not in phrase_indexes:
            op.create_index(name, "phrase", columns, unique=False)

    line_indexes = _index_names(bind, "conversation_line")
    for name, columns in (
        ("ix_conversation_line_conversation_id", ["conversation_id"]),
        ("ix_conversation_line_phrase_id", ["phrase_id"]),
    ):
        if name not in line_indexes:
            op.create_index(name, "conversation_line", columns, unique=False)

    if "uq_conversation_line_order" not in line_indexes:
        op.create_index(
            "uq_conversation_line_order",
            "conversation_line",
            ["conversation_id", "order"],
            unique=True,
        )


def downgrade():
    bind = op.get_bind()
    line_indexes = _index_names(bind, "conversation_line")
    for name in (
        "uq_conversation_line_order",
        "ix_conversation_line_phrase_id",
        "ix_conversation_line_conversation_id",
    ):
        if name in line_indexes:
            op.drop_index(name, table_name="conversation_line")

    phrase_indexes = _index_names(bind, "phrase")
    for name in ("ix_phrase_created_id",):
        if name in phrase_indexes:
            op.drop_index(name, table_name="phrase")
