"""End-to-end coverage for the first learning loop."""

from datetime import UTC, datetime

from app import db
from app.learning.scheduler import apply_rating, new_review_card
from app.models import Item, ReviewCard, ReviewLog


def test_learn_page_auto_seeds_and_shows_due_cards(client, app):
    response = client.get("/ko/learn")

    assert response.status_code == 200
    assert b"Due now" in response.data
    assert b"Start review" in response.data
    with app.app_context():
        assert Item.query.count() >= 25
        assert ReviewCard.query.count() == Item.query.count()


def test_new_card_daily_cap(client, app):
    response = client.get("/ko/learn")

    assert b'data-due="10"' in response.data

    with app.app_context():
        card_ids = [card.id for card in ReviewCard.query.limit(10).all()]

    for card_id in card_ids:
        client.post(f"/ko/learn/review/{card_id}", data={"rating": "3"})

    response = client.get("/ko/learn")
    assert b"You're caught up" in response.data


def test_progress_page_renders(client, app):
    client.get("/ko/learn")
    response = client.get("/ko/learn/progress")

    assert response.status_code == 200
    assert b"Skill breakdown" in response.data
    assert b"Recent reviews" in response.data


def test_review_page_renders_a_card(client, app):
    client.get("/ko/learn")
    response = client.get("/ko/learn/review")

    assert response.status_code == 200
    assert b"Reveal answer" in response.data
    assert b"grade-form" in response.data
    assert b"review-gradebar" in response.data


def test_rating_updates_card_and_writes_log(client, app):
    client.get("/ko/learn")
    with app.app_context():
        card = ReviewCard.query.order_by(ReviewCard.id.asc()).first()
        card_id = card.id
        original_reps = card.reps

    response = client.post(
        f"/ko/learn/review/{card_id}",
        data={"rating": "3", "elapsed_ms": "1200"},
    )

    assert response.status_code == 302
    with app.app_context():
        card = db.session.get(ReviewCard, card_id)
        assert card.reps == original_reps + 1
        assert card.last_review_at is not None
        assert ReviewLog.query.count() == 1
        log = ReviewLog.query.first()
        assert log.rating == 3
        assert log.elapsed_ms == 1200


def test_review_post_requires_csrf_token_when_enabled(client, app):
    app.config["WTF_CSRF_ENABLED"] = True
    client.get("/ko/learn")
    with app.app_context():
        card_id = ReviewCard.query.first().id

    response = client.post(
        f"/ko/learn/review/{card_id}", data={"rating": "3"}
    )

    assert response.status_code == 400
    with app.app_context():
        assert ReviewLog.query.count() == 0


def test_eleventh_new_card_is_rejected(client, app):
    client.get("/ko/learn")
    with app.app_context():
        card_ids = [card.id for card in ReviewCard.query.limit(11).all()]

    for card_id in card_ids[:10]:
        assert (
            client.post(f"/ko/learn/review/{card_id}", data={"rating": "3"}).status_code
            == 302
        )

    response = client.post(f"/ko/learn/review/{card_ids[10]}", data={"rating": "3"})

    assert response.status_code == 409
    with app.app_context():
        assert ReviewLog.query.count() == 10


def test_card_that_is_not_due_is_rejected(client, app):
    client.get("/ko/learn")
    with app.app_context():
        card_id = ReviewCard.query.first().id

    first = client.post(f"/ko/learn/review/{card_id}", data={"rating": "3"})
    assert first.status_code == 302

    second = client.post(f"/ko/learn/review/{card_id}", data={"rating": "3"})

    assert second.status_code == 409
    with app.app_context():
        assert ReviewLog.query.count() == 1


def test_invalid_rating_is_rejected(client, app):
    client.get("/ko/learn")
    with app.app_context():
        card_id = ReviewCard.query.first().id

    response = client.post(f"/ko/learn/review/{card_id}", data={"rating": "9"})

    assert response.status_code == 400
    with app.app_context():
        assert ReviewLog.query.count() == 0


def test_finishing_all_due_cards_shows_done_page(client, app):
    client.get("/ko/learn")
    with app.app_context():
        card_ids = [card.id for card in ReviewCard.query.all()]
    app.config["NEW_CARDS_PER_DAY"] = len(card_ids)

    for card_id in card_ids:
        response = client.post(
            f"/ko/learn/review/{card_id}", data={"rating": "3"}
        )
        assert response.status_code == 302

    response = client.get("/ko/learn/review")

    assert response.status_code == 200
    assert b"You are caught up" in response.data
    with app.app_context():
        assert ReviewLog.query.count() == len(card_ids)


def test_seed_content_is_idempotent(client, app):
    client.get("/ko/learn")
    with app.app_context():
        first_items = Item.query.count()
        first_cards = ReviewCard.query.count()

    client.get("/ko/learn")
    with app.app_context():
        assert Item.query.count() == first_items
        assert ReviewCard.query.count() == first_cards


def test_fsrs_schedules_good_and_easy_differently(app):
    with app.app_context():
        item = Item.query.first()
        # The seed may not have run in this test; create a minimal item.
        if item is None:
            item = Item(
                item_type="lexeme",
                target_text="테스트",
                gloss="test",
                level=1,
                default_skill="recognize",
            )
            db.session.add(item)
            db.session.commit()

        good = new_review_card(1, item.id, "recognize")
        easy = new_review_card(1, item.id, "recognize")
        now = datetime.now(UTC)

        apply_rating(good, 3, now=now)
        apply_rating(easy, 4, now=now)

        good_due = good.due_at.replace(tzinfo=UTC) if good.due_at.tzinfo is None else good.due_at
        easy_due = easy.due_at.replace(tzinfo=UTC) if easy.due_at.tzinfo is None else easy.due_at
        assert easy_due >= good_due
        assert good_due > now


def test_today_shows_dashboard_help(client):
    response = client.get("/ko/learn")
    assert response.status_code == 200
    assert b"How Kiku works" in response.data
    assert b"due" in response.data


def test_today_shows_my_terms_card(client):
    page = client.get("/ko/learn")
    assert page.status_code == 200
    assert b"My terms" in page.data
    assert b"Open My terms" in page.data


def test_seed_content_tags_korean_items_and_cards(app):
    from app.learning.seed_data import seed_content
    from app.models_language import Language

    with app.app_context():
        seed_content()
        korean = Language.query.filter_by(code="ko").one()
        untagged = Item.query.filter(Item.language_id.is_(None)).count()
        assert untagged == 0
        cards = ReviewCard.query.filter_by(user_id=1).all()
        assert cards
        assert all(card.item.language_id == korean.id for card in cards)


def _handoff_fixture(app, reps=3):
    from app.learning.scheduler import new_review_card
    from app.learning.service import get_or_create_local_user
    from app.models_language import Language

    language = Language.query.filter_by(code="ko").first()
    if language is None:
        language = Language(code="ko", name="Korean", native_name="한국어")
        db.session.add(language)
        db.session.commit()
    item = Item(
        item_type="lexeme",
        target_text="커피",
        gloss="coffee",
        level=1,
        language_id=language.id,
        default_skill="recognize",
    )
    db.session.add(item)
    db.session.commit()
    user = get_or_create_local_user()
    card = new_review_card(user.id, item.id, "recognize")
    card.reps = reps
    db.session.add(card)
    db.session.commit()
    return item, card


def test_recognition_graduates_to_production(app):
    from app.learning.scheduler import maybe_add_production_card, utcnow

    with app.app_context():
        item, card = _handoff_fixture(app)

        created = maybe_add_production_card(
            card, rating=3, now=utcnow(), scheduled_days=10
        )

        assert created is not None
        assert created.skill == "produce"
        assert created.item_id == item.id


def test_production_handoff_waits_for_a_stable_card(app):
    from app.learning.scheduler import maybe_add_production_card

    with app.app_context():
        _item, card = _handoff_fixture(app)

        # Too soon, or graded badly: no production card yet.
        assert maybe_add_production_card(card, rating=3, scheduled_days=2) is None
        assert maybe_add_production_card(card, rating=1, scheduled_days=30) is None


def test_production_handoff_is_idempotent(app):
    from app.learning.scheduler import maybe_add_production_card

    with app.app_context():
        _item, card = _handoff_fixture(app, reps=4)

        first = maybe_add_production_card(card, rating=4, scheduled_days=20)
        db.session.commit()
        second = maybe_add_production_card(card, rating=4, scheduled_days=20)

        assert first is not None
        assert second is None
