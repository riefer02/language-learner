"""Scripted mission scenes: tolerant matching, progress, and card creation."""

import json
from datetime import UTC, datetime

from flask import current_app

from app import db
from app.learning.scene_data import SCENES
from app.learning.service import ensure_review_cards
from app.models import CanDoArtifact, Item, SceneSession
from app.models_language import Language
from app.utils.text import normalize_text, similarity


def _normalize(text):
    return normalize_text(text)


def get_scene(slug):
    return next((scene for scene in SCENES if scene["slug"] == slug), None)


def list_scenes_with_status(user_id):
    sessions = {
        session.scene_slug: session
        for session in SceneSession.query.filter_by(user_id=user_id).all()
    }
    result = []
    for scene in SCENES:
        session = sessions.get(scene["slug"])
        if session and session.completed:
            status = "completed"
        elif session and session.step_index > 0:
            status = "in_progress"
        else:
            status = "new"
        result.append(
            {
                "scene": scene,
                "status": status,
                "step_index": session.step_index if session else 0,
                "total_steps": len(scene["steps"]),
            }
        )
    return result


def can_do_artifacts(user_id, limit=None, language_id=None):
    query = CanDoArtifact.query.filter_by(user_id=user_id)
    if language_id is not None:
        query = query.filter(CanDoArtifact.language_id == language_id)
    query = query.order_by(
        CanDoArtifact.created_at.desc(), CanDoArtifact.id.desc()
    )
    if limit:
        query = query.limit(limit)
    return query.all()


def next_scene(user_id):
    for row in list_scenes_with_status(user_id):
        if row["status"] != "completed":
            return row
    return None


def _korean_language():
    return Language.query.filter_by(code="ko").first()


def get_or_create_session(user_id, slug):
    session = SceneSession.query.filter_by(
        user_id=user_id, scene_slug=slug
    ).first()
    if session is None:
        language = _korean_language()
        session = SceneSession(
            user_id=user_id,
            scene_slug=slug,
            language_id=language.id if language else None,
        )
        db.session.add(session)
        db.session.commit()
    return session


def reset_session(session):
    session.step_index = 0
    session.completed = False
    session.transcript = None
    session.completed_at = None
    db.session.commit()
    return session


def session_transcript(session):
    if not session.transcript:
        return []
    try:
        value = json.loads(session.transcript)
        return value if isinstance(value, list) else []
    except (TypeError, ValueError):
        return []


def match_answer(expected_answers, answer, threshold=None):
    """Return ``(accepted, best_expected, best_score)``.

    Matching ignores punctuation and spacing. A close transcription (for
    speech input) is accepted above the configured threshold.
    """
    if threshold is None:
        threshold = current_app.config.get("SCENE_MATCH_THRESHOLD", 0.78)
    normalized = _normalize(answer)
    if not normalized:
        return False, expected_answers[0], 0.0

    best_expected = expected_answers[0]
    best_score = 0.0
    for expected in expected_answers:
        target = _normalize(expected)
        if normalized == target:
            return True, expected, 1.0
        score = similarity(target, normalized)
        if score > best_score:
            best_score = score
            best_expected = expected
    return best_score >= threshold, best_expected, best_score


def _create_debrief_cards(user, scene):
    language = _korean_language()
    language_id = language.id if language else None
    created_items = 0
    for card in scene["debrief"]["cards"]:
        existing = Item.query.filter_by(
            target_text=card["target_text"],
            gloss=card["gloss"],
            item_type="chunk",
        ).first()
        if existing:
            if existing.language_id is None:
                existing.language_id = language_id
            continue
        db.session.add(
            Item(
                item_type="chunk",
                target_text=card["target_text"],
                gloss=card["gloss"],
                transliteration=card.get("transliteration"),
                level=scene["level"],
                notes=card.get("notes"),
                default_skill="produce",
                language_id=language_id,
            )
        )
        created_items += 1
    db.session.commit()
    created_cards = ensure_review_cards(user.id, language_id)
    return created_items, created_cards


def submit_answer(user, session, scene, answer):
    """Advance one step on a correct answer; keep the step on a miss."""
    steps = scene["steps"]
    if session.completed or session.step_index >= len(steps):
        return {
            "accepted": False,
            "completed": True,
            "message": "This scene is already complete.",
        }

    step = steps[session.step_index]
    accepted, best_expected, score = match_answer(step["expected"], answer)
    if not accepted:
        return {
            "accepted": False,
            "completed": False,
            "step": step,
            "step_index": session.step_index,
            "hint": step["hint"],
            "best_expected": best_expected,
            "score": round(score, 3),
        }

    transcript = session_transcript(session)
    transcript.append(
        {
            "character": step["character_text"],
            "learner": answer.strip(),
            "expected": best_expected,
        }
    )
    session.transcript = json.dumps(transcript, ensure_ascii=False)
    session.step_index += 1

    completed = session.step_index >= len(steps)
    cards_created = 0
    items_created = 0
    artifact_created = False
    if completed:
        session.completed = True
        session.completed_at = datetime.now(UTC)
        items_created, cards_created = _create_debrief_cards(user, scene)
        artifact = CanDoArtifact.query.filter_by(
            user_id=user.id, scene_slug=scene["slug"]
        ).first()
        if artifact is None:
            db.session.add(
                CanDoArtifact(
                    user_id=user.id,
                    scene_slug=scene["slug"],
                    label=scene["can_do"],
                    language_id=(
                        _korean_language().id if _korean_language() else None
                    ),
                )
            )
            artifact_created = True
        else:
            artifact.label = scene["can_do"]
            artifact.created_at = datetime.now(UTC)

    db.session.commit()
    return {
        "accepted": True,
        "completed": completed,
        "step": step,
        "step_index": session.step_index,
        "success_note": step["success_note"],
        "cards_created": cards_created,
        "items_created": items_created,
        "artifact_created": artifact_created,
    }
