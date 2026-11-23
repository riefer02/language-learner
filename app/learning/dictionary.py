"""Dictionary search and the learner's personal term library."""

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from app import db
from app.learning.scheduler import new_review_card
from app.models import Item, ReviewCard
from app.models_language import TermCard


def item_query(language_id=None, query_text=None, item_type=None, level=None):
    query = Item.query
    if language_id is not None:
        query = query.filter(Item.language_id == language_id)
    if query_text:
        like = f"%{query_text}%"
        query = query.filter(
            or_(
                Item.target_text.ilike(like),
                Item.gloss.ilike(like),
                Item.transliteration.ilike(like),
                Item.notes.ilike(like),
            )
        )
    if item_type in {"lexeme", "chunk", "grammar", "sentence"}:
        query = query.filter(Item.item_type == item_type)
    if level in {1, 2, 3, 4, 5, 6}:
        query = query.filter(Item.level == level)
    return query


def search_items(language_id=None, query_text=None, item_type=None, level=None,
                 limit=50):
    return (
        item_query(language_id, query_text, item_type, level)
        .order_by(Item.level.asc(), Item.id.asc())
        .limit(limit)
        .all()
    )


def ensure_item_card(user_id, item):
    """Put a saved term into the review queue at its default skill."""
    card = ReviewCard.query.filter_by(
        user_id=user_id, item_id=item.id, skill=item.default_skill
    ).first()
    if card is None:
        card = new_review_card(user_id, item.id, item.default_skill)
        db.session.add(card)
        db.session.flush()
    return card


def save_term(user_id, language_id, item_id, context_sentence=None, source="dictionary"):
    item = db.session.get(Item, item_id)
    if item is None:
        raise ValueError("Item not found")
    if language_id is not None and item.language_id not in (None, language_id):
        raise ValueError("Item is not in the active language")

    card = TermCard.query.filter_by(user_id=user_id, item_id=item.id).first()
    if card is None:
        card = TermCard(
            user_id=user_id,
            language_id=item.language_id or language_id,
            item_id=item.id,
            source=source,
            context_sentence=context_sentence,
        )
        if card.language_id is None:
            raise ValueError("A language is required to save a term")
        db.session.add(card)
    elif context_sentence and not card.context_sentence:
        card.context_sentence = context_sentence
    ensure_item_card(user_id, item)
    try:
        db.session.flush()
    except IntegrityError:
        # Two saves (UI + teacher, or a double click) can race the unique
        # constraints. Roll back and return the winner's row.
        db.session.rollback()
        card = TermCard.query.filter_by(
            user_id=user_id, item_id=item.id
        ).first()
        if card is None:
            raise
        ensure_item_card(user_id, item)
        db.session.flush()
    return card


def list_terms(user_id, language_id=None, limit=200):
    query = TermCard.query.filter_by(user_id=user_id)
    if language_id is not None:
        query = query.filter(TermCard.language_id == language_id)
    return query.order_by(TermCard.created_at.desc()).limit(limit).all()


def serialize_item(item):
    return {
        "id": item.id,
        "text": item.target_text,
        "gloss": item.gloss,
        "transliteration": item.transliteration,
        "item_type": item.item_type,
        "level": item.level,
        "audio_url": item.audio_path,
        "notes": item.notes,
    }


def serialize_term(card):
    return {
        "id": card.id,
        "item_id": card.item_id,
        "text": card.item.target_text if card.item else None,
        "gloss": card.item.gloss if card.item else None,
        "transliteration": card.item.transliteration if card.item else None,
        "context_sentence": card.context_sentence,
        "source": card.source,
        "created_at": card.created_at.isoformat() if card.created_at else None,
    }
