"""FSRS scheduling glue.

The algorithm lives in the ``fsrs`` package. This module owns the translation
between its in-memory Card and our persisted ReviewCard row.
"""

from datetime import UTC, datetime, timedelta

from fsrs import Card, Rating, Scheduler, State

from app.models import ReviewCard

DESIRED_RETENTION = 0.90
_scheduler = Scheduler(desired_retention=DESIRED_RETENTION)


def utcnow():
    return datetime.now(UTC)


def ensure_utc(value):
    """Attach UTC to naive datetimes returned by SQLite."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _to_fsrs_card(card):
    return Card(
        card_id=card.id or card.item_id,
        state=State(card.state),
        step=card.step,
        stability=card.stability,
        difficulty=card.difficulty,
        due=ensure_utc(card.due_at) or utcnow(),
        last_review=ensure_utc(card.last_review_at),
    )


def new_review_card(user_id, item_id, skill, now=None):
    """Create an unsaved ReviewCard due immediately."""
    now = now or utcnow()
    fsrs_card = Card()
    return ReviewCard(
        user_id=user_id,
        item_id=item_id,
        skill=skill,
        state=int(fsrs_card.state),
        step=fsrs_card.step,
        stability=fsrs_card.stability,
        difficulty=fsrs_card.difficulty,
        due_at=now,
        last_review_at=None,
        reps=0,
        lapses=0,
    )


def apply_rating(card, rating, now=None, elapsed_ms=None):
    """Apply a 1–4 rating, mutate ``card``, and return the FSRS review log."""
    now = now or utcnow()
    rating = int(rating)
    if rating not in (1, 2, 3, 4):
        raise ValueError("rating must be between 1 and 4")

    fsrs_card = _to_fsrs_card(card)
    reviewed_card, _review_log = _scheduler.review_card(
        fsrs_card,
        Rating(rating),
        review_datetime=now,
        review_duration=elapsed_ms,
    )

    previous_state = int(card.state)
    card.state = int(reviewed_card.state)
    card.step = reviewed_card.step
    card.stability = reviewed_card.stability
    card.difficulty = reviewed_card.difficulty
    card.due_at = ensure_utc(reviewed_card.due)
    card.last_review_at = ensure_utc(reviewed_card.last_review)
    card.reps = (card.reps or 0) + 1
    # A lapse is a Review -> Relearning transition, not every "Again" on a
    # brand-new card.
    if rating == 1 and previous_state == int(State.Review):
        card.lapses = (card.lapses or 0) + 1

    scheduled_days = (card.due_at - now).total_seconds() / 86400
    return {
        "rating": rating,
        "reviewed_at": now,
        "elapsed_ms": elapsed_ms,
        "scheduled_days": scheduled_days,
        "stability": card.stability,
        "difficulty": card.difficulty,
    }


def upcoming_interval(card):
    """Human-readable next interval for the review UI."""
    due = ensure_utc(card.due_at)
    if due is None:
        return "now"
    delta = due - utcnow()
    if delta <= timedelta(0):
        return "now"
    if delta < timedelta(hours=1):
        return f"{max(1, int(delta.total_seconds() // 60))} min"
    if delta < timedelta(days=1):
        return f"{max(1, int(delta.total_seconds() // 3600))} h"
    return f"{int(delta.total_seconds() // 86400)} d"
