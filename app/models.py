import uuid
from datetime import UTC, datetime
from typing import ClassVar

from app import db


class Phrase(db.Model):
    __table_args__ = (
        db.Index("ix_phrase_created_id", "created_at", "id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    audio_path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    source_language_id = db.Column(
        db.Integer, db.ForeignKey("language.id"), nullable=True
    )
    target_language_id = db.Column(
        db.Integer, db.ForeignKey("language.id"), nullable=True
    )
    source_text = db.Column(db.String(500), nullable=True)
    target_text = db.Column(db.String(500), nullable=True)
    target_transliteration = db.Column(db.String(500), nullable=True)

    def __repr__(self):
        return f"<Phrase {self.source_text}>"

    def to_dict(self):
        return {
            "id": self.id,
            "uuid": self.uuid,
            "source_text": self.source_text,
            "target_text": self.target_text,
            "target_transliteration": self.target_transliteration,
            "audio_path": self.audio_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    audio_path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    language_id = db.Column(
        db.Integer, db.ForeignKey("language.id"), nullable=True, index=True
    )
    lines = db.relationship(
        "ConversationLine",
        backref="conversation",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="ConversationLine.order",
    )

    def __repr__(self):
        return f"<Conversation {self.title}>"

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "audio_path": self.audio_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "lines": [line.to_dict() for line in self.lines],
        }


class User(db.Model):
    __table_args__ = (
        db.Index(
            "uq_user_single_local",
            "is_local",
            unique=True,
            sqlite_where=db.text("is_local = 1"),
            postgresql_where=db.text("is_local = 1"),
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=True)
    display_name = db.Column(db.String(100), nullable=False, default="Learner")
    is_local = db.Column(db.Boolean, nullable=False, default=False, index=True)
    goal = db.Column(db.String(30), nullable=False, default="everyday")
    daily_minutes = db.Column(db.Integer, nullable=False, default=10)
    experience = db.Column(db.String(20), nullable=False, default="new")
    timezone = db.Column(db.String(64), nullable=False, default="UTC")
    onboarding_complete = db.Column(
        db.Boolean, nullable=False, default=False
    )
    reminder_enabled = db.Column(db.Boolean, nullable=False, default=False)
    reminder_time = db.Column(db.String(5), nullable=False, default="19:00")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    target_language_id = db.Column(
        db.Integer, db.ForeignKey("language.id"), nullable=True
    )
    ui_locale = db.Column(db.String(16), nullable=False, default="en")

    def __repr__(self):
        return f"<User {self.id} {self.display_name}>"


class Item(db.Model):
    """A single learnable unit, in any language (word, chunk, grammar, sentence)."""

    __table_args__ = (
        db.UniqueConstraint(
            "target_text", "gloss", "item_type", name="uq_item_content"
        ),
        db.Index("ix_item_level_type", "level", "item_type"),
        db.Index("ix_item_language_level_type", "language_id", "level", "item_type"),
    )

    id = db.Column(db.Integer, primary_key=True)
    item_type = db.Column(db.String(20), nullable=False, default="lexeme")
    target_text = db.Column(db.String(300), nullable=False, index=True)
    gloss = db.Column(db.String(300), nullable=False)
    transliteration = db.Column(db.String(300), nullable=True)
    level = db.Column(db.Integer, nullable=False, default=1, index=True)
    freq_rank = db.Column(db.Integer, nullable=True)
    audio_path = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    default_skill = db.Column(db.String(20), nullable=False, default="recognize")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Multilingual expand-phase columns (nullable until the contract phase).
    language_id = db.Column(
        db.Integer, db.ForeignKey("language.id"), nullable=True, index=True
    )
    primary_deck_id = db.Column(db.Integer, db.ForeignKey("deck.id"), nullable=True)
    dictionary_entry_id = db.Column(
        db.Integer,
        db.ForeignKey("dictionary_entry.id", use_alter=True),
        nullable=True,
    )
    level_scale_id = db.Column(
        db.Integer, db.ForeignKey("level_scale.id"), nullable=True
    )
    status = db.Column(db.String(16), nullable=False, default="published")
    key_normalized = db.Column(db.String(300), nullable=True)
    sense_key = db.Column(db.String(300), nullable=True, default="")
    content_hash = db.Column(db.String(64), nullable=True)
    version = db.Column(db.Integer, nullable=False, default=1)
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    superseded_by_id = db.Column(
        db.Integer, db.ForeignKey("item.id", use_alter=True), nullable=True
    )
    # unchecked | native_checked. Set by human triage, never inferred.
    review_status = db.Column(
        db.String(16),
        nullable=False,
        default="unchecked",
        server_default="unchecked",
    )
    reviewed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Item {self.target_text}>"

    def to_dict(self):
        return {
            "id": self.id,
            "item_type": self.item_type,
            "target_text": self.target_text,
            "gloss": self.gloss,
            "transliteration": self.transliteration,
            "level": self.level,
            "freq_rank": self.freq_rank,
            "audio_path": self.audio_path,
            "notes": self.notes,
            "default_skill": self.default_skill,
            "review_status": self.review_status,
        }


class ReviewCard(db.Model):
    """FSRS state for one (user, item, skill) pair."""

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "item_id",
            "skill",
            name="uq_review_card_user_item_skill",
        ),
        db.Index("ix_review_card_due", "user_id", "due_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    item_id = db.Column(
        db.Integer, db.ForeignKey("item.id", ondelete="CASCADE"), nullable=False
    )
    skill = db.Column(db.String(20), nullable=False, default="recognize")

    # FSRS fields. Times are stored as UTC; SQLite returns naive datetimes, so
    # the scheduler attaches UTC when reconstructing the FSRS Card.
    state = db.Column(db.Integer, nullable=False, default=1)
    step = db.Column(db.Integer, nullable=True)
    stability = db.Column(db.Float, nullable=True)
    difficulty = db.Column(db.Float, nullable=True)
    due_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    last_review_at = db.Column(db.DateTime(timezone=True), nullable=True)
    reps = db.Column(db.Integer, nullable=False, default=0)
    lapses = db.Column(db.Integer, nullable=False, default=0)
    version = db.Column(db.Integer, nullable=False, default=1)

    __mapper_args__: ClassVar[dict] = {"version_id_col": version}

    item = db.relationship("Item")
    user = db.relationship("User")

    def __repr__(self):
        return f"<ReviewCard user={self.user_id} item={self.item_id} skill={self.skill}>"


class ReviewLog(db.Model):
    __table_args__ = (
        db.Index("ix_review_log_user_date", "user_id", "reviewed_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(
        db.Integer,
        db.ForeignKey("review_card.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    rating = db.Column(db.Integer, nullable=False)
    reviewed_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    elapsed_ms = db.Column(db.Integer, nullable=True)
    was_new = db.Column(db.Boolean, nullable=False, default=False)
    scheduled_days = db.Column(db.Float, nullable=True)
    stability = db.Column(db.Float, nullable=True)
    difficulty = db.Column(db.Float, nullable=True)

    card = db.relationship("ReviewCard")


class CanDoArtifact(db.Model):
    """A dated proof that the learner completed a real-world task."""

    __table_args__ = (
        db.UniqueConstraint(
            "user_id", "scene_slug", name="uq_can_do_user_scene"
        ),
        db.Index("ix_can_do_user_date", "user_id", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    scene_slug = db.Column(db.String(60), nullable=False)
    label = db.Column(db.String(300), nullable=False)
    language_id = db.Column(
        db.Integer, db.ForeignKey("language.id"), nullable=True, index=True
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        index=True,
    )

    user = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "scene_slug": self.scene_slug,
            "label": self.label,
            "created_at": self.created_at.isoformat()
            if self.created_at
            else None,
        }


class SceneSession(db.Model):
    """Progress through one scripted mission scene for one learner."""

    __table_args__ = (
        db.UniqueConstraint(
            "user_id", "scene_slug", name="uq_scene_session_user_scene"
        ),
        db.Index("ix_scene_session_user", "user_id", "completed"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    scene_slug = db.Column(db.String(60), nullable=False)
    step_index = db.Column(db.Integer, nullable=False, default=0)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    transcript = db.Column(db.Text, nullable=True)
    language_id = db.Column(
        db.Integer, db.ForeignKey("language.id"), nullable=True, index=True
    )
    started_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    user = db.relationship("User")


class SpeechAttempt(db.Model):
    """One transcript-based speech check. Raw audio is never stored."""

    __table_args__ = (
        db.Index("ix_speech_attempt_user_date", "user_id", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    item_id = db.Column(
        db.Integer, db.ForeignKey("item.id", ondelete="SET NULL"), nullable=True
    )
    target_text = db.Column(db.String(300), nullable=False)
    transcript = db.Column(db.String(500), nullable=False)
    match_score = db.Column(db.Float, nullable=False)
    acceptable = db.Column(db.Boolean, nullable=False, default=False)
    provider = db.Column(db.String(30), nullable=False)
    model = db.Column(db.String(60), nullable=False)
    duration_ms = db.Column(db.Integer, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        index=True,
    )

    # Multilingual expand-phase columns.
    language_id = db.Column(
        db.Integer, db.ForeignKey("language.id"), nullable=True, index=True
    )
    item_form_id = db.Column(
        db.Integer, db.ForeignKey("item_form.id"), nullable=True
    )
    overall_score = db.Column(db.Float, nullable=True)
    phoneme_scores = db.Column(db.Text, nullable=True)  # JSON
    prosody_scores = db.Column(db.Text, nullable=True)  # JSON
    scoring_version = db.Column(db.String(24), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "target_text": self.target_text,
            "transcript": self.transcript,
            "match_score": round(self.match_score, 3),
            "acceptable": self.acceptable,
            "provider": self.provider,
            "created_at": self.created_at.isoformat()
            if self.created_at
            else None,
        }


class PushSubscription(db.Model):
    """A browser push endpoint for one learner."""

    __table_args__ = (
        db.Index("ix_push_subscription_user", "user_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    endpoint = db.Column(db.Text, nullable=False, unique=True)
    p256dh = db.Column(db.String(300), nullable=False)
    auth = db.Column(db.String(120), nullable=False)
    user_agent = db.Column(db.String(300), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    last_success_at = db.Column(db.DateTime(timezone=True), nullable=True)
    failure_count = db.Column(db.Integer, nullable=False, default=0)

    user = db.relationship("User")


class Event(db.Model):
    """Append-only product event for activation and retention analysis."""

    __table_args__ = (
        db.Index("ix_event_user_name_date", "user_id", "name", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    name = db.Column(db.String(60), nullable=False, index=True)
    props = db.Column(db.Text, nullable=True)
    language_id = db.Column(
        db.Integer, db.ForeignKey("language.id"), nullable=True, index=True
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        index=True,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "props": self.props,
            "created_at": self.created_at.isoformat()
            if self.created_at
            else None,
        }


class ContentReport(db.Model):
    """A learner-flagged correction for one piece of content.

    The snapshot keeps the report readable after the item or phrase changes or
    disappears. Triage only changes ``status``; content edits stay deliberate
    and manual so review cards and cached audio cannot drift silently.
    """

    __tablename__ = "content_report"
    __table_args__ = (
        db.Index("ix_content_report_status_created", "status", "created_at"),
        db.Index("ix_content_report_user_created", "user_id", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    language_id = db.Column(
        db.Integer, db.ForeignKey("language.id", ondelete="SET NULL"), nullable=True
    )
    item_id = db.Column(
        db.Integer, db.ForeignKey("item.id", ondelete="SET NULL"), nullable=True
    )
    phrase_id = db.Column(
        db.Integer, db.ForeignKey("phrase.id", ondelete="SET NULL"), nullable=True
    )
    # Scenes live in code, not the database; this points at the step to edit.
    scene_slug = db.Column(db.String(80), nullable=True)
    step_index = db.Column(db.Integer, nullable=True)
    # review | library | dictionary | translate | teacher | scene
    surface = db.Column(db.String(24), nullable=False)
    snapshot_text = db.Column(db.Text, nullable=True)
    # meaning | naturalness | register | spelling | audio | other
    kind = db.Column(db.String(24), nullable=False)
    suggested_text = db.Column(db.String(300), nullable=True)
    context = db.Column(db.String(200), nullable=True)
    note = db.Column(db.Text, nullable=True)
    # open | accepted | rejected
    status = db.Column(
        db.String(16),
        nullable=False,
        default="open",
        server_default="open",
    )
    resolution_note = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    resolved_at = db.Column(db.DateTime(timezone=True), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "surface": self.surface,
            "kind": self.kind,
            "status": self.status,
            "snapshot_text": self.snapshot_text,
            "suggested_text": self.suggested_text,
            "context": self.context,
            "note": self.note,
            "item_id": self.item_id,
            "phrase_id": self.phrase_id,
            "scene_slug": self.scene_slug,
            "step_index": self.step_index,
            "created_at": self.created_at.isoformat()
            if self.created_at
            else None,
        }


class ConversationLine(db.Model):
    __table_args__ = (
        db.UniqueConstraint(
            "conversation_id", "order", name="uq_conversation_line_order"
        ),
        db.Index("ix_conversation_line_conversation_id", "conversation_id"),
        db.Index("ix_conversation_line_phrase_id", "phrase_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(
        db.Integer,
        db.ForeignKey("conversation.id", ondelete="CASCADE"),
        nullable=False,
    )
    phrase_id = db.Column(
        db.Integer,
        db.ForeignKey("phrase.id", ondelete="RESTRICT"),
        nullable=False,
    )
    speaker = db.Column(db.String(20), nullable=False)  # e.g., "Speaker 1", "Speaker 2"
    order = db.Column(db.Integer, nullable=False)

    phrase = db.relationship("Phrase")

    def __repr__(self):
        return f"<ConversationLine {self.speaker} order={self.order}>"

    def to_dict(self):
        return {
            "id": self.id,
            "speaker": self.speaker,
            "order": self.order,
            "phrase": self.phrase.to_dict() if self.phrase else None,
        }


# Imported for its side effect: registering the language-neutral tables on
# ``db.metadata`` so ``create_all`` and Alembic autogenerate see them.
from app.models_language import (  # noqa: F401
    Course,
    Deck,
    DeckItem,
    DictionaryEntry,
    DictionarySense,
    ItemForm,
    ItemGloss,
    Language,
    LanguageScript,
    LevelScale,
    Script,
    TermCard,
    Translation,
)
from app.models_teacher import (  # noqa: F401
    Drill,
    DrillAttempt,
    TeacherSession,
    TeacherTurn,
)
