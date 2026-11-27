"""Listening practice: audio-first multiple choice from the deck's clips."""

from app import db
from app.learning.service import get_or_create_local_user
from app.models import Item
from app.models_language import Language

COUNT = 6


def _amharic(app):
    language = Language.query.filter_by(code="am").first()
    if language is None:
        language = Language(code="am", name="Amharic", native_name="አማርኛ")
        db.session.add(language)
        db.session.commit()
    return language


def _clips(app, count=COUNT):
    language = _amharic(app)
    user = get_or_create_local_user()
    user.target_language_id = language.id
    words = [
        ("ቡና", "coffee"),
        ("ውሃ", "water"),
        ("ዳቦ", "bread"),
        ("ቤት", "house"),
        ("መንገድ", "road"),
        ("ትምህርት", "lesson"),
        ("ሰዓት", "hour"),
        ("ልብስ", "clothes"),
    ][:count]
    items = []
    for index, (target, gloss) in enumerate(words):
        item = Item(
            item_type="lexeme",
            target_text=target,
            transliteration=f"t{index}",
            gloss=gloss,
            level=1,
            language_id=language.id,
            default_skill="recognize",
            audio_path=f"/static/audio/test_{index}.mp3",
        )
        db.session.add(item)
        items.append(item)
    db.session.commit()
    return items


def test_listen_page_offers_audio_questions(client, app):
    with app.app_context():
        _clips(app)

    page = client.get("/am/learn/listen")

    assert page.status_code == 200
    assert b"Listen, then choose the meaning." in page.data
    assert b"listen-audio" in page.data
    assert b"Check answers" in page.data


def test_listen_scores_a_perfect_round(client, app):
    with app.app_context():
        _clips(app)

    client.get("/am/learn/listen")
    with client.session_transaction() as session:
        quiz = session["listen_quiz"]
    answers = {f"answer-{entry['item_id']}": entry["item_id"] for entry in quiz}

    page = client.post("/am/learn/listen", data=answers)

    assert page.status_code == 200
    assert f"{len(quiz)} / {len(quiz)} correct".encode() in page.data


def test_listen_marks_wrong_answers(client, app):
    with app.app_context():
        _clips(app)

    client.get("/am/learn/listen")
    with client.session_transaction() as session:
        quiz = session["listen_quiz"]
    answers = {
        f"answer-{entry['item_id']}": next(
            option for option in entry["options"] if option != entry["item_id"]
        )
        for entry in quiz
    }

    page = client.post("/am/learn/listen", data=answers)

    assert page.status_code == 200
    assert f"0 / {len(quiz)} correct".encode() in page.data
    assert b"You chose" in page.data


def test_listen_redirects_when_the_deck_has_no_audio(client, app):
    with app.app_context():
        language = Language.query.filter_by(code="ko").first()
        if language is None:
            language = Language(code="ko", name="Korean", native_name="한국어")
            db.session.add(language)
            db.session.commit()
        user = get_or_create_local_user()
        user.target_language_id = language.id
        db.session.commit()

    response = client.get("/ko/learn/listen")

    assert response.status_code == 302
