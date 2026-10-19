"""Learner-facing service helpers for the review loop."""

from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import current_app
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app import db
from app.learning.scheduler import ensure_utc, new_review_card, utcnow
from app.models import Item, ReviewCard, ReviewLog, User


def learner_timezone():
    name = current_app.config.get("LEARNER_TIMEZONE", "UTC")
    try:
        return ZoneInfo(name)
    except (KeyError, ValueError, ZoneInfoNotFoundError):
        current_app.logger.warning("Unknown LEARNER_TIMEZONE %r; using UTC", name)
        return ZoneInfo("UTC")


def local_day_bounds(now=None):
    """Return the learner's local day as UTC [start, end) boundaries."""
    now = ensure_utc(now or utcnow())
    tz = learner_timezone()
    local_now = now.astimezone(tz)
    start_local = datetime.combine(local_now.date(), time.min, tzinfo=tz)
    end_local = start_local + timedelta(days=1)
    return start_local.astimezone(UTC), end_local.astimezone(UTC), local_now.date()


def get_or_create_local_user():
    user = User.query.filter_by(is_local=True).first()
    if user is not None:
        return user

    user = User(display_name="Learner", is_local=True)
    db.session.add(user)
    try:
        db.session.commit()
        return user
    except IntegrityError:
        # Another request won the race; use the row it created.
        db.session.rollback()
        user = User.query.filter_by(is_local=True).first()
        if user is None:
            raise
        return user


def new_cards_seen_today(user_id, now=None):
    start_of_day, end_of_day, _local_date = local_day_bounds(now)
    return ReviewLog.query.filter(
        ReviewLog.user_id == user_id,
        ReviewLog.was_new.is_(True),
        ReviewLog.reviewed_at >= start_of_day,
        ReviewLog.reviewed_at < end_of_day,
    ).count()


def available_cards(user_id, now=None, new_limit=None):
    """Due review cards plus a bounded number of new cards.

    New cards are capped per learner-local calendar day so a large seed deck
    cannot dump 30 unfamiliar items into a first session.
    """
    now = ensure_utc(now or utcnow())
    if new_limit is None:
        new_limit = current_app.config.get("NEW_CARDS_PER_DAY", 10)

    review_due = (
        ReviewCard.query.options(selectinload(ReviewCard.item))
        .filter(
            ReviewCard.user_id == user_id,
            ReviewCard.due_at <= now,
            ReviewCard.reps > 0,
        )
        .order_by(ReviewCard.due_at.asc(), ReviewCard.id.asc())
        .all()
    )

    remaining_new = max(
        0, int(new_limit) - new_cards_seen_today(user_id, now)
    )
    new_due = []
    if remaining_new:
        new_due = (
            ReviewCard.query.options(selectinload(ReviewCard.item))
            .filter(
                ReviewCard.user_id == user_id,
                ReviewCard.due_at <= now,
                ReviewCard.reps == 0,
            )
            .order_by(ReviewCard.due_at.asc(), ReviewCard.id.asc())
            .limit(remaining_new)
            .all()
        )

    # Review-first: due review cards are always presented before new material.
    return review_due + new_due


def due_cards(user_id, limit=None, now=None):
    cards = available_cards(user_id, now=now)
    if limit:
        return cards[:limit]
    return cards


def next_due_card(user_id, now=None):
    cards = due_cards(user_id, limit=1, now=now)
    return cards[0] if cards else None


def stats(user_id, now=None):
    now = ensure_utc(now or utcnow())
    total_items = Item.query.count()
    total_cards = ReviewCard.query.filter_by(user_id=user_id).count()
    due = len(available_cards(user_id, now=now))
    learned = ReviewCard.query.filter(
        ReviewCard.user_id == user_id, ReviewCard.reps > 0
    ).count()

    start_of_day, end_of_day, _local_date = local_day_bounds(now)
    reviews_today = ReviewLog.query.filter(
        ReviewLog.user_id == user_id,
        ReviewLog.reviewed_at >= start_of_day,
        ReviewLog.reviewed_at < end_of_day,
    ).count()

    new_limit = current_app.config.get("NEW_CARDS_PER_DAY", 10)
    new_seen = new_cards_seen_today(user_id, now)
    new_due_total = ReviewCard.query.filter(
        ReviewCard.user_id == user_id,
        ReviewCard.due_at <= now,
        ReviewCard.reps == 0,
    ).count()
    new_remaining = max(
        0, new_due_total - max(0, int(new_limit) - new_seen)
    )

    next_card = (
        ReviewCard.query.filter(
            ReviewCard.user_id == user_id, ReviewCard.due_at > now
        )
        .order_by(ReviewCard.due_at.asc())
        .first()
    )
    return {
        "total_items": total_items,
        "total_cards": total_cards,
        "due": due,
        "learned": learned,
        "reviews_today": reviews_today,
        "new_remaining": new_remaining,
        "next_due": ensure_utc(next_card.due_at) if next_card else None,
        "streak": streak_days(user_id, now),
    }


def streak_days(user_id, now=None):
    """Count consecutive learner-local calendar days with at least one review."""
    now = ensure_utc(now or utcnow())
    tz = learner_timezone()
    rows = (
        db.session.query(ReviewLog.reviewed_at)
        .filter(ReviewLog.user_id == user_id)
        .order_by(ReviewLog.reviewed_at.desc())
        .limit(1000)
        .all()
    )
    days = {
        ensure_utc(row[0]).astimezone(tz).date()
        for row in rows
        if row[0]
    }
    streak = 0
    cursor = now.astimezone(tz).date()
    # A streak survives until the end of the local day even before today's
    # first review, so it does not reset at midnight.
    if cursor not in days:
        cursor -= timedelta(days=1)
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def skill_breakdown(user_id):
    """Return per-skill totals and practiced counts for the progress screen."""
    cards = ReviewCard.query.filter_by(user_id=user_id).all()
    buckets = {}
    for card in cards:
        bucket = buckets.setdefault(
            card.skill, {"skill": card.skill, "total": 0, "practiced": 0}
        )
        bucket["total"] += 1
        if (card.reps or 0) > 0:
            bucket["practiced"] += 1
    return sorted(buckets.values(), key=lambda row: row["skill"])


def recent_reviews(user_id, limit=10):
    return (
        ReviewLog.query.options(selectinload(ReviewLog.card))
        .filter(ReviewLog.user_id == user_id)
        .order_by(ReviewLog.reviewed_at.desc(), ReviewLog.id.desc())
        .limit(limit)
        .all()
    )


def ensure_review_cards(user_id):
    """Create missing cards for every item, using its default skill."""
    existing = {
        (card.item_id, card.skill)
        for card in ReviewCard.query.filter_by(user_id=user_id).all()
    }
    created = 0
    for item in Item.query.order_by(Item.id.asc()).all():
        key = (item.id, item.default_skill)
        if key in existing:
            continue
        db.session.add(
            new_review_card(user_id, item.id, item.default_skill)
        )
        existing.add(key)
        created += 1
    if created:
        try:
            db.session.commit()
        except IntegrityError:
            # A concurrent request created the same cards first.
            db.session.rollback()
            return 0
    return created
