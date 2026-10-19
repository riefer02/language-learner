"""Transcript-based speech checks.

This is intentionally *not* a pronunciation grade. It answers "did the
transcript contain the target words?" and shows what the model heard. A real
phoneme/prosody scorer arrives behind the same interface in Phase 2.
"""

import re
from difflib import SequenceMatcher

from flask import current_app
from openai import OpenAIError

from app.services.ai import OpenAIConfigError, get_openai_client
from app.utils.retries import call_with_retries


class SpeechError(RuntimeError):
    """Base error for speech checks."""


class SpeechConfigError(SpeechError):
    """Raised when speech checking is disabled or not configured."""


def _normalize(text):
    """Keep Hangul, Latin letters, and digits; remove spacing and punctuation."""
    return re.sub(r"[^0-9A-Za-z\uac00-\ud7a3]", "", (text or "").lower())


def score_transcript(target_text, transcript, threshold=None):
    """Compare the target and transcript as strings, not as pronunciation."""
    if threshold is None:
        threshold = current_app.config.get("SPEECH_ACCEPT_THRESHOLD", 0.72)

    target = _normalize(target_text)
    heard = _normalize(transcript)
    if not target:
        raise ValueError("Target text must contain Korean characters")

    match = SequenceMatcher(None, target, heard).ratio()
    acceptable = bool(heard) and match >= threshold
    if match >= 0.9:
        band = "clear"
    elif match >= 0.72:
        band = "close"
    else:
        band = "try_again"

    return {
        "match_score": round(match, 4),
        "acceptable": acceptable,
        "band": band,
        "threshold": threshold,
        "heard": transcript,
    }


def transcribe_audio(audio_bytes, filename="answer.webm", content_type="audio/webm"):
    """Return the Korean transcript for an audio clip. Raw bytes are not stored."""
    if not current_app.config.get("SPEECH_SCORING_ENABLED", True):
        raise SpeechConfigError("Speech checking is disabled for this instance")

    max_bytes = current_app.config.get("SPEECH_MAX_BYTES", 5 * 1024 * 1024)
    if not audio_bytes:
        raise ValueError("Audio file is empty")
    if len(audio_bytes) > max_bytes:
        raise ValueError("Audio file is too large")

    model = current_app.config.get(
        "SPEECH_TRANSCRIBE_MODEL", "gpt-4o-transcribe"
    )
    try:
        client = get_openai_client()
    except OpenAIConfigError as error:
        raise SpeechConfigError(
            "Speech checking needs an OpenAI API key or a configured provider"
        ) from error

    def _call():
        response = client.audio.transcriptions.create(
            model=model,
            file=(filename, audio_bytes, content_type),
            language="ko",
            response_format="json",
        )
        text = getattr(response, "text", None)
        if text is None and isinstance(response, dict):
            text = response.get("text")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Speech service returned an empty transcript")
        return text.strip()

    try:
        return call_with_retries(_call)
    except OpenAIError as error:
        raise SpeechError(f"Speech service error: {error}") from error


def score_audio(target_text, audio_bytes, filename, content_type):
    transcript = transcribe_audio(audio_bytes, filename, content_type)
    result = score_transcript(target_text, transcript)
    result["transcript"] = transcript
    result["provider"] = current_app.config.get("SPEECH_PROVIDER", "openai")
    result["model"] = current_app.config.get(
        "SPEECH_TRANSCRIBE_MODEL", "gpt-4o-transcribe"
    )
    return result
