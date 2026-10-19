"""Small append-only analytics helpers for alpha instrumentation."""

import json
from datetime import timedelta

from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.learning.scheduler import ensure_utc, utcnow
from app.models import CanDoArtifact, Event, ReviewLog, User


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


def retention_signal(user_id):
    """Delayed-review retention from real review gaps.

    For each review, compare the gap from the previous review of the same card.
    A 7+ day gap is evidence of delayed retention; a 30+ day gap is the longer
    horizon. This is not a proctored test, and it is not a proficiency score.
    """
    logs = (
        ReviewLog.query.filter(ReviewLog.user_id == user_id)
        .order_by(ReviewLog.card_id.asc(), ReviewLog.reviewed_at.asc())
        .all()
    )

    buckets = {"day7": [], "day30": []}
    previous = {}
    for log in logs:
        reviewed = ensure_utc(log.reviewed_at)
        prior = previous.get(log.card_id)
        if prior is not None:
            gap_days = (reviewed - prior).total_seconds() / 86400
            if gap_days >= 30:
                buckets["day30"].append(log.rating)
            elif gap_days >= 7:
                buckets["day7"].append(log.rating)
        previous[log.card_id] = reviewed

    def summarize(ratings):
        if not ratings:
            return {"rate": None, "n": 0}
        return {
            "rate": round(
                sum(1 for rating in ratings if rating >= 3) / len(ratings), 3
            ),
            "n": len(ratings),
        }

    return {
        "day7": summarize(buckets["day7"]),
        "day30": summarize(buckets["day30"]),
        "total_delayed": len(buckets["day7"]) + len(buckets["day30"]),
    }


def weekly_recap(user_id, now=None):
    """Last 7 learner-local days plus a 30-day recall-success estimate."""
    from app.learning.service import learner_timezone, local_day_bounds

    now = ensure_utc(now or utcnow())
    tz = learner_timezone()
    start, _end, _today = local_day_bounds(now - timedelta(days=6))

    logs = (
        ReviewLog.query.filter(
            ReviewLog.user_id == user_id,
            ReviewLog.reviewed_at >= start,
            ReviewLog.reviewed_at <= now,
        )
        .order_by(ReviewLog.reviewed_at.asc())
        .all()
    )

    counts = {}
    for log in logs:
        local_date = ensure_utc(log.reviewed_at).astimezone(tz).date()
        counts[local_date] = counts.get(local_date, 0) + 1

    activity = []
    for offset in range(6, -1, -1):
        day = (now.astimezone(tz).date() - timedelta(days=offset))
        activity.append(
            {
                "date": day.isoformat(),
                "label": day.strftime("%a"),
                "count": counts.get(day, 0),
            }
        )
    peak = max([item["count"] for item in activity] + [1])

    thirty_start = now - timedelta(days=30)
    recent = (
        ReviewLog.query.filter(
            ReviewLog.user_id == user_id,
            ReviewLog.reviewed_at >= thirty_start,
        )
        .all()
    )
    recall_success = (
        round(
            sum(1 for log in recent if (log.rating or 0) >= 3)
            / len(recent),
            3,
        )
        if recent
        else None
    )

    can_dos = CanDoArtifact.query.filter(
        CanDoArtifact.user_id == user_id,
        CanDoArtifact.created_at >= start,
    ).count()

    return {
        "reviews": len(logs),
        "distinct_cards": len({log.card_id for log in logs}),
        "new_cards": sum(1 for log in logs if log.was_new),
        "active_days": sum(1 for item in activity if item["count"] > 0),
        "can_dos": can_dos,
        "recall_success": recall_success,
        "activity": activity,
        "peak": peak,
        "has_data": bool(logs or can_dos),
    }


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
