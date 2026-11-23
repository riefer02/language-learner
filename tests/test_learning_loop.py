"""End-to-end coverage for the first learning loop."""

from datetime import UTC, datetime

from app import db
from app.learning.scheduler import apply_rating, new_review_card
from app.models import Item, ReviewCard, ReviewLog


def test_learn_page_auto_seeds_and_shows_due_cards(client, app):
    response = client.get("/ko/learn")

    assert response.status_code == 200
    assert b"One small session" in response.data
    assert b"Start review" in response.data
    with app.app_context():
        assert Item.query.count() >= 25
        assert ReviewCard.query.count() == Item.query.count()


def test_new_card_daily_cap(client, app):
    response = client.get("/ko/learn")

    assert b"10 cards" in response.data

    with app.app_context():
        card_ids = [card.id for card in ReviewCard.query.limit(10).all()]

    for card_id in card_ids:
        client.post(f"/ko/learn/review/{card_id}", data={"rating": "3"})

    response = client.get("/ko/learn")
    assert b"You are caught up" in response.data


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
    assert b"Show answer" in response.data
    assert b"grade-form" in response.data


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


def test_today_shows_first_run_guidance(client):
    response = client.get("/ko/learn")
    assert response.status_code == 200
    assert b"New here? Start with three moves" in response.data
    assert b"What does" in response.data


def test_today_shows_my_terms_card(client):
    page = client.get("/ko/learn")
    assert page.status_code == 200
    assert b"My terms" in page.data
    assert b"Open My terms" in page.data
