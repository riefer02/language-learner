"""The first learner-facing loop: today's plan and FSRS review."""

from datetime import UTC, datetime

from flask import (
    Blueprint,
    abort,
    current_app,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_wtf.csrf import validate_csrf
from sqlalchemy.orm.exc import StaleDataError
from werkzeug.exceptions import BadRequest

from app import db
from app.learning.scheduler import (
    apply_rating,
    ensure_utc,
    upcoming_interval,
    utcnow,
)
from app.learning.seed_data import seed_content
from app.learning.service import (
    ensure_review_cards,
    get_or_create_local_user,
    new_cards_seen_today,
    next_due_card,
    recent_reviews,
    skill_breakdown,
    stats,
)
from app.models import Item, ReviewCard, ReviewLog

learn = Blueprint("learn", __name__, url_prefix="/learn")


def _user():
    if Item.query.count() == 0:
        user, _items, _cards = seed_content()
        return user
    user = get_or_create_local_user()
    ensure_review_cards(user.id)
    return user


def _format_next_due(value):
    if value is None:
        return None
    value = ensure_utc(value)
    now = datetime.now(UTC)
    delta = value - now
    if delta.total_seconds() <= 0:
        return "now"
    if delta.total_seconds() < 3600:
        return f"in {max(1, int(delta.total_seconds() // 60))} minutes"
    if delta.total_seconds() < 86400:
        return f"in {max(1, int(delta.total_seconds() // 3600))} hours"
    return f"in {int(delta.total_seconds() // 86400)} days"


@learn.route("/", strict_slashes=False)
def today():
    user = _user()
    summary = stats(user.id)
    summary["next_due_human"] = _format_next_due(summary["next_due"])
    return render_template("learn_today.html", summary=summary, user=user)


@learn.route("/progress")
def progress():
    user = _user()
    summary = stats(user.id)
    summary["next_due_human"] = _format_next_due(summary["next_due"])
    return render_template(
        "learn_progress.html",
        summary=summary,
        skills=skill_breakdown(user.id),
        reviews=recent_reviews(user.id),
    )


@learn.route("/review")
def review():
    user = _user()
    card = next_due_card(user.id)
    if card is None:
        summary = stats(user.id)
        summary["next_due_human"] = _format_next_due(summary["next_due"])
        return render_template("learn_done.html", summary=summary, user=user)

    item = card.item
    prompt_side = "korean" if card.skill in {"recognize", "listen"} else "english"
    answer_side = "english" if prompt_side == "korean" else "korean"
    due_count = stats(user.id)["due"]
    skill_labels = {
        "recognize": "Recognize",
        "produce": "Produce",
        "listen": "Listen",
    }
    type_labels = {
        "lexeme": "Word",
        "chunk": "Phrase",
        "grammar": "Grammar",
        "sentence": "Sentence",
    }

    return render_template(
        "learn_review.html",
        card=card,
        item=item,
        prompt_side=prompt_side,
        answer_side=answer_side,
        due_count=due_count,
        interval=upcoming_interval(card),
        skill_label=skill_labels.get(card.skill, card.skill.title()),
        type_label=type_labels.get(item.item_type, item.item_type.title()),
        is_new=(card.reps or 0) == 0,
    )


@learn.route("/review/<int:card_id>", methods=["POST"])
def submit_review(card_id):
    user = _user()
    card = db.session.get(ReviewCard, card_id)
    if card is None or card.user_id != user.id:
        abort(404)

    if current_app.config.get("WTF_CSRF_ENABLED", True):
        try:
            validate_csrf(request.form.get("csrf_token"))
        except Exception as error:
            raise BadRequest("Invalid or missing CSRF token") from error

    now = utcnow()
    if ensure_utc(card.due_at) > now:
        abort(409, description="This card is not due yet")

    expected_reps = request.form.get("expected_reps", type=int)
    if expected_reps is not None and expected_reps != (card.reps or 0):
        abort(409, description="This card was already graded in another tab")

    rating = request.form.get("rating", type=int)
    if rating not in (1, 2, 3, 4):
        abort(400, description="Rating must be between 1 and 4")

    elapsed_ms = request.form.get("elapsed_ms", type=int)
    if elapsed_ms is not None:
        elapsed_ms = max(0, min(elapsed_ms, 600_000))

    was_new = (card.reps or 0) == 0
    if was_new:
        daily_limit = current_app.config.get("NEW_CARDS_PER_DAY", 10)
        if new_cards_seen_today(user.id, now) >= daily_limit:
            abort(409, description="Today's new-card limit has been reached")

    result = apply_rating(card, rating, now=now, elapsed_ms=elapsed_ms)
    db.session.add(
        ReviewLog(
            card_id=card.id,
            user_id=user.id,
            rating=result["rating"],
            reviewed_at=result["reviewed_at"],
            elapsed_ms=result["elapsed_ms"],
            was_new=was_new,
            scheduled_days=result["scheduled_days"],
            stability=result["stability"],
            difficulty=result["difficulty"],
        )
    )
    try:
        db.session.commit()
    except StaleDataError as error:
        db.session.rollback()
        raise BadRequest("This card was graded in another tab") from error
    return redirect(url_for("learn.review"))
