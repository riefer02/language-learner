"""Real-time teacher engine: session creation, tools, drills, and debriefs.

The provider adapter is injected through ``current_app.extensions`` so tests can
run without a key or network. The browser connects directly to the provider
with the SDP answer; the API key never leaves this process.
"""

import hashlib
import json
import os
import uuid
from datetime import UTC, datetime

import httpx
from flask import current_app
from pydantic import BaseModel, Field, ValidationError

from app import db
from app.learning.dictionary import save_term
from app.learning.scheduler import ensure_utc, new_review_card
from app.learning.service import (
    available_cards,
    get_or_create_local_user,
    local_day_bounds,
)
from app.models import Item, ReviewCard
from app.models_language import TermCard
from app.models_teacher import Drill, DrillAttempt, TeacherSession, TeacherTurn
from app.utils.text import normalize_text, similarity

REALTIME_CALLS_URL = "https://api.openai.com/v1/realtime/calls"

PLANS = {
    "free_talk": {
        "title": "Free talk",
        "focus": "follow the learner's interests and keep them speaking",
    },
    "cafe": {
        "title": "Order at a café",
        "focus": "ordering, prices, and politely asking for something",
    },
    "directions": {
        "title": "Ask for directions",
        "focus": "locations, landmarks, and confirming what you heard",
    },
    "polite_refusal": {
        "title": "Refuse politely",
        "focus": "refusing an invitation without sounding rude",
    },
}


class TeacherError(RuntimeError):
    """Base error for teacher operations."""


class TeacherConfigError(TeacherError):
    """Raised when the teacher is disabled or has no provider key."""


class TeacherProviderError(TeacherError):
    """Raised when the realtime provider rejects a session."""


class TeacherLimitError(TeacherError):
    """Raised when the learner has used their daily teacher minutes."""


def _utcnow():
    return datetime.now(UTC)


def teacher_enabled():
    return bool(current_app.config.get("TEACHER_ENABLED", True))




def _item_payload(item):
    return {
        "item_id": item.id,
        "target": item.target_text,
        "gloss": item.gloss,
        "transliteration": item.transliteration,
        "level": item.level,
        "audio_url": item.audio_path,
    }


def _session_config(session, learner_name="Learner"):
    model = current_app.config.get(
        "TEACHER_MODEL", "gpt-realtime-2.1-mini"
    )
    voice = current_app.config.get("TEACHER_VOICE", "marin")
    transcribe_model = current_app.config.get(
        "TEACHER_TRANSCRIBE_MODEL", "gpt-transcribe"
    )
    plan = PLANS.get(session.plan_slug, PLANS["free_talk"])

    instructions = (
        f"You are Kiku, a warm Korean speaking tutor. The learner is {learner_name}, "
        "an English-speaking beginner (TOPIK 1-2). Today's plan: "
        f"{plan['title']} — {plan['focus']}.\n\n"
        "How to run the session:\n"
        "- Speak Korean first, slowly and naturally, then give a short English "
        "gloss only when the learner seems stuck. Aim for 70-80% Korean.\n"
        "- Ask one question at a time and wait for the learner to finish. Never "
        "talk over them; a long pause is fine.\n"
        "- Correct by recasting: repeat the corrected Korean naturally in your next "
        "turn, then continue. Make at most 3 explicit corrections in the whole "
        "session, each one sentence.\n"
        "- If the learner uses the wrong politeness level, model the polite form "
        "once and move on.\n"
        "- Keep your turns to 1-2 sentences. This is a 7-minute lesson, not a "
        "lecture.\n"
        "- At the end, say one concrete thing they did well.\n\n"
        "Tools:\n"
        "- Use lookup_dictionary when the learner asks what a word means.\n"
        "- Use get_due_items once near the start if you need material.\n"
        "- Offer 2 or 3 short drills near the end (or when asked) with "
        "create_drill. Tell the learner the drill out loud, wait for their answer, "
        "then call log_attempt with what they said.\n"
        "- If the learner says 'save that', call add_term_to_library with the item "
        "they mean and the sentence they heard it in.\n"
        "- Do not invent vocabulary lists or grammar rules. If unsure, say so and "
        "use a simpler sentence."
    )

    return {
        "type": "realtime",
        "model": model,
        "instructions": instructions,
        "output_modalities": ["audio"],
        "max_output_tokens": 800,
        "audio": {
            "input": {
                "noise_reduction": {"type": "near_field"},
                "transcription": {
                    "model": transcribe_model,
                    "language": "ko",
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 700,
                    "create_response": True,
                    "interrupt_response": True,
                },
            },
            "output": {"voice": voice, "speed": 0.95},
        },
        "tools": TOOL_SCHEMAS,
        "tool_choice": "auto",
        "truncation": "auto",
    }


class OpenAIRealtimeProvider:
    """Mints a browser session through OpenAI's unified WebRTC endpoint."""

    name = "openai_realtime"

    def create_call(self, session_config, sdp):
        api_key = current_app.config.get("OPENAI_API_KEY") or os.environ.get(
            "OPENAI_API_KEY"
        )
        if not api_key:
            raise TeacherConfigError("OPENAI_API_KEY is not configured")

        safety = hashlib.sha256(
            str(current_app.config.get("SECRET_KEY", "kiku")).encode()
        ).hexdigest()[:32]
        timeout = float(current_app.config.get("TEACHER_TIMEOUT_SECONDS", 20))
        try:
            response = httpx.post(
                REALTIME_CALLS_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "OpenAI-Safety-Identifier": safety,
                },
                files={
                    "sdp": (None, sdp, "application/sdp"),
                    "session": (
                        None,
                        json.dumps(session_config),
                        "application/json",
                    ),
                },
                timeout=timeout,
            )
        except httpx.HTTPError as error:
            raise TeacherProviderError(
                "Could not reach the realtime provider"
            ) from error

        if response.status_code >= 400:
            current_app.logger.warning(
                "Realtime session rejected (%s): %s",
                response.status_code,
                response.text[:300],
            )
            raise TeacherProviderError("The realtime provider rejected the session")

        location = response.headers.get("Location", "")
        provider_id = location.rstrip("/").rsplit("/", 1)[-1] or None
        return provider_id, response.text


def _provider():
    injected = current_app.extensions.get("teacher_provider")
    if injected is not None:
        return injected
    return OpenAIRealtimeProvider()


def daily_usage_minutes(user_id, now=None):
    """Minutes of teacher time consumed in the learner's local day."""
    now = ensure_utc(now or _utcnow())
    start, end, _local_date = local_day_bounds(now)
    sessions = TeacherSession.query.filter(
        TeacherSession.user_id == user_id,
        TeacherSession.started_at >= start,
        TeacherSession.started_at < end,
    ).all()
    total = 0.0
    for item in sessions:
        started = ensure_utc(item.started_at) or now
        finished = ensure_utc(item.ended_at) or (
            now if item.status == "active" else started
        )
        total += max(0.0, (finished - started).total_seconds() / 60.0)
    return total


def expire_if_over_limit(session, now=None):
    """End a session that has run past the configured maximum."""
    if session is None or session.status != "active":
        return session
    now = ensure_utc(now or _utcnow())
    maximum = int(current_app.config.get("TEACHER_MAX_SESSION_MINUTES", 15))
    started = ensure_utc(session.started_at) or now
    if maximum > 0 and (now - started).total_seconds() > maximum * 60:
        session.status = "ended"
        session.ended_at = now
        session.summary_text = (
            f"Session ended at the {maximum}-minute limit."
        )
        db.session.commit()
    return session


def create_session(user_id, language_id, plan_slug, sdp):
    if not teacher_enabled():
        raise TeacherConfigError("The teacher is disabled")
    if not isinstance(sdp, str) or "v=0" not in sdp[:200]:
        raise ValueError("A valid SDP offer is required")

    daily_limit = int(current_app.config.get("TEACHER_DAILY_MINUTES", 20))
    if daily_limit > 0 and daily_usage_minutes(user_id) >= daily_limit:
        raise TeacherLimitError(
            f"Daily teacher limit reached ({daily_limit} minutes). "
            "Try again tomorrow."
        )
    active = TeacherSession.query.filter_by(
        user_id=user_id, status="active"
    ).first()
    if active is not None:
        expire_if_over_limit(active)
        if active.status == "active":
            active.status = "ended"
            active.ended_at = _utcnow()
            db.session.commit()

    plan = PLANS.get(plan_slug, PLANS["free_talk"])
    session = TeacherSession(
        user_id=user_id,
        language_id=language_id,
        plan_slug=plan_slug if plan_slug in PLANS else "free_talk",
        plan_title=plan["title"],
        provider=_provider().name,
        status="pending",
    )
    db.session.add(session)
    db.session.commit()

    try:
        provider_id, answer = _provider().create_call(
            _session_config(session, learner_name=_learner_name(user_id)), sdp
        )
    except TeacherError:
        session.status = "failed"
        db.session.commit()
        raise

    session.status = "active"
    session.provider_session_id = provider_id
    session.metadata_json = json.dumps({"plan": session.plan_slug})
    db.session.commit()
    return session, answer


def _learner_name(user_id):
    user = get_or_create_local_user()
    return user.display_name if user.id == user_id else "Learner"


def get_session(user_id, session_id):
    session = TeacherSession.query.filter_by(
        id=session_id, user_id=user_id
    ).first()
    return expire_if_over_limit(session)


def next_turn_index(session):
    return (session.turn_count or 0) + 1


def record_turn(session, role, text=None, tool_name=None, tool_args=None,
                tool_result=None, latency_ms=None):
    if role not in {"teacher", "learner", "tool", "system"}:
        raise ValueError("Unknown turn role")
    turn = TeacherTurn(
        session_id=session.id,
        turn_index=next_turn_index(session),
        role=role,
        text=(text or "")[:8000] or None,
        tool_name=tool_name,
        tool_args=json.dumps(tool_args) if tool_args is not None else None,
        tool_result=json.dumps(tool_result) if tool_result is not None else None,
        latency_ms=latency_ms,
    )
    session.turn_count = turn.turn_index
    if role == "learner":
        session.learner_turn_count = (session.learner_turn_count or 0) + 1
    db.session.add(turn)
    db.session.commit()
    return turn


# --- Tool contracts -------------------------------------------------------


class GetDueItemsArgs(BaseModel):
    limit: int = Field(default=5, ge=1, le=10)


class LookupDictionaryArgs(BaseModel):
    query: str = Field(min_length=1, max_length=120)
    limit: int = Field(default=5, ge=1, le=10)


class CreateDrillArgs(BaseModel):
    item_ids: list[int] = Field(default_factory=list, max_length=5)
    drill_type: str = "translate_to_target"
    count: int = Field(default=2, ge=1, le=3)


class AddTermArgs(BaseModel):
    item_id: int | None = None
    context_sentence: str | None = Field(default=None, max_length=500)
    note: str | None = Field(default=None, max_length=500)


class LogAttemptArgs(BaseModel):
    drill_id: int
    response: str = Field(min_length=1, max_length=500)
    score: float | None = Field(default=None, ge=0, le=1)
    client_attempt_id: str = Field(min_length=1, max_length=64)
    duration_ms: int | None = Field(default=None, ge=0)


class EndSessionArgs(BaseModel):
    summary: str | None = Field(default=None, max_length=2000)


class TeacherToolError(TeacherError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def _find_item(session, item_id):
    item = db.session.get(Item, item_id)
    if item is None:
        raise TeacherToolError("item_not_found")
    if item.language_id not in (None, session.language_id):
        raise TeacherToolError("item_out_of_scope")
    return item


def tool_get_due_items(session, args):
    cards = available_cards(session.user_id)
    seen = set()
    payload = []
    for card in cards:
        item = card.item
        if item is None or item.id in seen:
            continue
        seen.add(item.id)
        payload.append(_item_payload(item))
        if len(payload) >= args.limit:
            break
    return {"items": payload}


def tool_lookup_dictionary(session, args):
    pattern = f"%{args.query.strip()}%"
    items = (
        Item.query.filter(
            db.or_(
                Item.target_text.ilike(pattern),
                Item.gloss.ilike(pattern),
                Item.transliteration.ilike(pattern),
            )
        )
        .order_by(Item.level.asc(), Item.id.asc())
        .limit(args.limit)
        .all()
    )
    return {"items": [_item_payload(item) for item in items]}


def tool_create_drill(session, args):
    if not args.item_ids:
        cards = tool_get_due_items(session, GetDueItemsArgs(limit=2))["items"]
        item_ids = [entry["item_id"] for entry in cards]
    else:
        item_ids = args.item_ids

    if not item_ids:
        raise TeacherToolError("no_items_to_drill")

    drills = []
    for item_id in item_ids[: args.count]:
        item = _find_item(session, item_id)
        if args.drill_type == "translate_to_english":
            prompt = f'What does "{item.target_text}" mean?'
            expected = item.gloss
        elif args.drill_type == "repeat":
            prompt = f"Repeat after me: {item.target_text}"
            expected = item.target_text
        else:
            prompt = f"Say in Korean: {item.gloss}"
            expected = item.target_text
        drill = Drill(
            uuid=str(uuid.uuid4()),
            session_id=session.id,
            user_id=session.user_id,
            language_id=session.language_id,
            item_id=item.id,
            source="teacher",
            drill_type=args.drill_type,
            prompt=prompt,
            expected=expected,
            payload=json.dumps(_item_payload(item), ensure_ascii=False),
            validated=True,
        )
        db.session.add(drill)
        drills.append(drill)

    db.session.flush()
    return {
        "drills": [
            {
                "drill_id": drill.id,
                "prompt": drill.prompt,
                "expected": drill.expected,
                "item_id": drill.item_id,
            }
            for drill in drills
        ]
    }


def tool_add_term_to_library(session, args):
    if args.item_id is None:
        raise TeacherToolError("item_id_required")
    item = _find_item(session, args.item_id)
    try:
        card = save_term(
            session.user_id,
            session.language_id or item.language_id,
            item.id,
            context_sentence=args.context_sentence,
            source="teacher",
        )
    except ValueError as error:
        raise TeacherToolError("language_required") from error
    if args.note:
        card.note = args.note
    return {"term_card_id": card.id, "item_id": item.id, "target": item.target_text}


def grade_drill(user_id, drill, response, score=None, client_attempt_id=None,
                duration_ms=None):
    """Grade one drill attempt and schedule an FSRS card when it is accepted."""
    existing = DrillAttempt.query.filter_by(
        drill_id=drill.id, client_attempt_id=client_attempt_id
    ).first()
    if existing is not None:
        return existing

    if score is None:
        score = similarity(drill.expected, response)
    threshold = current_app.config.get("SCENE_MATCH_THRESHOLD", 0.78)
    acceptable = bool(normalize_text(response)) and score >= threshold

    card_id = None
    if acceptable and drill.item_id:
        card = ReviewCard.query.filter_by(
            user_id=user_id, item_id=drill.item_id, skill="produce"
        ).first()
        if card is None:
            card = new_review_card(user_id, drill.item_id, "produce")
            db.session.add(card)
            db.session.flush()
        card_id = card.id

    attempt = DrillAttempt(
        drill_id=drill.id,
        user_id=user_id,
        response=response,
        score=score,
        acceptable=acceptable,
        feedback=(
            "Nice — that matches."
            if acceptable
            else f"Expected: {drill.expected}"
        ),
        client_attempt_id=client_attempt_id,
        review_card_id=card_id,
        duration_ms=duration_ms,
    )
    db.session.add(attempt)
    db.session.flush()
    return attempt


def tool_log_attempt(session, args):
    drill = db.session.get(Drill, args.drill_id)
    if drill is None or drill.user_id != session.user_id:
        raise TeacherToolError("drill_not_found")
    attempt = grade_drill(
        session.user_id,
        drill,
        args.response,
        score=args.score,
        client_attempt_id=args.client_attempt_id,
        duration_ms=args.duration_ms,
    )
    return attempt.to_dict()


def tool_end_session_summary(session, args):
    drills = Drill.query.filter_by(session_id=session.id).count()
    terms = TermCard.query.filter_by(
        user_id=session.user_id, source="teacher"
    ).count()
    summary = args.summary or (
        f"{session.plan_title}: {session.learner_turn_count} learner turns, "
        f"{drills} drill(s) created, {terms} saved term(s)."
    )
    session.summary_text = summary
    if session.status != "ended":
        session.status = "ended"
        session.ended_at = _utcnow()
    return {"summary": summary, "drills": drills, "terms": terms}


TOOL_HANDLERS = {
    "get_due_items": (GetDueItemsArgs, tool_get_due_items),
    "lookup_dictionary": (LookupDictionaryArgs, tool_lookup_dictionary),
    "create_drill": (CreateDrillArgs, tool_create_drill),
    "add_term_to_library": (AddTermArgs, tool_add_term_to_library),
    "log_attempt": (LogAttemptArgs, tool_log_attempt),
    "end_session_summary": (EndSessionArgs, tool_end_session_summary),
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "name": "get_due_items",
        "description": "Return review items due for this learner, with target text and gloss.",
        "parameters": {
            "type": "object",
            "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 10}},
        },
    },
    {
        "type": "function",
        "name": "lookup_dictionary",
        "description": "Search the learner's Korean dictionary by Korean, English, or romanization.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 10},
            },
            "required": ["query"],
        },
    },
    {
        "type": "function",
        "name": "create_drill",
        "description": "Create 1-3 short practice drills for specific item IDs and speak them.",
        "parameters": {
            "type": "object",
            "properties": {
                "item_ids": {"type": "array", "items": {"type": "integer"}},
                "drill_type": {
                    "type": "string",
                    "enum": [
                        "translate_to_target",
                        "translate_to_english",
                        "repeat",
                    ],
                },
                "count": {"type": "integer", "minimum": 1, "maximum": 3},
            },
            "required": ["item_ids"],
        },
    },
    {
        "type": "function",
        "name": "add_term_to_library",
        "description": "Save a term to the learner's personal library with its source sentence.",
        "parameters": {
            "type": "object",
            "properties": {
                "item_id": {"type": "integer"},
                "context_sentence": {"type": "string"},
                "note": {"type": "string"},
            },
            "required": ["item_id"],
        },
    },
    {
        "type": "function",
        "name": "log_attempt",
        "description": "Record the learner's spoken answer to a drill and schedule it for review.",
        "parameters": {
            "type": "object",
            "properties": {
                "drill_id": {"type": "integer"},
                "response": {"type": "string"},
                "client_attempt_id": {"type": "string"},
                "duration_ms": {"type": "integer"},
            },
            "required": ["drill_id", "response", "client_attempt_id"],
        },
    },
    {
        "type": "function",
        "name": "end_session_summary",
        "description": "Finish the lesson with a short summary of what was practiced.",
        "parameters": {
            "type": "object",
            "properties": {"summary": {"type": "string"}},
        },
    },
]


def dispatch_tool(session, name, args):
    spec = TOOL_HANDLERS.get(name)
    if spec is None:
        raise TeacherToolError("unknown_tool")
    model, handler = spec
    try:
        validated = model.model_validate(args or {})
    except ValidationError as error:
        raise TeacherToolError("invalid_args") from error

    try:
        result = handler(session, validated)
        record_turn(
            session,
            "tool",
            tool_name=name,
            tool_args=args,
            tool_result=result,
        )
    except TeacherToolError:
        db.session.rollback()
        raise
    db.session.commit()
    return result


def end_session(session, summary=None):
    result = tool_end_session_summary(session, EndSessionArgs(summary=summary))
    db.session.commit()
    return result


def session_to_dict(session):
    data = session.to_dict()
    data["turns"] = [turn.to_dict() for turn in session.turns]
    data["terms"] = [
        {
            "id": card.id,
            "item_id": card.item_id,
            "text": card.item.target_text if card.item else None,
            "gloss": card.item.gloss if card.item else None,
            "context_sentence": card.context_sentence,
        }
        for card in TermCard.query.filter_by(
            user_id=session.user_id, source="teacher"
        ).all()
    ]
    return data


__all__ = [
    "PLANS",
    "TeacherConfigError",
    "TeacherError",
    "TeacherLimitError",
    "TeacherProviderError",
    "create_session",
    "dispatch_tool",
    "end_session",
    "get_session",
    "record_turn",
    "session_to_dict",
    "teacher_enabled",
]
