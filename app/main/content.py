"""Dictionary, saved terms, library, and resource browsing."""

from flask import abort, jsonify, redirect, render_template, request, url_for
from sqlalchemy import or_

from app import db
from app.languages.variants import (
    REGISTER_LABELS,
    UNGENDERED_REGISTERS,
    addressee_label,
)
from app.learning.dictionary import (
    count_terms,
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
from app.main.helpers import _check_csrf, _error
from app.models import ContentReport, Item, Phrase


@main.route("/<lang_code>/library")
def library():
    page = request.args.get("page", 1, type=int)
    per_page = 10
    user = get_or_create_local_user()
    language = current_language(user)
    phrase_query = Phrase.query
    if language is not None:
        phrase_query = phrase_query.filter(
            or_(
                Phrase.target_language_id == language.id,
                Phrase.target_language_id.is_(None),
            )
        )
    phrases = phrase_query.order_by(
        Phrase.created_at.desc(), Phrase.id.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    terms = list_terms(
        user.id, language_id=language.id if language else None
    )
    # The tabs are about finding your own things fast, so the saved-word tab is
    # only the default when it has something in it.
    term_count = count_terms(
        user.id, language_id=language.id if language else None
    )
    phrase_count = phrase_query.count()
    tab = (request.args.get("tab") or "").strip()
    if tab not in {"terms", "lookups", "find"}:
        tab = "terms" if term_count else ("lookups" if phrase_count else "terms")
    # The "Find words" tab owns the old dictionary search, so looking a word up
    # and keeping it live on one page instead of two that each had a list.
    find_q = (request.args.get("q") or "").strip()[:100]
    item_type = request.args.get("type", "")
    level = request.args.get("level", type=int)
    browsing = request.args.get("browse") == "1"
    items = []
    suggestions = []
    if tab == "find":
        language_id = language.id if language else None
        show_results = bool(find_q or item_type or level or browsing)
        items = (
            search_items(
                language_id=language_id,
                query_text=find_q,
                item_type=item_type,
                level=level,
                limit=200 if browsing else 50,
            )
            if show_results
            else []
        )
        if not show_results:
            suggestions = search_items(language_id=language_id, limit=6)

    return render_template(
        "library.html",
        phrases=phrases,
        terms=terms,
        term_count=term_count,
        phrase_count=phrase_count,
        tab=tab,
        items=items,
        suggestions=suggestions,
        find_q=find_q,
        item_type=item_type,
        level=level,
        browsing=browsing,
        saved=request.args.get("saved") == "1",
        language=language,
        register_labels=(
            REGISTER_LABELS.get(language.code, {}) if language else {}
        ),
        ungendered_registers=(
            sorted(UNGENDERED_REGISTERS.get(language.code, ())) if language else []
        ),
        addressee_label=addressee_label,
    )


@main.route("/<lang_code>/dictionary")
def dictionary():
    """Legacy entry point: the search lives on My terms → Find words."""
    params = {"tab": "find"}
    for key in ("q", "type", "browse", "level"):
        value = request.args.get(key)
        if value:
            params[key] = value
    if request.args.get("saved") == "1":
        params["saved"] = "1"
    return redirect(url_for("main.library", **params), code=302)


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
    params = {"tab": "find", "saved": "1"}
    for key in ("q", "type", "browse", "level"):
        value = request.form.get(key)
        if value:
            params[key] = value
    return redirect(url_for("main.library", **params))


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


REPORT_SURFACES = {
    "review",
    "library",
    "dictionary",
    "translate",
    "teacher",
    "scene",
}
REPORT_KINDS = {
    "meaning",
    "naturalness",
    "register",
    "spelling",
    "audio",
    "other",
}


def _report_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@main.route("/api/content-reports", methods=["POST"])
def api_content_report():
    """Capture a learner correction without changing the content.

    The row keeps a snapshot of what was shown, so triage stays readable even
    after the item or phrase is edited. Applying a correction is a deliberate
    CLI/human step, never an automatic rewrite.
    """
    _check_csrf()
    if not request.is_json:
        return _error("Request body must be JSON", 415)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error("Request body must be a JSON object", 400)

    surface = str(payload.get("surface") or "").strip()
    if surface not in REPORT_SURFACES:
        return _error("Unknown surface", 400)
    kind = str(payload.get("kind") or "").strip()
    if kind not in REPORT_KINDS:
        return _error("Unknown issue kind", 400)

    item_id = _report_int(payload.get("item_id")) or None
    phrase_id = _report_int(payload.get("phrase_id")) or None
    scene_slug = str(payload.get("scene_slug") or "").strip()[:80] or None
    step_index = _report_int(payload.get("step_index"))
    if step_index is not None and not 0 <= step_index <= 50:
        return _error("Invalid step index", 400)
    if not any((item_id, phrase_id, scene_slug)):
        return _error("A report needs an item, phrase, or scene step", 400)

    user = get_or_create_local_user()
    language = request_language()

    item = db.session.get(Item, item_id) if item_id else None
    if item_id and item is None:
        return _error("Item not found", 404)
    if (
        item is not None
        and language is not None
        and item.language_id not in (None, language.id)
    ):
        return _error("Item is outside the active language", 400)

    phrase = db.session.get(Phrase, phrase_id) if phrase_id else None
    if phrase_id and phrase is None:
        return _error("Phrase not found", 404)
    if (
        phrase is not None
        and language is not None
        and phrase.target_language_id not in (None, language.id)
    ):
        return _error("Phrase is outside the active language", 400)

    if item is not None:
        snapshot = item.target_text
        if item.gloss:
            snapshot = f"{snapshot} — {item.gloss}"
    elif phrase is not None:
        snapshot = phrase.target_text or phrase.source_text
        if phrase.source_text and phrase.target_text:
            snapshot = f"{phrase.source_text} — {phrase.target_text}"
    else:
        snapshot = str(payload.get("snapshot_text") or "").strip()[:500]
    if not snapshot:
        return _error("A report needs the text it is about", 400)

    if item is not None:
        report_language_id = item.language_id
    elif language is not None:
        report_language_id = language.id
    else:
        report_language_id = None
    if report_language_id is None and language is not None:
        report_language_id = language.id

    report = ContentReport(
        user_id=user.id,
        language_id=report_language_id,
        item_id=item.id if item is not None else None,
        phrase_id=phrase.id if phrase is not None else None,
        scene_slug=scene_slug,
        step_index=step_index,
        surface=surface,
        snapshot_text=snapshot,
        kind=kind,
        suggested_text=(
            str(payload.get("suggested_text") or "").strip()[:300] or None
        ),
        context=str(payload.get("context") or "").strip()[:200] or None,
        note=str(payload.get("note") or "").strip()[:1000] or None,
    )
    db.session.add(report)
    db.session.commit()
    return jsonify({"id": report.id, "status": report.status}), 201
