"""OpenAI-backed translation and conversation generation."""

import json

from flask import current_app
from pydantic import ValidationError

from app.services.ai import get_openai_client
from app.utils.caching import cache_result
from app.utils.retries import call_with_retries
from app.utils.schemas import (
    ConversationRequest,
    ConversationScenario,
    TranslationRequest,
    TranslationResponse,
)

TRANSLATION_MODEL = "gpt-4.1-nano"
TRANSLATION_CACHE_VERSION = "translation-prompt-v2"
CONVERSATION_MODEL = "gpt-4.1-nano"
MAX_OUTPUT_ATTEMPTS = 3


def _message_content(response):
    try:
        content = response.choices[0].message.content
    except (AttributeError, IndexError, TypeError) as error:
        raise ValueError("OpenAI response did not contain a message") from error

    if not isinstance(content, str) or not content.strip():
        raise ValueError("OpenAI returned an empty response")
    return content


def _parse_translation_response(response):
    content = _message_content(response)

    try:
        payload = json.loads(content)
    except json.JSONDecodeError as error:
        raise ValueError("OpenAI translation response was not valid JSON") from error

    if not isinstance(payload, dict):
        raise ValueError(  # noqa: TRY004 - model output, not caller input
            "OpenAI translation response must be a JSON object"
        )

    try:
        return TranslationResponse.model_validate(payload).korean_translation
    except ValidationError as error:
        raise ValueError(
            "OpenAI translation response did not match the expected schema"
        ) from error


def _translation_model():
    return current_app.config.get("TRANSLATION_MODEL", TRANSLATION_MODEL)


def _conversation_model():
    return current_app.config.get("CONVERSATION_MODEL", CONVERSATION_MODEL)


def _request_translation(text):
    client = get_openai_client()
    response = call_with_retries(
        lambda: client.chat.completions.create(
            model=_translation_model(),
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful translator. Translate the given English "
                        "text to Korean. Respond with a JSON object containing a "
                        "single key 'korean_translation' whose value is the Korean "
                        "translation."
                    ),
                },
                {"role": "user", "content": text},
            ],
            temperature=0.3,
            max_tokens=150,
        )
    )
    return _parse_translation_response(response)


def _translate_with_output_retries(text):
    last_error = None

    for attempt in range(MAX_OUTPUT_ATTEMPTS):
        try:
            return _request_translation(text)
        except ValueError as error:
            last_error = error
            current_app.logger.warning(
                "Invalid translation response (attempt %s/%s): %s",
                attempt + 1,
                MAX_OUTPUT_ATTEMPTS,
                error,
            )

    raise ValueError(
        f"OpenAI returned an invalid translation response after "
        f"{MAX_OUTPUT_ATTEMPTS} attempts"
    ) from last_error


@cache_result(expire_seconds=86400)
def _translate_cached(cache_version, text):
    # The version is part of the cache key, so prompt/schema changes do not
    # serve stale translations for 24 hours.
    return _translate_with_output_retries(text)


def translate_to_korean(text):
    """Translate English text to Korean, returning validated Korean text."""
    try:
        request = TranslationRequest.model_validate({"text": text})
    except ValidationError as error:
        raise ValueError(
            "Text must be a non-empty string of at most 500 characters"
        ) from error

    cache_version = f"{TRANSLATION_CACHE_VERSION}:{_translation_model()}"
    return _translate_cached(cache_version, request.text)


def _conversation_system_prompt(min_lines, max_lines):
    return (
        "You write short, natural conversations for Korean language learners. "
        "Return exactly one JSON object and nothing else: no markdown, no code "
        "fences, and no commentary outside the JSON. The object must have this "
        "shape:\n"
        '{"title": "...", "description": "...", "lines": ['
        '{"speaker": 1, "english_text": "...", "korean_text": "..."}, ...]}\n'
        "Rules:\n"
        f"- Use between {min_lines} and {max_lines} lines.\n"
        "- Speakers must alternate, starting with speaker 1 (1, 2, 1, ...).\n"
        "- english_text and korean_text must be non-empty, at most 300 "
        "characters each.\n"
        "- korean_text must be natural Korean written in Hangul.\n"
        "- title must be non-empty and at most 200 characters; description at "
        "most 1000 characters.\n"
    )


def _parse_conversation_response(response, min_lines, max_lines):
    content = _message_content(response)

    try:
        payload = json.loads(content)
    except json.JSONDecodeError as error:
        raise ValueError("OpenAI conversation response was not valid JSON") from error

    if not isinstance(payload, dict):
        raise ValueError(  # noqa: TRY004 - model output, not caller input
            "OpenAI conversation response must be a JSON object"
        )

    try:
        scenario = ConversationScenario.model_validate(payload)
    except ValidationError as error:
        raise ValueError(
            "OpenAI conversation response did not match the expected schema"
        ) from error

    if not min_lines <= len(scenario.lines) <= max_lines:
        raise ValueError(
            f"Conversation must contain between {min_lines} and {max_lines} lines"
        )

    return scenario


def _request_conversation(prompt, min_lines, max_lines):
    client = get_openai_client()
    response = call_with_retries(
        lambda: client.chat.completions.create(
            model=_conversation_model(),
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": _conversation_system_prompt(min_lines, max_lines),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=600,
        )
    )
    return _parse_conversation_response(response, min_lines, max_lines)


def generate_conversation_scenario(prompt, min_lines=2, max_lines=4):
    """Generate a validated two-speaker conversation scenario.

    Returns a plain dict only after the model output has passed
    :class:`ConversationScenario` validation.
    """
    if (
        not isinstance(min_lines, int)
        or not isinstance(max_lines, int)
        or not 2 <= min_lines <= max_lines <= 4
    ):
        raise ValueError(
            "min_lines and max_lines must satisfy 2 <= min_lines <= max_lines <= 4"
        )

    try:
        request = ConversationRequest.model_validate({"prompt": prompt})
    except ValidationError as error:
        raise ValueError(
            "Prompt must be a non-empty string of at most 200 characters"
        ) from error

    last_error = None
    for attempt in range(MAX_OUTPUT_ATTEMPTS):
        try:
            scenario = _request_conversation(
                request.prompt, min_lines, max_lines
            )
            return scenario.model_dump()
        except ValueError as error:
            last_error = error
            current_app.logger.warning(
                "Invalid conversation response (attempt %s/%s): %s",
                attempt + 1,
                MAX_OUTPUT_ATTEMPTS,
                error,
            )

    raise ValueError(
        f"OpenAI returned an invalid conversation scenario after "
        f"{MAX_OUTPUT_ATTEMPTS} attempts"
    ) from last_error
