"""Shared pytest fixtures for the Kiku test suite.

Design notes
------------
* No network or real API key is used. AI services create their client lazily,
  but a dummy key is still set defensively in case an import-time client
  remains; it also guarantees a developer's real ``.env`` key is never used by
  the test suite.
* The database is always a throwaway SQLite file under pytest's ``tmp_path``,
  and ``AUDIO_DIR`` points at a throwaway directory.  Tests never touch the
  repository database or ``app/static/audio``.
* ``app.extensions["openai_client"]`` is populated with a tiny fake; the AI
  services read it through ``app.services.ai.get_openai_client()``.
"""

import base64
import json
import os
import sys
from pathlib import Path

# Must happen before importing anything from ``app``: ``app/__init__.py`` calls
# ``load_dotenv()`` and a lingering import-time client would otherwise require
# a key.  ``setdefault`` also means a developer's real key is never used by the
# test suite.
os.environ.setdefault("OPENAI_API_KEY", "test-key-not-used")

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# Fake OpenAI client
# ---------------------------------------------------------------------------


class _FakeMessage:
    def __init__(self, content):
        self.content = content
        # Chat-completions audio models return base64 audio alongside content.
        self.audio = type(
            "FakeAudioOutput",
            (),
            {"data": base64.b64encode(b"ID3-fake-audio").decode("ascii")},
        )()


class _FakeChoice:
    def __init__(self, content):
        self.message = _FakeMessage(content)


class _FakeCompletion:
    def __init__(self, content):
        self.choices = [_FakeChoice(content)]


# A single payload that satisfies both current consumers: translation reads
# ``translation`` and conversation generation reads ``lines``.
_DEFAULT_PAYLOAD = {
    "translation": "안녕하세요",
    "title": "Test conversation",
    "description": "A fake scenario for tests.",
    "lines": [
        {"speaker": 1, "source_text": "Hello.", "target_text": "안녕하세요."},
        {"speaker": 2, "source_text": "Hi.", "target_text": "안녕."},
    ],
}


class _FakeCompletions:
    """Minimal stand-in for ``client.chat.completions``."""

    def create(self, **kwargs):
        return _FakeCompletion(json.dumps(_DEFAULT_PAYLOAD))


class _FakeChat:
    def __init__(self):
        self.completions = _FakeCompletions()


class _FakeSpeechResponse:
    """Tiny non-decodable MP3-ish blob; enough to satisfy file-size checks."""

    MP3_BYTES = b"ID3\x04\x00\x00\x00\x00\x00\x00\xff\xfb\x90\x00" + b"\x00" * 32

    @property
    def content(self):
        return self.MP3_BYTES

    def stream_to_file(self, filepath):
        Path(filepath).write_bytes(self.MP3_BYTES)

    def write_to_file(self, filepath):
        self.stream_to_file(filepath)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeSpeech:
    """Supports both ``speech.create(...)`` and the streaming response form."""

    def __init__(self):
        self.with_streaming_response = self

    def create(self, **kwargs):
        return _FakeSpeechResponse()


class _FakeTranscriptions:
    def create(self, **_kwargs):
        return type("Transcription", (), {"text": "안녕하세요"})()


class _FakeAudio:
    def __init__(self):
        self.speech = _FakeSpeech()
        self.transcriptions = _FakeTranscriptions()


class FakeOpenAIClient:
    """Just enough of the OpenAI client surface for offline tests."""

    def __init__(self):
        self.chat = _FakeChat()
        self.audio = _FakeAudio()

    def close(self):
        pass


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def app(tmp_path_factory):
    """Create an isolated application instance backed by temporary storage."""
    from app import create_app, db
    from config import config

    tmpdir = tmp_path_factory.mktemp("kiku-tests")
    audio_dir = tmpdir / "audio"
    audio_dir.mkdir()

    overrides = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmpdir / 'test.db'}",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "WTF_CSRF_ENABLED": False,
        "AUDIO_DIR": str(audio_dir),
        "SECRET_KEY": "test",
    }

    if "testing" in config:
        app = create_app("testing", overrides=overrides)
    else:
        # TestingConfig is being added concurrently.  Fall back to the default
        # config, but register a derived class first: Flask-SQLAlchemy 2.5
        # binds its engine during ``init_app``, so patching app.config after
        # create_app() would leave the engine pointed at the real database.
        base = config.get("default")
        config["testing"] = type("PytestConfig", (base,), dict(overrides))
        app = create_app("testing", overrides=overrides)

    app.extensions["openai_client"] = FakeOpenAIClient()

    # Import models so their tables are registered on db.metadata.
    from app import models  # noqa: F401

    with app.app_context():
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    """Flask test client for route smoke tests."""
    return app.test_client()


@pytest.fixture()
def runner(app):
    """Flask CLI test runner."""
    return app.test_cli_runner()
