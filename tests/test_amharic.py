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
    index = client.get("/learn/fidel")
    assert index.status_code == 200
    assert b"Read Amharic" in index.data

    lesson = client.get("/learn/fidel/fidel-1")
    assert lesson.status_code == 200
    assert b"Meet the fidel" in lesson.data
    assert b'data-drills=' in lesson.data


def test_settings_switches_target_language(app, client):
    with app.app_context():
        seed_amharic()
        language = Language.query.filter_by(code="am").one()
        language_id = language.id

    response = client.post(
        "/settings",
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
