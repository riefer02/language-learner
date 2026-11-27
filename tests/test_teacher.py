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


def _item(app, target_text="커피", gloss="coffee", language_id=None):
    if language_id is None:
        language_id = _korean(app).id
    item = Item(
        item_type="lexeme",
        target_text=target_text,
        gloss=gloss,
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
    response = client.get("/ko/learn/teacher")
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
        assert card.session_id == session.id
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


def test_debrief_drill_attempt_works_after_the_call_ends(app, client):
    with app.app_context():
        item = _item(app)
        session = _session(app)
        drill = teacher_service.dispatch_tool(
            session, "create_drill", {"item_ids": [item.id], "count": 1}
        )["drills"][0]
        teacher_service.end_session(session)
        drill_id = drill["drill_id"]

    response = client.post(
        f"/api/teacher/drills/{drill_id}/attempt",
        json={"response": "커피", "client_attempt_id": "debrief-1"},
    )
    assert response.status_code == 200, response.get_data(as_text=True)
    payload = response.get_json()
    assert payload["acceptable"] is True
    assert payload["review_card_id"] is not None


def test_teacher_page_has_first_run_guidance_and_empty_transcript(client):
    page = client.get("/ko/learn/teacher")
    assert page.status_code == 200
    assert b"Before your first call" in page.data
    assert b"Your words will appear here after you start." in page.data


def test_get_due_items_is_scoped_to_the_session_language(app):
    from datetime import UTC, datetime

    from app.learning.scheduler import new_review_card

    with app.app_context():
        korean = _korean(app)
        amharic = Language.query.filter_by(code="am").first()
        if amharic is None:
            amharic = Language(code="am", name="Amharic", native_name="አማርኛ")
            db.session.add(amharic)
            db.session.commit()
        ko_item = _item(app, "커피", "coffee", korean.id)
        am_item = _item(app, "ቡና", "coffee", amharic.id)
        session = _session(app, korean.id)
        for item in (ko_item, am_item):
            card = new_review_card(session.user_id, item.id, "recognize")
            card.due_at = datetime.now(UTC)
            db.session.add(card)
        db.session.commit()

        result = teacher_service.dispatch_tool(
            session, "get_due_items", {"limit": 10}
        )
        ids = {row["item_id"] for row in result["items"]}
        assert ko_item.id in ids
        assert am_item.id not in ids


def test_ending_twice_preserves_the_model_summary(app):
    with app.app_context():
        session = _session(app)
        teacher_service.end_session(session, "Great job today.")
        teacher_service.end_session(session, None)
        assert db.session.get(TeacherSession, session.id).summary_text == (
            "Great job today."
        )


class FakeChat:
    """Minimal chat.completions double for the reply suggestion."""

    def __init__(self, content):
        self.completions = self
        self.calls = []
        self._content = content

    def create(self, **kwargs):
        self.calls.append(kwargs)

        class _Message:
            content = self._content

        class _Choice:
            def __init__(self):
                self.message = _Message()

        class _Response:
            def __init__(self):
                self.choices = [_Choice()]

        return _Response()


class FakeSuggestionClient:
    def __init__(self, content):
        self.chat = FakeChat(content)


def _amharic(app):
    language = Language.query.filter_by(code="am").first()
    if language is None:
        language = Language(code="am", name="Amharic", native_name="አማርኛ")
        db.session.add(language)
        db.session.commit()
    return language


def test_amharic_session_speaks_amharic_with_short_turns(app, fake_provider):
    with app.app_context():
        amharic = _amharic(app)
        session = _session(app, language_id=amharic.id)
        config = teacher_service._session_config(session, "Drew")

    instructions = config["instructions"]
    assert "Amharic speaking tutor" in instructions
    assert "Korean" not in instructions
    assert "12 words" in instructions
    # Ethiopic needs a far bigger output budget than Hangul: at 200 tokens every
    # Amharic reply was cut mid-word, which looked like the teacher going silent.
    assert config["max_output_tokens"] == 1200
    # The realtime transcription endpoint rejects `language: am` (400
    # invalid_value), so Amharic must rely on auto-detection.
    assert "language" not in config["audio"]["input"]["transcription"]
    # Beginners repeat themselves; an interrupt cancelled the reply each time.
    assert config["audio"]["input"]["turn_detection"]["interrupt_response"] is False


def test_amharic_teacher_session_is_created(app, client, fake_provider):
    with app.app_context():
        amharic_id = _amharic(app).id
        user = get_or_create_local_user()
        user.target_language_id = amharic_id
        db.session.commit()

    response = client.post(
        "/api/teacher/sessions", json={"sdp": "v=0\r\noffer", "plan": "cafe"}
    )
    assert response.status_code == 201, response.get_data(as_text=True)

    with app.app_context():
        session = db.session.get(
            TeacherSession, response.get_json()["session_id"]
        )
        assert session.language_id == amharic_id


def test_coach_reply_translates_and_suggests(app, monkeypatch):
    client = FakeSuggestionClient(
        '{"translation": "What would you like?", '
        '"target": "ቡና እፈልጋለሁ።", "romanization": "Buna efeligalehu.", '
        '"gloss": "I would like coffee."}'
    )
    app.extensions["openai_client"] = client

    with app.app_context():
        session = _session(app)
        teacher_service.record_turn(session, "teacher", "ምን ይፈልጋሉ?")
        hint = teacher_service.coach_reply(session)

    assert hint["target"] == "ቡና እፈልጋለሁ።"
    assert hint["gloss"] == "I would like coffee."
    assert hint["translation"] == "What would you like?"
    prompt = client.chat.calls[0]["messages"][1]["content"]
    assert "teacher: ምን ይፈልጋሉ?" in prompt


def test_coach_endpoint_needs_an_active_session(client):
    response = client.post("/api/teacher/sessions/999/coach", json={})
    assert response.status_code == 404


def test_teacher_panel_offers_the_suggestion_toggle_for_amharic(app, client):
    with app.app_context():
        amharic = _amharic(app)
        user = get_or_create_local_user()
        user.target_language_id = amharic.id
        db.session.commit()

    page = client.get("/am/learn/teacher")

    assert page.status_code == 200
    assert b'id="teacher-suggest-toggle"' in page.data
    assert b"Show me a line I could say" in page.data


def test_teacher_history_is_scoped_to_the_active_language(app, client):
    with app.app_context():
        korean = _korean(app)
        amharic = _amharic(app)
        user = get_or_create_local_user()
        db.session.add_all(
            [
                TeacherSession(
                    user_id=user.id,
                    language_id=korean.id,
                    plan_slug="cafe",
                    plan_title="Korean cafe",
                    status="ended",
                ),
                TeacherSession(
                    user_id=user.id,
                    language_id=amharic.id,
                    plan_slug="cafe",
                    plan_title="Amharic cafe",
                    status="ended",
                ),
            ]
        )
        user.target_language_id = amharic.id
        db.session.commit()

    page = client.get("/am/learn/teacher")

    assert b"Amharic cafe" in page.data
    assert b"Korean cafe" not in page.data


def test_coach_returns_409_before_anything_is_said(app, client):
    with app.app_context():
        session_id = _session(app).id

    response = client.post(
        f"/api/teacher/sessions/{session_id}/coach", json={}
    )

    assert response.status_code == 409
    assert b"Nothing has been said yet" in response.data


def test_turn_length_is_configurable(app):
    with app.app_context():
        app.config["TEACHER_MAX_OUTPUT_TOKENS"] = 300
        config = teacher_service._session_config(_session(app))

    assert config["max_output_tokens"] == 300


def test_dictionary_tool_stays_in_the_session_language(app):
    with app.app_context():
        amharic = _amharic(app)
        korean = _korean(app)
        _item(app, "ቡና", "coffee", language_id=amharic.id)
        _item(app, "커피", "coffee", language_id=korean.id)
        session = _session(app, language_id=amharic.id)

        result = teacher_service.tool_lookup_dictionary(
            session, teacher_service.LookupDictionaryArgs(query="coffee")
        )

    targets = [item["target"] for item in result["items"]]
    assert targets == ["ቡና"]


def test_drill_prompt_names_the_session_language(app):
    with app.app_context():
        amharic = _amharic(app)
        item = _item(app, "ቡና", "coffee", language_id=amharic.id)
        session = _session(app, language_id=amharic.id)

        drills = teacher_service.tool_create_drill(
            session,
            teacher_service.CreateDrillArgs(
                item_ids=[item.id], drill_type="translate_to_target"
            ),
        )

    assert drills["drills"][0]["prompt"] == "Say in Amharic: coffee"


def test_teacher_page_carries_the_spoken_language(app, client):
    with app.app_context():
        amharic = _amharic(app)
        user = get_or_create_local_user()
        user.target_language_id = amharic.id
        db.session.commit()

    page = client.get("/am/learn/teacher")

    assert b'data-speech-name="Amharic"' in page.data
    assert 'data-greeting="ሰላም"'.encode() in page.data


def test_turn_detection_is_tuned_for_hesitant_learners(app):
    with app.app_context():
        config = teacher_service._session_config(_session(app))
        detection = config["audio"]["input"]["turn_detection"]

    assert detection["type"] == "server_vad"
    assert detection["threshold"] == 0.4
    assert detection["silence_duration_ms"] == 900
    assert detection["interrupt_response"] is False


def test_turn_detection_is_configurable(app):
    with app.app_context():
        app.config["TEACHER_VAD_SILENCE_MS"] = 1200
        app.config["TEACHER_INTERRUPT_RESPONSE"] = True
        detection = teacher_service._session_config(_session(app))["audio"][
            "input"
        ]["turn_detection"]

    assert detection["silence_duration_ms"] == 1200
    assert detection["interrupt_response"] is True


def test_overdue_session_is_charged_the_cap_not_the_gap(app):
    """A browser closed mid-call must not bill hours of wall-clock minutes."""
    from datetime import UTC, datetime, timedelta

    from app.learning.scheduler import ensure_utc

    with app.app_context():
        app.config["TEACHER_MAX_SESSION_MINUTES"] = 15
        session = _session(app)
        started = datetime.now(UTC) - timedelta(minutes=120)
        session.started_at = started
        db.session.commit()

        teacher_service.expire_if_over_limit(session)

        assert session.status == "ended"
        # Ended at the cap, not at the moment the check happened.
        assert ensure_utc(session.ended_at) == started + timedelta(minutes=15)


def test_session_creation_reports_when_the_call_will_end(app, client, fake_provider):
    response = client.post(
        "/api/teacher/sessions", json={"sdp": "v=0\r\noffer", "plan": "cafe"}
    )
    payload = response.get_json()

    assert response.status_code == 201
    assert payload["max_minutes"] == 15
    assert payload["expires_at"].endswith("+00:00")


def test_amharic_prompt_forbids_english_mixed_into_sentences(app):
    with app.app_context():
        config = teacher_service._session_config(
            _session(app, language_id=_amharic(app).id)
        )

    instructions = config["instructions"]
    assert "Never mix English words into an Amharic sentence" in instructions
    assert "ቡና" not in instructions  # no invented vocabulary examples


# --- Gemini Live provider (second transport) ------------------------------


class FakeHTTPResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


def test_gemini_function_declarations_reuse_the_shared_tools():
    from app.services import teacher_gemini

    declarations = teacher_gemini.function_declarations()

    names = {item["name"] for item in declarations}
    assert names == {tool["name"] for tool in teacher_service.TOOL_SCHEMAS}
    lookup = next(d for d in declarations if d["name"] == "lookup_dictionary")
    assert lookup["parameters"]["properties"]["query"]["type"] == "string"
    assert lookup["parameters"]["required"] == ["query"]


def test_gemini_session_config_is_amharic_and_waits_for_the_learner(app):
    from app.services import teacher_gemini

    with app.app_context():
        amharic = _amharic(app)
        config = teacher_gemini.build_session(
            _session(app, language_id=amharic.id)
        )

    instructions = config["systemInstruction"]["parts"][0]["text"]
    assert "Amharic speaking tutor" in instructions
    assert config["generationConfig"]["responseModalities"] == ["AUDIO"]
    detection = config["realtimeInputConfig"]["automaticActivityDetection"]
    assert detection["silenceDurationMs"] == 900
    assert detection["disabled"] is False
    assert config["inputAudioTranscription"] == {}
    assert config["tools"][0]["functionDeclarations"]


def test_gemini_token_request_surfaces_provider_errors(app, monkeypatch):
    from app.services import teacher_gemini

    def fake_post(url, params=None, json=None, timeout=None):
        return FakeHTTPResponse(400, {"error": {"message": "API key not valid"}})

    monkeypatch.setattr(teacher_gemini.httpx, "post", fake_post)

    with app.app_context():
        app.config["GEMINI_API_KEY"] = "test-key"
        try:
            teacher_gemini.mint_ephemeral_token({"model": "models/gemini-3.8-live"})
        except teacher_service.TeacherProviderError as error:
            assert "API key not valid" in str(error)
        else:  # pragma: no cover - the call must fail
            raise AssertionError("expected a provider error")


def test_gemini_token_request_returns_a_handle(app, monkeypatch):
    from app.services import teacher_gemini

    captured = {}

    def fake_post(url, params=None, json=None, timeout=None):
        captured["url"] = url
        captured["params"] = params
        captured["body"] = json
        return FakeHTTPResponse(200, {"name": "tokens/abc123"})

    monkeypatch.setattr(teacher_gemini.httpx, "post", fake_post)

    with app.app_context():
        app.config["GEMINI_API_KEY"] = "test-key"
        handle = teacher_gemini.GeminiLiveProvider().create_handle(
            _session(app), "Drew"
        )

    assert handle["transport"] == "websocket"
    assert handle["token"] == "tokens/abc123"
    assert handle["url"].startswith("wss://")
    assert captured["params"] == {"key": "test-key"}
    setup = captured["body"]["bidiGenerateContentSetup"]
    assert setup["model"].startswith("models/")
    assert setup["generationConfig"]["speechConfig"]


def test_create_session_returns_a_websocket_handle_for_gemini(
    app, client, monkeypatch
):
    from datetime import UTC, datetime, timedelta

    from app.services import teacher_gemini

    monkeypatch.setattr(
        teacher_gemini,
        "mint_ephemeral_token",
        lambda config, **kwargs: (
            "tokens/live",
            datetime.now(UTC) + timedelta(minutes=30),
        ),
    )
    app.config["TEACHER_PROVIDER"] = "gemini_live"

    response = client.post(
        "/api/teacher/sessions", json={"plan": "cafe", "sdp": ""}
    )

    assert response.status_code == 201, response.get_data(as_text=True)
    payload = response.get_json()
    assert payload["transport"] == "websocket"
    assert payload["token"] == "tokens/live"
    assert "sdp" not in payload
    assert payload["max_minutes"] == 15


def test_coach_hint_uses_gemini_when_the_teacher_does(app, monkeypatch):
    """With only a Gemini key the hint must not fall back to OpenAI."""
    from app.services import teacher_gemini

    captured = {}

    def fake_post(url, params=None, json=None, timeout=None):
        captured["url"] = url
        captured["body"] = json
        return FakeHTTPResponse(
            200,
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": '{"translation": "What is your name?", '
                                    '"target": "ስምህ ማን ነው?", '
                                    '"romanization": "Simih man new?", '
                                    '"gloss": "What is your name?"}'
                                }
                            ]
                        }
                    }
                ]
            },
        )

    monkeypatch.setattr(teacher_gemini.httpx, "post", fake_post)

    with app.app_context():
        app.config["TEACHER_PROVIDER"] = "gemini_live"
        app.config["GEMINI_API_KEY"] = "test-key"
        session = _session(app)
        teacher_service.record_turn(session, "teacher", "ስምህ ማን ነው?")

        hint = teacher_service.coach_reply(session)

    assert hint["translation"] == "What is your name?"
    assert captured["url"].endswith(":generateContent")
    assert captured["body"]["generationConfig"]["responseMimeType"] == "application/json"


def test_gemini_handle_does_not_ship_the_prompt_to_the_browser(app, monkeypatch):
    from datetime import UTC, datetime, timedelta

    from app.services import teacher_gemini

    monkeypatch.setattr(
        teacher_gemini,
        "mint_ephemeral_token",
        lambda config, **kwargs: (
            "tokens/live",
            datetime.now(UTC) + timedelta(minutes=30),
        ),
    )
    with app.app_context():
        handle = teacher_gemini.GeminiLiveProvider().create_handle(
            _session(app), "Drew"
        )

    assert handle["transport"] == "websocket"
    assert "session_config" not in handle
    assert handle["model"].startswith("models/")


def test_gemini_hint_falls_back_when_the_model_is_busy(app, monkeypatch):
    """A 503 from the primary text model must not hide the suggested line."""
    from app.services import teacher_gemini

    calls = []

    def fake_post(url, params=None, json=None, timeout=None):
        model = url.rsplit("/", 1)[-1].split(":")[0]
        calls.append(model)
        if model == "gemini-3.8-flash":
            return FakeHTTPResponse(
                503,
                {"error": {"message": "This model is currently experiencing high demand."}},
            )
        return FakeHTTPResponse(
            200,
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": '{"translation": "Good morning.", '
                                    '"target": "ደህና አደሩ።", '
                                    '"romanization": "Dehna adu.", '
                                    '"gloss": "Good morning."}'
                                }
                            ]
                        }
                    }
                ]
            },
        )

    monkeypatch.setattr(teacher_gemini.httpx, "post", fake_post)
    with app.app_context():
        app.config["GEMINI_API_KEY"] = "test-key"
        app.config["GEMINI_TEACHER_TEXT_MODEL"] = "gemini-3.8-flash"
        text = teacher_gemini.json_completion("system", "user")

    assert "Good morning" in text
    assert calls[0] == "gemini-3.8-flash"
    assert len(calls) >= 2


def test_prompt_asks_for_sound_teaching_and_honest_mishearing(app):
    with app.app_context():
        instructions = teacher_service._session_config(_session(app))["instructions"]

    assert "syllable by syllable" in instructions
    assert "Never guess a word you did not hear" in instructions


def test_prompt_scaffolds_a_learner_who_answers_in_english(app):
    with app.app_context():
        instructions = teacher_service._session_config(_session(app))["instructions"]

    assert "gloss in parentheses after every" in instructions
    assert "do not repeat" in instructions
    assert "Never speak twice in a row" in instructions
