"""Generate and store audio for one review alternate form."""

import os
import uuid

from flask import current_app

from app import db
from app.languages.variants import variant_audio_filename, variant_audio_url
from app.models import Item
from app.services.audio import generate_audio
from app.utils.media import AudioBatch, remove_files, safe_audio_filename


def _stored_item_audio(items, audio_dir):
    for item in items:
        if not item.audio_path:
            continue
        path = os.path.join(audio_dir, os.path.basename(item.audio_path))
        try:
            if os.path.getsize(path) > 0:
                return item.audio_path
        except OSError:
            continue
    return None


def generate_variant_audio(language, text, voice=None, force=False):
    """Read one form aloud once and return its public audio URL.

    Gendered Amharic forms are also real ``Item`` rows, so the item rows are
    pointed at the same file and the main answer gains audio too. Forms that
    exist only as curated alternates get a stable content-hashed filename.
    """
    text = (text or "").strip()
    if not text:
        raise ValueError("Empty text provided for audio generation")

    audio_dir = current_app.config["AUDIO_DIR"]
    items = (
        Item.query.filter_by(language_id=language.id, target_text=text)
        .order_by(Item.id.asc())
        .all()
    )

    if not force:
        existing = _stored_item_audio(items, audio_dir)
        if existing is not None:
            for item in items:
                if item.audio_path != existing:
                    item.audio_path = existing
                    db.session.add(item)
            db.session.commit()
            return existing

        existing_variant = variant_audio_url(audio_dir, language.code, text)
        if existing_variant is not None:
            for item in items:
                item.audio_path = existing_variant
                db.session.add(item)
            db.session.commit()
            return existing_variant

    if items:
        filename = (
            f"item_{items[0].id}_"
            f"{safe_audio_filename(items[0].gloss, max_length=20)}_"
            f"{uuid.uuid4().hex[:6]}.mp3"
        )
    else:
        filename = variant_audio_filename(language.code, text)

    batch = AudioBatch(current_app.config["MEDIA_TMP_DIR"])
    moved = []
    try:
        staged = batch.path(filename)
        generate_audio(text, staged, voice=voice, language_code=language.code)
        moved = batch.commit_to(audio_dir, [(staged, filename)])
        public_path = f"/static/audio/{filename}"
        if items:
            for item in items:
                item.audio_path = public_path
                db.session.add(item)
            db.session.commit()
            # The database now references the file; do not delete it below.
            moved = []
        return public_path
    except Exception:
        db.session.rollback()
        remove_files(moved)
        raise
    finally:
        batch.cleanup()
