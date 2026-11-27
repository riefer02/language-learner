"""Translation and saved-phrase APIs."""

import uuid

from flask import current_app, jsonify, request

from app import db
from app.languages.variants import (
    addressee_label,
    normalize_addressee,
    normalize_register,
    register_label,
)
from app.learning.service import request_language, review_variants
from app.main import main
from app.main.helpers import _error, _parse_json
from app.models import Item, Phrase
from app.models_language import Language
from app.services.ai import OpenAIConfigError
from app.services.audio import generate_audio
from app.services.translation import translate_text_with_romanization
from app.services.variant_audio import generate_variant_audio
from app.utils.media import AudioBatch, remove_files, safe_audio_filename
from app.utils.rate_limit import rate_limit
from app.utils.schemas import TranslationRequest, VariantAudioRequest


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
    addressee = normalize_addressee(target_code, payload.addressee)
    register = normalize_register(target_code, payload.formality)
    try:
        result = translate_text_with_romanization(
            payload.text,
            target_code,
            addressee=addressee,
            register=register,
        )
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
            addressee=addressee,
            register=register,
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
            "addressee": addressee,
            "addressee_label": addressee_label(target_code, addressee, register),
            "register": register,
            "register_label": register_label(target_code, register),
            "target_lang": target_code,
            "target_language": language.name if language else "Korean",
        }
    )
    return jsonify(data)


@main.route("/api/variants/audio", methods=["POST"])
@rate_limit(
    limit=lambda: current_app.config.get("RATE_LIMIT_VARIANT_AUDIO", 30),
    window_seconds=lambda: current_app.config.get(
        "RATE_LIMIT_WINDOW_SECONDS", 60
    ),
    scope="variant_audio",
)
def api_variant_audio():
    """Generate and cache audio for one form on a review card.

    The text is allowlisted against the card's curated variants (or its own
    answer), so this cannot be used to generate arbitrary speech.
    """
    payload, error = _parse_json(VariantAudioRequest)
    if error:
        return error

    language = request_language()
    if language is None:
        return _error("No active language", 404)

    item = db.session.get(Item, payload.item_id)
    if item is None or item.language_id != language.id:
        return _error("That review card is not available", 404)

    variants = review_variants(item, language.code)
    match = next(
        (variant for variant in variants if variant["text"] == payload.text),
        None,
    )
    if match is None and payload.text != item.target_text:
        return _error("That form is not part of this card", 400)
    if match is not None and match["audio_path"]:
        return jsonify({"audio_path": match["audio_path"], "text": payload.text})
    if match is None and item.audio_path:
        return jsonify({"audio_path": item.audio_path, "text": payload.text})

    try:
        audio_path = generate_variant_audio(language, payload.text)
    except OpenAIConfigError:
        return _error("Audio service is not configured", 503)
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception:
        current_app.logger.exception("Variant audio generation failed")
        return _error("Could not generate audio", 500)

    return jsonify({"audio_path": audio_path, "text": payload.text})


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
