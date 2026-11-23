"""Real-time teacher sessions, turns, drills, and attempts.

The teacher is provider-agnostic at this layer: `provider` names the adapter
(OpenAI Realtime first, Gemini Live later) and `provider_session_id` is opaque.
Raw audio is never stored; only text transcripts and drill outcomes are.
"""

import uuid
from datetime import UTC, datetime

from app import db


def _utcnow():
    return datetime.now(UTC)


class TeacherSession(db.Model):
    __tablename__ = "teacher_session"
    __table_args__ = (
        db.Index("ix_teacher_session_user_started", "user_id", "started_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(
        db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4())
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    language_id = db.Column(
        db.Integer, db.ForeignKey("language.id"), nullable=True
    )
    mode = db.Column(db.String(16), nullable=False, default="voice")
    plan_slug = db.Column(db.String(40), nullable=False, default="free_talk")
    plan_title = db.Column(db.String(200), nullable=False, default="Free talk")
    provider = db.Column(db.String(40), nullable=False, default="openai_realtime")
    provider_session_id = db.Column(db.String(120), nullable=True)
    # pending | active | ended | failed
    status = db.Column(db.String(16), nullable=False, default="pending", index=True)
    started_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=_utcnow, index=True
    )
    ended_at = db.Column(db.DateTime(timezone=True), nullable=True)
    turn_count = db.Column(db.Integer, nullable=False, default=0)
    learner_turn_count = db.Column(db.Integer, nullable=False, default=0)
    summary_text = db.Column(db.Text, nullable=True)
    metadata_json = db.Column(db.Text, nullable=True)

    turns = db.relationship(
        "TeacherTurn",
        backref="session",
        lazy="select",
        cascade="all, delete-orphan",
        order_by="TeacherTurn.turn_index",
    )
    drills = db.relationship(
        "Drill", backref="session", lazy="select", order_by="Drill.id"
    )

    def __repr__(self):
        return f"<TeacherSession {self.id} {self.status}>"

    def to_dict(self):
        return {
            "id": self.id,
            "uuid": self.uuid,
            "status": self.status,
            "plan_slug": self.plan_slug,
            "plan_title": self.plan_title,
            "provider": self.provider,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "turn_count": self.turn_count,
            "learner_turn_count": self.learner_turn_count,
            "summary": self.summary_text,
            "drills": [drill.to_dict() for drill in self.drills],
        }


class TeacherTurn(db.Model):
    __tablename__ = "teacher_turn"
    __table_args__ = (
        db.UniqueConstraint(
            "session_id", "turn_index", name="uq_teacher_turn_session_index"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(
        db.Integer,
        db.ForeignKey("teacher_session.id", ondelete="CASCADE"),
        nullable=False,
    )
    turn_index = db.Column(db.Integer, nullable=False)
    # teacher | learner | tool | system
    role = db.Column(db.String(16), nullable=False)
    text = db.Column(db.Text, nullable=True)
    tool_name = db.Column(db.String(60), nullable=True)
    tool_args = db.Column(db.Text, nullable=True)
    tool_result = db.Column(db.Text, nullable=True)
    latency_ms = db.Column(db.Integer, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=_utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "turn_index": self.turn_index,
            "role": self.role,
            "text": self.text,
            "tool_name": self.tool_name,
            "created_at": self.created_at.isoformat()
            if self.created_at
            else None,
        }


class Drill(db.Model):
    __tablename__ = "drill"
    __table_args__ = (db.Index("ix_drill_user_created", "user_id", "created_at"),)

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(
        db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4())
    )
    session_id = db.Column(
        db.Integer, db.ForeignKey("teacher_session.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    language_id = db.Column(db.Integer, db.ForeignKey("language.id"), nullable=True)
    item_id = db.Column(
        db.Integer, db.ForeignKey("item.id", ondelete="SET NULL"), nullable=True
    )
    # teacher | scene | review
    source = db.Column(db.String(16), nullable=False, default="teacher")
    # translate_to_target | translate_to_english | repeat
    drill_type = db.Column(db.String(32), nullable=False, default="translate_to_target")
    prompt = db.Column(db.Text, nullable=False)
    expected = db.Column(db.Text, nullable=False)
    payload = db.Column(db.Text, nullable=True)  # JSON
    validated = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=_utcnow
    )
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "drill_type": self.drill_type,
            "item_id": self.item_id,
            "prompt": self.prompt,
            "expected": self.expected,
        }


class DrillAttempt(db.Model):
    __tablename__ = "drill_attempt"
    __table_args__ = (
        db.UniqueConstraint(
            "drill_id", "client_attempt_id", name="uq_drill_attempt_client"
        ),
        db.Index("ix_drill_attempt_user_created", "user_id", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    drill_id = db.Column(
        db.Integer, db.ForeignKey("drill.id", ondelete="CASCADE"), nullable=False
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    response = db.Column(db.Text, nullable=False)
    score = db.Column(db.Float, nullable=True)
    acceptable = db.Column(db.Boolean, nullable=False, default=False)
    feedback = db.Column(db.Text, nullable=True)
    client_attempt_id = db.Column(db.String(64), nullable=False)
    review_card_id = db.Column(
        db.Integer, db.ForeignKey("review_card.id", ondelete="SET NULL"),
        nullable=True,
    )
    duration_ms = db.Column(db.Integer, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=_utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "drill_id": self.drill_id,
            "score": round(self.score, 3) if self.score is not None else None,
            "acceptable": self.acceptable,
            "feedback": self.feedback,
            "review_card_id": self.review_card_id,
        }
