"""Tests for the hand-authored Hangul curriculum data."""

import pytest

from app.learning.hangul_data import HANGUL_LESSONS

EXPECTED_SLUGS = ["letters", "vowels-and-blocks", "batchim-sound-changes"]
EXPECTED_DRILL_COUNTS = {
    "letters": 10,
    "vowels-and-blocks": 10,
    "batchim-sound-changes": 12,
}
LESSON_KEYS = {
    "slug",
    "day",
    "title",
    "subtitle",
    "goal",
    "summary",
    "can_do",
    "sections",
    "drills",
    "notes",
}
SECTION_KEYS = {"heading", "body"}


def _lesson_ids(lesson):
    return lesson["slug"]


def test_curriculum_has_the_three_expected_lessons():
    assert [lesson["slug"] for lesson in HANGUL_LESSONS] == EXPECTED_SLUGS


def test_slugs_are_unique():
    slugs = [lesson["slug"] for lesson in HANGUL_LESSONS]

    assert len(slugs) == len(set(slugs))


def test_days_are_unique_and_ordered():
    days = [lesson["day"] for lesson in HANGUL_LESSONS]

    assert days == [1, 2, 3]


@pytest.mark.parametrize("lesson", HANGUL_LESSONS, ids=_lesson_ids)
def test_lesson_has_required_fields(lesson):
    assert LESSON_KEYS <= set(lesson)

    for key in ("slug", "title", "subtitle", "goal", "summary", "can_do"):
        assert isinstance(lesson[key], str)
        assert lesson[key].strip()

    assert isinstance(lesson["day"], int)


@pytest.mark.parametrize("lesson", HANGUL_LESSONS, ids=_lesson_ids)
def test_lesson_has_sections(lesson):
    assert isinstance(lesson["sections"], list)
    assert lesson["sections"]

    for section in lesson["sections"]:
        assert SECTION_KEYS <= set(section)
        assert isinstance(section["heading"], str)
        assert section["heading"].strip()
        assert isinstance(section["body"], str)
        assert section["body"].strip()


@pytest.mark.parametrize("lesson", HANGUL_LESSONS, ids=_lesson_ids)
def test_section_tables_are_rectangular(lesson):
    for section in lesson["sections"]:
        if "table" not in section:
            continue

        table = section["table"]
        headers = table["headers"]
        rows = table["rows"]

        assert isinstance(headers, list)
        assert headers
        assert all(isinstance(header, str) and header.strip() for header in headers)
        assert isinstance(rows, list)
        assert rows

        for row in rows:
            assert isinstance(row, list)
            assert len(row) == len(headers)
            assert all(isinstance(cell, str) and cell.strip() for cell in row)


@pytest.mark.parametrize("lesson", HANGUL_LESSONS, ids=_lesson_ids)
def test_lesson_has_expected_number_of_drills(lesson):
    assert len(lesson["drills"]) == EXPECTED_DRILL_COUNTS[lesson["slug"]]


@pytest.mark.parametrize("lesson", HANGUL_LESSONS, ids=_lesson_ids)
def test_every_drill_is_well_formed(lesson):
    for drill in lesson["drills"]:
        assert isinstance(drill["prompt"], str)
        assert drill["prompt"].strip()
        assert isinstance(drill["options"], list)
        assert len(drill["options"]) == 4
        assert all(isinstance(option, str) and option.strip() for option in drill["options"])
        assert len(set(drill["options"])) == 4
        assert drill["answer"] in drill["options"]
        assert isinstance(drill["explanation"], str)
        assert drill["explanation"].strip()


@pytest.mark.parametrize("lesson", HANGUL_LESSONS, ids=_lesson_ids)
def test_lesson_has_notes(lesson):
    assert isinstance(lesson["notes"], list)
    assert lesson["notes"]
    assert all(isinstance(note, str) and note.strip() for note in lesson["notes"])
