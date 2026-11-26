"""Phase 0 platform guarantees: rate limits, media safety, auth, headers."""

import json
import logging
import os

import pytest
from flask import g

from app.services.ai import OpenAIConfigError, get_openai_client, reset_openai_client
from app.utils.media import AudioBatch, audit_media
from app.utils.rate_limit import RateLimiter

# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------


def test_rate_limiter_enforces_limit_and_recovers():
    now = [100.0]
    limiter = RateLimiter(max_keys=10, clock=lambda: now[0])

    assert limiter.hit("ip", limit=2, window_seconds=60) == (True, 0)
    assert limiter.hit("ip", limit=2, window_seconds=60) == (True, 0)

    allowed, retry_after = limiter.hit("ip", limit=2, window_seconds=60)
    assert allowed is False
    assert retry_after >= 1

    now[0] += 61
    assert limiter.hit("ip", limit=2, window_seconds=60) == (True, 0)


def test_rate_limiter_is_bounded_and_evicts_oldest():
    now = [0.0]
    limiter = RateLimiter(max_keys=2, clock=lambda: now[0])

    limiter.hit("a", limit=5, window_seconds=60)
    limiter.hit("b", limit=5, window_seconds=60)
    limiter.hit("c", limit=5, window_seconds=60)

    assert len(limiter) == 2


def test_spoofed_forwarded_for_does_not_reset_rate_limit(app, client):
    app.config.update(
        RATE_LIMIT_ENABLED=True,
        RATE_LIMIT_TRANSLATE=2,
        RATE_LIMIT_WINDOW_SECONDS=60,
        TRUST_PROXY=False,
    )
    app.extensions["rate_limiter"].clear()

    client.post("/api/translate", json={}, headers={"X-Forwarded-For": "1.1.1.1"})
    client.post("/api/translate", json={}, headers={"X-Forwarded-For": "2.2.2.2"})
    response = client.post(
        "/api/translate", json={}, headers={"X-Forwarded-For": "3.3.3.3"}
    )

    assert response.status_code == 429


def test_rate_limit_decorator_returns_429_with_retry_after(app, client):
    app.config.update(
        RATE_LIMIT_ENABLED=True,
        RATE_LIMIT_TRANSLATE=2,
        RATE_LIMIT_WINDOW_SECONDS=60,
    )
    app.extensions["rate_limiter"].clear()

    assert client.post("/api/translate", json={}).status_code == 400
    assert client.post("/api/translate", json={}).status_code == 400

    response = client.post("/api/translate", json={})
    assert response.status_code == 429
    assert response.headers["Retry-After"]
    assert response.get_json()["error"]


# ---------------------------------------------------------------------------
# Media staging
# ---------------------------------------------------------------------------


def test_audio_batch_commits_and_cleans_up(tmp_path):
    staging = tmp_path / "staging"
    destination = tmp_path / "audio"
    staging.mkdir()

    with AudioBatch(str(staging)) as batch:
        staged = batch.path("line.mp3")
        with open(staged, "wb") as handle:
            handle.write(b"fake-mp3")

        moved = batch.commit_to(str(destination), [(staged, "line.mp3")])

    assert moved == [str(destination / "line.mp3")]
    assert os.path.exists(destination / "line.mp3")
    assert not os.path.exists(staged)


def test_audio_batch_rolls_back_moved_files_on_partial_failure(tmp_path):
    staging = tmp_path / "staging"
    destination = tmp_path / "audio"
    staging.mkdir()

    with AudioBatch(str(staging)) as batch:
        staged = batch.path("first.mp3")
        with open(staged, "wb") as handle:
            handle.write(b"fake-mp3")
        missing = batch.path("missing.mp3")

        with pytest.raises(FileNotFoundError):
            batch.commit_to(
                str(destination),
                [(staged, "first.mp3"), (missing, "missing.mp3")],
            )

    assert not os.path.exists(destination / "first.mp3")


def test_audit_media_reports_orphans_and_missing(tmp_path):
    audio = tmp_path / "audio"
    audio.mkdir()
    (audio / "kept.mp3").write_bytes(b"x")
    (audio / "orphan.mp3").write_bytes(b"x")

    orphans, missing = audit_media(str(audio), {"kept.mp3", "gone.mp3"})

    assert orphans == ["orphan.mp3"]
    assert missing == ["gone.mp3"]


def test_media_audit_cli_is_read_only_by_default(app, runner):
    audio_dir = app.config["AUDIO_DIR"]
    orphan = os.path.join(audio_dir, "orphan.mp3")
    with open(orphan, "wb") as handle:
        handle.write(b"x")

    result = runner.invoke(args=["media-audit", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert "orphan.mp3" in payload["orphans"]
    assert os.path.exists(orphan)


def test_media_gc_keeps_audio_referenced_by_an_item(app, runner):
    from app import db
    from app.models import Item

    audio_dir = app.config["AUDIO_DIR"]
    item_audio = os.path.join(audio_dir, "item_seed.mp3")
    with open(item_audio, "wb") as handle:
        handle.write(b"x")

    with app.app_context():
        db.session.add(
            Item(
                item_type="lexeme",
                target_text="테스트",
                gloss="test",
                level=1,
                default_skill="recognize",
                audio_path="/static/audio/item_seed.mp3",
            )
        )
        db.session.commit()

    result = runner.invoke(
        args=["media-gc", "--delete", "--older-than", "0"]
    )

    assert result.exit_code == 0
    assert os.path.exists(item_audio)


def test_media_gc_deletes_only_with_flag(app, runner):
    audio_dir = app.config["AUDIO_DIR"]
    orphan = os.path.join(audio_dir, "orphan.mp3")
    with open(orphan, "wb") as handle:
        handle.write(b"x")

    dry = runner.invoke(args=["media-gc", "--older-than", "0"])
    assert dry.exit_code == 0
    assert os.path.exists(orphan)

    deleted = runner.invoke(
        args=["media-gc", "--delete", "--older-than", "0"]
    )
    assert deleted.exit_code == 0
    assert not os.path.exists(orphan)


# ---------------------------------------------------------------------------
# Lazy AI client
# ---------------------------------------------------------------------------


def test_missing_key_raises_clear_error_instead_of_import_failure(
    app, monkeypatch
):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    app.config["OPENAI_API_KEY"] = None
    reset_openai_client()
    app.extensions.pop("openai_client", None)

    with app.app_context(), pytest.raises(OpenAIConfigError):
        get_openai_client()
    reset_openai_client()
    app.extensions["openai_client"] = object()


# ---------------------------------------------------------------------------
# Headers and auth
# ---------------------------------------------------------------------------


def test_request_id_logging_filter(app):
    from app.logging_utils import RequestIdFilter

    log_filter = RequestIdFilter()
    record = logging.LogRecord(
        "test", logging.INFO, __file__, 1, "hello", None, None
    )

    with app.test_request_context("/"):
        g.request_id = "abc123"
        assert log_filter.filter(record) is True
        assert record.request_id == "abc123"

    outside = logging.LogRecord(
        "test", logging.INFO, __file__, 1, "hello", None, None
    )
    with app.app_context():
        log_filter.filter(outside)
    assert outside.request_id == "-"


def test_security_headers_are_present(client):
    response = client.get("/ko/translate")

    assert response.status_code == 200
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Request-ID"]


def test_healthz_is_available(client):
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_optional_basic_auth_gate(app, client):
    app.config.update(REQUIRE_AUTH=True, APP_USERNAME="kiku", APP_PASSWORD="secret")

    assert client.get("/healthz").status_code == 200
    assert client.get("/ko/").status_code == 401

    response = client.get("/ko/translate", auth=("kiku", "secret"))
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Transactional failure path
# ---------------------------------------------------------------------------


class _FailingTTS:
    def __init__(self):
        self.calls = 0
        self.with_streaming_response = self

    def create(self, **_kwargs):
        self.calls += 1
        if self.calls >= 2:
            raise RuntimeError("simulated TTS outage")

        class _Context:
            def __enter__(self):
                return self

            def __exit__(self, *_exc):
                return False

            def stream_to_file(self, filepath):
                with open(filepath, "wb") as handle:
                    handle.write(b"ID3fake-mp3")

        return _Context()


class _ChatCompletion:
    def __init__(self, payload):
        self.choices = [type("Choice", (), {"message": type("Message", (), {"content": json.dumps(payload)})()})()]


class _FailingConversationClient:
    def __init__(self):
        self.chat = type(
            "Chat",
            (),
            {
                "completions": type(
                    "Completions",
                    (),
                    {
                        "create": lambda _self, **_kwargs: _ChatCompletion(
                            {
                                "title": "Test",
                                "description": "Test scenario",
                                "lines": [
                                    {
                                        "speaker": 1,
                                        "source_text": "Hello.",
                                        "target_text": "안녕하세요.",
                                    },
                                    {
                                        "speaker": 2,
                                        "source_text": "Hi.",
                                        "target_text": "안녕.",
                                    },
                                ],
                            }
                        )
                    },
                )()
            },
        )()
        self.audio = type("Audio", (), {"speech": _FailingTTS()})()


class _EnglishOnlyCompletions:
    def create(self, **_kwargs):
        return _ChatCompletion({"korean_translation": "hello"})


def test_translation_rejects_non_hangul_output(app):
    from app.services.translation import translate_to_korean

    app.extensions["openai_client"] = type(
        "Client",
        (),
        {"chat": type("Chat", (), {"completions": _EnglishOnlyCompletions()})()},
    )()

    with pytest.raises(ValueError):
        translate_to_korean("A unique phrase that is not cached 92837")


def test_failed_conversation_leaves_no_rows_or_files(app, client):
    from app.models import Conversation, Phrase

    app.extensions["openai_client"] = _FailingConversationClient()
    audio_dir = app.config["AUDIO_DIR"]
    before = set(os.listdir(audio_dir))

    response = client.post("/api/conversation", json={"prompt": "At a cafe"})

    assert response.status_code == 500
    assert response.get_json()["request_id"]
    with app.app_context():
        assert Phrase.query.count() == 0
        assert Conversation.query.count() == 0
    assert set(os.listdir(audio_dir)) == before


def test_translate_api_returns_romanization_and_saves_phrase(client):
    from app.utils import caching

    caching._cache.clear()
    client.get("/ko/learn")

    response = client.post("/api/translate", json={"text": "Hello"})

    assert response.status_code == 200
    data = response.get_json()
    assert data["target_text"] == "안녕하세요"
    assert data["romanization"] == "annyeonghaseyo"
    assert data["addressee"] == "any"

    library = client.get("/ko/library")
    assert b"annyeonghaseyo" in library.data


def test_translate_api_records_the_addressee(client):
    from app.utils import caching

    caching._cache.clear()
    client.get("/ko/learn")

    response = client.post(
        "/api/translate",
        json={"text": "Hello", "addressee": "female"},
    )

    assert response.status_code == 200
    assert response.get_json()["addressee"] == "female"

    library = client.get("/ko/library")
    assert b"To a woman" in library.data


def test_translate_api_records_the_register(client):
    from app.utils import caching

    caching._cache.clear()
    client.get("/ko/learn")

    response = client.post(
        "/api/translate",
        json={"text": "Thank you", "formality": "formal"},
    )

    assert response.status_code == 200
    assert response.get_json()["register"] == "formal"

    library = client.get("/ko/library")
    assert b"Formal" in library.data

    phrases = client.get("/api/phrases").get_json()["phrases"]
    assert phrases[0]["register"] == "formal"


def test_translate_api_defaults_to_the_everyday_polite_register(client):
    from app.utils import caching

    caching._cache.clear()
    client.get("/ko/learn")

    response = client.post("/api/translate", json={"text": "Hello"})

    assert response.status_code == 200
    assert response.get_json()["register"] == "polite"


def test_phrase_url_renders_a_saved_result_without_translating(client, app):
    from app.models import Phrase
    from app.utils import caching

    caching._cache.clear()
    client.get("/ko/learn")
    created = client.post(
        "/api/translate",
        json={"text": "Hello", "formality": "formal"},
    ).get_json()

    with app.app_context():
        before = Phrase.query.count()

    page = client.get(f"/ko/translate?phrase={created['uuid']}")

    assert page.status_code == 200
    assert b'id="result"' in page.data
    assert f'data-phrase-uuid="{created["uuid"]}"'.encode() in page.data
    assert b'value="Hello"' in page.data
    assert created["target_text"].encode() in page.data
    assert created["romanization"].encode() in page.data
    assert b"Formal" in page.data
    assert created["audio_path"].encode() in page.data

    with app.app_context():
        assert Phrase.query.count() == before


def test_phrase_url_is_scoped_to_the_page_language(client, app):
    from app.languages.seed import seed_amharic
    from app.utils import caching

    caching._cache.clear()
    client.get("/ko/learn")
    created = client.post("/api/translate", json={"text": "Hello"}).get_json()
    with app.app_context():
        seed_amharic()

    page = client.get(f"/am/translate?phrase={created['uuid']}")

    assert page.status_code == 200
    assert b"not available in this language" in page.data
    assert created["target_text"].encode() not in page.data


def test_missing_phrase_url_falls_back_to_the_form(client):
    client.get("/ko/learn")

    page = client.get("/ko/translate?phrase=not-a-real-phrase")

    assert page.status_code == 200
    assert b"not available in this language" in page.data
    assert b'data-phrase-uuid=""' in page.data
