"""Stored audio for curated review alternate forms."""

import json
from pathlib import Path

from app.languages.seed import seed_amharic
from app.languages.variants import variant_audio_filename
from app.learning.service import review_variants
from app.models import Item
from app.models_language import Language


def _man_name_card(app):
    language = Language.query.filter_by(code="am").one()
    item = Item.query.filter_by(gloss="What is your name? (to a man)").one()
    return language, item


def test_every_curated_alternate_matches_a_seeded_item(app, client):
    from app.languages.variants import ALTERNATES
    from app.models_language import Language

    client.get("/ko/learn")
    with app.app_context():
        seed_amharic()
        targets = {}
        for language in Language.query.all():
            targets[language.code] = {
                item.target_text
                for item in Item.query.filter_by(language_id=language.id).all()
            }

    for code, groups in ALTERNATES.items():
        assert set(groups) <= targets.get(code, set())


def test_variant_audio_filename_is_stable_and_language_scoped():
    amharic = variant_audio_filename("am", "ስምሽ ማን ነው?")
    assert amharic == variant_audio_filename("am", "ስምሽ ማን ነው?")
    assert amharic.startswith("variant_am_")
    assert amharic.endswith(".mp3")
    assert amharic != variant_audio_filename("ko", "ስምሽ ማን ነው?")


def test_review_variants_use_stored_variant_audio(app, client):
    client.get("/ko/learn")
    with app.app_context():
        seed_amharic()
        _, item = _man_name_card(app)
        filename = variant_audio_filename("am", "ስምሽ ማን ነው?")
        Path(app.config["AUDIO_DIR"], filename).write_bytes(b"ID3-audio")

        variants = review_variants(item, "am")

    woman = next(v for v in variants if v["text"] == "ስምሽ ማን ነው?")
    assert woman["audio_path"] == f"/static/audio/{filename}"


def test_variant_audio_endpoint_generates_and_updates_the_item(app, client):
    client.get("/ko/learn")
    with app.app_context():
        seed_amharic()
        _, item = _man_name_card(app)
        item_id = item.id
        text = "ስምሽ ማን ነው?"

    response = client.post(
        "/api/variants/audio?lang=am",
        json={"item_id": item_id, "text": text},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["text"] == text
    assert data["audio_path"].startswith("/static/audio/")
    filename = data["audio_path"].rsplit("/", 1)[-1]
    assert Path(app.config["AUDIO_DIR"], filename).is_file()
    with app.app_context():
        woman = Item.query.filter_by(target_text=text).one()
        assert woman.audio_path == data["audio_path"]


def test_variant_audio_endpoint_rejects_text_outside_the_card(app, client):
    client.get("/ko/learn")
    with app.app_context():
        seed_amharic()
        _, item = _man_name_card(app)
        item_id = item.id

    response = client.post(
        "/api/variants/audio?lang=am",
        json={"item_id": item_id, "text": "not part of this card"},
    )

    assert response.status_code == 400
    assert response.get_json()["error"]


def test_variant_audio_endpoint_is_scoped_to_the_page_language(app, client):
    client.get("/ko/learn")
    with app.app_context():
        seed_amharic()
        korean = Item.query.filter_by(gloss="Hello").one()
        korean_id = korean.id

    response = client.post(
        "/api/variants/audio?lang=am",
        json={"item_id": korean_id, "text": "안녕하세요"},
    )

    assert response.status_code == 404


def test_generate_variant_audio_dry_run_lists_missing_forms(app, runner):
    with app.app_context():
        seed_amharic()

    result = runner.invoke(
        args=["generate-variant-audio", "--language", "am", "--dry-run"]
    )

    assert result.exit_code == 0
    assert "Dry run: would generate" in result.output
    assert "ስምሽ ማን ነው?" in result.output


def test_variant_audio_files_are_not_media_orphans(app, runner):
    text = "እንደምን ነዎት?"
    with app.app_context():
        filename = variant_audio_filename("am", text)
        Path(app.config["AUDIO_DIR"], filename).write_bytes(b"ID3-audio")

    result = runner.invoke(args=["media-audit", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert filename not in payload["orphans"]
