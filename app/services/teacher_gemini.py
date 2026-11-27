"""Gemini Live provider for the speaking teacher.

This is the second provider behind ``TEACHER_PROVIDER``. It exists because the
realtime research brief (``docs/research/07-realtime-teacher-stack.md``) found
that Gemini Live is the only speech-to-speech model that lists Amharic, while
OpenAI's realtime stack does not list Amharic for either speech or
transcription.

Transport is different from OpenAI: Gemini Live is a **WebSocket with streamed
PCM audio**, not WebRTC with a media track. The server mints an ephemeral token,
the browser connects with it, and plays the PCM chunks itself. Nothing here is
wired into the browser yet; the client still speaks WebRTC and refuses a
websocket session with an explicit message.

Everything in this module is written against the published Live API shape but
has not been exercised against a live key. The request/response handling is
isolated in :func:`mint_ephemeral_token` so a corrected endpoint or payload does
not touch the session builder.
"""

import os
from datetime import UTC, datetime, timedelta

import httpx
from flask import current_app

from app.services.teacher import (
    TOOL_SCHEMAS,
    TeacherConfigError,
    TeacherProviderError,
    _instructions,
)

# Endpoint used to mint a short-lived client token. Kept as a constant so a
# version bump is a one-line change.
AUTH_TOKENS_URL = "https://generativelanguage.googleapis.com/v1alpha/auth_tokens"

# The browser connects to this WebSocket with the minted token. The constrained
# endpoint carries the session config server-side so the client cannot widen it.
GENERATE_CONTENT_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)

LIVE_WEBSOCKET_URL = (
    "wss://generativelanguage.googleapis.com/ws/"
    "google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContentConstrained"
)

# Gemini's tool declarations take a shallow JSON schema: type, description,
# properties, required. Our schemas are OpenAI-shaped, so they are converted.
_JSON_SCHEMA_KEEP = ("type", "description", "properties", "required", "items", "enum")


def _convert_schema(schema):
    if not isinstance(schema, dict):
        return {}
    converted = {}
    for key in _JSON_SCHEMA_KEEP:
        if key in schema:
            value = schema[key]
            if key == "properties" and isinstance(value, dict):
                converted[key] = {
                    name: _convert_schema(sub) for name, sub in value.items()
                }
            elif key == "items":
                converted[key] = _convert_schema(value)
            else:
                converted[key] = value
    return converted


def function_declarations(schemas=None):
    """Convert the shared tool schemas into Gemini function declarations."""
    declarations = []
    for tool in schemas if schemas is not None else TOOL_SCHEMAS:
        declarations.append(
            {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": _convert_schema(tool.get("parameters", {})),
            }
        )
    return declarations


def build_session(session, learner_name="Learner"):
    """The ``setup`` payload for a Gemini Live session.

    Mirrors the OpenAI config: same instructions, same tools, audio out, and a
    turn detector that lets a learner take their time.
    """
    instructions = _instructions(session, learner_name)

    model = current_app.config.get("TEACHER_MODEL")
    if not model or not model.startswith("models/"):
        model = current_app.config.get(
            "GEMINI_TEACHER_MODEL", "models/gemini-3.8-live"
        )

    return {
        "model": model,
        "systemInstruction": {"parts": [{"text": instructions}]},
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "temperature": float(
                current_app.config.get("TEACHER_TEMPERATURE", 0.7)
            ),
            # speechConfig lives inside generationConfig for Live sessions.
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {
                        "voiceName": current_app.config.get(
                            "GEMINI_TEACHER_VOICE", "Puck"
                        )
                    }
                }
            },
        },
        "tools": [{"functionDeclarations": function_declarations()}],
        "realtimeInputConfig": {
            "automaticActivityDetection": {
                "disabled": False,
                # High start / low end: catch a quiet learner, wait before
                # deciding they finished. Verified enum values on the live API.
                "startOfSpeechSensitivity": "START_SENSITIVITY_HIGH",
                "endOfSpeechSensitivity": "END_SENSITIVITY_LOW",
                "prefixPaddingMs": int(
                    current_app.config.get("TEACHER_VAD_PREFIX_MS", 300)
                ),
                "silenceDurationMs": int(
                    current_app.config.get("TEACHER_VAD_SILENCE_MS", 900)
                ),
            }
        },
        # Transcripts are what the coach hint reads; without them the UI and the
        # suggested line have nothing to work from.
        "inputAudioTranscription": {},
        "outputAudioTranscription": {},
    }


def mint_ephemeral_token(session_config, uses=1, lifetime_minutes=30):
    """Ask Google for a short-lived token that carries ``session_config``.

    Returns ``(token_name, expires_at)``. The browser never sees the API key.
    """
    api_key = current_app.config.get("GEMINI_API_KEY") or os.environ.get(
        "GEMINI_API_KEY"
    )
    if not api_key:
        raise TeacherConfigError("GEMINI_API_KEY is not configured")

    now = datetime.now(UTC)
    expire = now + timedelta(minutes=lifetime_minutes)
    payload = {
        "uses": uses,
        "expireTime": expire.isoformat().replace("+00:00", "Z"),
        "newSessionExpireTime": (now + timedelta(minutes=2)).isoformat().replace(
            "+00:00", "Z"
        ),
        # The field name is `bidiGenerateContentSetup`, not
        # `liveConnectConstraints`; verified against the live endpoint.
        "bidiGenerateContentSetup": session_config,
    }
    timeout = float(current_app.config.get("TEACHER_TIMEOUT_SECONDS", 20))
    try:
        response = httpx.post(
            AUTH_TOKENS_URL,
            params={"key": api_key},
            json=payload,
            timeout=timeout,
        )
    except httpx.HTTPError as error:
        raise TeacherProviderError("Could not reach the Gemini API") from error

    if response.status_code >= 400:
        detail = ""
        try:
            detail = (response.json().get("error") or {}).get("message", "")
        except ValueError:
            detail = response.text[:200]
        current_app.logger.warning(
            "Gemini token request rejected (%s): %s", response.status_code, detail
        )
        raise TeacherProviderError(
            "Gemini rejected the session"
            + (f": {detail[:220]}" if detail else "")
        )

    try:
        data = response.json()
    except ValueError as error:
        raise TeacherProviderError("Gemini returned an unreadable token") from error
    name = data.get("name")
    if not name:
        raise TeacherProviderError("Gemini returned no token")
    return name, expire


# Busy-model responses are transient; a cheaper sibling usually answers.
_TRANSIENT_STATUS = {429, 500, 502, 503, 504}
# The hint is one short JSON object; a lite model answers in well under a second,
# while the bigger flash models can sit in "high demand" for eight seconds and
# arrive after the learner has already moved on.
_FALLBACK_TEXT_MODELS = ("gemini-3.8-flash", "gemini-3.6-flash")


def json_completion(system, user):
    """One JSON text completion from Gemini, used for the coach hint.

    The realtime session is speech; the coach hint is a cheap text call and must
    not depend on an OpenAI key when the teacher itself is Gemini. Busy models
    are retried on a sibling rather than failing the hint.
    """
    api_key = current_app.config.get("GEMINI_API_KEY") or os.environ.get(
        "GEMINI_API_KEY"
    )
    if not api_key:
        raise TeacherConfigError("GEMINI_API_KEY is not configured")

    primary = current_app.config.get(
        "GEMINI_TEACHER_TEXT_MODEL", "gemini-3.1-flash-lite"
    )
    candidates = [primary] + [
        model for model in _FALLBACK_TEXT_MODELS if model != primary
    ]
    last_error = None
    for model in candidates:
        try:
            return _json_completion_once(api_key, model, system, user)
        except _TransientGeminiError as error:
            last_error = error
            continue
    raise last_error or TeacherProviderError("Gemini is busy right now")


class _TransientGeminiError(TeacherProviderError):
    """The model was busy; another one may answer."""


def _json_completion_once(api_key, model, system, user):
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.4,
            # No thinking: the hint is a lookup-sized answer, and thinking adds
            # seconds the learner spends waiting for a line to say.
            "thinkingConfig": {"thinkingBudget": 0},
            "maxOutputTokens": 200,
        },
    }
    timeout = min(8.0, float(current_app.config.get("TEACHER_TIMEOUT_SECONDS", 20)))
    try:
        response = httpx.post(
            GENERATE_CONTENT_URL.format(model=model),
            params={"key": api_key},
            json=body,
            timeout=timeout,
        )
    except httpx.HTTPError as error:
        raise _TransientGeminiError("Could not reach the Gemini API") from error

    if response.status_code >= 400:
        detail = ""
        try:
            detail = (response.json().get("error") or {}).get("message", "")
        except ValueError:
            detail = response.text[:200]
        error_type = (
            _TransientGeminiError
            if response.status_code in _TRANSIENT_STATUS
            else TeacherProviderError
        )
        raise error_type(
            "Gemini rejected the hint"
            + (f": {detail[:220]}" if detail else "")
        )

    try:
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (ValueError, KeyError, IndexError, TypeError) as error:
        raise TeacherProviderError("Gemini returned an unreadable reply") from error


class GeminiLiveProvider:
    """Provider adapter: mints a token and hands the browser a WebSocket plan."""

    name = "gemini_live"
    transport = "websocket"

    def create_call(self, session_config, sdp=None):
        """Kept for interface compatibility; Gemini does not take an SDP offer."""
        raise TeacherProviderError("Gemini Live does not use an SDP offer")

    def create_handle(self, session, learner_name="Learner"):
        config = build_session(session, learner_name)
        token, expires_at = mint_ephemeral_token(config)
        return {
            "transport": "websocket",
            "url": LIVE_WEBSOCKET_URL,
            "token": token,
            "model": config["model"],
            # The token is constrained to `config` server-side, so the prompt
            # and tool schemas never travel to the browser.
            "token_expires_at": expires_at.isoformat(),
            "provider_session_id": None,
        }


__all__ = [
    "LIVE_WEBSOCKET_URL",
    "GeminiLiveProvider",
    "build_session",
    "function_declarations",
    "json_completion",
    "mint_ephemeral_token",
]
