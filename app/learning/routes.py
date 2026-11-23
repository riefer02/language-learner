"""The first learner-facing loop: today's plan and FSRS review."""

from datetime import UTC, datetime

from flask import (
    Blueprint,
    abort,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_wtf.csrf import validate_csrf
from sqlalchemy.orm.exc import StaleDataError
from werkzeug.exceptions import BadRequest

from app import db
from app.learning.analytics import (
    record_event,
    retention_signal,
    weekly_recap,
)
from app.learning.hangul_data import HANGUL_LESSONS
from app.learning.scenes import (
    can_do_artifacts,
    get_or_create_session,
    get_scene,
    list_scenes_with_status,
    match_answer,
    next_scene,
    reset_session,
    session_transcript,
    submit_answer,
)
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
from app.learning.sound_gym_data import (
    DISCLAIMER,
    MINIMAL_PAIRS,
    PRODUCTION_PROMPTS,
)
from app.models import Item, ReviewCard, ReviewLog, SpeechAttempt
from app.services.speech import (
    SpeechConfigError,
    SpeechError,
    score_audio,
    transcribe_audio,
)
from app.utils.rate_limit import rate_limit
from app.utils.schemas import contains_hangul

learn = Blueprint("learn", __name__, url_prefix="/learn")


def _user():
    if Item.query.count() == 0:
        user, _items, _cards = seed_content()
        return user
    user = get_or_create_local_user()
    ensure_review_cards(user.id)
    return user


def _needs_onboarding(user):
    return current_app.config.get(
        "ONBOARDING_ENABLED", True
    ) and not user.onboarding_complete


def _session_limits():
    return current_app.config.get(
        "REVIEW_SESSION_LIMITS", {3: 4, 10: 20, 25: 50}
    )


def _start_review_session(mode):
    limits = _session_limits()
    if mode not in limits:
        mode = 10 if 10 in limits else next(iter(limits))
    session["review_mode"] = mode
    session["review_limit"] = limits[mode]
    session["review_count"] = 0
    return mode, limits[mode]


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
    if _needs_onboarding(user):
        return redirect(url_for("onboarding.welcome"))
    summary = stats(user.id)
    summary["next_due_human"] = _format_next_due(summary["next_due"])
    return render_template(
        "learn_today.html",
        summary=summary,
        user=user,
        next_mission=next_scene(user.id),
        weekly=weekly_recap(user.id),
        session_modes=sorted(_session_limits()),
    )


@learn.route("/scenes")
def scenes():
    user = _user()
    if _needs_onboarding(user):
        return redirect(url_for("onboarding.welcome"))
    return render_template(
        "scene_list.html", rows=list_scenes_with_status(user.id)
    )


@learn.route("/scenes/<slug>")
def scene_detail(slug):
    user = _user()
    if _needs_onboarding(user):
        return redirect(url_for("onboarding.welcome"))
    scene = get_scene(slug)
    if scene is None:
        abort(404)
    session = get_or_create_session(user.id, slug)
    transcript = session_transcript(session)
    if session.completed:
        return render_template(
            "scene_complete.html",
            scene=scene,
            session=session,
            transcript=transcript,
        )
    step = scene["steps"][session.step_index]
    return render_template(
        "scene_play.html",
        scene=scene,
        session=session,
        step=step,
        step_number=session.step_index + 1,
        total_steps=len(scene["steps"]),
        transcript=transcript,
        error=None,
        last_answer="",
    )


@learn.route("/scenes/<slug>/answer", methods=["POST"])
def scene_answer(slug):
    user = _user()
    if _needs_onboarding(user):
        return redirect(url_for("onboarding.welcome"))
    scene = get_scene(slug)
    if scene is None:
        abort(404)
    session = get_or_create_session(user.id, slug)

    if current_app.config.get("WTF_CSRF_ENABLED", True):
        try:
            validate_csrf(request.form.get("csrf_token"))
        except Exception as error:
            raise BadRequest("Invalid or missing CSRF token") from error

    answer = (request.form.get("answer") or "").strip()
    if not answer:
        step = scene["steps"][session.step_index]
        return render_template(
            "scene_play.html",
            scene=scene,
            session=session,
            step=step,
            step_number=session.step_index + 1,
            total_steps=len(scene["steps"]),
            transcript=session_transcript(session),
            error="Type or say one line before continuing.",
            last_answer="",
        )

    result = submit_answer(user, session, scene, answer)
    if result["accepted"]:
        if result["completed"]:
            record_event(user.id, "scene_completed", scene_slug=slug)
        else:
            record_event(
                user.id,
                "scene_step",
                scene_slug=slug,
                step_index=result["step_index"],
            )
        return redirect(url_for("learn.scene_detail", slug=slug))

    step = scene["steps"][session.step_index]
    return render_template(
        "scene_play.html",
        scene=scene,
        session=session,
        step=step,
        step_number=session.step_index + 1,
        total_steps=len(scene["steps"]),
        transcript=session_transcript(session),
        error="Not quite. Use the hint, then try once more.",
        hint=result["hint"],
        last_answer=answer,
    )


@learn.route("/scenes/<slug>/speak", methods=["POST"])
@rate_limit(
    limit=lambda: current_app.config.get("RATE_LIMIT_SPEECH", 20),
    window_seconds=lambda: current_app.config.get(
        "RATE_LIMIT_WINDOW_SECONDS", 60
    ),
    scope="scene_speech",
)
def scene_speak(slug):
    user = _user()
    if _needs_onboarding(user):
        return jsonify({"error": "Finish onboarding first"}), 403
    scene = get_scene(slug)
    if scene is None:
        return jsonify({"error": "Scene not found"}), 404
    session = get_or_create_session(user.id, slug)
    if session.completed:
        return jsonify({"accepted": True, "completed": True}), 200

    if current_app.config.get("WTF_CSRF_ENABLED", True):
        try:
            validate_csrf(request.form.get("csrf_token"))
        except Exception as error:
            raise BadRequest("Invalid or missing CSRF token") from error

    upload = request.files.get("audio")
    if upload is None or not upload.filename:
        return jsonify({"error": "Audio file is required"}), 400

    content_type = upload.mimetype or "application/octet-stream"
    extension = upload.filename.rsplit(".", 1)[-1].lower()
    if not content_type.startswith("audio/") and extension not in {
        "webm",
        "wav",
        "mp3",
        "m4a",
        "ogg",
    }:
        return jsonify({"error": "Unsupported audio format"}), 415

    max_bytes = current_app.config.get("SPEECH_MAX_BYTES", 5 * 1024 * 1024)
    audio_bytes = upload.read(max_bytes + 1)
    if len(audio_bytes) > max_bytes:
        return jsonify({"error": "Audio file is too large"}), 413

    try:
        transcript = transcribe_audio(
            audio_bytes, upload.filename, content_type
        )
    except SpeechConfigError as error:
        current_app.logger.warning("Scene speech unavailable: %s", error)
        return jsonify({"error": "Speech checking is not configured"}), 503
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except SpeechError as error:
        current_app.logger.warning("Scene speech failed: %s", error)
        return jsonify({"error": "Speech service is unavailable"}), 502

    step = scene["steps"][session.step_index]
    accepted, best_expected, score = match_answer(step["expected"], transcript)
    duration_ms = request.form.get("duration_ms", type=int)
    if duration_ms is not None:
        duration_ms = max(0, min(duration_ms, 60_000))

    attempt = SpeechAttempt(
        user_id=user.id,
        target_text=best_expected,
        transcript=transcript[:500],
        match_score=score,
        acceptable=accepted,
        provider=current_app.config.get("SPEECH_PROVIDER", "openai"),
        model=current_app.config.get(
            "SPEECH_TRANSCRIBE_MODEL", "gpt-transcribe"
        ),
        duration_ms=duration_ms,
    )
    db.session.add(attempt)

    if not accepted:
        db.session.commit()
        record_event(
            user.id,
            "scene_speech_attempt",
            scene_slug=slug,
            accepted=False,
        )
        return jsonify(
            {
                "accepted": False,
                "transcript": transcript,
                "hint": step["hint"],
                "best_expected": best_expected,
                "match_score": round(score, 3),
            }
        )

    result = submit_answer(user, session, scene, transcript)
    db.session.add(attempt)
    db.session.commit()
    record_event(
        user.id,
        "scene_speech_attempt",
        scene_slug=slug,
        accepted=True,
        completed=result["completed"],
    )
    return jsonify(
        {
            "accepted": True,
            "transcript": transcript,
            "completed": result["completed"],
            "step_index": result["step_index"],
            "redirect_url": url_for("learn.scene_detail", slug=slug),
        }
    )


@learn.route("/scenes/<slug>/reset", methods=["POST"])
def scene_reset(slug):
    user = _user()
    if _needs_onboarding(user):
        return redirect(url_for("onboarding.welcome"))
    scene = get_scene(slug)
    if scene is None:
        abort(404)
    if current_app.config.get("WTF_CSRF_ENABLED", True):
        try:
            validate_csrf(request.form.get("csrf_token"))
        except Exception as error:
            raise BadRequest("Invalid or missing CSRF token") from error
    session = get_or_create_session(user.id, slug)
    reset_session(session)
    record_event(user.id, "scene_reset", scene_slug=slug)
    return redirect(url_for("learn.scene_detail", slug=slug))


@learn.route("/sound-gym")
def sound_gym():
    user = _user()
    if _needs_onboarding(user):
        return redirect(url_for("onboarding.welcome"))
    record_event(user.id, "sound_gym_opened")
    return render_template(
        "sound_gym.html",
        pairs=MINIMAL_PAIRS,
        prompts=PRODUCTION_PROMPTS,
        disclaimer=DISCLAIMER,
    )


@learn.route("/api/speech-score", methods=["POST"])
@rate_limit(
    limit=lambda: current_app.config.get("RATE_LIMIT_SPEECH", 20),
    window_seconds=lambda: current_app.config.get(
        "RATE_LIMIT_WINDOW_SECONDS", 60
    ),
    scope="speech",
)
def api_speech_score():
    user = _user()
    if _needs_onboarding(user):
        return jsonify({"error": "Finish onboarding first"}), 403

    if current_app.config.get("WTF_CSRF_ENABLED", True):
        try:
            validate_csrf(request.form.get("csrf_token"))
        except Exception as error:
            raise BadRequest("Invalid or missing CSRF token") from error

    target_text = (request.form.get("target_text") or "").strip()
    if (
        not target_text
        or len(target_text) > 300
        or not contains_hangul(target_text)
    ):
        return jsonify({"error": "A short Korean target text is required"}), 400

    upload = request.files.get("audio")
    if upload is None or not upload.filename:
        return jsonify({"error": "Audio file is required"}), 400

    content_type = upload.mimetype or "application/octet-stream"
    extension = upload.filename.rsplit(".", 1)[-1].lower()
    if not content_type.startswith("audio/") and extension not in {
        "webm",
        "wav",
        "mp3",
        "m4a",
        "ogg",
    }:
        return jsonify({"error": "Unsupported audio format"}), 415

    max_bytes = current_app.config.get("SPEECH_MAX_BYTES", 5 * 1024 * 1024)
    audio_bytes = upload.read(max_bytes + 1)
    if len(audio_bytes) > max_bytes:
        return jsonify({"error": "Audio file is too large"}), 413

    duration_ms = request.form.get("duration_ms", type=int)
    if duration_ms is not None:
        duration_ms = max(0, min(duration_ms, 60_000))

    try:
        result = score_audio(
            target_text, audio_bytes, upload.filename, content_type
        )
    except SpeechConfigError as error:
        current_app.logger.warning("Speech scoring unavailable: %s", error)
        return jsonify({"error": "Speech checking is not configured"}), 503
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except SpeechError as error:
        current_app.logger.warning("Speech scoring failed: %s", error)
        return jsonify({"error": "Speech service is unavailable"}), 502

    attempt = SpeechAttempt(
        user_id=user.id,
        target_text=target_text,
        transcript=result["transcript"][:500],
        match_score=result["match_score"],
        acceptable=result["acceptable"],
        provider=result["provider"],
        model=result["model"],
        duration_ms=duration_ms,
    )
    db.session.add(attempt)
    db.session.commit()
    record_event(
        user.id,
        "speech_attempt",
        target_text=target_text,
        match_score=result["match_score"],
        acceptable=result["acceptable"],
    )

    return jsonify(
        {
            "attempt_id": attempt.id,
            "transcript": result["transcript"],
            "match_score": result["match_score"],
            "acceptable": result["acceptable"],
            "band": result["band"],
            "heard": result["heard"],
            "threshold": result["threshold"],
            "note": "Transcript match, not a pronunciation grade.",
        }
    )


@learn.route("/hangul")
def hangul():
    return render_template("hangul_index.html", lessons=HANGUL_LESSONS)


@learn.route("/hangul/<slug>")
def hangul_lesson(slug):
    lesson = next(
        (item for item in HANGUL_LESSONS if item["slug"] == slug), None
    )
    if lesson is None:
        abort(404)
    index = HANGUL_LESSONS.index(lesson)
    next_lesson = (
        HANGUL_LESSONS[index + 1] if index + 1 < len(HANGUL_LESSONS) else None
    )
    return render_template(
        "hangul_lesson.html",
        lesson=lesson,
        next_lesson=next_lesson,
        lesson_number=index + 1,
        lesson_total=len(HANGUL_LESSONS),
    )


@learn.route("/progress")
def progress():
    user = _user()
    if _needs_onboarding(user):
        return redirect(url_for("onboarding.welcome"))
    summary = stats(user.id)
    summary["next_due_human"] = _format_next_due(summary["next_due"])
    return render_template(
        "learn_progress.html",
        summary=summary,
        skills=skill_breakdown(user.id),
        reviews=recent_reviews(user.id),
        can_dos=can_do_artifacts(user.id),
        weekly=weekly_recap(user.id),
        retention=retention_signal(user.id),
    )


@learn.route("/review")
def review():
    user = _user()
    if _needs_onboarding(user):
        return redirect(url_for("onboarding.welcome"))

    if request.args.get("continue"):
        session.pop("review_limit", None)
        session.pop("review_count", None)
        session.pop("review_mode", None)

    mode = request.args.get("mode", type=int)
    if mode in _session_limits():
        _start_review_session(mode)
    elif "review_limit" not in session:
        default_mode = user.daily_minutes if user.daily_minutes in _session_limits() else 10
        _start_review_session(default_mode)

    limit = session.get("review_limit", 20)
    count = session.get("review_count", 0)
    if count >= limit:
        return redirect(url_for("learn.review_complete"))

    card = next_due_card(user.id)
    if card is None:
        summary = stats(user.id)
        summary["next_due_human"] = _format_next_due(summary["next_due"])
        session.pop("review_limit", None)
        session.pop("review_count", None)
        session.pop("review_mode", None)
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
        session_remaining=max(0, limit - count),
        session_limit=limit,
        session_mode=session.get("review_mode", user.daily_minutes),
        interval=upcoming_interval(card),
        skill_label=skill_labels.get(card.skill, card.skill.title()),
        type_label=type_labels.get(item.item_type, item.item_type.title()),
        is_new=(card.reps or 0) == 0,
    )


@learn.route("/review/<int:card_id>", methods=["POST"])
def submit_review(card_id):
    user = _user()
    if _needs_onboarding(user):
        return redirect(url_for("onboarding.welcome"))
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
    record_event(
        user.id,
        "review_submitted",
        card_id=card.id,
        rating=rating,
        skill=card.skill,
        was_new=was_new,
        elapsed_ms=elapsed_ms,
    )

    session["review_count"] = session.get("review_count", 0) + 1
    if session["review_count"] >= session.get("review_limit", 20):
        return redirect(url_for("learn.review_complete"))
    return redirect(url_for("learn.review"))


@learn.route("/review/complete")
def review_complete():
    user = _user()
    if _needs_onboarding(user):
        return redirect(url_for("onboarding.welcome"))
    summary = stats(user.id)
    summary["next_due_human"] = _format_next_due(summary["next_due"])
    return render_template(
        "review_session_complete.html",
        summary=summary,
        user=user,
        mode=session.get("review_mode", user.daily_minutes),
        limit=session.get("review_limit", 20),
        count=session.get("review_count", 0),
    )
