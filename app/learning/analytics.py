"""Small append-only analytics helpers for alpha instrumentation."""

import json
from datetime import timedelta

from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.learning.scheduler import ensure_utc, utcnow
from app.models import Event, User


def record_event(user_id, name, **props):
    """Persist a product event. Never let analytics break a learner action."""
    event = Event(
        user_id=user_id,
        name=name,
        props=json.dumps(props, ensure_ascii=False) if props else None,
        created_at=utcnow(),
    )
    db.session.add(event)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
    return event


def metrics_summary(now=None):
    now = ensure_utc(now or utcnow())
    users = User.query.all()
    total_users = len(users)
    onboarded = sum(1 for user in users if user.onboarding_complete)
    review_users = {
        row[0]
        for row in db.session.query(Event.user_id)
        .filter(Event.name == "review_submitted")
        .distinct()
        .all()
        if row[0]
    }
    speech_attempts = (
        db.session.query(Event)
        .filter(Event.name == "speech_attempt")
        .count()
    )

    def retained(days):
        eligible = [
            user
            for user in users
            if user.created_at
            and ensure_utc(user.created_at) <= now - timedelta(days=days)
        ]
        if not eligible:
            return None
        retained_users = 0
        for user in eligible:
            target_date = ensure_utc(user.created_at).date() + timedelta(days=days)
            hit = (
                Event.query.filter(
                    Event.user_id == user.id,
                    db.func.date(Event.created_at) == target_date.isoformat(),
                )
                .first()
            )
            if hit:
                retained_users += 1
        return round(retained_users / len(eligible), 3)

    return {
        "total_users": total_users,
        "onboarded": onboarded,
        "activation_rate": round(onboarded / total_users, 3)
        if total_users
        else 0.0,
        "users_with_reviews": len(review_users),
        "speech_attempts": speech_attempts,
        "d1_retention": retained(1),
        "d7_retention": retained(7),
    }
