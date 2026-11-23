"""Dictionary search, saved terms, and the term library page."""

from app import db
from app.learning.service import get_or_create_local_user
from app.models import Item, ReviewCard
from app.models_language import Language, TermCard


def _language(app, code="ko", name="Korean", native="한국어"):
    language = Language.query.filter_by(code=code).first()
    if language is None:
        language = Language(code=code, name=name, native_name=native)
        db.session.add(language)
        db.session.commit()
    return language


def _item(target_text, gloss, language_id):
    item = Item(
        item_type="lexeme",
        target_text=target_text,
        gloss=gloss,
        level=1,
        language_id=language_id,
        default_skill="recognize",
    )
    db.session.add(item)
    db.session.commit()
    return item


def test_dictionary_search_and_save_creates_term_and_review_card(app, client):
    with app.app_context():
        language = _language(app)
        user = get_or_create_local_user()
        user.target_language_id = language.id
        db.session.commit()
        item = _item("커피", "coffee", language.id)
        item_id = item.id

    page = client.get("/ko/dictionary?q=coffee")
    assert page.status_code == 200
    assert "커피".encode() in page.data

    response = client.post(
        f"/ko/dictionary/{item_id}/save",
        data={"context_sentence": "커피 한 잔 주세요.", "q": "coffee"},
    )
    assert response.status_code == 302

    with app.app_context():
        term = TermCard.query.one()
        assert term.item_id == item_id
        assert term.context_sentence == "커피 한 잔 주세요."
        assert term.source == "dictionary"
        card = ReviewCard.query.filter_by(item_id=item_id, skill="recognize").one()
        assert card.reps == 0

    library = client.get("/ko/library")
    assert library.status_code == 200
    assert b"My terms" in library.data
    assert "커피".encode() in library.data


def test_dictionary_is_language_scoped(app, client):
    with app.app_context():
        korean = _language(app)
        amharic = _language(app, "am", "Amharic", "አማርኛ")
        user = get_or_create_local_user()
        user.target_language_id = korean.id
        db.session.commit()
        _item("커피", "coffee", korean.id)
        _item("ቡና", "coffee", amharic.id)

    page = client.get("/ko/dictionary?q=coffee")
    assert page.status_code == 200
    assert "커피".encode() in page.data
    assert "ቡና".encode() not in page.data

    api = client.get("/api/dictionary?q=coffee")
    assert api.status_code == 200
    payload = api.get_json()
    assert [row["text"] for row in payload["items"]] == ["커피"]


def test_api_terms_returns_saved_terms(app, client):
    with app.app_context():
        language = _language(app)
        user = get_or_create_local_user()
        user.target_language_id = language.id
        db.session.commit()
        item = _item("물", "water", language.id)
        db.session.add(
            TermCard(
                user_id=user.id,
                language_id=language.id,
                item_id=item.id,
                source="teacher",
                context_sentence="물 주세요.",
            )
        )
        db.session.commit()

    response = client.get("/api/terms")
    assert response.status_code == 200
    terms = response.get_json()["terms"]
    assert terms[0]["text"] == "물"
    assert terms[0]["context_sentence"] == "물 주세요."


def test_library_only_shows_phrases_for_the_active_language(app, client):
    from app.models import Phrase

    with app.app_context():
        korean = _language(app)
        amharic = _language(app, "am", "Amharic", "አማርኛ")
        user = get_or_create_local_user()
        user.target_language_id = korean.id
        db.session.add_all(
            [
                Phrase(
                    source_text="Hello",
                    target_text="안녕하세요",
                    target_language_id=korean.id,
                    audio_path="/static/audio/ko.mp3",
                ),
                Phrase(
                    source_text="Hello",
                    target_text="ሰላም",
                    target_language_id=amharic.id,
                    audio_path="/static/audio/am.mp3",
                ),
            ]
        )
        db.session.commit()

    page = client.get("/ko/library")
    assert page.status_code == 200
    assert "안녕하세요".encode() in page.data
    assert "ሰላም".encode() not in page.data


def test_empty_dictionary_prompts_instead_of_dumping_the_deck(client):
    page = client.get("/ko/dictionary")
    assert page.status_code == 200
    assert b"Search your" in page.data
    assert b"Browse the whole deck" in page.data
    assert b'class="dictionary-entry"' not in page.data
