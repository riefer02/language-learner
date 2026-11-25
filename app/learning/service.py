"""Learner-facing service helpers for the review loop."""

import re
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import abort, current_app, g, request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app import db
from app.learning.scheduler import ensure_utc, new_review_card, utcnow
from app.models import Item, ReviewCard, ReviewLog, User
from app.models_language import Language


def learner_timezone():
    user = User.query.filter_by(is_local=True).first()
    name = (
        (user.timezone if user and user.timezone else None)
        or current_app.config.get("LEARNER_TIMEZONE", "UTC")
    )
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


def current_language(user=None):
    """Prefer the language in the URL, then the learner's choice, then Korean."""
    language = getattr(g, "language", None)
    if language is not None:
        return language
    user = user or get_or_create_local_user()
    language = None
    if user.target_language_id:
        language = db.session.get(Language, user.target_language_id)
    if language is None:
        language = Language.query.filter_by(code="ko").first()
    return language


def addressee_variants(item):
    """Return the other curated forms of a gendered phrase.

    The Amharic seed encodes the addressee in the gloss, e.g.
    ``What is your name? (to a man)``. Variants share the same base gloss.
    """
    if item is None or not item.gloss:
        return []
    match = re.search(r"\s*\(to (a man|a woman|a group)\)\s*$", item.gloss)
    if match is None:
        return []
    base = item.gloss[: match.start()].strip()
    rows = Item.query.filter(
        Item.language_id == item.language_id,
        Item.id != item.id,
        Item.gloss.startswith(base),
    ).all()
    variants = []
    for row in rows:
        row_match = re.search(
            r"\s*\(to (a man|a woman|a group)\)\s*$", row.gloss or ""
        )
        if row_match is None:
            continue
        if (row.gloss or "")[: row_match.start()].strip() != base:
            continue
        variants.append(
            {"item": row, "label": f"To {row_match.group(1)}"}
        )
    return sorted(variants, key=lambda variant: variant["label"])


def request_language():
    """Resolve a language for unprefixed APIs from ``?lang`` or JSON."""
    code = request.args.get("lang")
    if code is not None and code != "" and (
        not isinstance(code, str) or len(code) > 16
    ):
        abort(400, description="Invalid language code")
    if not code and request.is_json:
        payload = request.get_json(silent=True) or {}
        code = payload.get("lang")
        if code is not None and code != "" and (
            not isinstance(code, str) or len(code) > 16
        ):
            abort(400, description="Invalid language code")
    if code:
        language = Language.query.filter_by(code=code, is_active=True).first()
        if language is not None:
            return language
    return current_language()


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


def new_cards_seen_today(user_id, now=None, language_id=None):
    start_of_day, end_of_day, _local_date = local_day_bounds(now)
    query = ReviewLog.query.filter(
        ReviewLog.user_id == user_id,
        ReviewLog.was_new.is_(True),
        ReviewLog.reviewed_at >= start_of_day,
        ReviewLog.reviewed_at < end_of_day,
    )
    if language_id is not None:
        query = query.filter(
            ReviewLog.card.has(
                ReviewCard.item.has(Item.language_id == language_id)
            )
        )
    return query.count()


def _for_language(query, language_id):
    if language_id is None:
        return query
    return query.filter(ReviewCard.item.has(Item.language_id == language_id))


def available_cards(user_id, now=None, new_limit=None, language_id=None):
    """Due review cards plus a bounded number of new cards.

    New cards are capped per learner-local calendar day so a large seed deck
    cannot dump 30 unfamiliar items into a first session.
    """
    now = ensure_utc(now or utcnow())
    if new_limit is None:
        new_limit = current_app.config.get("NEW_CARDS_PER_DAY", 10)

    review_due = (
        _for_language(
            ReviewCard.query.options(selectinload(ReviewCard.item)), language_id
        )
        .filter(
            ReviewCard.user_id == user_id,
            ReviewCard.due_at <= now,
            ReviewCard.reps > 0,
        )
        .order_by(ReviewCard.due_at.asc(), ReviewCard.id.asc())
        .all()
    )

    remaining_new = max(
        0,
        int(new_limit)
        - new_cards_seen_today(user_id, now, language_id),
    )
    new_due = []
    if remaining_new:
        new_due = (
            _for_language(
                ReviewCard.query.options(selectinload(ReviewCard.item)),
                language_id,
            )
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


def due_cards(user_id, limit=None, now=None, language_id=None):
    cards = available_cards(user_id, now=now, language_id=language_id)
    if limit:
        return cards[:limit]
    return cards


def next_due_card(user_id, now=None, language_id=None):
    cards = due_cards(user_id, limit=1, now=now, language_id=language_id)
    return cards[0] if cards else None


def stats(user_id, now=None, language_id=None):
    now = ensure_utc(now or utcnow())
    items_query = Item.query
    cards_query = ReviewCard.query.filter_by(user_id=user_id)
    if language_id is not None:
        items_query = items_query.filter(Item.language_id == language_id)
        cards_query = _for_language(cards_query, language_id)
    total_items = items_query.count()
    total_cards = cards_query.count()
    due = len(available_cards(user_id, now=now, language_id=language_id))
    learned = _for_language(
        ReviewCard.query.filter(
            ReviewCard.user_id == user_id, ReviewCard.reps > 0
        ),
        language_id,
    ).count()

    start_of_day, end_of_day, _local_date = local_day_bounds(now)
    reviews_query = ReviewLog.query.filter(
        ReviewLog.user_id == user_id,
        ReviewLog.reviewed_at >= start_of_day,
        ReviewLog.reviewed_at < end_of_day,
    )
    if language_id is not None:
        reviews_query = reviews_query.filter(
            ReviewLog.card.has(
                ReviewCard.item.has(Item.language_id == language_id)
            )
        )
    reviews_today = reviews_query.count()

    new_limit = current_app.config.get("NEW_CARDS_PER_DAY", 10)
    new_seen = new_cards_seen_today(user_id, now, language_id)
    new_due_total = _for_language(
        ReviewCard.query.filter(
            ReviewCard.user_id == user_id,
            ReviewCard.due_at <= now,
            ReviewCard.reps == 0,
        ),
        language_id,
    ).count()
    new_remaining = max(
        0, new_due_total - max(0, int(new_limit) - new_seen)
    )

    next_card = (
        _for_language(
            ReviewCard.query.filter(
                ReviewCard.user_id == user_id, ReviewCard.due_at > now
            ),
            language_id,
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


def skill_breakdown(user_id, language_id=None):
    """Return per-skill totals and practiced counts for the progress screen."""
    cards = _for_language(
        ReviewCard.query.filter_by(user_id=user_id), language_id
    ).all()
    buckets = {}
    for card in cards:
        bucket = buckets.setdefault(
            card.skill, {"skill": card.skill, "total": 0, "practiced": 0}
        )
        bucket["total"] += 1
        if (card.reps or 0) > 0:
            bucket["practiced"] += 1
    return sorted(buckets.values(), key=lambda row: row["skill"])


def recent_reviews(user_id, limit=10, language_id=None):
    query = (
        ReviewLog.query.options(selectinload(ReviewLog.card))
        .filter(ReviewLog.user_id == user_id)
        .order_by(ReviewLog.reviewed_at.desc(), ReviewLog.id.desc())
    )
    if language_id is not None:
        query = query.filter(
            ReviewLog.card.has(
                ReviewCard.item.has(Item.language_id == language_id)
            )
        )
    return query.limit(limit).all()


def ensure_review_cards(user_id, language_id=None):
    """Create missing cards for every item in a language (or all items)."""
    existing = {
        (card.item_id, card.skill)
        for card in ReviewCard.query.filter_by(user_id=user_id).all()
    }
    items = Item.query
    if language_id is not None:
        items = items.filter(Item.language_id == language_id)
    created = 0
    for item in items.order_by(Item.id.asc()).all():
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
