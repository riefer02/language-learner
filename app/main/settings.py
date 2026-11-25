"""Learner settings and push subscriptions."""

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import (
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_wtf.csrf import validate_csrf
from werkzeug.exceptions import BadRequest

from app import db
from app.learning.service import current_language, get_or_create_local_user
from app.main import main
from app.main.helpers import _check_csrf
from app.models_language import Language
from app.services.push import push_configured, subscribe, unsubscribe


@main.route("/<lang_code>/settings", methods=["GET", "POST"])
def settings():
    user = get_or_create_local_user()
    if request.method == "POST":
        _check_csrf()
        goal = request.form.get("goal", user.goal)
        daily_minutes = request.form.get("daily_minutes", type=int)
        experience = request.form.get("experience", user.experience)
        timezone = request.form.get("timezone") or user.timezone
        reminder_time = request.form.get("reminder_time") or "19:00"

        try:
            ZoneInfo(timezone)
        except (KeyError, ValueError, ZoneInfoNotFoundError):
            timezone = "UTC"

        if daily_minutes in {3, 10, 25}:
            user.daily_minutes = daily_minutes
        if goal in {
            "everyday",
            "travel",
            "work",
            "culture",
            "topik",
            "family",
        }:
            user.goal = goal
        if experience in {"new", "hangul", "some", "intermediate"}:
            user.experience = experience
        user.timezone = timezone
        try:
            hour, minute = [
                int(part) for part in reminder_time.split(":")
            ]
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                user.reminder_time = f"{hour:02d}:{minute:02d}"
        except (TypeError, ValueError):
            pass
        language_code = request.form.get("language")
        selected_code = None
        selected = Language.query.filter_by(
            code=language_code, is_active=True
        ).first()
        if selected is not None:
            selected_code = selected.code
            user.target_language_id = selected.id
            session.pop("review_limit", None)
            session.pop("review_count", None)
            session.pop("review_mode", None)
        user.reminder_enabled = request.form.get("reminder_enabled") == "on"
        db.session.commit()
        if selected_code is None:
            language = current_language(user)
            selected_code = language.code if language else "ko"
        return redirect(
            url_for(
                "main.settings",
                lang_code=selected_code,
                saved=1,
            )
        )

    languages = Language.query.filter_by(is_active=True).order_by(
        Language.id.asc()
    ).all()
    return render_template(
        "settings.html",
        user=user,
        language=current_language(user),
        languages=languages,
        push_enabled=push_configured(),
        vapid_public_key=current_app.config.get("VAPID_PUBLIC_KEY"),
        saved=request.args.get("saved") == "1",
    )


@main.route("/api/push/subscribe", methods=["POST"])
def push_subscribe():
    user = get_or_create_local_user()
    if not push_configured():
        return jsonify({"error": "Push is not configured on this server"}), 503

    if current_app.config.get("WTF_CSRF_ENABLED", True):
        try:
            validate_csrf(request.headers.get("X-CSRFToken"))
        except Exception as error:
            raise BadRequest("Invalid or missing CSRF token") from error

    payload = request.get_json(silent=True) or {}
    keys = payload.get("keys") or {}
    try:
        subscribe(
            user,
            endpoint=payload.get("endpoint"),
            p256dh=keys.get("p256dh"),
            auth=keys.get("auth"),
            user_agent=request.user_agent.string,
        )
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    return jsonify({"ok": True})


@main.route("/api/push/unsubscribe", methods=["POST"])
def push_unsubscribe():
    user = get_or_create_local_user()
    if current_app.config.get("WTF_CSRF_ENABLED", True):
        try:
            validate_csrf(request.headers.get("X-CSRFToken"))
        except Exception as error:
            raise BadRequest("Invalid or missing CSRF token") from error
    payload = request.get_json(silent=True) or {}
    unsubscribe(user, payload.get("endpoint"))
    return jsonify({"ok": True})
