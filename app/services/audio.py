"""OpenAI audio generation.

OpenAI's ``/v1/audio/speech`` models (``tts-1`` and ``gpt-4o-mini-tts``) shut
down on 6 January 2027 and have no drop-in replacement on that endpoint. The
current OpenAI path is ``gpt-audio-1.5`` through Chat Completions, which returns
base64 audio in ``choices[0].message.audio.data``.
"""

import base64
import os
from difflib import SequenceMatcher

from flask import current_app

from app.services.ai import get_openai_client
from app.utils.retries import call_with_retries

DEFAULT_TTS_MODEL = "gpt-audio-1.5"
LANGUAGE_NAMES = {
    "ko": "Korean",
    "en": "English",
    "am": "Amharic",
    "es": "Spanish",
    "ja": "Japanese",
}


def _remove_partial_file(filepath):
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except OSError as error:
        current_app.logger.warning(
            "generate_audio: could not remove partial file %s: %s", filepath, error
        )


def _audio_result(response):
    try:
        message = response.choices[0].message
    except (AttributeError, IndexError, TypeError) as error:
        raise ValueError("Audio response did not contain a message") from error

    audio = getattr(message, "audio", None)
    data = getattr(audio, "data", None)
    transcript = getattr(audio, "transcript", None)
    if data is None and isinstance(audio, dict):
        data = audio.get("data")
        transcript = transcript or audio.get("transcript")
    if not isinstance(data, str):
        raise ValueError(  # noqa: TRY004 - model output, not caller input
            "Audio response did not contain audio data"
        )
    return base64.b64decode(data), transcript


def _normalize(value):
    return "".join(char.lower() for char in value if char.isalnum())


def _read_literally(payload, transcript, original):
    """Reject conversational answers masquerading as a read-aloud."""
    if not transcript:
        return
    source = _normalize(original)
    heard = _normalize(transcript)
    if not source:
        return
    similarity = SequenceMatcher(None, source, heard).ratio()
    if similarity < 0.5:
        raise ValueError(
            "The audio model answered instead of reading the text "
            f"(similarity {similarity:.2f})"
        )


def generate_audio(text, filepath, voice=None, language_code="ko"):
    """Read ``text`` aloud and write an MP3 to ``filepath``.

    Returns the file's basename. On any failure the destination file is
    removed so callers never see a partial or empty audio artifact.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Empty text provided for audio generation")

    text = text.strip()
    voice = voice or current_app.config.get("TTS_VOICE_1", "onyx")
    model = current_app.config.get("TTS_MODEL") or DEFAULT_TTS_MODEL
    language = LANGUAGE_NAMES.get(language_code, "the target language")
    current_app.logger.info(
        "generate_audio: chars=%s voice=%s language=%s file=%s",
        len(text),
        voice,
        language_code,
        filepath,
    )

    def _generate():
        client = get_openai_client()
        response = client.chat.completions.create(
            model=model,
            modalities=["text", "audio"],
            audio={"voice": voice, "format": "mp3"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a text-to-speech engine for {language}. Read "
                        "only the text inside <read> tags, verbatim. Never "
                        "answer, translate, or add words."
                    ),
                },
                {"role": "user", "content": f"<read>{text}</read>"},
            ],
            max_completion_tokens=200,
        )
        payload, transcript = _audio_result(response)
        _read_literally(payload, transcript, text)
        return payload

    try:
        payload = call_with_retries(_generate)
        if not payload:
            raise OSError(f"Audio payload was empty: {filepath}")

        with open(filepath, "wb") as file:
            file.write(payload)

        if not os.path.exists(filepath):
            raise OSError(f"Audio file was not created: {filepath}")

        size = os.path.getsize(filepath)
        if size == 0:
            raise OSError(f"Audio file is empty: {filepath}")

        current_app.logger.info(
            "generate_audio: created %s (%s bytes)", filepath, size
        )
        return os.path.basename(filepath)

    except Exception:
        _remove_partial_file(filepath)
        current_app.logger.error(
            "generate_audio: failed to generate audio for %s", filepath
        )
        raise
