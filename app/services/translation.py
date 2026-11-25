"""OpenAI-backed translation and conversation generation."""

import json
from dataclasses import dataclass

from flask import current_app
from pydantic import ValidationError

from app.services.ai import get_openai_client
from app.utils.caching import cache_result
from app.utils.retries import call_with_retries
from app.utils.schemas import (
    ConversationRequest,
    ConversationScenario,
    GenericTranslationResponse,
    TranslationRequest,
    contains_hangul,
)

TRANSLATION_MODEL = "gpt-5.6-luna"
TRANSLATION_CACHE_VERSION = "translation-prompt-v5"
TARGET_LANGUAGES = {
    "ko": "Korean",
    "am": "Amharic",
    "es": "Spanish",
    "ja": "Japanese",
    "en": "English",
}
CONVERSATION_MODEL = "gpt-5.6-luna"
MAX_OUTPUT_ATTEMPTS = 3


@dataclass(frozen=True)
class TranslationResult:
    translation: str
    romanization: str | None = None

# Reasoning-tier chat models (GPT-5/6, o-series) reject ``temperature`` and use
# ``max_completion_tokens`` instead of ``max_tokens``. ``gpt-5.6-luna`` replaces
# the retired ``gpt-4.1-nano`` default from October 2026.
_REASONING_PREFIXES = ("gpt-5", "gpt-6", "o1", "o3", "o4")


def _is_reasoning_model(model):
    return isinstance(model, str) and model.startswith(_REASONING_PREFIXES)


def _chat_options(model, max_tokens, temperature):
    """Build chat-completions options that work for classic and reasoning models."""
    if _is_reasoning_model(model):
        return {
            "max_completion_tokens": max_tokens,
            "reasoning_effort": "none",
        }
    return {"max_tokens": max_tokens, "temperature": temperature}


def _message_content(response):
    try:
        content = response.choices[0].message.content
    except (AttributeError, IndexError, TypeError) as error:
        raise ValueError("OpenAI response did not contain a message") from error

    if not isinstance(content, str) or not content.strip():
        raise ValueError("OpenAI returned an empty response")
    return content


def _script_ok(value, target_code):
    if target_code == "ko":
        return contains_hangul(value)
    if target_code == "am":
        return any("\u1200" <= char <= "\u137f" for char in value)
    return True


def _parse_translation_response(response, target_code="ko"):
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
        result = GenericTranslationResponse.model_validate(payload)
    except ValidationError as error:
        raise ValueError(
            "OpenAI translation response did not match the expected schema"
        ) from error
    if not _script_ok(result.translation, target_code):
        raise ValueError(
            f"Translation was not written in the target script ({target_code})"
        )
    if target_code in {"ko", "am"} and not result.romanization:
        current_app.logger.warning(
            "Translation response omitted romanization for %s", target_code
        )
    return TranslationResult(
        translation=result.translation,
        romanization=result.romanization,
    )


def _translation_model():
    return current_app.config.get("TRANSLATION_MODEL", TRANSLATION_MODEL)


def _conversation_model():
    return current_app.config.get("CONVERSATION_MODEL", CONVERSATION_MODEL)


def _request_translation(text, target_code="ko", addressee="any"):
    language = TARGET_LANGUAGES.get(target_code, "Korean")
    if target_code == "ko":
        romanization_rule = "use Revised Romanization for Korean"
    elif target_code == "am":
        romanization_rule = "use a simple Latin transliteration for Amharic"
    else:
        romanization_rule = "use a simple Latin transliteration"
    addressee_rule = ""
    if target_code == "am":
        if addressee == "male":
            addressee_rule = (
                " Address one man: use masculine second-person forms "
                "(for example -ህ, ነህ, ሁን)."
            )
        elif addressee == "female":
            addressee_rule = (
                " Address one woman: use feminine second-person forms "
                "(for example -ሽ, ነሽ, ሁኚ)."
            )
        elif addressee == "group":
            addressee_rule = " Address a group: use plural second-person forms."
        else:
            addressee_rule = (
                " The addressee is unspecified: if the phrase changes with the"
                " addressee's gender, give the masculine form first and the"
                " feminine form in parentheses."
            )
    client = get_openai_client()
    model = _translation_model()
    max_tokens = min(1200, max(220, len(text) * 4))
    response = call_with_retries(
        lambda: client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful translator. Translate the given "
                        f"English text to {language}. Respond with a JSON "
                        "object with exactly two keys: 'translation' (the "
                        "translation in its native script) and 'romanization' "
                        "(a learner-friendly Latin-script reading of the "
                        f"translation; {romanization_rule}; do not translate "
                        "it)." + addressee_rule
                    ),
                },
                {"role": "user", "content": text},
            ],
            **_chat_options(model, max_tokens=max_tokens, temperature=0.3),
        )
    )
    return _parse_translation_response(response, target_code)


def _translate_with_output_retries(text, target_code="ko", addressee="any"):
    last_error = None

    for attempt in range(MAX_OUTPUT_ATTEMPTS):
        try:
            return _request_translation(text, target_code, addressee)
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
def _translate_cached(cache_version, target_code, text, addressee):
    # The version is part of the cache key, so prompt/schema changes do not
    # serve stale translations for 24 hours.
    return _translate_with_output_retries(text, target_code, addressee)


def translate_text_with_romanization(text, target_code="ko", addressee="any"):
    """Translate and return the text plus its learner-facing romanization."""
    if addressee not in {"male", "female", "group", "any"}:
        addressee = "any"
    try:
        request = TranslationRequest.model_validate(
            {"text": text, "addressee": addressee}
        )
    except ValidationError as error:
        raise ValueError(
            "Text must be a non-empty string of at most 500 characters"
        ) from error

    cache_version = (
        f"{TRANSLATION_CACHE_VERSION}:{_translation_model()}:"
        f"{target_code}:{request.addressee}"
    )
    return _translate_cached(
        cache_version, target_code, request.text, request.addressee
    )


def translate_text(text, target_code="ko"):
    """Translate and return only the target text (backward-compatible)."""
    return translate_text_with_romanization(text, target_code).translation


def translate_to_korean(text):
    """Backward-compatible Korean wrapper."""
    return translate_text(text, "ko")


def _conversation_system_prompt(min_lines, max_lines):
    return (
        "You write short, natural conversations for Korean language learners. "
        "Return exactly one JSON object and nothing else: no markdown, no code "
        "fences, and no commentary outside the JSON. The object must have this "
        "shape:\n"
        '{"title": "...", "description": "...", "lines": ['
        '{"speaker": 1, "source_text": "...", "target_text": "..."}, ...]}\n'
        "Rules:\n"
        f"- Use between {min_lines} and {max_lines} lines.\n"
        "- Speakers must alternate, starting with speaker 1 (1, 2, 1, ...).\n"
        "- source_text and target_text must be non-empty, at most 300 "
        "characters each.\n"
        "- target_text must be natural Korean written in Hangul.\n"
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
    model = _conversation_model()
    response = call_with_retries(
        lambda: client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": _conversation_system_prompt(min_lines, max_lines),
                },
                {"role": "user", "content": prompt},
            ],
            **_chat_options(model, max_tokens=600, temperature=0.4),
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
