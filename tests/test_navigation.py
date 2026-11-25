"""Navigation and IA regressions: header lookup, nav groups, course stepper."""

from app import db
from app.languages.seed import seed_amharic
from app.learning.hangul_data import HANGUL_LESSONS
from app.learning.service import get_or_create_local_user
from app.models_language import Language


def test_header_lookup_and_grouped_nav(client):
    client.get("/ko/learn")
    page = client.get("/ko/learn")

    assert b'class="nav-lookup"' in page.data
    assert b'name="q"' in page.data
    assert b'action="/ko/translate"' in page.data
    assert b"<summary>Learn</summary>" in page.data
    assert b"<summary>Practice</summary>" in page.data
    assert b"<summary>Words</summary>" in page.data
    assert b"Look up" in page.data
    assert b"Hangul" in page.data
    assert b"Resources" not in page.data


def test_look_up_prefills_query(client):
    client.get("/ko/learn")

    page = client.get("/ko/translate?q=thank%20you")

    assert page.status_code == 200
    assert b'value="thank you"' in page.data
    assert b"Look up a word or phrase" in page.data


def test_hangul_lesson_has_clickable_stepper(client):
    client.get("/ko/learn")
    lesson = HANGUL_LESSONS[1]

    page = client.get(f"/ko/learn/hangul/{lesson['slug']}")

    assert page.status_code == 200
    assert b"course-stepper" in page.data
    assert b'aria-current="step"' in page.data
    assert HANGUL_LESSONS[0]["slug"].encode() in page.data
    assert b'id="hangul-bar"' in page.data


def test_amharic_nav_hides_practice_and_moves_fidel_to_learn(client, app):
    client.get("/ko/learn")
    with app.app_context():
        seed_amharic()
        user = get_or_create_local_user()
        amharic = Language.query.filter_by(code="am").one()
        user.target_language_id = amharic.id
        db.session.commit()

    page = client.get("/am/learn")
    if page.status_code == 302:
        page = client.get(page.headers["Location"])

    assert b"<summary>Practice</summary>" not in page.data
    assert b"Fidel" in page.data

    fidel = client.get("/am/learn/fidel/fidel-1")
    assert fidel.status_code == 200
    assert b"course-stepper" in fidel.data
