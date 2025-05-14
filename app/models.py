from datetime import datetime
import uuid
from app import db


class Phrase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    english_text = db.Column(db.String(500), nullable=False, index=True)
    korean_text = db.Column(db.String(500), nullable=False)
    audio_path = db.Column(db.String(200), nullable=False)
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
            "created_at": self.created_at.isoformat(),
        }


class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    audio_path = db.Column(db.String(200), nullable=False)
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
            "created_at": self.created_at.isoformat(),
            "lines": [line.to_dict() for line in self.lines],
        }


class ConversationLine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(
        db.Integer, db.ForeignKey("conversation.id"), nullable=False
    )
    phrase_id = db.Column(db.Integer, db.ForeignKey("phrase.id"), nullable=False)
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
