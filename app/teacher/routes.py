"""HTTP and page routes for the real-time teacher."""

from datetime import UTC, datetime, timedelta

from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_wtf.csrf import validate_csrf
from werkzeug.exceptions import BadRequest

from app import db
from app.learning.scheduler import ensure_utc
from app.learning.service import current_language, get_or_create_local_user
from app.models_teacher import Drill, TeacherSession
from app.services import teacher as teacher_service
from app.services.ai import OpenAIConfigError
from app.utils.rate_limit import rate_limit

teacher = Blueprint("teacher", __name__)


def _csrf():
    if current_app.config.get("WTF_CSRF_ENABLED", True):
        try:
            validate_csrf(request.headers.get("X-CSRFToken"))
        except Exception as error:
            raise BadRequest("Invalid or missing CSRF token") from error


def _supported(language):
    return language is None or (
        language.code in teacher_service.SUPPORTED_TEACHER_LANGUAGES
    )


def _error(message, status):
    return jsonify({"error": message}), status


@teacher.route("/<lang_code>/learn/teacher")
def panel():
    if not teacher_service.teacher_enabled():
        return _error("The teacher is disabled", 404)
    user = get_or_create_local_user()
    language = current_language(user)
    if not _supported(language):
        return redirect(url_for("learn.today"))
    session_query = TeacherSession.query.filter_by(user_id=user.id)
    if language is not None:
        # History belongs to the language it was spoken in.
        session_query = session_query.filter(
            TeacherSession.language_id == language.id
        )
    sessions = session_query.order_by(
        TeacherSession.started_at.desc()
    ).limit(5).all()
    session_rows = []
    for item in sessions:
        minutes = None
        if item.started_at and item.ended_at:
            minutes = max(
                1, round((item.ended_at - item.started_at).total_seconds() / 60)
            )
        session_rows.append(
            {
                "plan_title": item.plan_title,
                "when": item.started_at.strftime("%d %b %H:%M")
                if item.started_at
                else "",
                "minutes": minutes,
                "turns": item.turn_count or 0,
                "status": item.status,
                "status_label": {
                    "ended": "",
                    "failed": "didn't connect",
                    "active": "in progress",
                }.get(item.status, item.status),
            }
        )

    return render_template(
        "teacher.html",
        user=user,
        language=language,
        plans=teacher_service.PLANS,
        sessions=session_rows,
        provider_configured=bool(current_app.config.get("OPENAI_API_KEY")),
        max_minutes=int(current_app.config.get("TEACHER_MAX_SESSION_MINUTES", 15)),
        provider=current_app.config.get("TEACHER_PROVIDER", "openai_realtime"),
        voice_supported=_supported(language),
        speech_language=(
            teacher_service.TEACHER_LANGUAGES[language.code]["greeting"]
            if language and language.code in teacher_service.TEACHER_LANGUAGES
            else teacher_service.TEACHER_LANGUAGES["ko"]["greeting"]
        ),
        speech_name=(
            teacher_service.TEACHER_LANGUAGES[language.code]["name"]
            if language and language.code in teacher_service.TEACHER_LANGUAGES
            else teacher_service.TEACHER_LANGUAGES["ko"]["name"]
        ),
    )


@teacher.route("/api/teacher/sessions", methods=["POST"])
@rate_limit(limit=6, window_seconds=60, scope="teacher_session")
def create_session():
    _csrf()
    if not teacher_service.teacher_enabled():
        return _error("The teacher is disabled", 404)

    payload = request.get_json(silent=True) or {}
    user = get_or_create_local_user()
    language = current_language(user)
    if not _supported(language):
        return _error(
            "The voice teacher does not support this language yet", 503
        )
    try:
        session, handle = teacher_service.create_session(
            user_id=user.id,
            language_id=language.id if language else None,
            plan_slug=payload.get("plan") or "free_talk",
            sdp=payload.get("sdp"),
        )
    except teacher_service.TeacherConfigError as error:
        current_app.logger.warning("Teacher config error: %s", error)
        return _error(str(error), 503)
    except teacher_service.TeacherLimitError as error:
        return _error(str(error), 429)
    except teacher_service.TeacherProviderError as error:
        return _error(str(error), 502)
    except ValueError as error:
        return _error(str(error), 400)

    max_minutes = int(current_app.config.get("TEACHER_MAX_SESSION_MINUTES", 15))
    expires_at = (ensure_utc(session.started_at) or datetime.now(UTC)) + timedelta(
        minutes=max_minutes
    )
    body = {
        "session_id": session.id,
        "max_minutes": max_minutes,
        "expires_at": expires_at.isoformat(),
    }
    body.update(handle if isinstance(handle, dict) else {"sdp": handle})
    return jsonify(body), 201


@teacher.route("/api/teacher/tools/<name>", methods=["POST"])
def run_tool(name):
    _csrf()
    payload = request.get_json(silent=True) or {}
    user = get_or_create_local_user()
    session = teacher_service.get_session(user.id, payload.get("session_id"))
    if session is None or session.status == "ended":
        return _error("Teacher session is not active", 404)

    try:
        result = teacher_service.dispatch_tool(session, name, payload.get("args") or {})
    except teacher_service.TeacherToolError as error:
        return _error(error.code, 400)
    return jsonify({"result": result})


@teacher.route("/api/teacher/sessions/<int:session_id>/turns", methods=["POST"])
def add_turn(session_id):
    _csrf()
    payload = request.get_json(silent=True) or {}
    role = payload.get("role")
    if role not in {"teacher", "learner"}:
        return _error("role must be teacher or learner", 400)

    user = get_or_create_local_user()
    session = teacher_service.get_session(user.id, session_id)
    if session is None:
        return _error("Teacher session not found", 404)

    text = (payload.get("text") or "").strip()
    if not text:
        return _error("text is required", 400)
    turn = teacher_service.record_turn(session, role, text[:4000])
    return jsonify({"turn_index": turn.turn_index}), 201


@teacher.route("/api/teacher/sessions/<int:session_id>/end", methods=["POST"])
def end_session(session_id):
    _csrf()
    payload = request.get_json(silent=True) or {}
    user = get_or_create_local_user()
    session = teacher_service.get_session(user.id, session_id)
    if session is None:
        return _error("Teacher session not found", 404)

    result = teacher_service.end_session(session, payload.get("summary"))
    return jsonify(result)


@teacher.route("/api/teacher/drills/<int:drill_id>/attempt", methods=["POST"])
def grade_drill(drill_id):
    """Practice a drill from the debrief, after the call has ended."""
    _csrf()
    payload = request.get_json(silent=True) or {}
    user = get_or_create_local_user()
    drill = Drill.query.filter_by(id=drill_id, user_id=user.id).first()
    if drill is None:
        return _error("Drill not found", 404)
    response_text = (payload.get("response") or "").strip()
    if not response_text:
        return _error("An answer is required", 400)

    args = teacher_service.LogAttemptArgs(
        drill_id=drill.id,
        response=response_text[:500],
        client_attempt_id=(
            payload.get("client_attempt_id") or f"debrief-{drill.id}-{user.id}"
        )[:64],
    )
    attempt = teacher_service.grade_drill(
        user.id,
        drill,
        args.response,
        client_attempt_id=args.client_attempt_id,
    )
    db.session.commit()
    return jsonify(attempt.to_dict())


@teacher.route("/api/teacher/sessions/<int:session_id>/coach", methods=["POST"])
@rate_limit(limit=30, window_seconds=60, scope="teacher_suggest")
def coach(session_id):
    """English of the tutor's last line plus a suggested reply. Text only."""
    _csrf()
    user = get_or_create_local_user()
    session = teacher_service.get_session(user.id, session_id)
    if session is None or session.status != "active":
        return _error("Teacher session is not active", 404)

    try:
        return jsonify(teacher_service.coach_reply(session))
    except teacher_service.TeacherNotReadyError as error:
        return _error(str(error), 409)
    except teacher_service.TeacherError as error:
        return _error(str(error), 502)
    except OpenAIConfigError:
        return _error("The suggestion service is not configured", 503)


@teacher.route("/api/teacher/sessions/<int:session_id>")
def get_session(session_id):
    user = get_or_create_local_user()
    session = teacher_service.get_session(user.id, session_id)
    if session is None:
        return _error("Teacher session not found", 404)
    return jsonify(teacher_service.session_to_dict(session))


@teacher.route("/api/teacher/sessions/<int:session_id>/close", methods=["POST"])
def close_session(session_id):
    """Mark a session ended without a model-authored summary."""
    _csrf()
    user = get_or_create_local_user()
    session = teacher_service.get_session(user.id, session_id)
    if session is None:
        return _error("Teacher session not found", 404)
    if session.status != "ended":
        session.status = "ended"
        session.ended_at = datetime.now(UTC)
        db.session.commit()
    return jsonify({"ok": True})
