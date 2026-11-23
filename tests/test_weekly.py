"""Weekly recap and recall signal."""

from datetime import UTC, datetime, timedelta

from app import db
from app.learning.analytics import retention_signal, weekly_recap
from app.learning.scheduler import new_review_card
from app.learning.service import get_or_create_local_user
from app.models import CanDoArtifact, Item, ReviewCard, ReviewLog


def _log(user, card, when, rating=3, was_new=False):
    db.session.add(
        ReviewLog(
            card_id=card.id,
            user_id=user.id,
            rating=rating,
            reviewed_at=when,
            was_new=was_new,
        )
    )


def test_weekly_recap_counts_reviews_days_and_recall(app):
    now = datetime(2026, 10, 19, 12, 0, tzinfo=UTC)
    with app.app_context():
        user = get_or_create_local_user()
        item = Item(
            item_type="lexeme",
            target_text="테스트",
            gloss="test",
            level=1,
            default_skill="recognize",
        )
        db.session.add(item)
        db.session.commit()
        card = new_review_card(user.id, item.id, "recognize")
        db.session.add(card)
        db.session.commit()

        _log(user, card, now, rating=3, was_new=True)
        _log(user, card, now - timedelta(days=1), rating=1)
        _log(user, card, now - timedelta(days=8), rating=3)
        db.session.add(
            CanDoArtifact(
                user_id=user.id,
                scene_slug="cafe-order",
                label="I can order a drink.",
                created_at=now - timedelta(days=1),
            )
        )
        db.session.commit()

        recap = weekly_recap(user.id, now=now)

        assert recap["reviews"] == 2
        assert recap["new_cards"] == 1
        assert recap["active_days"] == 2
        assert recap["can_dos"] == 1
        assert recap["recall_success"] == 0.667
        assert len(recap["activity"]) == 7
        assert recap["has_data"] is True


def test_retention_signal_uses_real_review_gaps(app):
    now = datetime(2026, 10, 19, 12, 0, tzinfo=UTC)
    with app.app_context():
        user = get_or_create_local_user()
        item = Item(
            item_type="lexeme",
            target_text="테스트",
            gloss="test",
            level=1,
            default_skill="recognize",
        )
        db.session.add(item)
        db.session.commit()
        card = new_review_card(user.id, item.id, "recognize")
        db.session.add(card)
        db.session.commit()

        _log(user, card, now - timedelta(days=50), rating=3)
        _log(user, card, now - timedelta(days=42), rating=1)
        _log(user, card, now - timedelta(days=12), rating=3)
        _log(user, card, now, rating=3)
        db.session.commit()

        signal = retention_signal(user.id)

        assert signal["day7"]["n"] == 2
        assert signal["day7"]["rate"] == 0.5
        assert signal["day30"]["n"] == 1
        assert signal["day30"]["rate"] == 1.0
        assert signal["total_delayed"] == 3


def test_progress_and_today_show_weekly_recap(client, app):
    now = datetime.now(UTC)
    client.get("/ko/learn")
    with app.app_context():
        user = get_or_create_local_user()
        card = ReviewCard.query.first()
        _log(user, card, now, rating=3, was_new=True)
        db.session.commit()

    progress = client.get("/ko/learn/progress")
    assert b"Last 7 days" in progress.data
    assert b"Recent recall success" in progress.data
    assert b"Delayed retention" in progress.data
    assert b"7+ day recall" in progress.data

    today = client.get("/ko/learn")
    assert b"This week:" in today.data
