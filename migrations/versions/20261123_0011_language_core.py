"""Add language-neutral content, dictionary, and term-library tables.

Revision ID: 20261123_0011
Revises: 20261019_0010
Create Date: 2026-11-23

Expand phase only. No existing column is dropped, renamed, or made NOT NULL,
and no read path changes. The backfill lives in ``20261123_0012``.
"""

import sqlalchemy as sa
from alembic import op

revision = "20261123_0011"
down_revision = "20261019_0010"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "language",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("native_name", sa.String(length=64), nullable=False),
        sa.Column(
            "direction", sa.String(length=3), nullable=False, server_default="ltr"
        ),
        sa.Column("ui_locale", sa.String(length=16), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_language_code", "language", ["code"], unique=True)
    op.create_index("ix_language_is_active", "language", ["is_active"])

    op.create_table(
        "script",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=24), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("script_type", sa.String(length=24), nullable=False),
        sa.Column(
            "direction", sa.String(length=3), nullable=False, server_default="ltr"
        ),
        sa.Column("unicode_ranges", sa.Text(), nullable=True),
        sa.Column(
            "composition",
            sa.String(length=24),
            nullable=False,
            server_default="linear",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_script_code", "script", ["code"], unique=True)

    op.create_table(
        "language_script",
        sa.Column("language_id", sa.Integer(), nullable=False),
        sa.Column("script_id", sa.Integer(), nullable=False),
        sa.Column(
            "role", sa.String(length=24), nullable=False, server_default="primary"
        ),
        sa.Column(
            "is_default", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.ForeignKeyConstraint(
            ["language_id"], ["language.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["script_id"], ["script.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("language_id", "script_id"),
    )

    op.create_table(
        "level_scale",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("language_id", sa.Integer(), nullable=True),
        sa.Column("code", sa.String(length=24), nullable=False),
        sa.Column(
            "is_default", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "min_level", sa.Integer(), nullable=False, server_default="1"
        ),
        sa.Column(
            "max_level", sa.Integer(), nullable=False, server_default="6"
        ),
        sa.Column(
            "labels", sa.Text(), nullable=False, server_default="{}"
        ),
        sa.Column("descriptors", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["language_id"], ["language.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_level_scale_code"),
    )
    op.create_index("ix_level_scale_language_id", "level_scale", ["language_id"])

    op.create_table(
        "course",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("language_id", sa.Integer(), nullable=False),
        sa.Column("level_scale_id", sa.Integer(), nullable=True),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["language_id"], ["language.id"]),
        sa.ForeignKeyConstraint(["level_scale_id"], ["level_scale.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "language_id", "slug", name="uq_course_language_slug"
        ),
    )
    op.create_index("ix_course_language_id", "course", ["language_id"])

    op.create_table(
        "deck",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("language_id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=True),
        sa.Column("owner_id", sa.Integer(), nullable=True),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column(
            "kind", sa.String(length=24), nullable=False, server_default="core"
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["language_id"], ["language.id"]),
        sa.ForeignKeyConstraint(["course_id"], ["course.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_deck_language_id", "deck", ["language_id"])
    op.create_index(
        "uq_deck_system_slug",
        "deck",
        ["language_id", "slug"],
        unique=True,
        sqlite_where=sa.text("owner_id IS NULL"),
        postgresql_where=sa.text("owner_id IS NULL"),
    )
    op.create_index(
        "uq_deck_owner_slug",
        "deck",
        ["owner_id", "language_id", "slug"],
        unique=True,
        sqlite_where=sa.text("owner_id IS NOT NULL"),
        postgresql_where=sa.text("owner_id IS NOT NULL"),
    )

    op.create_table(
        "deck_item",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("deck_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["deck_id"], ["deck.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_id"], ["item.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("deck_id", "item_id", name="uq_deck_item_deck_item"),
    )

    op.create_table(
        "item_form",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("script_id", sa.Integer(), nullable=False),
        sa.Column(
            "form_kind",
            sa.String(length=24),
            nullable=False,
            server_default="citation",
        ),
        sa.Column("text", sa.String(length=500), nullable=False),
        sa.Column("normalized_text", sa.String(length=500), nullable=False),
        sa.Column("transliteration", sa.String(length=500), nullable=True),
        sa.Column("transliteration_scheme", sa.String(length=24), nullable=True),
        sa.Column("ipa", sa.String(length=500), nullable=True),
        sa.Column("audio_path", sa.String(length=255), nullable=True),
        sa.Column(
            "is_primary", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("morphology", sa.Text(), nullable=True),
        sa.Column("morphology_family", sa.String(length=24), nullable=True),
        sa.Column("form_group", sa.String(length=80), nullable=True),
        sa.Column("form_condition", sa.String(length=80), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["item_id"], ["item.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["script_id"], ["script.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_item_form_item", "item_form", ["item_id"])
    op.create_index("ix_item_form_script", "item_form", ["script_id"])
    op.create_index(
        "uq_item_form_text",
        "item_form",
        ["item_id", "form_kind", "normalized_text"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "item_gloss",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("lang", sa.String(length=16), nullable=False, server_default="en"),
        sa.Column("text", sa.String(length=500), nullable=False),
        sa.Column(
            "gloss_type",
            sa.String(length=24),
            nullable=False,
            server_default="translation",
        ),
        sa.Column(
            "is_primary", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["item.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_item_gloss_item", "item_gloss", ["item_id"])
    op.create_index("ix_item_gloss_lang", "item_gloss", ["lang"])

    op.create_table(
        "dictionary_entry",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("language_id", sa.Integer(), nullable=False),
        sa.Column("lemma_item_id", sa.Integer(), nullable=True),
        sa.Column("headword", sa.String(length=300), nullable=False),
        sa.Column("normalized_headword", sa.String(length=300), nullable=False),
        sa.Column("pos", sa.String(length=24), nullable=False),
        sa.Column("gender_class", sa.String(length=24), nullable=True),
        sa.Column("register", sa.String(length=24), nullable=True),
        sa.Column("frequency_rank", sa.Integer(), nullable=True),
        sa.Column("etymology", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default="published",
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["language_id"], ["language.id"]),
        sa.ForeignKeyConstraint(["lemma_item_id"], ["item.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_dictionary_entry_language_id", "dictionary_entry", ["language_id"]
    )
    op.create_index(
        "uq_dictionary_entry_headword",
        "dictionary_entry",
        ["language_id", "normalized_headword", "pos"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "dictionary_sense",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("entry_id", sa.Integer(), nullable=False),
        sa.Column("sense_order", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "gloss_lang", sa.String(length=16), nullable=False, server_default="en"
        ),
        sa.Column("gloss", sa.String(length=300), nullable=False),
        sa.Column("definition", sa.Text(), nullable=True),
        sa.Column("example_item_id", sa.Integer(), nullable=True),
        sa.Column("register", sa.String(length=24), nullable=True),
        sa.Column("domain", sa.String(length=60), nullable=True),
        sa.ForeignKeyConstraint(
            ["entry_id"], ["dictionary_entry.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["example_item_id"], ["item.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "entry_id",
            "sense_order",
            "gloss_lang",
            name="uq_dictionary_sense_order",
        ),
    )
    op.create_index("ix_dictionary_sense_entry", "dictionary_sense", ["entry_id"])

    op.create_table(
        "translation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_language_id", sa.Integer(), nullable=False),
        sa.Column("target_language_id", sa.Integer(), nullable=False),
        sa.Column("sense_id", sa.Integer(), nullable=True),
        sa.Column("source_item_id", sa.Integer(), nullable=True),
        sa.Column("target_item_id", sa.Integer(), nullable=True),
        sa.Column("source_text_hash", sa.String(length=64), nullable=False),
        sa.Column("source_text", sa.String(length=500), nullable=False),
        sa.Column("target_text", sa.String(length=500), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=True),
        sa.Column("model", sa.String(length=80), nullable=True),
        sa.Column("quality", sa.String(length=16), nullable=True),
        sa.Column(
            "is_human_reviewed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_language_id"], ["language.id"]
        ),
        sa.ForeignKeyConstraint(
            ["target_language_id"], ["language.id"]
        ),
        sa.ForeignKeyConstraint(["sense_id"], ["dictionary_sense.id"]),
        sa.ForeignKeyConstraint(["source_item_id"], ["item.id"]),
        sa.ForeignKeyConstraint(["target_item_id"], ["item.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_translation_lookup",
        "translation",
        ["source_language_id", "target_language_id", "source_text_hash"],
    )

    op.create_table(
        "term_card",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("language_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=True),
        sa.Column("dictionary_entry_id", sa.Integer(), nullable=True),
        sa.Column(
            "source", sa.String(length=24), nullable=False, server_default="manual"
        ),
        sa.Column("context_sentence", sa.Text(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("tags", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["language_id"], ["language.id"]),
        sa.ForeignKeyConstraint(["item_id"], ["item.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["dictionary_entry_id"], ["dictionary_entry.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_term_card_created_at", "term_card", ["created_at"])
    op.create_index(
        "ix_term_card_user_language", "term_card", ["user_id", "language_id"]
    )
    op.create_index(
        "uq_term_card_user_item",
        "term_card",
        ["user_id", "item_id"],
        unique=True,
        sqlite_where=sa.text("item_id IS NOT NULL"),
        postgresql_where=sa.text("item_id IS NOT NULL"),
    )
    op.create_index(
        "uq_term_card_user_entry",
        "term_card",
        ["user_id", "dictionary_entry_id"],
        unique=True,
        sqlite_where=sa.text("dictionary_entry_id IS NOT NULL"),
        postgresql_where=sa.text("dictionary_entry_id IS NOT NULL"),
    )

    # --- Expand-phase columns on existing tables -------------------------
    # Deliberately plain ADD COLUMN: no table rebuild and no new foreign key
    # constraints. SQLite blocks a batch rebuild of ``phrase`` / ``item`` while
    # existing rows reference them with foreign_keys=ON. These columns are
    # nullable and unused until the dual-write phase; constraints arrive with
    # the contract migration.
    op.add_column(
        "phrase", sa.Column("source_language_id", sa.Integer(), nullable=True)
    )
    op.add_column(
        "phrase", sa.Column("target_language_id", sa.Integer(), nullable=True)
    )
    op.add_column(
        "phrase", sa.Column("source_text", sa.String(length=500), nullable=True)
    )
    op.add_column(
        "phrase", sa.Column("target_text", sa.String(length=500), nullable=True)
    )

    op.add_column(
        "conversation", sa.Column("language_id", sa.Integer(), nullable=True)
    )
    op.create_index("ix_conversation_language_id", "conversation", ["language_id"])

    op.add_column(
        "user", sa.Column("target_language_id", sa.Integer(), nullable=True)
    )
    op.add_column("user", sa.Column("ui_locale", sa.String(length=16), nullable=True))

    op.add_column("item", sa.Column("language_id", sa.Integer(), nullable=True))
    op.add_column("item", sa.Column("primary_deck_id", sa.Integer(), nullable=True))
    op.add_column(
        "item", sa.Column("dictionary_entry_id", sa.Integer(), nullable=True)
    )
    op.add_column("item", sa.Column("level_scale_id", sa.Integer(), nullable=True))
    op.add_column(
        "item",
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default="published",
        ),
    )
    op.add_column(
        "item", sa.Column("key_normalized", sa.String(length=300), nullable=True)
    )
    op.add_column(
        "item",
        sa.Column(
            "sense_key", sa.String(length=300), nullable=False, server_default=""
        ),
    )
    op.add_column(
        "item", sa.Column("content_hash", sa.String(length=64), nullable=True)
    )
    op.add_column(
        "item",
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "item", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("item", sa.Column("superseded_by_id", sa.Integer(), nullable=True))
    op.create_index("ix_item_language_id", "item", ["language_id"])
    op.create_index(
        "ix_item_language_level_type", "item", ["language_id", "level", "item_type"]
    )

    op.add_column(
        "speech_attempt", sa.Column("language_id", sa.Integer(), nullable=True)
    )
    op.add_column(
        "speech_attempt", sa.Column("item_form_id", sa.Integer(), nullable=True)
    )
    op.add_column(
        "speech_attempt", sa.Column("overall_score", sa.Float(), nullable=True)
    )
    op.add_column(
        "speech_attempt", sa.Column("phoneme_scores", sa.Text(), nullable=True)
    )
    op.add_column(
        "speech_attempt", sa.Column("prosody_scores", sa.Text(), nullable=True)
    )
    op.add_column(
        "speech_attempt",
        sa.Column("scoring_version", sa.String(length=24), nullable=True),
    )
    op.create_index(
        "ix_speech_attempt_language_id", "speech_attempt", ["language_id"]
    )

    op.add_column(
        "scene_session", sa.Column("language_id", sa.Integer(), nullable=True)
    )
    op.create_index(
        "ix_scene_session_language_id", "scene_session", ["language_id"]
    )

    op.add_column(
        "can_do_artifact", sa.Column("language_id", sa.Integer(), nullable=True)
    )
    op.create_index(
        "ix_can_do_artifact_language_id", "can_do_artifact", ["language_id"]
    )

    op.add_column("event", sa.Column("language_id", sa.Integer(), nullable=True))
    op.create_index("ix_event_language_id", "event", ["language_id"])


def downgrade():
    op.drop_index("ix_event_language_id", table_name="event")
    op.drop_column("event", "language_id")

    op.drop_index("ix_can_do_artifact_language_id", table_name="can_do_artifact")
    op.drop_column("can_do_artifact", "language_id")

    op.drop_index("ix_scene_session_language_id", table_name="scene_session")
    op.drop_column("scene_session", "language_id")

    op.drop_index("ix_speech_attempt_language_id", table_name="speech_attempt")
    for column in (
        "scoring_version",
        "prosody_scores",
        "phoneme_scores",
        "overall_score",
        "item_form_id",
        "language_id",
    ):
        op.drop_column("speech_attempt", column)

    op.drop_index("ix_item_language_level_type", table_name="item")
    op.drop_index("ix_item_language_id", table_name="item")
    for column in (
        "superseded_by_id",
        "deleted_at",
        "version",
        "content_hash",
        "sense_key",
        "key_normalized",
        "status",
        "level_scale_id",
        "dictionary_entry_id",
        "primary_deck_id",
        "language_id",
    ):
        op.drop_column("item", column)

    op.drop_column("user", "ui_locale")
    op.drop_column("user", "target_language_id")

    op.drop_index("ix_conversation_language_id", table_name="conversation")
    op.drop_column("conversation", "language_id")

    for column in (
        "target_text",
        "source_text",
        "target_language_id",
        "source_language_id",
    ):
        op.drop_column("phrase", column)

    op.drop_index("uq_term_card_user_entry", table_name="term_card")
    op.drop_index("uq_term_card_user_item", table_name="term_card")
    op.drop_index("ix_term_card_user_language", table_name="term_card")
    op.drop_index("ix_term_card_created_at", table_name="term_card")
    op.drop_table("term_card")

    op.drop_index("ix_translation_lookup", table_name="translation")
    op.drop_table("translation")

    op.drop_index("ix_dictionary_sense_entry", table_name="dictionary_sense")
    op.drop_table("dictionary_sense")

    op.drop_index("uq_dictionary_entry_headword", table_name="dictionary_entry")
    op.drop_index("ix_dictionary_entry_language_id", table_name="dictionary_entry")
    op.drop_table("dictionary_entry")

    op.drop_index("ix_item_gloss_lang", table_name="item_gloss")
    op.drop_index("ix_item_gloss_item", table_name="item_gloss")
    op.drop_table("item_gloss")

    op.drop_index("uq_item_form_text", table_name="item_form")
    op.drop_index("ix_item_form_script", table_name="item_form")
    op.drop_index("ix_item_form_item", table_name="item_form")
    op.drop_table("item_form")

    op.drop_table("deck_item")

    op.drop_index("uq_deck_owner_slug", table_name="deck")
    op.drop_index("uq_deck_system_slug", table_name="deck")
    op.drop_index("ix_deck_language_id", table_name="deck")
    op.drop_table("deck")

    op.drop_index("ix_course_language_id", table_name="course")
    op.drop_table("course")

    op.drop_index("ix_level_scale_language_id", table_name="level_scale")
    op.drop_table("level_scale")

    op.drop_table("language_script")

    op.drop_index("ix_script_code", table_name="script")
    op.drop_table("script")

    op.drop_index("ix_language_is_active", table_name="language")
    op.drop_index("ix_language_code", table_name="language")
    op.drop_table("language")
