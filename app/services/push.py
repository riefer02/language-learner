"""Web Push subscriptions and the daily reminder job."""

import json
from datetime import time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import current_app

from app import db
from app.learning.analytics import record_event
from app.learning.scheduler import ensure_utc, utcnow
from app.learning.service import local_day_bounds
from app.models import Event, PushSubscription, ReviewCard, User


class PushError(RuntimeError):
    """Base push error."""


class PushConfigError(PushError):
    """Raised when VAPID settings are missing."""


def _vapid_private_key():
    return current_app.config.get("VAPID_PRIVATE_KEY")


def _vapid_public_key():
    return current_app.config.get("VAPID_PUBLIC_KEY")


def _vapid_subject():
    return current_app.config.get("VAPID_SUBJECT", "mailto:hello@kiku.example")


def push_configured():
    return bool(
        current_app.config.get("PUSH_ENABLED", True)
        and _vapid_public_key()
        and _vapid_private_key()
    )


def subscribe(user, endpoint, p256dh, auth, user_agent=None):
    if not endpoint or not p256dh or not auth:
        raise ValueError("A complete push subscription is required")

    subscription = PushSubscription.query.filter_by(endpoint=endpoint).first()
    if subscription is None:
        subscription = PushSubscription(
            user_id=user.id,
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth,
            user_agent=(user_agent or "")[:300] or None,
        )
        db.session.add(subscription)
    else:
        subscription.user_id = user.id
        subscription.p256dh = p256dh
        subscription.auth = auth
        subscription.user_agent = (user_agent or "")[:300] or None
    db.session.commit()
    return subscription


def unsubscribe(user, endpoint):
    subscription = PushSubscription.query.filter_by(
        user_id=user.id, endpoint=endpoint
    ).first()
    if subscription is None:
        return False
    db.session.delete(subscription)
    db.session.commit()
    return True


def _send(subscription, payload):
    try:
        from pywebpush import WebPushException, webpush
    except ImportError as error:
        raise PushConfigError("pywebpush is not installed") from error

    info = {
        "endpoint": subscription.endpoint,
        "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
    }
    try:
        webpush(
            info,
            data=json.dumps(payload, ensure_ascii=False),
            vapid_private_key=_vapid_private_key(),
            vapid_claims={"sub": _vapid_subject()},
            timeout=10,
        )
        subscription.last_success_at = utcnow()
        subscription.failure_count = 0
        db.session.commit()
        return True
    except WebPushException as error:
        response = getattr(error, "response", None)
        status = getattr(response, "status_code", None)
        if status in (404, 410):
            db.session.delete(subscription)
        else:
            subscription.failure_count = (subscription.failure_count or 0) + 1
        db.session.commit()
        return False
    except Exception as error:  # noqa: BLE001 - one bad endpoint must not stop the job
        current_app.logger.warning("push send failed: %s", error)
        subscription.failure_count = (subscription.failure_count or 0) + 1
        db.session.commit()
        return False


def _user_timezone(user):
    name = user.timezone or current_app.config.get("LEARNER_TIMEZONE", "UTC")
    try:
        return ZoneInfo(name)
    except (KeyError, ValueError, ZoneInfoNotFoundError):
        return ZoneInfo("UTC")


def reminder_candidates(now=None):
    """Return users whose local reminder window is open and have cards due."""
    now = ensure_utc(now or utcnow())
    window = max(1, int(current_app.config.get("REMINDER_WINDOW_MINUTES", 15)))
    candidates = []

    for user in User.query.filter_by(reminder_enabled=True).all():
        if not user.reminder_time:
            continue
        try:
            hour, minute = [int(part) for part in user.reminder_time.split(":")]
            reminder = time(hour=hour, minute=minute)
        except (TypeError, ValueError):
            continue

        tz = _user_timezone(user)
        local_now = now.astimezone(tz)
        reminder_dt = local_now.replace(
            hour=reminder.hour, minute=reminder.minute, second=0, microsecond=0
        )
        elapsed = (local_now - reminder_dt).total_seconds() / 60
        if elapsed < 0 or elapsed >= window:
            continue

        start_of_day, _end, _date = local_day_bounds(now)
        already_sent = Event.query.filter(
            Event.user_id == user.id,
            Event.name == "reminder_sent",
            Event.created_at >= start_of_day,
        ).first()
        if already_sent:
            continue

        due = ReviewCard.query.filter(
            ReviewCard.user_id == user.id, ReviewCard.due_at <= now
        ).count()
        if due <= 0:
            continue

        subscriptions = PushSubscription.query.filter_by(
            user_id=user.id
        ).all()
        if not subscriptions:
            continue

        candidates.append(
            {
                "user": user,
                "due": due,
                "subscriptions": subscriptions,
                "local_time": local_now.strftime("%H:%M"),
            }
        )
    return candidates


def send_due_reminders(now=None, dry_run=False):
    """Send at most one reminder per learner per local day."""
    if not push_configured() and not dry_run:
        raise PushConfigError(
            "PUSH_ENABLED, VAPID_PUBLIC_KEY, and VAPID_PRIVATE_KEY are required"
        )

    results = []
    for candidate in reminder_candidates(now):
        user = candidate["user"]
        payload = {
            "title": "Kiku",
            "body": (
                f"{candidate['due']} cards due. "
                "A 3-minute session is enough."
            ),
            "url": "/learn/",
        }
        if dry_run:
            results.append(
                {
                    "user_id": user.id,
                    "due": candidate["due"],
                    "subscriptions": len(candidate["subscriptions"]),
                    "local_time": candidate["local_time"],
                    "sent": 0,
                }
            )
            continue

        sent = sum(
            1
            for subscription in candidate["subscriptions"]
            if _send(subscription, payload)
        )
        if sent:
            record_event(user.id, "reminder_sent", due=candidate["due"])
        results.append(
            {
                "user_id": user.id,
                "due": candidate["due"],
                "subscriptions": len(candidate["subscriptions"]),
                "local_time": candidate["local_time"],
                "sent": sent,
            }
        )
    return results
