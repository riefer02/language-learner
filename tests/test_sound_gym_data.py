"""Tests for the hand-authored Sound Gym content."""

from app.learning.sound_gym_data import (
    DISCLAIMER,
    MINIMAL_PAIRS,
    PRODUCTION_PROMPTS,
)

PAIR_KEYS = {"id", "words", "contrast", "tip", "level"}
WORD_KEYS = {"target_text", "transliteration", "gloss"}
PROMPT_KEYS = {
    "id",
    "target_text",
    "transliteration",
    "gloss",
    "focus",
    "tip",
    "level",
}


def test_enough_minimal_pairs_and_prompts():
    assert 10 <= len(MINIMAL_PAIRS) <= 12
    assert 6 <= len(PRODUCTION_PROMPTS) <= 8


def test_minimal_pair_ids_are_unique():
    ids = [pair["id"] for pair in MINIMAL_PAIRS]

    assert len(ids) == len(set(ids))


def test_production_prompt_ids_are_unique():
    ids = [prompt["id"] for prompt in PRODUCTION_PROMPTS]

    assert len(ids) == len(set(ids))


def test_minimal_pairs_have_required_shape():
    for pair in MINIMAL_PAIRS:
        assert PAIR_KEYS <= set(pair), pair["id"]
        assert 2 <= len(pair["words"]) <= 3, pair["id"]
        assert pair["level"] in {1, 2}, pair["id"]
        assert isinstance(pair["contrast"], str) and pair["contrast"].strip()
        assert isinstance(pair["tip"], str) and pair["tip"].strip()


def test_minimal_pair_words_have_required_shape():
    for pair in MINIMAL_PAIRS:
        for word in pair["words"]:
            assert WORD_KEYS <= set(word), pair["id"]
            for key in WORD_KEYS:
                assert isinstance(word[key], str) and word[key].strip(), (
                    pair["id"],
                    key,
                )


def test_no_duplicate_korean_within_a_pair():
    for pair in MINIMAL_PAIRS:
        korean = [word["target_text"] for word in pair["words"]]

        assert len(korean) == len(set(korean)), pair["id"]


def test_required_contrasts_are_covered():
    covered = {word["target_text"] for pair in MINIMAL_PAIRS for word in pair["words"]}

    expected = {
        "불", "뿔", "풀",
        "달", "딸", "탈",
        "자", "짜", "차",
        "밥", "빵",
        "살", "쌀",
        "알", "말",
        "거리", "고리",
        "그리", "구리",
        "배", "베",
        "밤", "방", "반",
    }
    assert expected <= covered


def test_production_prompts_have_required_shape():
    for prompt in PRODUCTION_PROMPTS:
        assert PROMPT_KEYS <= set(prompt), prompt["id"]
        for key in PROMPT_KEYS - {"level"}:
            assert isinstance(prompt[key], str) and prompt[key].strip(), (
                prompt["id"],
                key,
            )
        assert prompt["level"] in {1, 2}, prompt["id"]


def test_disclaimer_mentions_native_audio_and_transcript_scoring():
    lowered = DISCLAIMER.lower()

    assert DISCLAIMER.strip()
    assert "native audio" in lowered
    assert "transcript" in lowered
