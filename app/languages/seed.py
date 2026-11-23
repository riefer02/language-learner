"""Seed the Amharic starter pack into the language core."""

from app import db
from app.languages.am_content import AMHARIC_ITEMS
from app.learning.service import ensure_review_cards, get_or_create_local_user
from app.models import Item
from app.models_language import (
    Course,
    Deck,
    DeckItem,
    ItemForm,
    ItemGloss,
    Language,
    LanguageScript,
    LevelScale,
    Script,
)


def _get_or_create(model, defaults=None, **filters):
    row = model.query.filter_by(**filters).first()
    if row is not None:
        return row, False
    row = model(**(defaults or {}), **filters)
    db.session.add(row)
    db.session.flush()
    return row, True


def seed_amharic():
    """Idempotently insert the Amharic deck, forms, glosses, and cards."""
    language, _ = _get_or_create(
        Language,
        defaults={
            "name": "Amharic",
            "native_name": "አማርኛ",
            "direction": "ltr",
            "is_active": True,
        },
        code="am",
    )
    language.is_active = True

    geez, _ = _get_or_create(
        Script,
        defaults={
            "name": "Ge'ez (Fidel)",
            "script_type": "abugida",
            "direction": "ltr",
            "composition": "abugida",
            "unicode_ranges": "[[4608,4991],[4992,5023]]",
        },
        code="geez",
    )
    link = LanguageScript.query.filter_by(
        language_id=language.id, script_id=geez.id
    ).first()
    if link is None:
        db.session.add(
            LanguageScript(
                language_id=language.id,
                script_id=geez.id,
                role="primary",
                is_default=True,
            )
        )

    cefr = LevelScale.query.filter_by(code="cefr").first()
    course, _ = _get_or_create(
        Course,
        defaults={
            "language_id": language.id,
            "level_scale_id": cefr.id if cefr else None,
            "title": "Amharic Core",
            "description": "Fidel literacy plus survival Amharic.",
            "is_active": True,
        },
        slug="amharic-core",
    )
    deck, _ = _get_or_create(
        Deck,
        defaults={
            "language_id": language.id,
            "course_id": course.id,
            "title": "Amharic Core Deck",
            "kind": "core",
        },
        slug="am-core",
    )

    created_items = 0
    for fidel, roman, english, item_type, level, note in AMHARIC_ITEMS:
        item = Item.query.filter_by(
            korean=fidel, english=english, item_type=item_type
        ).first()
        if item is None:
            item = Item(
                item_type=item_type,
                korean=fidel,
                english=english,
                romanization=roman,
                level=level,
                notes=note,
                language_id=language.id,
                primary_deck_id=deck.id,
                key_normalized=fidel,
                default_skill="produce" if item_type != "lexeme" else "recognize",
            )
            db.session.add(item)
            db.session.flush()
            created_items += 1
        else:
            item.language_id = language.id
            item.primary_deck_id = item.primary_deck_id or deck.id

        form = ItemForm.query.filter_by(item_id=item.id, form_kind="citation").first()
        if form is None:
            db.session.add(
                ItemForm(
                    item_id=item.id,
                    script_id=geez.id,
                    form_kind="citation",
                    text=fidel,
                    normalized_text=fidel,
                    transliteration=roman,
                    transliteration_scheme="am_latin",
                    is_primary=True,
                )
            )
        gloss = ItemGloss.query.filter_by(
            item_id=item.id, lang="en", gloss_type="translation"
        ).first()
        if gloss is None:
            db.session.add(
                ItemGloss(
                    item_id=item.id,
                    lang="en",
                    text=english,
                    gloss_type="translation",
                    is_primary=True,
                )
            )
        deck_item = DeckItem.query.filter_by(deck_id=deck.id, item_id=item.id).first()
        if deck_item is None:
            db.session.add(DeckItem(deck_id=deck.id, item_id=item.id, position=item.id))

    db.session.commit()
    user = get_or_create_local_user()
    created_cards = ensure_review_cards(user.id, language_id=language.id)
    return {
        "language_id": language.id,
        "created_items": created_items,
        "created_cards": created_cards,
        "total_items": Item.query.filter_by(language_id=language.id).count(),
    }
