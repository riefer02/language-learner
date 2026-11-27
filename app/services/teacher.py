"""Real-time teacher engine: session creation, tools, drills, and debriefs.

The provider adapter is injected through ``current_app.extensions`` so tests can
run without a key or network. The browser connects directly to the provider
with the SDP answer; the API key never leaves this process.
"""

import hashlib
import json
import os
import uuid
from datetime import UTC, datetime, timedelta

import httpx
from flask import current_app
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app import db
from app.learning.dictionary import save_term
from app.learning.scheduler import ensure_utc, new_review_card
from app.learning.service import (
    available_cards,
    get_or_create_local_user,
    local_day_bounds,
)
from app.models import Item, ReviewCard
from app.models_language import Language, TermCard
from app.models_teacher import Drill, DrillAttempt, TeacherSession, TeacherTurn
from app.services.ai import OpenAIConfigError, get_openai_client
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


# Languages the live voice teacher can hold a conversation in. The prompt and
# the transcription language follow the session's language; everything else
# (tools, drills, debrief) is language-neutral.
TEACHER_LANGUAGES = {
    "ko": {
        "name": "Korean",
        "level_hint": "TOPIK 1-2",
        "greeting": "안녕하세요",
        "politeness": (
            "Model polite 해요 forms; use casual 반말 only if the learner does."
        ),
        "transcription_language": "ko",
        "max_output_tokens": 600,
        "style": (
            "Keep sentences short and repeatable, and stay in 해요 speech with a "
            "beginner unless they use 반말 first."
        ),
    },
    "am": {
        "name": "Amharic",
        "level_hint": "beginner",
        "greeting": "ሰላም",
        "politeness": (
            "Use እርስዎ and plural agreement with adults the learner does not "
            "know, and አንተ/አንቺ everyday forms only if the learner does."
        ),
        "transcription_language": "am",
        # Ethiopic tokenizes badly: 200 tokens bought about five words and cut
        # every reply mid-word, which read as "it stopped answering".
        "max_output_tokens": 1200,
        "style": (
            "Use short, simple Amharic a beginner can repeat, anchored in the "
            "learner's deck phrases: ሰላም, አመሰግናለሁ, እባክህ/እባክሽ, ደህና ሁን. Never mix "
            "English words into an Amharic sentence except a two-word gloss in "
            "parentheses. If the learner does not understand, repeat the same "
            "sentence slower and simpler instead of switching to English for the "
            "whole turn. Do not invent words; if you are unsure of a form, use a "
            "simpler sentence you are sure of."
        ),
    },
}

SUPPORTED_TEACHER_LANGUAGES = frozenset(TEACHER_LANGUAGES)

# Languages the realtime transcription endpoint accepts. Amharic is not on the
# list (the provider answers 400 `invalid_value`), so Amharic sessions omit the
# language and rely on auto-detection. Keep this in sync with the provider's
# error message rather than guessing: a wrong code fails session creation.
SUPPORTED_TRANSCRIPTION_LANGUAGES = frozenset(
    {
        "af", "ar", "az", "be", "bg", "bs", "ca", "cs", "cy", "da", "de", "el",
        "en", "es", "et", "fa", "fi", "fr", "gl", "he", "hi", "hr", "hu", "hy",
        "id", "is", "it", "iw", "ja", "kk", "kn", "ko", "lt", "lv", "mi", "mk",
        "mr", "ms", "ne", "nl", "no", "pl", "pt", "ro", "ru", "sk", "sl", "sr",
        "sv", "sw", "ta", "th", "tl", "tr", "uk", "ur", "vi", "zh",
    }
)


class TeacherError(RuntimeError):
    """Base error for teacher operations."""


class TeacherConfigError(TeacherError):
    """Raised when the teacher is disabled or has no provider key."""


class TeacherProviderError(TeacherError):
    """Raised when the realtime provider rejects a session."""


class TeacherNotReadyError(TeacherError):
    """Raised when an action needs the session to have said something first."""


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


def _session_language(session):
    """Return ``(code, spec)`` for the language this session teaches.

    Falls back to Korean when the session predates language-scoped teachers, so
    old rows keep working.
    """
    code = "ko"
    if session is not None and session.language_id is not None:
        language = db.session.get(Language, session.language_id)
        if language is not None and language.code in TEACHER_LANGUAGES:
            code = language.code
    return code, TEACHER_LANGUAGES[code]


def _instructions(session, learner_name="Learner"):
    """The language-scoped teaching prompt. Shared by every provider."""
    plan = PLANS.get(session.plan_slug, PLANS["free_talk"])
    _code, target = _session_language(session)
    name = target["name"]

    return (
        f"You are Kiku, a warm {name} speaking tutor. The learner is "
        f"{learner_name}, an English-speaking beginner ({target['level_hint']}). "
        f"Today's plan: {plan['title']} — {plan['focus']}.\n\n"
        "How to run the session:\n"
        f"- Speak {name} first, slowly and naturally. Put a short English gloss "
        f"in parentheses after every {name} sentence until the learner has "
        f"answered in {name} twice in a row; after that, gloss only when they "
        f"seem stuck. Aim for 70-80% {name}.\n"
        "- If the learner answers in English or another language, do not repeat "
        f"your last question. Acknowledge what they meant in English, give the "
        f"{name} phrase for it, and ask them to repeat it.\n"
        "- Never speak twice in a row. If the learner is silent, wait; if you "
        "must prompt, ask one short question.\n"
        f"- {target['style']}\n"
        "- Keep every turn to at most two short sentences and about 12 words. "
        "One question at a time. If you feel like explaining, ask a question "
        "instead; the explanation belongs in the debrief.\n"
        "- Ask one question at a time and wait for the learner to finish. Never "
        "talk over them; a long pause is fine.\n"
        "- Correct by recasting: repeat the corrected sentence naturally in your "
        "next turn, then continue. Make at most 3 explicit corrections in the "
        "whole session, each one sentence.\n"
        "- Teach the sound, not only the meaning. When the learner's sentence is "
        "understandable but imperfect, recast it once and ask them to say it "
        "back. Every few turns, model one word slowly, syllable by syllable, "
        "and have them repeat it.\n"
        "- If you cannot make out a word, say so plainly and ask them to repeat "
        "it slowly. Never guess a word you did not hear.\n"
        f"- {target['politeness']} If the learner uses the wrong politeness "
        "level, model the right one once and move on.\n"
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


def _session_config(session, learner_name="Learner"):
    model = current_app.config.get(
        "TEACHER_MODEL", "gpt-realtime-2.1-mini"
    )
    voice = current_app.config.get("TEACHER_VOICE", "marin")
    transcribe_model = current_app.config.get(
        "TEACHER_TRANSCRIBE_MODEL", "gpt-transcribe"
    )
    instructions = _instructions(session, learner_name)
    _code, target = _session_language(session)

    # Name the language when the provider supports it. Amharic is not a valid
    # transcription language here (the provider rejects the session with a 400
    # invalid_value), so it relies on auto-detection.
    transcription = {"model": transcribe_model}
    if target["transcription_language"] in SUPPORTED_TRANSCRIPTION_LANGUAGES:
        transcription["language"] = target["transcription_language"]

    return {
        "type": "realtime",
        "model": model,
        "instructions": instructions,
        "output_modalities": ["audio"],
        # Audio tokens are coarse: 800 allowed roughly a minute of speech, which
        # is what made turns feel like lectures. Kept in config so a language
        # that needs a little more room can be tuned without a code change.
        "max_output_tokens": int(
            current_app.config.get("TEACHER_MAX_OUTPUT_TOKENS")
            or target["max_output_tokens"]
        ),
        "audio": {
            "input": {
                "noise_reduction": {"type": "near_field"},
                "transcription": transcription,
                "turn_detection": {
                    "type": "server_vad",
                    # A learner pauses mid-sentence and speaks softly. A lower
                    # threshold catches them, and a longer silence window stops
                    # one sentence being split into three turns.
                    "threshold": float(
                        current_app.config.get("TEACHER_VAD_THRESHOLD", 0.4)
                    ),
                    "prefix_padding_ms": int(
                        current_app.config.get("TEACHER_VAD_PREFIX_MS", 300)
                    ),
                    "silence_duration_ms": int(
                        current_app.config.get("TEACHER_VAD_SILENCE_MS", 900)
                    ),
                    "create_response": True,
                    # Beginners repeat themselves while the reply is still
                    # being generated; interrupting cancelled the answer over
                    # and over, which looked like the teacher going silent.
                    "interrupt_response": bool(
                        current_app.config.get("TEACHER_INTERRUPT_RESPONSE", False)
                    ),
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
            detail = ""
            try:
                payload = response.json()
                detail = (payload.get("error") or {}).get("message", "")
            except ValueError:
                detail = ""
            raise TeacherProviderError(
                "The realtime provider rejected the session"
                + (f": {detail[:220]}" if detail else "")
            )

        location = response.headers.get("Location", "")
        provider_id = location.rstrip("/").rsplit("/", 1)[-1] or None
        return provider_id, response.text


def _provider():
    injected = current_app.extensions.get("teacher_provider")
    if injected is not None:
        return injected
    if current_app.config.get("TEACHER_PROVIDER") == "gemini_live":
        # Imported here: the Gemini module reuses this module's prompt and tools.
        from app.services.teacher_gemini import GeminiLiveProvider

        return GeminiLiveProvider()
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
        # Charge the cap, not the wall clock. A browser closed mid-call leaves
        # the row active; using `now` billed the gap (e.g. twelve hours overnight)
        # and exhausted the learner's daily minutes.
        session.ended_at = started + timedelta(minutes=maximum)
        session.summary_text = (
            f"Session ended at the {maximum}-minute limit."
        )
        db.session.commit()
    return session


def create_session(user_id, language_id, plan_slug, sdp):
    if not teacher_enabled():
        raise TeacherConfigError("The teacher is disabled")
    provider = _provider()
    transport = getattr(provider, "transport", "webrtc")
    if transport == "webrtc" and (
        not isinstance(sdp, str) or "v=0" not in sdp[:200]
    ):
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

    learner_name = _learner_name(user_id)
    try:
        if transport == "websocket":
            handle = provider.create_handle(session, learner_name=learner_name)
            session.status = "active"
            session.provider_session_id = handle.get("provider_session_id")
            session.metadata_json = json.dumps(
                {"plan": session.plan_slug, "transport": "websocket"}
            )
            db.session.commit()
            return session, handle

        provider_id, answer = provider.create_call(
            _session_config(session, learner_name=learner_name), sdp
        )
    except TeacherError:
        session.status = "failed"
        db.session.commit()
        raise

    session.status = "active"
    session.provider_session_id = provider_id
    session.metadata_json = json.dumps({"plan": session.plan_slug})
    db.session.commit()
    return session, {"transport": "webrtc", "sdp": answer}


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

    def _next_index():
        current = (
            db.session.query(func.max(TeacherTurn.turn_index))
            .filter(TeacherTurn.session_id == session.id)
            .scalar()
        )
        return (current or 0) + 1

    turn = TeacherTurn(
        session_id=session.id,
        turn_index=_next_index(),
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
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        turn.turn_index = _next_index()
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
    cards = available_cards(session.user_id, language_id=session.language_id)
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
            db.or_(Item.language_id.is_(None), Item.language_id == session.language_id),
            db.or_(
                Item.target_text.ilike(pattern),
                Item.gloss.ilike(pattern),
                Item.transliteration.ilike(pattern),
            ),
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
            prompt = f"Say in {_session_language(session)[1]['name']}: {item.gloss}"
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
        card.session_id = session.id
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
        user_id=session.user_id, session_id=session.id
    ).count()
    summary = args.summary or session.summary_text or (
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
        "description": "Search the learner's dictionary by target text, English, or romanization.",
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
    except Exception as error:
        # A database or handler bug must reach the model as a tool error it can
        # work around, not Flask's HTML 500 that the client cannot parse.
        db.session.rollback()
        current_app.logger.exception("Teacher tool %s failed", name)
        raise TeacherToolError("tool_failed") from error
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
            user_id=session.user_id, session_id=session.id
        ).all()
    ]
    return data


# --- Coach hint: what the tutor said, and what to say back -----------------

COACH_SYSTEM = (
    "You help a beginner follow a spoken lesson. Given the transcript, return "
    "JSON only with four keys: "
    '"translation": an English translation of the tutor\'s LAST line, kept '
    "short and literal; "
    '"target": ONE short reply the learner could say next, at most 12 words, '
    "in the same language and the same register the tutor used. Prefer a line "
    "that answers the tutor's last question. Never suggest apologising for not "
    "speaking the language, and never suggest ending the conversation. If the "
    "learner's last line is in another language, give the target-language "
    "version of what they said. Learner lines are machine transcripts and are "
    "often wrong; when they look garbled, suggest an answer to the tutor's last "
    "question rather than reacting to the transcript; "
    '"romanization": that reply in simple Latin letters; '
    '"gloss": that reply in short English. '
    "No quotes around the values, no explanation, no extra keys."
)


class CoachHint(BaseModel):
    translation: str = Field(default="", max_length=400)
    target: str = Field(default="", max_length=200)
    romanization: str = Field(default="", max_length=200)
    gloss: str = Field(default="", max_length=200)


def coach_reply(session, limit=10):
    """English of the tutor's last line plus one line the learner could say.

    This is a separate text call, never the realtime session, so it cannot
    disturb the conversation. The translation is always requested; the learner
    can hide the suggested reply without losing it.
    """
    _code, target = _session_language(session)
    turns = (
        TeacherTurn.query.filter(
            TeacherTurn.session_id == session.id,
            TeacherTurn.text.isnot(None),
        )
        .order_by(TeacherTurn.turn_index.desc())
        .limit(limit)
        .all()
    )
    turns.reverse()
    transcript = "\n".join(
        f"{turn.role}: {turn.text}" for turn in turns if turn.text
    )
    if not transcript:
        raise TeacherNotReadyError("Nothing has been said yet")

    user_prompt = (
        f"Language: {target['name']}.\n"
        "Learner: English-speaking beginner. Learner turns are rough phonetic "
        "transcripts; read them for meaning, not for spelling.\n"
        f"Transcript so far:\n{transcript}"
    )
    provider = current_app.config.get("TEACHER_PROVIDER", "openai_realtime")
    try:
        if provider == "gemini_live":
            # The teacher has no OpenAI key when it runs on Gemini; the hint
            # must use the same provider or it silently disappears.
            from app.services.teacher_gemini import json_completion

            content = json_completion(COACH_SYSTEM, user_prompt)
        else:
            client = get_openai_client()
            model = current_app.config.get(
                "TEACHER_SUGGEST_MODEL",
                current_app.config.get("TRANSLATION_MODEL", "gpt-5.6-luna"),
            )
            response = client.chat.completions.create(
                model=model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": COACH_SYSTEM},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = response.choices[0].message.content or "{}"
    except OpenAIConfigError:
        raise
    except TeacherError:
        raise
    except Exception as error:
        current_app.logger.warning("Coach hint failed: %s", error)
        raise TeacherError("Could not read the last turn") from error
    try:
        return CoachHint.model_validate_json(content).model_dump()
    except ValidationError as error:
        raise TeacherError("The coach hint was unusable") from error


__all__ = [
    "PLANS",
    "SUPPORTED_TEACHER_LANGUAGES",
    "TeacherConfigError",
    "TeacherError",
    "TeacherLimitError",
    "TeacherNotReadyError",
    "TeacherProviderError",
    "coach_reply",
    "create_session",
    "dispatch_tool",
    "end_session",
    "get_session",
    "record_turn",
    "session_to_dict",
    "teacher_enabled",
]
