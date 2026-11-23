"""Teacher session creation, tools, drills, and FSRS handoff."""

import json

import pytest

from app import db
from app.learning.service import get_or_create_local_user
from app.models import Item, ReviewCard
from app.models_language import Language, TermCard
from app.models_teacher import Drill, DrillAttempt, TeacherSession
from app.services import teacher as teacher_service


class FakeProvider:
    name = "fake_realtime"

    def __init__(self, fail=False):
        self.fail = fail
        self.calls = []

    def create_call(self, session_config, sdp):
        self.calls.append({"config": session_config, "sdp": sdp})
        if self.fail:
            raise teacher_service.TeacherProviderError("provider unavailable")
        return "call_test_123", "v=0\r\nfake-answer"


@pytest.fixture()
def fake_provider(app):
    provider = FakeProvider()
    app.extensions["teacher_provider"] = provider
    return provider


def _korean(app):
    language = Language.query.filter_by(code="ko").first()
    if language is None:
        language = Language(code="ko", name="Korean", native_name="한국어")
        db.session.add(language)
        db.session.commit()
    return language


def _item(app, korean="커피", english="coffee", language_id=None):
    if language_id is None:
        language_id = _korean(app).id
    item = Item(
        item_type="lexeme",
        korean=korean,
        english=english,
        level=1,
        language_id=language_id,
    )
    db.session.add(item)
    db.session.commit()
    return item


def _session(app, language_id=None):
    if language_id is None:
        language_id = _korean(app).id
    user = get_or_create_local_user()
    session = TeacherSession(
        user_id=user.id,
        language_id=language_id,
        plan_slug="cafe",
        plan_title="Order at a café",
        status="active",
    )
    db.session.add(session)
    db.session.commit()
    return session


def test_panel_renders(client):
    response = client.get("/learn/teacher")
    assert response.status_code == 200
    assert b"Talk to Kiku" in response.data
    assert b"Start speaking" in response.data


def test_session_creation_mints_sdp_and_keeps_provider_config_server_side(
    app, client, fake_provider
):
    response = client.post(
        "/api/teacher/sessions",
        json={"sdp": "v=0\r\noffer", "plan": "cafe"},
    )
    assert response.status_code == 201, response.get_data(as_text=True)
    payload = response.get_json()
    assert payload["sdp"] == "v=0\r\nfake-answer"
    assert "OPENAI" not in json.dumps(payload).upper()

    with app.app_context():
        session = db.session.get(TeacherSession, payload["session_id"])
        assert session.status == "active"
        assert session.provider_session_id == "call_test_123"
        assert session.plan_slug == "cafe"

    config = fake_provider.calls[0]["config"]
    assert config["model"] == "gpt-realtime-2.1-mini"
    assert config["audio"]["input"]["transcription"]["language"] == "ko"
    assert config["audio"]["input"]["transcription"]["model"] == "gpt-transcribe"
    assert {tool["name"] for tool in config["tools"]} == {
        "get_due_items",
        "lookup_dictionary",
        "create_drill",
        "add_term_to_library",
        "log_attempt",
        "end_session_summary",
    }


def test_provider_failure_marks_session_failed(app, client):
    app.extensions["teacher_provider"] = FakeProvider(fail=True)
    response = client.post(
        "/api/teacher/sessions", json={"sdp": "v=0\r\noffer", "plan": "cafe"}
    )
    assert response.status_code == 502
    with app.app_context():
        session = TeacherSession.query.one()
        assert session.status == "failed"


def test_create_drill_is_scoped_to_the_session_language(app):
    with app.app_context():
        korean = _korean(app)
        spanish = Language(code="es", name="Spanish", native_name="Español")
        db.session.add(spanish)
        db.session.commit()

        item = _item(app, language_id=korean.id)
        their_item = _item(app, "agua", "water", language_id=spanish.id)
        session = _session(app, language_id=korean.id)

        result = teacher_service.dispatch_tool(
            session,
            "create_drill",
            {
                "item_ids": [item.id],
                "drill_type": "translate_to_target",
                "count": 1,
            },
        )
        assert result["drills"][0]["prompt"] == "Say in Korean: coffee"
        assert result["drills"][0]["expected"] == "커피"

        with pytest.raises(teacher_service.TeacherToolError) as error:
            teacher_service.dispatch_tool(
                session,
                "create_drill",
                {"item_ids": [their_item.id], "count": 1},
            )
        assert error.value.code == "item_out_of_scope"


def test_log_attempt_creates_one_review_card_and_is_idempotent(app):
    with app.app_context():
        item = _item(app)
        session = _session(app)
        drill_payload = teacher_service.dispatch_tool(
            session,
            "create_drill",
            {"item_ids": [item.id], "count": 1},
        )
        drill_id = drill_payload["drills"][0]["drill_id"]

        first = teacher_service.dispatch_tool(
            session,
            "log_attempt",
            {
                "drill_id": drill_id,
                "response": "커피",
                "client_attempt_id": "attempt-1",
            },
        )
        assert first["acceptable"] is True
        assert first["review_card_id"] is not None

        second = teacher_service.dispatch_tool(
            session,
            "log_attempt",
            {
                "drill_id": drill_id,
                "response": "커피",
                "client_attempt_id": "attempt-1",
            },
        )
        assert second["id"] == first["id"]
        assert DrillAttempt.query.count() == 1
        assert ReviewCard.query.filter_by(item_id=item.id, skill="produce").count() == 1


def test_add_to_library_deduplicates_with_context(app):
    with app.app_context():
        item = _item(app)
        session = _session(app)

        first = teacher_service.dispatch_tool(
            session,
            "add_term_to_library",
            {"item_id": item.id, "context_sentence": "커피 한 잔 주세요."},
        )
        second = teacher_service.dispatch_tool(
            session,
            "add_term_to_library",
            {"item_id": item.id, "context_sentence": "다른 문장."},
        )
        assert first["term_card_id"] == second["term_card_id"]
        assert TermCard.query.count() == 1
        card = TermCard.query.one()
        assert card.source == "teacher"
        assert card.context_sentence == "커피 한 잔 주세요."


def test_end_session_writes_summary_and_status(app):
    with app.app_context():
        session = _session(app)
        result = teacher_service.end_session(session, "Practiced ordering.")
        assert result["summary"] == "Practiced ordering."
        reloaded = db.session.get(TeacherSession, session.id)
        assert reloaded.status == "ended"
        assert reloaded.ended_at is not None


def test_tool_route_rejects_ended_session(app, client):
    with app.app_context():
        item = _item(app)
        session = _session(app)
        session.status = "ended"
        db.session.commit()
        session_id = session.id
        item_id = item.id

    response = client.post(
        "/api/teacher/tools/create_drill",
        json={"session_id": session_id, "args": {"item_ids": [item_id]}},
    )
    assert response.status_code == 404


def test_unknown_tool_is_rejected(app):
    with app.app_context():
        session = _session(app)
        with pytest.raises(teacher_service.TeacherToolError) as error:
            teacher_service.dispatch_tool(session, "drop_database", {})
        assert error.value.code == "unknown_tool"
        assert Drill.query.count() == 0


def test_daily_limit_blocks_a_new_session(app, client):
    from datetime import UTC, datetime, timedelta

    with app.app_context():
        session = _session(app)
        session.started_at = datetime.now(UTC) - timedelta(minutes=10)
        session.ended_at = datetime.now(UTC) - timedelta(minutes=2)
        session.status = "ended"
        db.session.commit()

    app.config["TEACHER_DAILY_MINUTES"] = 5
    response = client.post(
        "/api/teacher/sessions", json={"sdp": "v=0\r\noffer", "plan": "cafe"}
    )
    assert response.status_code == 429
    assert "Daily teacher limit" in response.get_json()["error"]


def test_session_is_ended_after_the_maximum(app, client):
    from datetime import UTC, datetime, timedelta

    with app.app_context():
        session = _session(app)
        session.started_at = datetime.now(UTC) - timedelta(minutes=30)
        db.session.commit()
        session_id = session.id

    app.config["TEACHER_MAX_SESSION_MINUTES"] = 15
    response = client.get(f"/api/teacher/sessions/{session_id}")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ended"
    assert "15-minute limit" in payload["summary"]
