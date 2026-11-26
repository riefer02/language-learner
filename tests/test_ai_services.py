"""Self-contained tests for the AI services, schemas, retries, and TTS."""

import base64
import json
from types import SimpleNamespace

import httpx
import pytest
from flask import Flask
from openai import (
    APITimeoutError,
    AuthenticationError,
    InternalServerError,
    RateLimitError,
)
from pydantic import ValidationError

from app.services import ai
from app.services import audio as audio_service
from app.services import translation as translation_service
from app.utils import caching
from app.utils import retries as retries_module
from app.utils.retries import call_with_retries
from app.utils.schemas import ConversationScenario, GenericTranslationResponse

API_URL = "https://api.openai.com/v1/chat/completions"


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.update(TESTING=True, OPENAI_API_KEY="test-key")
    return app


@pytest.fixture(autouse=True)
def reset_ai_state():
    ai.reset_openai_client()
    caching._cache.clear()
    yield
    ai.reset_openai_client()
    caching._cache.clear()


def chat_response(content):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


class FakeChatCompletions:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        index = min(len(self.calls) - 1, len(self._responses) - 1)
        response = self._responses[index]
        if isinstance(response, BaseException):
            raise response
        return response


class FakeOpenAIClient:
    def __init__(self, responses):
        self.completions = FakeChatCompletions(responses)
        self.chat = SimpleNamespace(completions=self.completions)


class FakeStreamingResponse:
    def __init__(self, payload=b"", error=None):
        self.payload = payload
        self.error = error

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def stream_to_file(self, path):
        with open(path, "wb") as file:
            file.write(self.payload)
        if self.error:
            raise self.error


class FakeAudioClient:
    def __init__(self, payload=b"mp3-bytes", error=None):
        self.payload = payload
        self.error = error
        self.calls = []
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self._create)
        )

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        audio = SimpleNamespace(
            data=base64.b64encode(self.payload).decode("ascii")
        )
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(audio=audio))]
        )


def scenario_payload(lines):
    return {
        "title": "At the cafe",
        "description": "Ordering a coffee.",
        "lines": lines,
    }


def line(speaker, gloss="Hello", target_text="안녕하세요"):
    return {
        "speaker": speaker,
        "source_text": gloss,
        "target_text": target_text,
    }


def http_response(status):
    return httpx.Response(status, request=httpx.Request("POST", API_URL))


def rate_limit_error():
    return RateLimitError("rate limited", response=http_response(429), body=None)


def server_error():
    return InternalServerError("server error", response=http_response(500), body=None)


def auth_error():
    return AuthenticationError("bad key", response=http_response(401), body=None)


def timeout_error():
    return APITimeoutError(request=httpx.Request("POST", API_URL))


# --- Lazy client -----------------------------------------------------------


def test_missing_key_raises_clear_config_error(app, monkeypatch):
    app.config["OPENAI_API_KEY"] = None
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with (
        app.app_context(),
        pytest.raises(ai.OpenAIConfigError, match="OPENAI_API_KEY"),
    ):
        ai.get_openai_client()


def test_client_is_lazy_and_uses_explicit_timeouts(app, monkeypatch):
    captured = {}

    class DummyClient:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(ai, "OpenAI", DummyClient)

    with app.app_context():
        client = ai.get_openai_client()
        assert ai.get_openai_client() is client

    assert captured["api_key"] == "test-key"
    assert captured["max_retries"] == 0
    assert captured["timeout"].connect == 5.0
    assert captured["timeout"].read == 30.0
    assert captured["timeout"].write == 10.0
    assert captured["timeout"].pool == 5.0


def test_injected_client_takes_precedence(app):
    fake = FakeOpenAIClient([chat_response('{"translation": "안녕"}')])
    ai.set_openai_client_for_testing(fake)
    app.config["OPENAI_API_KEY"] = None

    with app.app_context():
        assert ai.get_openai_client() is fake


# --- Translation -----------------------------------------------------------


def test_translate_success(app):
    fake = FakeOpenAIClient(
        [chat_response(
            '{"translation": "안녕하세요", "romanization": "annyeonghaseyo"}'
        )]
    )
    app.extensions["openai_client"] = fake

    with app.app_context():
        result = translation_service.translate_to_korean("Hello")

    assert result == "안녕하세요"
    assert len(fake.completions.calls) == 1
    call = fake.completions.calls[0]
    assert call["model"] == translation_service.TRANSLATION_MODEL
    assert call["response_format"] == {"type": "json_object"}


def test_translate_returns_romanization(app):
    fake = FakeOpenAIClient(
        [
            chat_response(
                '{"translation": "안녕하세요", '
                '"romanization": "annyeonghaseyo"}'
            )
        ]
    )
    app.extensions["openai_client"] = fake

    with app.app_context():
        result = translation_service.translate_text_with_romanization(
            "Hello there", "ko"
        )

    assert result.translation == "안녕하세요"
    assert result.romanization == "annyeonghaseyo"


def test_reasoning_model_omits_temperature_and_uses_completion_tokens(app):
    fake = FakeOpenAIClient(
        [chat_response(
            '{"translation": "안녕하세요", "romanization": "annyeonghaseyo"}'
        )]
    )
    app.extensions["openai_client"] = fake

    with app.app_context():
        app.config["TRANSLATION_MODEL"] = "gpt-5.6-luna"
        translation_service.translate_to_korean("Hello")

    call = fake.completions.calls[0]
    assert call["max_completion_tokens"] == 220
    assert call["reasoning_effort"] == "none"
    assert "max_tokens" not in call
    assert "temperature" not in call


def test_classic_model_keeps_temperature_and_max_tokens(app):
    fake = FakeOpenAIClient(
        [chat_response(
            '{"translation": "안녕하세요", "romanization": "annyeonghaseyo"}'
        )]
    )
    app.extensions["openai_client"] = fake

    with app.app_context():
        app.config["TRANSLATION_MODEL"] = "gpt-4.1-nano"
        translation_service.translate_to_korean("Hello")

    call = fake.completions.calls[0]
    assert call["max_tokens"] == 220
    assert call["temperature"] == 0.3
    assert "max_completion_tokens" not in call


def test_translate_invalid_json_raises_after_bounded_retries(app):
    fake = FakeOpenAIClient([chat_response("this is not JSON")])
    app.extensions["openai_client"] = fake

    with (
        app.app_context(),
        pytest.raises(ValueError, match="invalid translation response"),
    ):
        translation_service.translate_to_korean("not valid JSON")

    assert len(fake.completions.calls) == translation_service.MAX_OUTPUT_ATTEMPTS


def test_translate_missing_key_in_response_raises(app):
    fake = FakeOpenAIClient([chat_response('{"wrong_key": "안녕"}')])
    app.extensions["openai_client"] = fake

    with (
        app.app_context(),
        pytest.raises(ValueError, match="invalid translation response"),
    ):
        translation_service.translate_to_korean("missing key")

    assert len(fake.completions.calls) == translation_service.MAX_OUTPUT_ATTEMPTS


def test_translation_response_schema_rejects_blank_and_oversized_text():
    with pytest.raises(ValidationError):
        GenericTranslationResponse.model_validate({"translation": "   "})

    with pytest.raises(ValidationError):
        GenericTranslationResponse.model_validate({"translation": "가" * 501})


def test_translation_schema_accepts_optional_romanization():
    with_romanization = GenericTranslationResponse.model_validate(
        {"translation": "안녕하세요", "romanization": "annyeonghaseyo"}
    )
    without = GenericTranslationResponse.model_validate(
        {"translation": "안녕하세요"}
    )

    assert with_romanization.romanization == "annyeonghaseyo"
    assert without.romanization is None


# --- Conversation schema and generation ------------------------------------


def test_conversation_schema_accepts_valid_scenario():
    scenario = ConversationScenario.model_validate(
        scenario_payload([line(1), line(2)])
    )
    assert [item.speaker for item in scenario.lines] == [1, 2]


@pytest.mark.parametrize(
    "lines",
    [
        [line(1)],  # too few
        [line(1), line(2), line(1), line(2), line(1)],  # too many
        [line(1), line(1)],  # speakers do not alternate
        [line(1), line(2), line(2)],  # speakers do not alternate mid-scenario
    ],
)
def test_conversation_schema_rejects_invalid_line_structure(lines):
    with pytest.raises(ValidationError):
        ConversationScenario.model_validate(scenario_payload(lines))


def test_conversation_schema_accepts_alternation_starting_with_speaker_2():
    scenario = ConversationScenario.model_validate(
        scenario_payload([line(2), line(1)])
    )
    assert [item.speaker for item in scenario.lines] == [2, 1]


def test_conversation_schema_requires_hangul_in_target_text():
    with pytest.raises(ValidationError, match="Hangul"):
        ConversationScenario.model_validate(
            scenario_payload([line(1), line(2, target_text="annyeong")])
        )


def test_generate_conversation_success_returns_validated_dict(app):
    fake = FakeOpenAIClient(
        [chat_response(json.dumps(scenario_payload([line(1), line(2)])))]
    )
    app.extensions["openai_client"] = fake

    with app.app_context():
        result = translation_service.generate_conversation_scenario("Order coffee")

    assert result["title"] == "At the cafe"
    assert [item["speaker"] for item in result["lines"]] == [1, 2]
    assert result["lines"][0]["target_text"] == "안녕하세요"


def test_generate_conversation_rejects_invalid_output_after_retries(app):
    fake = FakeOpenAIClient(
        [chat_response(json.dumps(scenario_payload([line(1), line(1)])))]
    )
    app.extensions["openai_client"] = fake

    with (
        app.app_context(),
        pytest.raises(ValueError, match="invalid conversation scenario"),
    ):
        translation_service.generate_conversation_scenario("Order coffee")

    assert len(fake.completions.calls) == translation_service.MAX_OUTPUT_ATTEMPTS


def test_generate_conversation_rejects_out_of_range_line_count(app):
    fake = FakeOpenAIClient(
        [
            chat_response(
                json.dumps(
                    scenario_payload([line(1), line(2), line(1), line(2)])
                )
            )
        ]
    )
    app.extensions["openai_client"] = fake

    with (
        app.app_context(),
        pytest.raises(ValueError, match="invalid conversation scenario"),
    ):
        translation_service.generate_conversation_scenario(
            "Order coffee", min_lines=2, max_lines=2
        )


# --- Retry policy ----------------------------------------------------------


def test_call_with_retries_retries_transient_errors_with_backoff(monkeypatch):
    monkeypatch.setattr(retries_module.random, "uniform", lambda low, high: 1.0)
    sleeps = []
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise rate_limit_error()
        return "ok"

    result = call_with_retries(
        flaky, attempts=3, base_delay=0.5, max_delay=4.0, sleep=sleeps.append
    )

    assert result == "ok"
    assert len(calls) == 3
    assert sleeps == [0.5, 1.0]


def test_call_with_retries_treats_timeout_as_transient():
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) == 1:
            raise timeout_error()
        return "ok"

    assert call_with_retries(flaky, attempts=2, sleep=lambda _: None) == "ok"
    assert len(calls) == 2


def test_call_with_retries_does_not_retry_auth_errors():
    calls = []

    def always_unauthorized():
        calls.append(1)
        raise auth_error()

    with pytest.raises(AuthenticationError):
        call_with_retries(
            always_unauthorized,
            attempts=3,
            sleep=lambda _: pytest.fail("non-transient error must not sleep"),
        )

    assert len(calls) == 1


def test_call_with_retries_reraises_last_error_after_exhaustion():
    calls = []
    sleeps = []

    def always_failing():
        calls.append(1)
        raise server_error()

    with pytest.raises(InternalServerError):
        call_with_retries(
            always_failing,
            attempts=2,
            base_delay=1.0,
            sleep=sleeps.append,
        )

    assert len(calls) == 2
    assert len(sleeps) == 1


# --- Audio -----------------------------------------------------------------


def test_generate_audio_success_uses_config_model(app, tmp_path):
    fake = FakeAudioClient(payload=b"ID3-fake-audio")
    app.extensions["openai_client"] = fake
    app.config["TTS_MODEL"] = "gpt-audio-test"
    path = tmp_path / "line.mp3"

    with app.app_context():
        result = audio_service.generate_audio("안녕하세요", str(path), voice="nova")

    assert result == "line.mp3"
    assert path.read_bytes() == b"ID3-fake-audio"
    assert fake.calls[0]["model"] == "gpt-audio-test"
    assert fake.calls[0]["audio"]["voice"] == "nova"
    assert fake.calls[0]["messages"][-1]["content"] == "<read>안녕하세요</read>"


def test_generate_audio_defaults_to_gpt_audio(app, tmp_path):
    fake = FakeAudioClient()
    app.extensions["openai_client"] = fake
    path = tmp_path / "line.mp3"

    with app.app_context():
        audio_service.generate_audio("안녕하세요", str(path))

    assert fake.calls[0]["model"] == "gpt-audio-1.5"


def test_generate_audio_failure_removes_partial_file(app, tmp_path):
    fake = FakeAudioClient(payload=b"partial", error=RuntimeError("tts failed"))
    app.extensions["openai_client"] = fake
    path = tmp_path / "line.mp3"

    with app.app_context(), pytest.raises(RuntimeError, match="tts failed"):
        audio_service.generate_audio("안녕하세요", str(path))

    assert not path.exists()
    assert len(fake.calls) == 1


def test_generate_audio_empty_file_is_removed(app, tmp_path):
    fake = FakeAudioClient(payload=b"")
    app.extensions["openai_client"] = fake
    path = tmp_path / "line.mp3"

    with app.app_context(), pytest.raises(OSError, match="empty"):
        audio_service.generate_audio("안녕하세요", str(path))

    assert not path.exists()


def test_generate_audio_rejects_blank_text(app):
    with app.app_context(), pytest.raises(ValueError):
        audio_service.generate_audio("   ", "/tmp/never-written.mp3")


def test_translate_amharic_female_prompt(app):
    fake = FakeOpenAIClient(
        [
            chat_response(
                '{"translation": "እንደምን ነሽ?", '
                '"romanization": "endemin nesh?"}'
            )
        ]
    )
    app.extensions["openai_client"] = fake

    with app.app_context():
        result = translation_service.translate_text_with_romanization(
            "How are you?", "am", addressee="female", register="casual"
        )

    assert result.translation == "እንደምን ነሽ?"
    assert result.romanization == "endemin nesh?"
    system = fake.completions.calls[0]["messages"][0]["content"]
    assert "Address one woman" in system
    assert "feminine" in system


def test_translate_amharic_unspecified_asks_for_both(app):
    fake = FakeOpenAIClient(
        [chat_response('{"translation": "እንደምን ነህ?", "romanization": "endemin neh?"}')]
    )
    app.extensions["openai_client"] = fake

    with app.app_context():
        translation_service.translate_text_with_romanization(
            "How are you?", "am", addressee="any", register="casual"
        )

    system = fake.completions.calls[0]["messages"][0]["content"]
    assert "addressee is unspecified" in system
    assert "feminine form in parentheses" in system


def test_translate_korean_formal_register_prompt(app):
    fake = FakeOpenAIClient(
        [chat_response('{"translation": "감사합니다", "romanization": "gamsahamnida"}')]
    )
    app.extensions["openai_client"] = fake

    with app.app_context():
        translation_service.translate_text_with_romanization(
            "Thank you", "ko", register="formal"
        )

    system = fake.completions.calls[0]["messages"][0]["content"]
    assert "formal polite speech" in system
    assert "합니다체" in system


def test_translate_korean_casual_register_prompt(app):
    fake = FakeOpenAIClient(
        [chat_response('{"translation": "고마워", "romanization": "gomawo"}')]
    )
    app.extensions["openai_client"] = fake

    with app.app_context():
        translation_service.translate_text_with_romanization(
            "Thank you", "ko", register="casual"
        )

    system = fake.completions.calls[0]["messages"][0]["content"]
    assert "casual plain speech" in system
    assert "반말" in system


def test_translate_amharic_formal_register_prompt(app):
    fake = FakeOpenAIClient(
        [chat_response('{"translation": "እንደምን ነዎት?", "romanization": "endemin newot?"}')]
    )
    app.extensions["openai_client"] = fake

    with app.app_context():
        translation_service.translate_text_with_romanization(
            "How are you?", "am", addressee="male", register="formal"
        )

    system = fake.completions.calls[0]["messages"][0]["content"]
    assert "formal/polite second person" in system
    assert "እርስዎ" in system
    assert "not gendered" in system
    assert "Address one man" not in system
    assert "-ህ/-ሽ" in system


def test_translate_amharic_formal_ignores_female_forms(app):
    fake = FakeOpenAIClient(
        [chat_response('{"translation": "እንደምን ነዎት?", "romanization": "endemin newot?"}')]
    )
    app.extensions["openai_client"] = fake

    with app.app_context():
        translation_service.translate_text_with_romanization(
            "How are you?", "am", addressee="female", register="formal"
        )

    system = fake.completions.calls[0]["messages"][0]["content"]
    assert "not gendered" in system
    assert "Address one woman" not in system
    assert "feminine" not in system


def test_translate_amharic_rejects_polite_register(app):
    fake = FakeOpenAIClient(
        [chat_response('{"translation": "እንደምን ነዎት?", "romanization": "endemin newot?"}')]
    )
    app.extensions["openai_client"] = fake

    with app.app_context():
        translation_service.translate_text_with_romanization(
            "How are you?", "am", register="polite"
        )

    system = fake.completions.calls[0]["messages"][0]["content"]
    assert "formal/polite second person" in system
    assert "everyday informal" not in system


def test_translate_uses_the_language_default_register(app):
    fake = FakeOpenAIClient(
        [chat_response('{"translation": "እንደምን ነህ?", "romanization": "endemin neh?"}')]
    )
    app.extensions["openai_client"] = fake

    with app.app_context():
        translation_service.translate_text_with_romanization("How are you?", "am")

    system = fake.completions.calls[0]["messages"][0]["content"]
    assert "formal/polite second person" in system
    assert "እርስዎ" in system
    assert "everyday informal" not in system


def test_register_and_addressee_are_normalized_per_language():
    from app.languages.variants import (
        addressee_label,
        normalize_addressee,
        normalize_register,
        register_label,
    )

    assert normalize_register("am", "polite") == "formal"
    assert normalize_register("am", None) == "formal"
    assert normalize_register("ko", "formal") == "formal"
    assert normalize_register("es", "formal") is None
    assert normalize_addressee("ko", "female") == "any"
    assert normalize_addressee("am", "female") == "female"
    assert normalize_addressee("es", "female") == "any"
    assert addressee_label("am", "female") == "To a woman"
    assert addressee_label("ko", "female") == ""
    assert register_label("am", "casual") == "Everyday"
    assert register_label("am", "polite") == ""


def test_translate_text_scales_the_output_budget(app):
    fake = FakeOpenAIClient(
        [
            chat_response(
                '{"translation": "안녕하세요", '
                '"romanization": "annyeonghaseyo"}'
            )
        ]
    )
    app.extensions["openai_client"] = fake
    long_text = "a" * 500

    with app.app_context():
        translation_service.translate_text(long_text, "ko")

    call = fake.completions.calls[0]
    assert call["max_completion_tokens"] == 1200


def test_translate_text_targets_amharic(app):
    fake = FakeOpenAIClient([chat_response(
            '{"translation": "ቡናው የት አለ?", "romanization": "bunaw yät alä?"}'
        )])
    app.extensions["openai_client"] = fake

    with app.app_context():
        result = translation_service.translate_text("Where is the coffee?", "am")

    assert result == "ቡናው የት አለ?"
    system = fake.completions.calls[0]["messages"][0]["content"]
    assert "Amharic" in system
    assert "Korean" not in system
