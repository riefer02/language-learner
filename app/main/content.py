"""Dictionary, saved terms, library, and resource browsing."""

from flask import abort, jsonify, redirect, render_template, request, url_for
from sqlalchemy import or_

from app import db
from app.learning.dictionary import (
    list_terms,
    save_term,
    search_items,
    serialize_item,
    serialize_term,
)
from app.learning.service import (
    current_language,
    get_or_create_local_user,
    request_language,
)
from app.main import main
from app.main.helpers import _check_csrf
from app.models import Item, Phrase


@main.route("/<lang_code>/library")
def library():
    page = request.args.get("page", 1, type=int)
    per_page = 10
    user = get_or_create_local_user()
    language = current_language(user)
    phrases = Phrase.query.order_by(
        Phrase.created_at.desc(), Phrase.id.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    terms = list_terms(
        user.id, language_id=language.id if language else None
    )
    return render_template(
        "library.html",
        phrases=phrases,
        terms=terms,
        language=language,
    )


@main.route("/<lang_code>/dictionary")
def dictionary():
    query_text = (request.args.get("q") or "").strip()[:100]
    item_type = request.args.get("type", "")
    level = request.args.get("level", type=int)
    user = get_or_create_local_user()
    language = current_language(user)
    items = search_items(
        language_id=language.id if language else None,
        query_text=query_text,
        item_type=item_type,
        level=level,
    )
    return render_template(
        "dictionary.html",
        items=items,
        q=query_text,
        item_type=item_type,
        level=level,
        language=language,
        saved=request.args.get("saved") == "1",
    )


@main.route("/api/dictionary")
def api_dictionary():
    query_text = (request.args.get("q") or "").strip()[:100]
    language = request_language()
    items = search_items(
        language_id=language.id if language else None,
        query_text=query_text,
        limit=20,
    )
    return jsonify({"items": [serialize_item(item) for item in items]})


@main.route("/<lang_code>/dictionary/<int:item_id>/save", methods=["POST"])
def save_dictionary_item(item_id):
    _check_csrf()
    user = get_or_create_local_user()
    language = current_language(user)
    context = (request.form.get("context_sentence") or "").strip()[:500] or None
    try:
        save_term(
            user.id,
            language.id if language else None,
            item_id,
            context_sentence=context,
            source="dictionary",
        )
        db.session.commit()
    except ValueError as error:
        db.session.rollback()
        abort(400, description=str(error))
    return redirect(url_for("main.dictionary", q=request.form.get("q", ""), saved=1))


@main.route("/api/terms")
def api_terms():
    user = get_or_create_local_user()
    language = request_language()
    terms = list_terms(
        user.id, language_id=language.id if language else None
    )
    return jsonify({"terms": [serialize_term(card) for card in terms]})


@main.route("/<lang_code>/resources")
def resources():
    query_text = (request.args.get("q") or "").strip()[:100]
    item_type = request.args.get("type", "")
    level = request.args.get("level", type=int)
    language = current_language()

    query = Item.query
    if language is not None:
        query = query.filter(Item.language_id == language.id)
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

    items = query.order_by(Item.level.asc(), Item.id.asc()).limit(100).all()
    scope = Item.query
    if language is not None:
        scope = scope.filter(Item.language_id == language.id)
    counts = {
        "total": scope.count(),
        "grammar": scope.filter_by(item_type="grammar").count(),
        "chunks": scope.filter_by(item_type="chunk").count(),
        "words": scope.filter_by(item_type="lexeme").count(),
    }

    return render_template(
        "resources.html",
        items=items,
        q=query_text,
        item_type=item_type,
        level=level,
        counts=counts,
        language=language,
    )
