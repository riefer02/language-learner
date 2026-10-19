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
    english_text = db.Column(db.String(500), nullable=False, index=True)
    korean_text = db.Column(db.String(500), nullable=False)
    audio_path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<Phrase {self.english_text}>"

    def to_dict(self):
        return {
            "id": self.id,
            "uuid": self.uuid,
            "english_text": self.english_text,
            "korean_text": self.korean_text,
            "audio_path": self.audio_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    audio_path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<User {self.id} {self.display_name}>"


class Item(db.Model):
    """A single learnable unit: word, chunk, grammar point, or sentence."""

    __table_args__ = (
        db.UniqueConstraint(
            "korean", "english", "item_type", name="uq_item_content"
        ),
        db.Index("ix_item_level_type", "level", "item_type"),
    )

    id = db.Column(db.Integer, primary_key=True)
    item_type = db.Column(db.String(20), nullable=False, default="lexeme")
    korean = db.Column(db.String(300), nullable=False)
    english = db.Column(db.String(300), nullable=False)
    romanization = db.Column(db.String(300), nullable=True)
    level = db.Column(db.Integer, nullable=False, default=1, index=True)
    freq_rank = db.Column(db.Integer, nullable=True)
    audio_path = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    default_skill = db.Column(db.String(20), nullable=False, default="recognize")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<Item {self.korean}>"

    def to_dict(self):
        return {
            "id": self.id,
            "item_type": self.item_type,
            "korean": self.korean,
            "english": self.english,
            "romanization": self.romanization,
            "level": self.level,
            "freq_rank": self.freq_rank,
            "audio_path": self.audio_path,
            "notes": self.notes,
            "default_skill": self.default_skill,
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
