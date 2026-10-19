"""Unit tests for small, stable utility modules."""

from types import SimpleNamespace

import pytest

from app.utils import caching
from app.utils.audio_merge import merge_audio_files
from app.utils.caching import cache_result
from app.utils.validators import validate_phrase

# ---------------------------------------------------------------------------
# validators.validate_phrase
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("text", [None, "", "   ", "\n\t  \r\n"])
def test_validate_phrase_rejects_empty_values(text):
    is_valid, message = validate_phrase(text)

    assert is_valid is False
    assert message == "Text cannot be empty"


def test_validate_phrase_rejects_text_over_500_characters():
    is_valid, message = validate_phrase("a" * 501)

    assert is_valid is False
    assert "500" in message


def test_validate_phrase_accepts_normal_text():
    is_valid, message = validate_phrase("Hello, how are you?")

    assert is_valid is True
    assert message == ""


def test_validate_phrase_accepts_exactly_500_characters():
    is_valid, _ = validate_phrase("a" * 500)

    assert is_valid is True


# ---------------------------------------------------------------------------
# caching.cache_result
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clear_cache():
    """Prevent cached values from leaking between tests."""
    caching._cache.clear()
    yield
    caching._cache.clear()


def test_cache_returns_cached_result_on_hit(app):
    calls = []

    @cache_result(expire_seconds=60)
    def add(a, b):
        calls.append((a, b))
        return a + b

    with app.app_context():
        assert add(1, 2) == 3
        assert add(1, 2) == 3

    assert calls == [(1, 2)]


def test_cache_miss_calls_function_with_different_arguments(app):
    calls = []

    @cache_result(expire_seconds=60)
    def double(value):
        calls.append(value)
        return value * 2

    with app.app_context():
        assert double(2) == 4
        assert double(3) == 6
        assert double(2) == 4

    assert calls == [2, 3]


def test_cache_entry_expires(app, monkeypatch):
    clock = SimpleNamespace(time=lambda: 1000.0)
    monkeypatch.setattr(caching, "time", clock)
    calls = []

    @cache_result(expire_seconds=10)
    def now_value():
        calls.append(1)
        return len(calls)

    with app.app_context():
        assert now_value() == 1

        clock.time = lambda: 1009.0  # still inside the TTL
        assert now_value() == 1

        clock.time = lambda: 1011.0  # TTL has elapsed
        assert now_value() == 2

    assert calls == [1, 1]


# ---------------------------------------------------------------------------
# audio_merge.merge_audio_files
# ---------------------------------------------------------------------------


def test_merge_audio_files_rejects_empty_list(app, tmp_path):
    with app.app_context(), pytest.raises(ValueError, match="No audio files"):
        merge_audio_files([], str(tmp_path / "merged.mp3"))


def test_merge_audio_files_rejects_missing_file(app, tmp_path):
    missing = tmp_path / "does-not-exist.mp3"

    with app.app_context(), pytest.raises(
        FileNotFoundError, match="Audio file not found"
    ):
        merge_audio_files([str(missing)], str(tmp_path / "merged.mp3"))
