"""Script-aware text helpers shared by review, speech, scenes, and the teacher.

One normalization rule for every language: keep letters and digits from any
script, drop punctuation and whitespace, compare case-insensitively. This is
deliberately script-agnostic so Hangul, Ethiopic, and Latin content go through
the same matching path.
"""

import re
from difflib import SequenceMatcher

HANGUL_RANGES = ((0xAC00, 0xD7A3), (0x1100, 0x11FF), (0x3130, 0x318F))
ETHIOPIC_RANGES = ((0x1200, 0x137F), (0x1380, 0x139F), (0x2D80, 0x2DDF))

TTS_LANGUAGES = {
    "ko": "ko-KR",
    "am": "am-ET",
    "en": "en-US",
    "es": "es-ES",
    "ja": "ja-JP",
}

LANGUAGE_NAMES = {
    "ko": "Korean",
    "am": "Amharic",
    "en": "English",
    "es": "Spanish",
    "ja": "Japanese",
}


def normalize_text(value):
    """Return a comparable form: letters/digits only, lowercased."""
    return re.sub(r"[^\w]", "", (value or "").lower(), flags=re.UNICODE).replace(
        "_", ""
    )


def similarity(left, right):
    return SequenceMatcher(
        None, normalize_text(left), normalize_text(right)
    ).ratio()


def in_ranges(value, ranges):
    return any(
        start <= ord(char) <= end
        for char in str(value or "")
        for start, end in ranges
    )


def is_hangul(value):
    return in_ranges(value, HANGUL_RANGES)


def is_ethiopic(value):
    return in_ranges(value, ETHIOPIC_RANGES)


def tts_lang(code, fallback="ko-KR"):
    return TTS_LANGUAGES.get(code, fallback)


def language_name(code, fallback="Korean"):
    return LANGUAGE_NAMES.get(code, fallback)
