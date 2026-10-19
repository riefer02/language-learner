"""Seed-audio generation CLI coverage."""

import os

from app import db
from app.models import Item


def _make_item(korean="안녕하세요", english="hello"):
    return Item(
        item_type="chunk",
        korean=korean,
        english=english,
        level=1,
        default_skill="produce",
    )


def test_generate_item_audio_writes_file_and_updates_item(app, runner):
    with app.app_context():
        item = _make_item()
        db.session.add(item)
        db.session.commit()
        item_id = item.id

    result = runner.invoke(args=["generate-item-audio"])

    assert result.exit_code == 0
    assert "Generated audio for 1 item" in result.output
    with app.app_context():
        item = db.session.get(Item, item_id)
        assert item.audio_path.startswith("/static/audio/item_")
        filename = item.audio_path.rsplit("/", 1)[-1]
        assert os.path.exists(os.path.join(app.config["AUDIO_DIR"], filename))


def test_generate_item_audio_dry_run_does_not_write(app, runner):
    with app.app_context():
        item = _make_item("감사합니다", "thank you")
        db.session.add(item)
        db.session.commit()
        item_id = item.id

    result = runner.invoke(args=["generate-item-audio", "--dry-run"])

    assert result.exit_code == 0
    assert "Dry run" in result.output
    with app.app_context():
        assert db.session.get(Item, item_id).audio_path is None
    assert os.listdir(app.config["AUDIO_DIR"]) == []


def test_generate_item_audio_is_idempotent(app, runner):
    with app.app_context():
        db.session.add(_make_item())
        db.session.commit()

    first = runner.invoke(args=["generate-item-audio"])
    second = runner.invoke(args=["generate-item-audio"])

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert "No items need audio" in second.output
