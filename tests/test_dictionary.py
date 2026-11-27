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

    page = client.get("/ko/library?tab=find&q=coffee")
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

    page = client.get("/ko/library?tab=find&q=coffee")
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


def test_library_labels_formal_amharic_as_ungendered(app, client):
    """Two "good morning" lookups used to both read "To a woman"."""
    from app.models import Phrase

    with app.app_context():
        amharic = _language(app, "am", "Amharic", "አማርኛ")
        user = get_or_create_local_user()
        user.target_language_id = amharic.id
        db.session.add_all(
            [
                Phrase(
                    source_text="good morning",
                    target_text="እንደምን አደርሽ?",
                    target_transliteration="Endemin adersh?",
                    target_language_id=amharic.id,
                    addressee="female",
                    register="casual",
                    audio_path="/static/audio/am1.mp3",
                ),
                Phrase(
                    source_text="good morning",
                    target_text="እንደምን አደሩ",
                    target_transliteration="Endemin aderu",
                    target_language_id=amharic.id,
                    addressee="female",
                    register="formal",
                    audio_path="/static/audio/am2.mp3",
                ),
            ]
        )
        db.session.commit()

    page = client.get("/am/library")
    assert page.status_code == 200
    html = page.data.decode()
    assert "To a woman" in html
    assert "Anyone — formal is not gendered" in html


def test_library_phrase_rows_collapse_behind_a_summary(app, client):
    """Ten lookups should not mean ten audio players above the fold."""
    from app.models import Phrase

    with app.app_context():
        amharic = _language(app, "am", "Amharic", "አማርኛ")
        user = get_or_create_local_user()
        user.target_language_id = amharic.id
        db.session.add(
            Phrase(
                source_text="thank you",
                target_text="አመሰግናለሁ",
                target_transliteration="Ameseginalehu",
                target_language_id=amharic.id,
                addressee="any",
                register="formal",
                audio_path="/static/audio/am3.mp3",
            )
        )
        db.session.commit()

    html = client.get("/am/library").data.decode()
    assert '<div class="phrase-entry"' in html
    assert '<details class="phrase-entry-details"' in html
    # The row itself advertises the register; the audio sits in the body.
    phrases = html.split('id="phrases-container"', 1)[1]
    summary = phrases.split("<summary>", 1)[1].split("</summary>", 1)[0]
    assert "Formal" in summary
    # The collapsed row carries the transliteration and its own play control,
    # but not the audio element (that lives in the body).
    assert "Ameseginalehu" in summary
    assert 'class="phrase-entry-caret"' in summary
    # The play button is a sibling of the disclosure, not a nested control
    # inside <summary>: nesting it folded its label into the summary's name.
    assert 'class="phrase-entry-play"' not in summary
    assert 'data-label-play="Play pronunciation for አመሰግናለሁ"' in html
    assert "<audio" not in summary
    assert "<audio" in html


def test_empty_find_tab_prompts_instead_of_dumping_the_deck(client):
    page = client.get("/ko/library?tab=find")
    assert page.status_code == 200
    assert b"Try a word in the target language" in page.data
    assert b"See all entries" in page.data
    assert b'class="dictionary-entry"' not in page.data


def test_library_tabs_separate_saved_words_from_lookups(app, client):
    from app.models import Phrase

    with app.app_context():
        language = _language(app)
        user = get_or_create_local_user()
        user.target_language_id = language.id
        item = _item("커피", "coffee", language.id)
        db.session.add(
            TermCard(
                user_id=user.id,
                language_id=language.id,
                item_id=item.id,
                source="dictionary",
            )
        )
        db.session.add(
            Phrase(
                source_text="good morning",
                target_text="እንደምን አደሩ",
                target_language_id=language.id,
                audio_path="/static/audio/am.mp3",
            )
        )
        db.session.commit()

    terms = client.get("/ko/library?tab=terms")
    assert terms.status_code == 200
    terms_html = terms.data.decode()
    assert 'aria-current="page"' in terms_html
    assert "Words you kept." in terms_html
    assert "커피" in terms_html
    assert "good morning" not in terms_html

    lookups = client.get("/ko/library?tab=lookups")
    lookups_html = lookups.data.decode()
    assert "Phrases you looked up." in lookups_html
    assert "good morning" in lookups_html
    assert "커피" not in lookups_html


def test_library_opens_the_lookups_tab_when_nothing_is_saved(app, client):
    from app.models import Phrase

    with app.app_context():
        language = _language(app)
        user = get_or_create_local_user()
        user.target_language_id = language.id
        db.session.add(
            Phrase(
                source_text="thank you",
                target_text="감사합니다",
                target_language_id=language.id,
                audio_path="/static/audio/ko.mp3",
            )
        )
        db.session.commit()

    page = client.get("/ko/library")
    assert page.status_code == 200
    html = page.data.decode()
    assert "Phrases you looked up." in html
    assert "No saved words yet" not in html


def test_old_dictionary_url_redirects_to_the_find_tab(client):
    client.get("/ko/learn")

    response = client.get("/ko/dictionary?q=coffee")

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/ko/library?tab=find&q=coffee"
    )


def test_words_nav_drops_the_separate_dictionary_entry(client):
    client.get("/ko/learn")
    html = client.get("/ko/learn").data.decode()
    nav = html.split("<summary>Words</summary>", 1)[1].split("</details>", 1)[0]

    assert "Look up" in nav
    assert "My terms" in nav
    assert "Dictionary" not in nav
