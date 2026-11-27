"""The first learner-facing loop: today's plan and FSRS review."""

import random
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
from app.languages.am_content import VOWEL_ORDERS, fidel_lessons
from app.learning.analytics import (
    record_event,
    retention_signal,
    weekly_recap,
)
from app.learning.dictionary import list_terms
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
    maybe_add_production_card,
    upcoming_interval,
    utcnow,
)
from app.learning.seed_data import seed_content
from app.learning.service import (
    current_language,
    ensure_review_cards,
    get_or_create_local_user,
    learner_timezone,
    new_cards_seen_today,
    next_due_card,
    recent_reviews,
    review_variants,
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

learn = Blueprint("learn", __name__, url_prefix="/<lang_code>/learn")


def _current_user():
    """Resolve the local learner and keep their cards in sync.

    The Korean seed runs only for a genuinely empty database, so adding an
    Amharic deck cannot silently stop Korean seeding later.
    """
    if Item.query.count() == 0:
        user, _items, _cards = seed_content()
        return user
    user = get_or_create_local_user()
    language = current_language(user)
    ensure_review_cards(user.id, language.id if language else None)
    return user


def _korean_only():
    language = current_language()
    return language is not None and language.code != "ko"


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
        minutes = max(1, int(delta.total_seconds() // 60))
        return f"in {minutes} minute{'s' if minutes != 1 else ''}"
    if delta.total_seconds() < 86400:
        hours = max(1, int(delta.total_seconds() // 3600))
        return f"in {hours} hour{'s' if hours != 1 else ''}"
    days = int(delta.total_seconds() // 86400)
    return f"in {days} day{'s' if days != 1 else ''}"


@learn.route("/", strict_slashes=False)
def today():
    user = _current_user()
    if _needs_onboarding(user):
        return redirect(url_for("onboarding.welcome"))
    language = current_language(user)
    summary = stats(user.id, language_id=language.id if language else None)
    summary["next_due_human"] = _format_next_due(summary["next_due"])
    terms = list_terms(
        user.id, language_id=language.id if language else None
    )
    return render_template(
        "learn_today.html",
        summary=summary,
        terms=terms[:3],
        term_count=len(terms),
        user=user,
        next_mission=(
            None
            if language and language.code == "am"
            else next_scene(user.id)
        ),
        weekly=weekly_recap(
            user.id, language_id=language.id if language else None
        ),
        session_modes=sorted(_session_limits()),
        language=language,
        today_label=datetime.now(learner_timezone()).strftime("%A, %d %B"),
    )


@learn.route("/scenes")
def scenes():
    if _korean_only():
        return redirect(url_for("learn.today"))
    user = _current_user()
    if _needs_onboarding(user):
        return redirect(url_for("onboarding.welcome"))
    return render_template(
        "scene_list.html", rows=list_scenes_with_status(user.id)
    )


@learn.route("/scenes/<slug>")
def scene_detail(slug):
    if _korean_only():
        return redirect(url_for("learn.today"))
    user = _current_user()
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
    if _korean_only():
        return redirect(url_for("learn.today"))
    user = _current_user()
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
    if _korean_only():
        return jsonify({"error": "Scene speech is Korean-only"}), 404
    user = _current_user()
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
    if _korean_only():
        return redirect(url_for("learn.today"))
    user = _current_user()
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
    if _korean_only():
        return redirect(url_for("learn.today"))
    user = _current_user()
    if _needs_onboarding(user):
        return redirect(url_for("onboarding.welcome"))
    record_event(user.id, "sound_gym_opened")
    return render_template(
        "sound_gym.html",
        pairs=MINIMAL_PAIRS,
        prompts=PRODUCTION_PROMPTS,
        disclaimer=DISCLAIMER,
    )


def _listen_items(language_id):
    """Items that can be played in a listening quiz."""
    return (
        Item.query.filter(
            Item.language_id == language_id,
            Item.audio_path.isnot(None),
            Item.audio_path != "",
        )
        .order_by(Item.level.asc(), Item.id.asc())
        .all()
    )


@learn.route("/listen", methods=["GET", "POST"])
def listen():
    """Listen and choose the meaning. Audio-first practice for languages whose
    deck ships recorded audio (Amharic today; Korean synthesises on demand)."""
    user = _current_user()
    if _needs_onboarding(user):
        return redirect(url_for("onboarding.welcome"))
    language = current_language(user)
    if language is None:
        abort(404)
    items = _listen_items(language.id)
    if len(items) < 4:
        return redirect(url_for("learn.today"))

    if request.method == "POST":
        quiz = session.pop("listen_quiz", None)
        if not quiz:
            return redirect(url_for("learn.listen"))
        ids = {entry["item_id"] for entry in quiz}
        by_id = {item.id: item for item in Item.query.filter(Item.id.in_(ids))}
        results = []
        score = 0
        for entry in quiz:
            chosen = request.form.get(f"answer-{entry['item_id']}", type=int)
            correct = by_id.get(entry["item_id"])
            ok = chosen == entry["item_id"]
            score += 1 if ok else 0
            results.append(
                {
                    "item": correct,
                    "chosen": by_id.get(chosen) if chosen else None,
                    "ok": ok,
                }
            )
        record_event(
            user.id, "listen_quiz_submitted", score=score, total=len(quiz)
        )
        return render_template(
            "listen_gym.html",
            language=language,
            questions=None,
            results=results,
            score=score,
            total=len(quiz),
        )

    sample = random.sample(items, min(8, len(items)))
    quiz = []
    questions = []
    for item in sample:
        distractors = random.sample(
            [other for other in items if other.id != item.id], 3
        )
        options = distractors + [item]
        random.shuffle(options)
        quiz.append({"item_id": item.id, "options": [o.id for o in options]})
        questions.append({"item": item, "options": options})
    session["listen_quiz"] = quiz
    record_event(user.id, "listen_opened", total=len(questions))
    return render_template(
        "listen_gym.html",
        language=language,
        questions=questions,
        results=None,
        score=0,
        total=len(questions),
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
    user = _current_user()
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


@learn.route("/fidel")
def fidel():
    if current_language() and current_language().code != "am":
        return redirect(url_for("learn.today"))
    return render_template("fidel_index.html", lessons=fidel_lessons())


@learn.route("/fidel/<slug>")
def fidel_lesson(slug):
    if current_language() and current_language().code != "am":
        return redirect(url_for("learn.today"))
    lessons = fidel_lessons()
    lesson = next((row for row in lessons if row["slug"] == slug), None)
    if lesson is None:
        abort(404)
    return render_template(
        "fidel_lesson.html",
        lesson=lesson,
        lessons=lessons,
        vowel_orders=VOWEL_ORDERS,
    )


@learn.route("/hangul")
def hangul():
    if _korean_only():
        return redirect(url_for("learn.today"))
    return render_template("hangul_index.html", lessons=HANGUL_LESSONS)


@learn.route("/hangul/<slug>")
def hangul_lesson(slug):
    if _korean_only():
        return redirect(url_for("learn.today"))
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
        lessons=HANGUL_LESSONS,
        next_lesson=next_lesson,
        lesson_number=index + 1,
        lesson_total=len(HANGUL_LESSONS),
    )


@learn.route("/progress")
def progress():
    user = _current_user()
    if _needs_onboarding(user):
        return redirect(url_for("onboarding.welcome"))
    language = current_language(user)
    summary = stats(user.id, language_id=language.id if language else None)
    summary["next_due_human"] = _format_next_due(summary["next_due"])
    return render_template(
        "learn_progress.html",
        summary=summary,
        skills=skill_breakdown(
            user.id, language.id if language else None
        ),
        reviews=recent_reviews(
            user.id, language_id=language.id if language else None
        ),
        can_dos=can_do_artifacts(
            user.id, language_id=language.id if language else None
        ),
        weekly=weekly_recap(
            user.id, language_id=language.id if language else None
        ),
        retention=retention_signal(
            user.id, language_id=language.id if language else None
        ),
        language=language,
    )


@learn.route("/review")
def review():
    user = _current_user()
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

    language = current_language(user)
    card = next_due_card(user.id, language_id=language.id if language else None)
    if card is None:
        summary = stats(user.id, language_id=language.id if language else None)
        summary["next_due_human"] = _format_next_due(summary["next_due"])
        session.pop("review_limit", None)
        session.pop("review_count", None)
        session.pop("review_mode", None)
        return render_template(
            "learn_done.html", summary=summary, user=user, language=language
        )

    item = card.item
    prompt_side = "target" if card.skill in {"recognize", "listen"} else "source"
    answer_side = "source" if prompt_side == "target" else "target"
    due_count = stats(
        user.id, language_id=language.id if language else None
    )["due"]
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
        language=language,
        item_lang="am" if language and language.code == "am" else "ko",
        variants=review_variants(
            item, language.code if language else "ko"
        ),
    )


@learn.route("/review/<int:card_id>", methods=["POST"])
def submit_review(card_id):
    user = _current_user()
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
        language_id = card.item.language_id if card.item else None
        if (
            new_cards_seen_today(user.id, now, language_id=language_id)
            >= daily_limit
        ):
            abort(409, description="Today's new-card limit has been reached")

    result = apply_rating(card, rating, now=now, elapsed_ms=elapsed_ms)
    maybe_add_production_card(
        card, rating, now=now, scheduled_days=result["scheduled_days"]
    )
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
    user = _current_user()
    if _needs_onboarding(user):
        return redirect(url_for("onboarding.welcome"))
    language = current_language(user)
    summary = stats(user.id, language_id=language.id if language else None)
    summary["next_due_human"] = _format_next_due(summary["next_due"])
    return render_template(
        "review_session_complete.html",
        summary=summary,
        user=user,
        mode=session.get("review_mode", user.daily_minutes),
        limit=session.get("review_limit", 20),
        count=session.get("review_count", 0),
    )
