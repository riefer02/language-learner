"""Tests for the hand-authored roleplay scenes."""

import pytest

from app.learning.scene_data import SCENES

EXPECTED_SLUGS = {
    "cafe-order",
    "directions",
    "pharmacy",
    "workplace-intro",
}
EXPECTED_LEVELS = {
    "cafe-order": 1,
    "directions": 1,
    "pharmacy": 2,
    "workplace-intro": 2,
}

SCENE_KEYS = {
    "slug",
    "title",
    "subtitle",
    "level",
    "goal",
    "persona",
    "setting",
    "can_do",
    "steps",
    "debrief",
}
STEP_KEYS = {
    "character_text",
    "character_gloss",
    "expected",
    "hint",
    "success_note",
    "target_item",
}
TARGET_KEYS = {"target_text", "gloss", "transliteration", "notes"}
DEBRIEF_KEYS = {"strengths", "fix", "cards"}
CARD_KEYS = {"target_text", "gloss", "transliteration", "notes"}


def _assert_nonempty_string(value):
    assert isinstance(value, str)
    assert value.strip()


def test_scene_count_and_slugs():
    assert len(SCENES) == 4

    slugs = [scene["slug"] for scene in SCENES]

    assert len(slugs) == len(set(slugs))
    assert set(slugs) == EXPECTED_SLUGS


@pytest.mark.parametrize(
    "scene", SCENES, ids=lambda scene: scene["slug"]
)
def test_scene_has_required_shape(scene):
    assert SCENE_KEYS <= set(scene)

    _assert_nonempty_string(scene["slug"])
    _assert_nonempty_string(scene["title"])
    _assert_nonempty_string(scene["subtitle"])
    _assert_nonempty_string(scene["goal"])
    _assert_nonempty_string(scene["persona"])
    _assert_nonempty_string(scene["setting"])
    _assert_nonempty_string(scene["can_do"])

    assert scene["level"] == EXPECTED_LEVELS[scene["slug"]]
    assert len(scene["steps"]) >= 3


@pytest.mark.parametrize(
    "scene", SCENES, ids=lambda scene: scene["slug"]
)
def test_steps_have_character_lines_and_answers(scene):
    for step in scene["steps"]:
        assert STEP_KEYS <= set(step)

        _assert_nonempty_string(step["character_text"])
        _assert_nonempty_string(step["character_gloss"])
        _assert_nonempty_string(step["hint"])
        _assert_nonempty_string(step["success_note"])

        expected = step["expected"]

        assert 2 <= len(expected) <= 4
        assert len(expected) == len(set(expected))
        for answer in expected:
            _assert_nonempty_string(answer)

        target = step["target_item"]

        assert TARGET_KEYS <= set(target)
        for key in TARGET_KEYS:
            _assert_nonempty_string(target[key])


@pytest.mark.parametrize(
    "scene", SCENES, ids=lambda scene: scene["slug"]
)
def test_debrief_has_two_strengths_and_three_cards(scene):
    debrief = scene["debrief"]

    assert DEBRIEF_KEYS <= set(debrief)

    strengths = debrief["strengths"]

    assert len(strengths) == 2
    assert len(strengths) == len(set(strengths))
    for strength in strengths:
        _assert_nonempty_string(strength)

    _assert_nonempty_string(debrief["fix"])

    cards = debrief["cards"]

    assert len(cards) == 3

    korean_chunks = []
    for card in cards:
        assert CARD_KEYS <= set(card)
        for key in CARD_KEYS:
            _assert_nonempty_string(card[key])
        korean_chunks.append(card["target_text"])

    assert len(korean_chunks) == len(set(korean_chunks))
