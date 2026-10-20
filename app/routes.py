import uuid
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import (
    Blueprint,
    abort,
    current_app,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_wtf.csrf import validate_csrf
from pydantic import ValidationError
from sqlalchemy import or_, text
from sqlalchemy.orm import selectinload
from werkzeug.exceptions import BadRequest

from app import db
from app.learning.service import get_or_create_local_user
from app.models import Conversation, ConversationLine, Item, Phrase
from app.services.ai import OpenAIConfigError
from app.services.audio import generate_audio
from app.services.push import (
    push_configured,
    subscribe,
    unsubscribe,
)
from app.services.translation import (
    generate_conversation_scenario,
    translate_to_korean,
)
from app.utils.audio_merge import merge_audio_files
from app.utils.media import (
    AudioBatch,
    remove_files,
    safe_audio_filename,
)
from app.utils.rate_limit import rate_limit
from app.utils.schemas import (
    ConversationRequest,
    ConversationScenario,
    TranslationRequest,
)

main = Blueprint("main", __name__)


def _request_id():
    return getattr(g, "request_id", "")


def _error(message, status):
    return jsonify({"error": message, "request_id": _request_id()}), status


def _parse_json(schema):
    """Return ``(model, None)`` or ``(None, error_response)``."""
    if not request.is_json:
        return None, _error("Request body must be JSON", 415)

    payload = request.get_json(silent=True)
    if payload is None:
        return None, _error("Request body must be valid JSON", 400)

    try:
        return schema.model_validate(payload), None
    except ValidationError as error:
        details = error.errors()
        message = "Invalid request"
        if details:
            location = ".".join(str(part) for part in details[0].get("loc", ()))
            message = (
                f"{location}: {details[0].get('msg')}"
                if location
                else details[0].get("msg", message)
            )
        return None, _error(message, 400)


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/library")
def library():
    page = request.args.get("page", 1, type=int)
    per_page = 10
    phrases = Phrase.query.order_by(
        Phrase.created_at.desc(), Phrase.id.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    return render_template("library.html", phrases=phrases)


@main.route("/resources")
def resources():
    query_text = (request.args.get("q") or "").strip()[:100]
    item_type = request.args.get("type", "")
    level = request.args.get("level", type=int)

    query = Item.query
    if query_text:
        like = f"%{query_text}%"
        query = query.filter(
            or_(
                Item.korean.ilike(like),
                Item.english.ilike(like),
                Item.romanization.ilike(like),
                Item.notes.ilike(like),
            )
        )
    if item_type in {"lexeme", "chunk", "grammar", "sentence"}:
        query = query.filter(Item.item_type == item_type)
    if level in {1, 2, 3, 4, 5, 6}:
        query = query.filter(Item.level == level)

    items = query.order_by(Item.level.asc(), Item.id.asc()).limit(100).all()
    counts = {
        "total": Item.query.count(),
        "grammar": Item.query.filter_by(item_type="grammar").count(),
        "chunks": Item.query.filter_by(item_type="chunk").count(),
        "words": Item.query.filter_by(item_type="lexeme").count(),
    }

    return render_template(
        "resources.html",
        items=items,
        q=query_text,
        item_type=item_type,
        level=level,
        counts=counts,
    )


def _check_csrf():
    if current_app.config.get("WTF_CSRF_ENABLED", True):
        try:
            validate_csrf(request.form.get("csrf_token"))
        except Exception as error:
            raise BadRequest("Invalid or missing CSRF token") from error


@main.route("/settings", methods=["GET", "POST"])
def settings():
    user = get_or_create_local_user()
    if request.method == "POST":
        _check_csrf()
        goal = request.form.get("goal", user.goal)
        daily_minutes = request.form.get("daily_minutes", type=int)
        experience = request.form.get("experience", user.experience)
        timezone = request.form.get("timezone") or user.timezone
        reminder_time = request.form.get("reminder_time") or "19:00"

        try:
            ZoneInfo(timezone)
        except (KeyError, ValueError, ZoneInfoNotFoundError):
            timezone = "UTC"

        if daily_minutes in {3, 10, 25}:
            user.daily_minutes = daily_minutes
        if goal in {
            "everyday",
            "travel",
            "work",
            "culture",
            "topik",
            "family",
        }:
            user.goal = goal
        if experience in {"new", "hangul", "some", "intermediate"}:
            user.experience = experience
        user.timezone = timezone
        try:
            hour, minute = [
                int(part) for part in reminder_time.split(":")
            ]
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                user.reminder_time = f"{hour:02d}:{minute:02d}"
        except (TypeError, ValueError):
            pass
        user.reminder_enabled = request.form.get("reminder_enabled") == "on"
        db.session.commit()
        return redirect(url_for("main.settings", saved=1))

    return render_template(
        "settings.html",
        user=user,
        push_enabled=push_configured(),
        vapid_public_key=current_app.config.get("VAPID_PUBLIC_KEY"),
        saved=request.args.get("saved") == "1",
    )


@main.route("/api/push/subscribe", methods=["POST"])
def push_subscribe():
    user = get_or_create_local_user()
    if not push_configured():
        return jsonify({"error": "Push is not configured on this server"}), 503

    if current_app.config.get("WTF_CSRF_ENABLED", True):
        try:
            validate_csrf(request.headers.get("X-CSRFToken"))
        except Exception as error:
            raise BadRequest("Invalid or missing CSRF token") from error

    payload = request.get_json(silent=True) or {}
    keys = payload.get("keys") or {}
    try:
        subscribe(
            user,
            endpoint=payload.get("endpoint"),
            p256dh=keys.get("p256dh"),
            auth=keys.get("auth"),
            user_agent=request.user_agent.string,
        )
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    return jsonify({"ok": True})


@main.route("/api/push/unsubscribe", methods=["POST"])
def push_unsubscribe():
    user = get_or_create_local_user()
    if current_app.config.get("WTF_CSRF_ENABLED", True):
        try:
            validate_csrf(request.headers.get("X-CSRFToken"))
        except Exception as error:
            raise BadRequest("Invalid or missing CSRF token") from error
    payload = request.get_json(silent=True) or {}
    unsubscribe(user, payload.get("endpoint"))
    return jsonify({"ok": True})


@main.route("/offline")
def offline():
    return render_template("offline.html")


@main.route("/sw.js")
def service_worker():
    response = send_from_directory(
        current_app.static_folder, "sw.js", mimetype="application/javascript"
    )
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache"
    return response


@main.route("/healthz")
def healthz():
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        current_app.logger.exception("Health check database probe failed")
        return jsonify({"status": "degraded", "database": "unavailable"}), 503
    return jsonify({"status": "ok"}), 200


@main.route("/api/translate", methods=["POST"])
@rate_limit(
    limit=lambda: current_app.config.get("RATE_LIMIT_TRANSLATE", 10),
    window_seconds=lambda: current_app.config.get(
        "RATE_LIMIT_WINDOW_SECONDS", 60
    ),
    scope="translate",
)
def api_translate():
    payload, error = _parse_json(TranslationRequest)
    if error:
        return error

    try:
        korean_text = translate_to_korean(payload.text)
    except ValueError as exc:
        return _error(str(exc), 400)
    except OpenAIConfigError as exc:
        current_app.logger.error("AI configuration error: %s", exc)
        return _error("Translation service is not configured", 503)

    unique_id = uuid.uuid4().hex[:8]
    filename = (
        f"{safe_audio_filename(payload.text, max_length=30)}_{unique_id}.mp3"
    )
    batch = AudioBatch(current_app.config["MEDIA_TMP_DIR"])
    moved = []
    try:
        staged = batch.path(filename)
        generate_audio(korean_text, staged)
        moved = batch.commit_to(
            current_app.config["AUDIO_DIR"], [(staged, filename)]
        )

        phrase = Phrase(
            english_text=payload.text,
            korean_text=korean_text,
            audio_path=f"/static/audio/{filename}",
        )
        db.session.add(phrase)
        db.session.commit()
    except OpenAIConfigError as exc:
        db.session.rollback()
        remove_files(moved)
        current_app.logger.error("AI configuration error: %s", exc)
        return _error("Audio service is not configured", 503)
    except Exception:
        db.session.rollback()
        remove_files(moved)
        current_app.logger.exception("Translation request failed")
        return _error("An error occurred during translation or audio generation", 500)
    finally:
        batch.cleanup()

    # Serialize after the commit so a response-formatting error cannot trigger
    # the media cleanup and leave committed rows pointing at deleted files.
    return jsonify(phrase.to_dict())


@main.route("/api/phrases", methods=["GET"])
def api_phrases():
    page = request.args.get("page", 1, type=int)
    per_page = min(max(request.args.get("per_page", 20, type=int), 1), 100)
    pagination = Phrase.query.order_by(
        Phrase.created_at.desc(), Phrase.id.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify(
        {
            "phrases": [phrase.to_dict() for phrase in pagination.items],
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": pagination.page,
            "per_page": per_page,
        }
    )


def _conversation_voices():
    return {
        1: current_app.config.get("TTS_VOICE_1", "onyx"),
        2: current_app.config.get("TTS_VOICE_2", "nova"),
    }


@main.route("/api/conversation", methods=["POST"])
@rate_limit(
    limit=lambda: current_app.config.get("RATE_LIMIT_CONVERSATION", 5),
    window_seconds=lambda: current_app.config.get(
        "RATE_LIMIT_WINDOW_SECONDS", 60
    ),
    scope="conversation",
)
def api_conversation():
    payload, error = _parse_json(ConversationRequest)
    if error:
        return error

    try:
        scenario = generate_conversation_scenario(payload.prompt)
        scenario = ConversationScenario.model_validate(scenario)
    except ValueError as exc:
        return _error(str(exc), 400)
    except OpenAIConfigError as exc:
        current_app.logger.error("AI configuration error: %s", exc)
        return _error("Conversation service is not configured", 503)

    audio_dir = current_app.config["AUDIO_DIR"]
    voices = _conversation_voices()
    batch = AudioBatch(current_app.config["MEDIA_TMP_DIR"])
    moved = []

    try:
        # Generate every line into the private staging directory first. No
        # database write transaction is open during these network calls.
        staging = []
        merged_filename = f"conversation_{uuid.uuid4().hex[:8]}.mp3"
        for index, line in enumerate(scenario.lines):
            unique_id = uuid.uuid4().hex[:8]
            filename = (
                f"conv_{safe_audio_filename(line.english_text, max_length=20)}"
                f"_{unique_id}.mp3"
            )
            staged = batch.path(filename)
            generate_audio(
                line.korean_text,
                staged,
                voice=voices.get(line.speaker, voices[1]),
            )
            staging.append((staged, filename, line, index))

        merged_staged = batch.path(merged_filename)
        merge_audio_files(
            [item[0] for item in staging],
            merged_staged,
            pause_seconds=1.5,
        )

        mapping = [(item[0], item[1]) for item in staging]
        mapping.append((merged_staged, merged_filename))
        moved = batch.commit_to(audio_dir, mapping)

        phrases = [
            Phrase(
                english_text=line.english_text,
                korean_text=line.korean_text,
                audio_path=f"/static/audio/{filename}",
            )
            for _, filename, line, _ in staging
        ]
        db.session.add_all(phrases)
        db.session.flush()

        conversation = Conversation(
            title=scenario.title,
            description=scenario.description or "",
            audio_path=f"/static/audio/{merged_filename}",
        )
        db.session.add(conversation)
        db.session.flush()

        for phrase, (_, _, line, index) in zip(phrases, staging):
            db.session.add(
                ConversationLine(
                    conversation_id=conversation.id,
                    phrase_id=phrase.id,
                    speaker=f"Speaker {line.speaker}",
                    order=index,
                )
            )

        db.session.commit()
    except OpenAIConfigError as exc:
        db.session.rollback()
        remove_files(moved)
        current_app.logger.error("AI configuration error: %s", exc)
        return _error("Audio service is not configured", 503)
    except Exception:
        db.session.rollback()
        remove_files(moved)
        current_app.logger.exception("Conversation request failed")
        return _error(
            "An error occurred during conversation generation", 500
        )
    finally:
        batch.cleanup()

    return jsonify(conversation.to_dict())


@main.route("/api/conversations", methods=["GET"])
def api_conversations():
    page = request.args.get("page", 1, type=int)
    per_page = min(max(request.args.get("per_page", 10, type=int), 1), 50)
    pagination = (
        Conversation.query.options(
            selectinload(Conversation.lines).selectinload(
                ConversationLine.phrase
            )
        )
        .order_by(Conversation.created_at.desc(), Conversation.id.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return jsonify(
        {
            "conversations": [
                conversation.to_dict() for conversation in pagination.items
            ],
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": pagination.page,
            "per_page": per_page,
        }
    )


@main.route("/api/conversations/<int:conversation_id>", methods=["GET"])
def api_conversation_detail(conversation_id):
    conversation = (
        Conversation.query.options(
            selectinload(Conversation.lines).selectinload(
                ConversationLine.phrase
            )
        )
        .filter(Conversation.id == conversation_id)
        .first()
    )
    if conversation is None:
        return _error("Conversation not found", 404)
    return jsonify(conversation.to_dict())


@main.route("/conversations")
def conversations():
    page = request.args.get("page", 1, type=int)
    per_page = 10
    conversations_page = Conversation.query.order_by(
        Conversation.created_at.desc(), Conversation.id.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    return render_template(
        "conversations.html", conversations=conversations_page
    )


@main.route("/conversations/<int:conversation_id>")
def conversation_detail(conversation_id):
    conversation = (
        Conversation.query.options(
            selectinload(Conversation.lines).selectinload(
                ConversationLine.phrase
            )
        )
        .filter(Conversation.id == conversation_id)
        .first()
    )
    if conversation is None:
        abort(404)
    return render_template(
        "conversation_detail.html", conversation=conversation
    )


@main.route("/conversations/new")
def new_conversation():
    return render_template("new_conversation.html")
