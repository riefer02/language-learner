"""Generated conversations and their audio."""

import uuid

from flask import (
    abort,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from sqlalchemy.orm import selectinload

from app import db
from app.learning.service import current_language, request_language
from app.main import main
from app.main.helpers import _error, _parse_json
from app.models import Conversation, ConversationLine, Phrase
from app.models_language import Language
from app.services.ai import OpenAIConfigError
from app.services.audio import generate_audio
from app.services.translation import generate_conversation_scenario
from app.utils.audio_merge import merge_audio_files
from app.utils.media import AudioBatch, remove_files, safe_audio_filename
from app.utils.rate_limit import rate_limit
from app.utils.schemas import ConversationRequest, ConversationScenario


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
    language = request_language()
    if language is not None and language.code != "ko":
        return _error("Conversations are Korean-only for now", 400)
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
                f"conv_{safe_audio_filename(line.source_text, max_length=20)}"
                f"_{unique_id}.mp3"
            )
            staged = batch.path(filename)
            generate_audio(
                line.target_text,
                staged,
                voice=voices.get(line.speaker, voices[1]),
                language_code=language.code if language else "ko",
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

        source_language = Language.query.filter_by(code="en").first()
        phrases = [
            Phrase(
                source_text=line.source_text,
                target_text=line.target_text,
                audio_path=f"/static/audio/{filename}",
                source_language_id=(
                    source_language.id if source_language else None
                ),
                target_language_id=language.id if language else None,
            )
            for _, filename, line, _ in staging
        ]
        db.session.add_all(phrases)
        db.session.flush()

        conversation = Conversation(
            title=scenario.title,
            description=scenario.description or "",
            audio_path=f"/static/audio/{merged_filename}",
            language_id=language.id if language else None,
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
    language = request_language()
    query = Conversation.query
    if language is not None:
        query = query.filter(Conversation.language_id == language.id)
    pagination = (
        query.options(
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
    language = request_language()
    query = Conversation.query.options(
        selectinload(Conversation.lines).selectinload(ConversationLine.phrase)
    ).filter(Conversation.id == conversation_id)
    if language is not None:
        query = query.filter(Conversation.language_id == language.id)
    conversation = query.first()
    if conversation is None:
        return _error("Conversation not found", 404)
    return jsonify(conversation.to_dict())


@main.route("/<lang_code>/conversations")
def conversations():
    language = current_language()
    if language is not None and language.code != "ko":
        return redirect(url_for("learn.today"))
    page = request.args.get("page", 1, type=int)
    per_page = 10
    query = Conversation.query
    if language is not None:
        query = query.filter(Conversation.language_id == language.id)
    conversations_page = query.order_by(
        Conversation.created_at.desc(), Conversation.id.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    return render_template(
        "conversations.html", conversations=conversations_page
    )


@main.route("/<lang_code>/conversations/<int:conversation_id>")
def conversation_detail(conversation_id):
    language = current_language()
    if language is not None and language.code != "ko":
        return redirect(url_for("learn.today"))
    query = Conversation.query.options(
        selectinload(Conversation.lines).selectinload(ConversationLine.phrase)
    ).filter(Conversation.id == conversation_id)
    if language is not None:
        query = query.filter(Conversation.language_id == language.id)
    conversation = query.first()
    if conversation is None:
        abort(404)
    return render_template(
        "conversation_detail.html", conversation=conversation
    )


@main.route("/<lang_code>/conversations/new")
def new_conversation():
    language = current_language()
    if language is not None and language.code != "ko":
        return redirect(url_for("learn.today"))
    return render_template("new_conversation.html")
