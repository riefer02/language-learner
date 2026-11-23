"""Shared script-aware text helpers."""

from app.utils.text import (
    is_ethiopic,
    is_hangul,
    language_name,
    normalize_text,
    similarity,
    tts_lang,
)


def test_normalize_keeps_letters_and_digits_from_any_script():
    assert normalize_text("커피 한 잔!") == "커피한잔"
    assert normalize_text("ቡና፣ እባክህ።") == "ቡናእባክህ"
    assert normalize_text("Café 2!") == "café2"


def test_script_detection_and_tts_codes():
    assert is_hangul("한국어")
    assert not is_hangul("አማርኛ")
    assert is_ethiopic("አማርኛ")
    assert not is_ethiopic("한국어")
    assert tts_lang("am") == "am-ET"
    assert tts_lang("ko") == "ko-KR"
    assert language_name("am") == "Amharic"


def test_similarity_is_script_agnostic():
    assert similarity("커피", "커피!") == 1.0
    assert similarity("ቡና", "ቡና።") == 1.0
    assert similarity("커피", "차") < 0.5
