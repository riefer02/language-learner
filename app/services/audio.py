"""OpenAI text-to-speech helpers."""

import os

from flask import current_app

from app.services.ai import get_openai_client
from app.utils.retries import call_with_retries


def _remove_partial_file(filepath):
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except OSError as error:
        current_app.logger.warning(
            "generate_audio: could not remove partial file %s: %s", filepath, error
        )


def generate_audio(text, filepath, voice="onyx"):
    """Convert text to speech and save it as an MP3 file.

    Returns the file's basename. On any failure the destination file is
    removed so callers never see a partial or empty audio artifact.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Empty text provided for audio generation")

    text = text.strip()
    model = current_app.config.get("TTS_MODEL") or "tts-1"
    current_app.logger.info(
        "generate_audio: chars=%s voice=%s file=%s",
        len(text),
        voice,
        filepath,
    )

    def _stream_audio():
        client = get_openai_client()
        with client.audio.speech.with_streaming_response.create(
            model=model,
            voice=voice,
            input=text,
            response_format="mp3",
        ) as response:
            response.stream_to_file(filepath)

    try:
        call_with_retries(_stream_audio)

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
