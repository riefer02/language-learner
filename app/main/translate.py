"""Translation and saved-phrase APIs."""

import uuid

from flask import current_app, jsonify, request

from app import db
from app.learning.service import request_language
from app.main import main
from app.main.helpers import _error, _parse_json
from app.models import Phrase
from app.models_language import Language
from app.services.ai import OpenAIConfigError
from app.services.audio import generate_audio
from app.services.translation import translate_text_with_romanization
from app.utils.media import AudioBatch, remove_files, safe_audio_filename
from app.utils.rate_limit import rate_limit
from app.utils.schemas import TranslationRequest


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

    language = request_language()
    target_code = language.code if language else "ko"
    try:
        result = translate_text_with_romanization(payload.text, target_code)
    except ValueError as exc:
        return _error(str(exc), 400)
    except OpenAIConfigError as exc:
        current_app.logger.error("AI configuration error: %s", exc)
        return _error("Translation service is not configured", 503)

    target_text = result.translation

    unique_id = uuid.uuid4().hex[:8]
    filename = (
        f"{safe_audio_filename(payload.text, max_length=30)}_{unique_id}.mp3"
    )
    batch = AudioBatch(current_app.config["MEDIA_TMP_DIR"])
    moved = []
    try:
        staged = batch.path(filename)
        generate_audio(target_text, staged, language_code=target_code)
        moved = batch.commit_to(
            current_app.config["AUDIO_DIR"], [(staged, filename)]
        )

        source_language = Language.query.filter_by(code="en").first()
        phrase = Phrase(
            audio_path=f"/static/audio/{filename}",
            source_language_id=source_language.id if source_language else None,
            target_language_id=language.id if language else None,
            source_text=payload.text,
            target_text=target_text,
            target_transliteration=result.romanization,
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
    data = phrase.to_dict()
    data.update(
        {
            "target_text": target_text,
            "romanization": result.romanization,
            "target_lang": target_code,
            "target_language": language.name if language else "Korean",
        }
    )
    return jsonify(data)


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
