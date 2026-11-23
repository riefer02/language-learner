"""Backfill the language core from the Korean-shaped legacy columns.

Revision ID: 20261123_0012
Revises: 20261123_0011
Create Date: 2026-11-23

This migration is data-preserving and idempotent for the content tables: every
existing row is tagged ``ko`` and copied into ``item_form`` / ``item_gloss``.
Legacy columns are left untouched and remain the read/write path.
"""

import sqlalchemy as sa
from alembic import op

revision = "20261123_0012"
down_revision = "20261123_0011"
branch_labels = None
depends_on = None

LANGUAGES = [
    # code, name, native_name, is_active
    ("ko", "Korean", "한국어", 1),
    ("en", "English", "English", 1),
    ("am", "Amharic", "አማርኛ", 0),
    ("es", "Spanish", "Español", 0),
    ("ja", "Japanese", "日本語", 0),
]

SCRIPTS = [
    # code, name, script_type, composition, ranges
    (
        "hangul",
        "Hangul",
        "alphabet",
        "block",
        "[[44032,55203],[4352,4607],[12592,12687]]",
    ),
    ("geez", "Ge'ez (Fidel)", "abugida", "abugida", "[[4608,4991],[4992,5023]]"),
    ("latin", "Latin", "alphabet", "linear", "[[65,90],[97,122],[192,591]]"),
    ("kana", "Kana", "syllabary", "linear", "[[12352,12447],[12448,12543]]"),
    ("han", "Han", "logosyllabic", "linear", "[[19968,40959],[13312,19903]]"),
]


def _id(bind, table, code):
    return bind.execute(
        sa.text(f"SELECT id FROM {table} WHERE code = :code"), {"code": code}
    ).scalar_one()


def upgrade():
    bind = op.get_bind()

    for code, name, native, active in LANGUAGES:
        bind.execute(
            sa.text(
                "INSERT INTO language "
                "(code, name, native_name, direction, is_active, created_at, updated_at) "
                "VALUES (:code, :name, :native, 'ltr', :active, "
                "CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            ),
            {"code": code, "name": name, "native": native, "active": active},
        )

    for code, name, script_type, composition, ranges in SCRIPTS:
        bind.execute(
            sa.text(
                "INSERT INTO script "
                "(code, name, script_type, direction, composition, unicode_ranges, "
                "created_at) VALUES (:code, :name, :type, 'ltr', :composition, "
                ":ranges, CURRENT_TIMESTAMP)"
            ),
            {
                "code": code,
                "name": name,
                "type": script_type,
                "composition": composition,
                "ranges": ranges,
            },
        )

    language_ids = {
        code: _id(bind, "language", code) for code, *_rest in LANGUAGES
    }
    script_ids = {code: _id(bind, "script", code) for code, *_rest in SCRIPTS}

    for language_code, script_code, role, is_default in (
        ("ko", "hangul", "primary", 1),
        ("en", "latin", "primary", 1),
        ("am", "geez", "primary", 1),
        ("es", "latin", "primary", 1),
        ("ja", "kana", "primary", 1),
        ("ja", "han", "auxiliary", 0),
        ("ja", "latin", "auxiliary", 0),
    ):
        bind.execute(
            sa.text(
                "INSERT INTO language_script "
                "(language_id, script_id, role, is_default) "
                "VALUES (:language_id, :script_id, :role, :is_default)"
            ),
            {
                "language_id": language_ids[language_code],
                "script_id": script_ids[script_code],
                "role": role,
                "is_default": is_default,
            },
        )

    bind.execute(
        sa.text(
            "INSERT INTO level_scale "
            "(language_id, code, is_default, min_level, max_level, labels) "
            "VALUES (:language_id, 'topik', 1, 1, 6, :labels)"
        ),
        {
            "language_id": language_ids["ko"],
            "labels": (
                '{"1":"TOPIK 1","2":"TOPIK 2","3":"TOPIK 3",'
                '"4":"TOPIK 4","5":"TOPIK 5","6":"TOPIK 6"}'
            ),
        },
    )
    bind.execute(
        sa.text(
            "INSERT INTO level_scale "
            "(language_id, code, is_default, min_level, max_level, labels) "
            "VALUES (NULL, 'cefr', 0, 1, 6, :labels)"
        ),
        {
            "labels": (
                '{"1":"A1","2":"A2","3":"B1",'
                '"4":"B2","5":"C1","6":"C2"}'
            )
        },
    )

    topik_id = bind.execute(
        sa.text("SELECT id FROM level_scale WHERE code = 'topik'")
    ).scalar_one()
    bind.execute(
        sa.text(
            "INSERT INTO course "
            "(language_id, level_scale_id, slug, title, description, is_active, "
            "created_at) VALUES (:language_id, :level_scale_id, 'korean-core', "
            "'Korean Core', 'The existing Kiku Korean curriculum.', 1, "
            "CURRENT_TIMESTAMP)"
        ),
        {"language_id": language_ids["ko"], "level_scale_id": topik_id},
    )
    course_id = bind.execute(
        sa.text("SELECT id FROM course WHERE slug = 'korean-core'")
    ).scalar_one()
    bind.execute(
        sa.text(
            "INSERT INTO deck "
            "(language_id, course_id, slug, title, kind, version, created_at) "
            "VALUES (:language_id, :course_id, 'ko-core', 'Korean Core Deck', "
            "'core', 1, CURRENT_TIMESTAMP)"
        ),
        {"language_id": language_ids["ko"], "course_id": course_id},
    )
    deck_id = bind.execute(
        sa.text("SELECT id FROM deck WHERE slug = 'ko-core'")
    ).scalar_one()

    ko_id = language_ids["ko"]
    hangul_id = script_ids["hangul"]

    bind.execute(
        sa.text(
            "UPDATE item SET language_id = :ko, status = 'published', "
            "key_normalized = korean, sense_key = '' WHERE language_id IS NULL"
        ),
        {"ko": ko_id},
    )

    # Copy target-language forms and glosses. NOT EXISTS keeps this safe to
    # re-run after a partial failure on databases without transactional DDL.
    bind.execute(
        sa.text(
            "INSERT INTO item_form "
            "(item_id, script_id, form_kind, text, normalized_text, "
            "transliteration, transliteration_scheme, audio_path, is_primary, "
            "version, created_at) "
            "SELECT i.id, :hangul, 'citation', i.korean, i.korean, "
            "i.romanization, CASE WHEN i.romanization IS NULL THEN NULL ELSE 'rr' END, "
            "i.audio_path, 1, 1, CURRENT_TIMESTAMP "
            "FROM item i WHERE i.language_id = :ko AND NOT EXISTS ("
            "SELECT 1 FROM item_form f WHERE f.item_id = i.id "
            "AND f.form_kind = 'citation')"
        ),
        {"hangul": hangul_id, "ko": ko_id},
    )
    bind.execute(
        sa.text(
            "INSERT INTO item_gloss "
            "(item_id, lang, text, gloss_type, is_primary, version, created_at) "
            "SELECT i.id, 'en', i.english, 'translation', 1, 1, CURRENT_TIMESTAMP "
            "FROM item i WHERE i.language_id = :ko AND NOT EXISTS ("
            "SELECT 1 FROM item_gloss g WHERE g.item_id = i.id "
            "AND g.lang = 'en' AND g.gloss_type = 'translation')"
        ),
        {"ko": ko_id},
    )

    # Assign every legacy item to the core deck once.
    bind.execute(
        sa.text(
            "INSERT INTO deck_item (deck_id, item_id, position, added_at) "
            "SELECT :deck_id, i.id, i.id, CURRENT_TIMESTAMP FROM item i "
            "WHERE i.language_id = :ko AND NOT EXISTS ("
            "SELECT 1 FROM deck_item d WHERE d.deck_id = :deck_id "
            "AND d.item_id = i.id)"
        ),
        {"deck_id": deck_id, "ko": ko_id},
    )

    bind.execute(
        sa.text(
            "UPDATE phrase SET source_language_id = :en, "
            "target_language_id = :ko, source_text = english_text, "
            "target_text = korean_text "
            "WHERE source_language_id IS NULL OR target_language_id IS NULL"
        ),
        {"en": language_ids["en"], "ko": ko_id},
    )
    bind.execute(
        sa.text("UPDATE conversation SET language_id = :ko WHERE language_id IS NULL"),
        {"ko": ko_id},
    )
    bind.execute(
        sa.text(
            "UPDATE user SET target_language_id = :ko, ui_locale = 'en' "
            "WHERE target_language_id IS NULL"
        ),
        {"ko": ko_id},
    )
    bind.execute(
        sa.text(
            "UPDATE speech_attempt SET language_id = :ko WHERE language_id IS NULL"
        ),
        {"ko": ko_id},
    )
    bind.execute(
        sa.text(
            "UPDATE scene_session SET language_id = :ko WHERE language_id IS NULL"
        ),
        {"ko": ko_id},
    )
    bind.execute(
        sa.text(
            "UPDATE can_do_artifact SET language_id = :ko WHERE language_id IS NULL"
        ),
        {"ko": ko_id},
    )
    bind.execute(
        sa.text("UPDATE event SET language_id = :ko WHERE language_id IS NULL"),
        {"ko": ko_id},
    )


def downgrade():
    bind = op.get_bind()

    bind.execute(sa.text("UPDATE event SET language_id = NULL"))
    bind.execute(sa.text("UPDATE can_do_artifact SET language_id = NULL"))
    bind.execute(sa.text("UPDATE scene_session SET language_id = NULL"))
    bind.execute(sa.text("UPDATE speech_attempt SET language_id = NULL"))
    bind.execute(sa.text("UPDATE user SET target_language_id = NULL"))
    bind.execute(sa.text("UPDATE conversation SET language_id = NULL"))
    bind.execute(
        sa.text(
            "UPDATE phrase SET source_language_id = NULL, "
            "target_language_id = NULL, source_text = NULL, target_text = NULL"
        )
    )
    bind.execute(sa.text("UPDATE item SET language_id = NULL"))
    bind.execute(sa.text("DELETE FROM deck_item"))
    bind.execute(sa.text("DELETE FROM item_gloss"))
    bind.execute(sa.text("DELETE FROM item_form"))
    bind.execute(sa.text("DELETE FROM deck"))
    bind.execute(sa.text("DELETE FROM course"))
    bind.execute(sa.text("DELETE FROM level_scale"))
    bind.execute(sa.text("DELETE FROM language_script"))
    bind.execute(sa.text("DELETE FROM script"))
    bind.execute(sa.text("DELETE FROM language"))
