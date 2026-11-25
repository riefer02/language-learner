"""Language-core schema, backfill, and downgrade coverage."""

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Item, User
from app.models_language import (
    ItemForm,
    ItemGloss,
    Language,
    LanguageScript,
    Script,
    TermCard,
)

ROOT = Path(__file__).resolve().parents[1]
LEGACY_REVISION = "20261019_0010"


def _flask(db_path, *args):
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{db_path}"
    env["FLASK_APP"] = "run.py"
    env["FLASK_ENV"] = "development"
    result = subprocess.run(
        [sys.executable, "-m", "flask", *args],
        cwd=ROOT,
        check=False,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"flask {' '.join(args)} failed:\n{result.stdout}\n{result.stderr}"
        )
    return result


def test_language_tables_are_registered(app):
    with app.app_context():
        tables = set(inspect(db.engine).get_table_names())

    assert {
        "language",
        "script",
        "language_script",
        "level_scale",
        "course",
        "deck",
        "deck_item",
        "item_form",
        "item_gloss",
        "dictionary_entry",
        "dictionary_sense",
        "translation",
        "term_card",
    } <= tables


def test_item_forms_and_glosses_carry_language_and_script(app):
    with app.app_context():
        korean = Language(code="ko", name="Korean", native_name="한국어")
        english = Language(code="en", name="English", native_name="English")
        hangul = Script(
            code="hangul",
            name="Hangul",
            script_type="alphabet",
            composition="block",
        )
        db.session.add_all([korean, english, hangul])
        db.session.flush()
        db.session.add(
            LanguageScript(
                language_id=korean.id, script_id=hangul.id, is_default=True
            )
        )

        item = Item(
            item_type="lexeme",
            target_text="커피",
            gloss="coffee",
            level=1,
            language_id=korean.id,
            key_normalized="커피",
        )
        db.session.add(item)
        db.session.flush()
        db.session.add(
            ItemForm(
                item_id=item.id,
                script_id=hangul.id,
                text="커피",
                normalized_text="커피",
                transliteration="keopi",
                transliteration_scheme="rr",
                is_primary=True,
            )
        )
        db.session.add(
            ItemGloss(item_id=item.id, lang="en", text="coffee", is_primary=True)
        )
        db.session.commit()

        reloaded = db.session.get(Item, item.id)
        assert reloaded.language_id == korean.id
        assert [form.text for form in reloaded.forms] == ["커피"]
        assert reloaded.forms[0].script.code == "hangul"
        assert reloaded.forms[0].transliteration_scheme == "rr"
        assert [gloss.text for gloss in reloaded.glosses] == ["coffee"]
        # Phase 1 must not change the legacy serialization contract.
        assert reloaded.to_dict()["target_text"] == "커피"


def test_term_card_is_unique_per_user_and_item(app):
    with app.app_context():
        language = Language(code="ko", name="Korean", native_name="한국어")
        db.session.add(language)
        db.session.flush()
        user = User(display_name="Learner", is_local=False)
        item = Item(
            item_type="lexeme",
            target_text="커피",
            gloss="coffee",
            level=1,
            language_id=language.id,
        )
        db.session.add_all([user, item])
        db.session.flush()

        db.session.add(
            TermCard(
                user_id=user.id,
                language_id=language.id,
                item_id=item.id,
                source="teacher",
                context_sentence="커피 한 잔 주세요.",
            )
        )
        db.session.commit()

        db.session.add(
            TermCard(user_id=user.id, language_id=language.id, item_id=item.id)
        )
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()


def test_language_audit_cli_reports_unbackfilled_content(app, runner):
    with app.app_context():
        db.session.add(
            Item(item_type="lexeme", target_text="물", gloss="water", level=1)
        )
        db.session.commit()

    result = runner.invoke(args=["language-audit"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["items"] == 1
    assert payload["items_untagged"] == 1
    assert payload["items_without_primary_form"] == 1


def test_flask_db_command_is_registered(app):
    """Do not rely only on Flask-Migrate's entry point; it can be missed."""
    assert "db" in app.cli.commands


def test_legacy_database_backfills_and_downgrades(tmp_path):
    db_path = tmp_path / "legacy.db"
    _flask(db_path, "db", "upgrade", LEGACY_REVISION)

    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            "INSERT INTO user (display_name, is_local, created_at) "
            "VALUES ('Learner', 1, CURRENT_TIMESTAMP)"
        )
        connection.execute(
            "INSERT INTO item "
            "(item_type, korean, english, romanization, level, audio_path, "
            "default_skill, created_at) "
            "VALUES ('lexeme', '커피', 'coffee', 'keopi', 1, 'coffee.mp3', "
            "'recognize', CURRENT_TIMESTAMP)"
        )
        connection.execute(
            "INSERT INTO phrase "
            "(uuid, english_text, korean_text, audio_path, created_at) "
            "VALUES ('legacy-1', 'coffee', '커피', 'coffee.mp3', CURRENT_TIMESTAMP)"
        )
        # Rows that reference ``phrase`` / ``item`` with foreign keys on. These
        # are what made an earlier batch-table migration fail only on real data.
        connection.execute(
            "INSERT INTO conversation "
            "(title, description, audio_path, created_at) "
            "VALUES ('Legacy', 'A legacy conversation', 'conv.mp3', CURRENT_TIMESTAMP)"
        )
        connection.execute(
            "INSERT INTO conversation_line "
            "(conversation_id, phrase_id, speaker, \"order\") "
            "VALUES (1, 1, 'Speaker 1', 1)"
        )
        connection.execute(
            "INSERT INTO review_card "
            "(user_id, item_id, skill, state, step, stability, difficulty, "
            "due_at, reps, lapses, version) "
            "VALUES (1, 1, 'recognize', 1, 0, 1.0, 1.0, CURRENT_TIMESTAMP, 0, 0, 1)"
        )
        connection.commit()
    finally:
        connection.close()

    _flask(db_path, "db", "upgrade", "head")

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        korean_id = connection.execute(
            "SELECT id FROM language WHERE code = 'ko'"
        ).fetchone()["id"]
        item = connection.execute("SELECT * FROM item").fetchone()
        form = connection.execute("SELECT * FROM item_form").fetchone()
        gloss = connection.execute("SELECT * FROM item_gloss").fetchone()
        phrase = connection.execute("SELECT * FROM phrase").fetchone()
        deck_item = connection.execute("SELECT * FROM deck_item").fetchone()

        assert item["language_id"] == korean_id
        item_columns = set(item.keys())
        assert "review_status" in item_columns
        assert (
            connection.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'table' AND name = 'content_report'"
            ).fetchone()
            is not None
        )
        assert item["key_normalized"] == "커피"
        assert form["text"] == "커피"
        assert form["normalized_text"] == "커피"
        assert form["transliteration"] == "keopi"
        assert form["transliteration_scheme"] == "rr"
        assert form["is_primary"] == 1
        assert gloss["lang"] == "en"
        assert gloss["text"] == "coffee"
        assert deck_item["item_id"] == item["id"]
        assert phrase["source_text"] == "coffee"
        assert phrase["target_text"] == "커피"
        assert "target_transliteration" in set(phrase.keys())
        assert "addressee" in set(phrase.keys())
        assert "register" in set(phrase.keys())
        assert phrase["target_language_id"] == korean_id
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        connection.close()

    _flask(db_path, "db", "downgrade", LEGACY_REVISION)

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        tables = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        assert "item_form" not in tables
        assert "language" not in tables
        assert "content_report" not in tables
        item = connection.execute("SELECT * FROM item").fetchone()
        phrase = connection.execute("SELECT * FROM phrase").fetchone()
        assert item["korean"] == "커피"
        assert item["english"] == "coffee"
        assert "language_id" not in item
        assert "review_status" not in set(item.keys())
        assert phrase["korean_text"] == "커피"
        assert "target_transliteration" not in set(phrase.keys())
        assert "addressee" not in set(phrase.keys())
        assert "register" not in set(phrase.keys())
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        connection.close()
