"""Amharic starter pack, fidel bootcamp, and language-scoped review."""

from app import db
from app.languages.am_content import AMHARIC_ITEMS
from app.languages.seed import seed_amharic
from app.learning.service import (
    available_cards,
    current_language,
    get_or_create_local_user,
    stats,
)
from app.models import Item
from app.models_language import ItemForm, ItemGloss, Language


def test_seed_amharic_creates_items_forms_glosses_and_cards(app):
    with app.app_context():
        result = seed_amharic()
        language = Language.query.filter_by(code="am").one()
        assert language.is_active is True
        assert result["total_items"] >= len(AMHARIC_ITEMS)
        assert Item.query.filter_by(language_id=language.id).count() >= len(
            AMHARIC_ITEMS
        )
        assert ItemForm.query.count() >= len(AMHARIC_ITEMS)
        assert ItemGloss.query.filter_by(lang="en").count() >= len(AMHARIC_ITEMS)
        # Re-running is idempotent.
        again = seed_amharic()
        assert again["created_items"] == 0


def test_review_queue_is_scoped_to_the_active_language(app):
    with app.app_context():
        seed_amharic()
        user = get_or_create_local_user()
        amharic = Language.query.filter_by(code="am").one()
        user.target_language_id = amharic.id
        db.session.commit()

        assert current_language(user).code == "am"
        cards = available_cards(user.id, language_id=amharic.id)
        assert cards
        assert all(card.item.language_id == amharic.id for card in cards)
        summary = stats(user.id, language_id=amharic.id)
        assert summary["total_items"] == Item.query.filter_by(
            language_id=amharic.id
        ).count()


def test_fidel_pages_render(client):
    index = client.get("/ko/learn/fidel")
    assert index.status_code == 200
    assert b"Read Amharic" in index.data

    lesson = client.get("/ko/learn/fidel/fidel-1")
    assert lesson.status_code == 200
    assert b"Meet the fidel" in lesson.data
    assert b'id="fidel-data"' in lesson.data


def test_settings_switches_target_language(app, client):
    with app.app_context():
        seed_amharic()
        language = Language.query.filter_by(code="am").one()
        language_id = language.id

    response = client.post(
        "/ko/settings",
        data={
            "language": "am",
            "goal": "everyday",
            "daily_minutes": "10",
            "experience": "new",
            "timezone": "UTC",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302

    with app.app_context():
        user = get_or_create_local_user()
        assert user.target_language_id == language_id


def test_korean_only_pages_redirect_for_amharic(app, client):
    from app.learning.service import get_or_create_local_user

    with app.app_context():
        seed_amharic()
        user = get_or_create_local_user()
        amharic = Language.query.filter_by(code="am").one()
        user.target_language_id = amharic.id
        db.session.commit()

    scenes = client.get("/ko/learn/scenes")
    assert scenes.status_code == 302
    assert scenes.headers["Location"].endswith("/ko/learn/")

    conversations = client.get("/ko/conversations/new")
    assert conversations.status_code == 302


def test_amharic_url_prefix_is_explicit(app, client):
    with app.app_context():
        seed_amharic()

    page = client.get("/am/learn")
    assert page.status_code == 200
    assert b"Today" in page.data
    assert b"Amharic" in page.data

    fidel = client.get("/am/learn/fidel")
    assert fidel.status_code == 200
    assert b"Read Amharic" in fidel.data


def test_legacy_learn_url_redirects_to_ko(client):
    response = client.get("/learn")
    assert response.status_code == 301
    assert response.headers["Location"].endswith("/ko/learn")


def test_fidel_drills_use_the_full_syllable(app):
    from app.languages.am_content import fidel_lessons

    first = fidel_lessons()[0]["drills"][0]
    assert first["glyph"] == "ሀ"
    assert first["roman"] == "hä"


def test_amharic_settings_hide_topik(app, client):
    with app.app_context():
        seed_amharic()

    page = client.get("/am/settings")
    assert page.status_code == 200
    assert b"TOPIK" not in page.data
    assert b"Everyday language" in page.data


def test_fidel_page_explains_the_grid(client):
    page = client.get("/am/learn/fidel/fidel-1")
    assert page.status_code == 200
    assert b"How to read the fidel grid" in page.data
    assert b'id="fidel-bar"' in page.data


def test_header_language_switch_updates_target(app, client):
    with app.app_context():
        seed_amharic()
        korean = Language.query.filter_by(code="ko").first()
        user = get_or_create_local_user()
        user.target_language_id = korean.id if korean else None
        db.session.commit()
        amharic_id = Language.query.filter_by(code="am").one().id

    response = client.post("/language", data={"code": "am"})
    assert response.status_code == 302
    assert "/am/learn" in response.headers["Location"]

    with app.app_context():
        assert get_or_create_local_user().target_language_id == amharic_id
