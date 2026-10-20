"""Settings, PWA assets, push subscriptions, and reminder eligibility."""

from datetime import UTC, datetime

from app import db
from app.learning.analytics import record_event
from app.learning.scheduler import new_review_card
from app.learning.service import get_or_create_local_user
from app.models import Event, Item, PushSubscription, User
from app.services.push import send_due_reminders


def test_settings_page_renders(client):
    response = client.get("/settings")

    assert response.status_code == 200
    assert b"Make the loop fit your life" in response.data
    assert b"Reminder" in response.data


def test_settings_post_updates_profile_and_reminder(client, app):
    response = client.post(
        "/settings",
        data={
            "goal": "work",
            "daily_minutes": "25",
            "experience": "some",
            "timezone": "Asia/Seoul",
            "reminder_enabled": "on",
            "reminder_time": "20:15",
        },
    )

    assert response.status_code == 302
    with app.app_context():
        user = User.query.first()
        assert user.goal == "work"
        assert user.daily_minutes == 25
        assert user.experience == "some"
        assert user.timezone == "Asia/Seoul"
        assert user.reminder_enabled is True
        assert user.reminder_time == "20:15"


def test_manifest_and_service_worker_are_served(client):
    manifest = client.get("/static/manifest.webmanifest")
    worker = client.get("/sw.js")
    offline = client.get("/offline")

    assert manifest.status_code == 200
    assert b"Kiku" in manifest.data
    assert worker.status_code == 200
    assert worker.headers["Service-Worker-Allowed"] == "/"
    assert offline.status_code == 200


def test_push_subscription_round_trip(app, client):
    app.config.update(
        VAPID_PUBLIC_KEY="test-public",
        VAPID_PRIVATE_KEY="test-private",
        PUSH_ENABLED=True,
    )

    subscribed = client.post(
        "/api/push/subscribe",
        json={
            "endpoint": "https://push.example/endpoint-1",
            "keys": {"p256dh": "key", "auth": "secret"},
        },
    )

    assert subscribed.status_code == 200
    with app.app_context():
        assert PushSubscription.query.count() == 1

    removed = client.post(
        "/api/push/unsubscribe",
        json={"endpoint": "https://push.example/endpoint-1"},
    )

    assert removed.status_code == 200
    with app.app_context():
        assert PushSubscription.query.count() == 0


def test_push_subscribe_is_503_without_vapid(client):
    response = client.post(
        "/api/push/subscribe",
        json={"endpoint": "https://push.example/endpoint-1", "keys": {}},
    )

    assert response.status_code == 503


def test_reminder_dry_run_finds_eligible_user(app, client):
    now = datetime(2026, 10, 19, 19, 5, tzinfo=UTC)
    with app.app_context():
        user = get_or_create_local_user()
        user.reminder_enabled = True
        user.reminder_time = "19:00"
        user.timezone = "UTC"
        item = Item(
            item_type="lexeme",
            korean="테스트",
            english="test",
            level=1,
            default_skill="recognize",
        )
        db.session.add(item)
        db.session.commit()
        card = new_review_card(user.id, item.id, "recognize", now=now)
        db.session.add(card)
        db.session.add(
            PushSubscription(
                user_id=user.id,
                endpoint="https://push.example/endpoint-1",
                p256dh="key",
                auth="secret",
            )
        )
        db.session.commit()

        results = send_due_reminders(now=now, dry_run=True)

        assert len(results) == 1
        assert results[0]["due"] == 1
        assert results[0]["subscriptions"] == 1
        assert results[0]["sent"] == 0


def test_reminder_window_rejects_wrong_time(app, client):
    now = datetime(2026, 10, 19, 19, 30, tzinfo=UTC)
    with app.app_context():
        user = get_or_create_local_user()
        user.reminder_enabled = True
        user.reminder_time = "19:00"
        user.timezone = "UTC"
        db.session.commit()

        assert send_due_reminders(now=now, dry_run=True) == []


def test_reminder_send_records_one_event_per_day(app, client, monkeypatch):
    now = datetime(2026, 10, 19, 19, 5, tzinfo=UTC)
    calls = []

    def fake_webpush(*args, **kwargs):
        calls.append((args, kwargs))
        return object()

    monkeypatch.setattr("pywebpush.webpush", fake_webpush)
    app.config.update(
        VAPID_PUBLIC_KEY="test-public",
        VAPID_PRIVATE_KEY="test-private",
        PUSH_ENABLED=True,
    )

    with app.app_context():
        user = get_or_create_local_user()
        user.reminder_enabled = True
        user.reminder_time = "19:00"
        user.timezone = "UTC"
        item = Item(
            item_type="lexeme",
            korean="알림",
            english="reminder",
            level=1,
            default_skill="recognize",
        )
        db.session.add(item)
        db.session.commit()
        db.session.add(new_review_card(user.id, item.id, "recognize", now=now))
        db.session.add(
            PushSubscription(
                user_id=user.id,
                endpoint="https://push.example/endpoint-send",
                p256dh="key",
                auth="secret",
            )
        )
        db.session.commit()

        results = send_due_reminders(now=now)

        assert results[0]["sent"] == 1
        assert len(calls) == 1
        assert "cards due" in calls[0][1]["data"]
        assert Event.query.filter_by(name="reminder_sent").count() == 1


def test_reminder_is_skipped_after_one_send_per_local_day(app, client):
    now = datetime(2026, 10, 19, 19, 5, tzinfo=UTC)
    with app.app_context():
        user = get_or_create_local_user()
        user.reminder_enabled = True
        user.reminder_time = "19:00"
        user.timezone = "UTC"
        item = Item(
            item_type="lexeme",
            korean="하루",
            english="day",
            level=1,
            default_skill="recognize",
        )
        db.session.add(item)
        db.session.commit()
        db.session.add(new_review_card(user.id, item.id, "recognize", now=now))
        db.session.add(
            PushSubscription(
                user_id=user.id,
                endpoint="https://push.example/endpoint-2",
                p256dh="key",
                auth="secret",
            )
        )
        db.session.commit()
        record_event(user.id, "reminder_sent", due=1)

        assert send_due_reminders(now=now, dry_run=True) == []


def test_push_subscription_is_upserted_by_endpoint(app, client):
    app.config.update(
        VAPID_PUBLIC_KEY="test-public",
        VAPID_PRIVATE_KEY="test-private",
        PUSH_ENABLED=True,
    )
    payload = {
        "endpoint": "https://push.example/endpoint-3",
        "keys": {"p256dh": "key", "auth": "secret"},
    }

    assert client.post("/api/push/subscribe", json=payload).status_code == 200
    payload["keys"] = {"p256dh": "rotated", "auth": "rotated-secret"}
    assert client.post("/api/push/subscribe", json=payload).status_code == 200

    with app.app_context():
        assert PushSubscription.query.count() == 1
        assert PushSubscription.query.first().p256dh == "rotated"
