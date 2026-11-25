"""HTTP and page routes for the real-time teacher."""

from datetime import UTC, datetime

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
from app.learning.service import current_language, get_or_create_local_user
from app.models_language import Language
from app.models_teacher import Drill, TeacherSession
from app.services import teacher as teacher_service
from app.utils.rate_limit import rate_limit

teacher = Blueprint("teacher", __name__)


def _csrf():
    if current_app.config.get("WTF_CSRF_ENABLED", True):
        try:
            validate_csrf(request.headers.get("X-CSRFToken"))
        except Exception as error:
            raise BadRequest("Invalid or missing CSRF token") from error


def _language():
    return Language.query.filter_by(code="ko").first()


def _error(message, status):
    return jsonify({"error": message}), status


@teacher.route("/<lang_code>/learn/teacher")
def panel():
    if not teacher_service.teacher_enabled():
        return _error("The teacher is disabled", 404)
    user = get_or_create_local_user()
    language = current_language(user)
    if language is not None and language.code != "ko":
        return redirect(url_for("learn.today"))
    sessions = (
        TeacherSession.query.filter_by(user_id=user.id)
        .order_by(TeacherSession.started_at.desc())
        .limit(5)
        .all()
    )
    return render_template(
        "teacher.html",
        user=user,
        language=language,
        plans=teacher_service.PLANS,
        sessions=sessions,
        provider_configured=bool(current_app.config.get("OPENAI_API_KEY")),
        voice_supported=bool(language and language.code == "ko"),
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
    if language is not None and language.code != "ko":
        return _error("The voice teacher is Korean-only for now", 503)
    try:
        session, answer = teacher_service.create_session(
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

    return jsonify({"session_id": session.id, "sdp": answer}), 201


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
