"""Language-neutral content, dictionary, and library tables.

Phase 1 of the multilingual refactor adds these tables alongside the legacy
the Korean-shaped columns that predate the language core
without reading from or writing to them yet. That keeps the running app and the
existing test suite behaviourally unchanged while the schema gets a language
dimension.

Design rules:

* One ``item`` table for every language. FSRS is keyed by
  ``(user_id, item_id, skill)`` and must not be fragmented per language.
* Target-language text lives in ``item_form`` rows so a single item can carry a
  citation form, an inflected form, and a script-specific transliteration.
* Glosses live in ``item_gloss`` and record their own language code; ``english``
  is a UI/gloss language, never a property of the item.
* Content rows are soft-deletable and versioned. Learner history is never
  deleted because content changed.
"""

from datetime import UTC, datetime

from app import db


def _utcnow():
    return datetime.now(UTC)


class Language(db.Model):
    """A learnable language, not a UI locale."""

    __tablename__ = "language"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), nullable=False, unique=True, index=True)
    name = db.Column(db.String(64), nullable=False)
    native_name = db.Column(db.String(64), nullable=False)
    direction = db.Column(db.String(3), nullable=False, default="ltr")
    ui_locale = db.Column(db.String(16), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    scripts = db.relationship(
        "Script",
        secondary="language_script",
        lazy="select",
        back_populates="languages",
    )
    level_scales = db.relationship("LevelScale", back_populates="language")
    courses = db.relationship("Course", back_populates="language")

    def __repr__(self):
        return f"<Language {self.code}>"

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "native_name": self.native_name,
            "direction": self.direction,
            "ui_locale": self.ui_locale,
            "is_active": self.is_active,
        }


class Script(db.Model):
    """A writing system: Hangul, Ge'ez fidel, Latin, kana, han, ..."""

    __tablename__ = "script"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(24), nullable=False, unique=True, index=True)
    name = db.Column(db.String(64), nullable=False)
    # alphabet | abjad | abugida | syllabary | logosyllabic | mixed
    script_type = db.Column(db.String(24), nullable=False)
    direction = db.Column(db.String(3), nullable=False, default="ltr")
    # JSON list of inclusive [start, end] code points, for normalizers/validators.
    unicode_ranges = db.Column(db.Text, nullable=True)
    # linear | block | abugida | mixed
    composition = db.Column(db.String(24), nullable=False, default="linear")
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=_utcnow
    )

    languages = db.relationship(
        "Language",
        secondary="language_script",
        lazy="select",
        back_populates="scripts",
    )

    def __repr__(self):
        return f"<Script {self.code}>"


class LanguageScript(db.Model):
    """Which scripts a language uses, and in what role."""

    __tablename__ = "language_script"

    language_id = db.Column(
        db.Integer,
        db.ForeignKey("language.id", ondelete="CASCADE"),
        primary_key=True,
    )
    script_id = db.Column(
        db.Integer,
        db.ForeignKey("script.id", ondelete="CASCADE"),
        primary_key=True,
    )
    # primary | auxiliary | romanization
    role = db.Column(db.String(24), nullable=False, default="primary")
    is_default = db.Column(db.Boolean, nullable=False, default=False)


class LevelScale(db.Model):
    """A proficiency scale: TOPIK, CEFR, JLPT, or a custom one."""

    __tablename__ = "level_scale"
    __table_args__ = (db.UniqueConstraint("code", name="uq_level_scale_code"),)

    id = db.Column(db.Integer, primary_key=True)
    language_id = db.Column(
        db.Integer, db.ForeignKey("language.id"), nullable=True, index=True
    )
    code = db.Column(db.String(24), nullable=False)
    is_default = db.Column(db.Boolean, nullable=False, default=False)
    min_level = db.Column(db.Integer, nullable=False, default=1)
    max_level = db.Column(db.Integer, nullable=False, default=6)
    # JSON object: {"1": "TOPIK 1", ...}
    labels = db.Column(db.Text, nullable=False, default="{}")
    descriptors = db.Column(db.Text, nullable=True)

    language = db.relationship("Language", back_populates="level_scales")

    def __repr__(self):
        return f"<LevelScale {self.code}>"


class Course(db.Model):
    """A named, ordered curriculum for one language."""

    __tablename__ = "course"
    __table_args__ = (
        db.UniqueConstraint("language_id", "slug", name="uq_course_language_slug"),
    )

    id = db.Column(db.Integer, primary_key=True)
    language_id = db.Column(
        db.Integer, db.ForeignKey("language.id"), nullable=False, index=True
    )
    level_scale_id = db.Column(
        db.Integer, db.ForeignKey("level_scale.id"), nullable=True
    )
    slug = db.Column(db.String(80), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=_utcnow
    )

    language = db.relationship("Language", back_populates="courses")
    decks = db.relationship("Deck", back_populates="course")

    def __repr__(self):
        return f"<Course {self.slug}>"


class Deck(db.Model):
    """A system deck or a learner's private deck."""

    __tablename__ = "deck"
    __table_args__ = (
        db.Index(
            "uq_deck_system_slug",
            "language_id",
            "slug",
            unique=True,
            sqlite_where=db.text("owner_id IS NULL"),
            postgresql_where=db.text("owner_id IS NULL"),
        ),
        db.Index(
            "uq_deck_owner_slug",
            "owner_id",
            "language_id",
            "slug",
            unique=True,
            sqlite_where=db.text("owner_id IS NOT NULL"),
            postgresql_where=db.text("owner_id IS NOT NULL"),
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    language_id = db.Column(
        db.Integer, db.ForeignKey("language.id"), nullable=False, index=True
    )
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=True)
    owner_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=True
    )
    slug = db.Column(db.String(80), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    # core | script | scenes | sound_gym | user_private
    kind = db.Column(db.String(24), nullable=False, default="core")
    version = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=_utcnow
    )
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)

    course = db.relationship("Course", back_populates="decks")

    def __repr__(self):
        return f"<Deck {self.slug}>"


class DeckItem(db.Model):
    __tablename__ = "deck_item"
    __table_args__ = (
        db.UniqueConstraint("deck_id", "item_id", name="uq_deck_item_deck_item"),
    )

    id = db.Column(db.Integer, primary_key=True)
    deck_id = db.Column(
        db.Integer, db.ForeignKey("deck.id", ondelete="CASCADE"), nullable=False
    )
    item_id = db.Column(
        db.Integer, db.ForeignKey("item.id", ondelete="CASCADE"), nullable=False
    )
    position = db.Column(db.Integer, nullable=False, default=0)
    added_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=_utcnow
    )


class ItemForm(db.Model):
    """One written (or spoken) realization of an item."""

    __tablename__ = "item_form"
    __table_args__ = (
        db.Index(
            "uq_item_form_text",
            "item_id",
            "form_kind",
            "normalized_text",
            unique=True,
            sqlite_where=db.text("deleted_at IS NULL"),
            postgresql_where=db.text("deleted_at IS NULL"),
        ),
        db.Index("ix_item_form_item", "item_id"),
        db.Index("ix_item_form_script", "script_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(
        db.Integer, db.ForeignKey("item.id", ondelete="CASCADE"), nullable=False
    )
    script_id = db.Column(
        db.Integer, db.ForeignKey("script.id"), nullable=False
    )
    # citation | surface | inflected | variant | phonetic
    form_kind = db.Column(db.String(24), nullable=False, default="citation")
    text = db.Column(db.String(500), nullable=False)
    normalized_text = db.Column(db.String(500), nullable=False)
    transliteration = db.Column(db.String(500), nullable=True)
    # rr | yale | bgn_pcgn | ala_lc | hepburn | pinyin | ...
    transliteration_scheme = db.Column(db.String(24), nullable=True)
    ipa = db.Column(db.String(500), nullable=True)
    audio_path = db.Column(db.String(255), nullable=True)
    is_primary = db.Column(db.Boolean, nullable=False, default=False)
    # Pack-validated JSON: particles, endings, root/pattern, etc.
    morphology = db.Column(db.Text, nullable=True)
    morphology_family = db.Column(db.String(24), nullable=True)
    form_group = db.Column(db.String(80), nullable=True)
    form_condition = db.Column(db.String(80), nullable=True)
    version = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=_utcnow
    )
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)

    item = db.relationship("Item", backref=db.backref("forms", lazy="select"))
    script = db.relationship("Script")

    def __repr__(self):
        return f"<ItemForm {self.text}>"

    def to_dict(self):
        return {
            "id": self.id,
            "item_id": self.item_id,
            "text": self.text,
            "transliteration": self.transliteration,
            "audio_path": self.audio_path,
            "is_primary": self.is_primary,
        }


class ItemGloss(db.Model):
    """A meaning of an item in a UI/gloss language."""

    __tablename__ = "item_gloss"
    __table_args__ = (
        db.Index("ix_item_gloss_item", "item_id"),
        db.Index("ix_item_gloss_lang", "lang"),
    )

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(
        db.Integer, db.ForeignKey("item.id", ondelete="CASCADE"), nullable=False
    )
    lang = db.Column(db.String(16), nullable=False, default="en")
    text = db.Column(db.String(500), nullable=False)
    # translation | definition | note | usage
    gloss_type = db.Column(db.String(24), nullable=False, default="translation")
    is_primary = db.Column(db.Boolean, nullable=False, default=False)
    version = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=_utcnow
    )

    item = db.relationship("Item", backref=db.backref("glosses", lazy="select"))

    def __repr__(self):
        return f"<ItemGloss {self.lang}:{self.text}>"


class DictionaryEntry(db.Model):
    """A lexicon headword: lemma + part of speech."""

    __tablename__ = "dictionary_entry"
    __table_args__ = (
        db.Index(
            "uq_dictionary_entry_headword",
            "language_id",
            "normalized_headword",
            "pos",
            unique=True,
            sqlite_where=db.text("deleted_at IS NULL"),
            postgresql_where=db.text("deleted_at IS NULL"),
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    language_id = db.Column(
        db.Integer, db.ForeignKey("language.id"), nullable=False, index=True
    )
    lemma_item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=True)
    headword = db.Column(db.String(300), nullable=False)
    normalized_headword = db.Column(db.String(300), nullable=False)
    # noun | verb | adjective | particle | ending | phrase | ...
    pos = db.Column(db.String(24), nullable=False)
    gender_class = db.Column(db.String(24), nullable=True)
    register = db.Column(db.String(24), nullable=True)
    frequency_rank = db.Column(db.Integer, nullable=True)
    etymology = db.Column(db.Text, nullable=True)
    # draft | published | deprecated
    status = db.Column(db.String(16), nullable=False, default="published")
    version = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=_utcnow
    )
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)

    senses = db.relationship(
        "DictionarySense",
        back_populates="entry",
        order_by="DictionarySense.sense_order",
    )

    def __repr__(self):
        return f"<DictionaryEntry {self.headword}>"


class DictionarySense(db.Model):
    __tablename__ = "dictionary_sense"
    __table_args__ = (
        db.UniqueConstraint(
            "entry_id", "sense_order", "gloss_lang", name="uq_dictionary_sense_order"
        ),
        db.Index("ix_dictionary_sense_entry", "entry_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(
        db.Integer,
        db.ForeignKey("dictionary_entry.id", ondelete="CASCADE"),
        nullable=False,
    )
    sense_order = db.Column(db.Integer, nullable=False, default=1)
    gloss_lang = db.Column(db.String(16), nullable=False, default="en")
    gloss = db.Column(db.String(300), nullable=False)
    definition = db.Column(db.Text, nullable=True)
    example_item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=True)
    register = db.Column(db.String(24), nullable=True)
    domain = db.Column(db.String(60), nullable=True)

    entry = db.relationship("DictionaryEntry", back_populates="senses")

    def __repr__(self):
        return f"<DictionarySense {self.gloss}>"


class Translation(db.Model):
    """A cached, reviewable source→target translation."""

    __tablename__ = "translation"
    __table_args__ = (
        db.Index(
            "ix_translation_lookup",
            "source_language_id",
            "target_language_id",
            "source_text_hash",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    source_language_id = db.Column(
        db.Integer, db.ForeignKey("language.id"), nullable=False
    )
    target_language_id = db.Column(
        db.Integer, db.ForeignKey("language.id"), nullable=False
    )
    sense_id = db.Column(
        db.Integer, db.ForeignKey("dictionary_sense.id"), nullable=True
    )
    source_item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=True)
    target_item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=True)
    source_text_hash = db.Column(db.String(64), nullable=False)
    source_text = db.Column(db.String(500), nullable=False)
    target_text = db.Column(db.String(500), nullable=False)
    provider = db.Column(db.String(40), nullable=True)
    model = db.Column(db.String(80), nullable=True)
    quality = db.Column(db.String(16), nullable=True)
    is_human_reviewed = db.Column(db.Boolean, nullable=False, default=False)
    version = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=_utcnow
    )


class TermCard(db.Model):
    """A term the learner personally saved, with its original context."""

    __tablename__ = "term_card"
    __table_args__ = (
        db.Index(
            "uq_term_card_user_item",
            "user_id",
            "item_id",
            unique=True,
            sqlite_where=db.text("item_id IS NOT NULL"),
            postgresql_where=db.text("item_id IS NOT NULL"),
        ),
        db.Index(
            "uq_term_card_user_entry",
            "user_id",
            "dictionary_entry_id",
            unique=True,
            sqlite_where=db.text("dictionary_entry_id IS NOT NULL"),
            postgresql_where=db.text("dictionary_entry_id IS NOT NULL"),
        ),
        db.Index("ix_term_card_user_language", "user_id", "language_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    language_id = db.Column(
        db.Integer, db.ForeignKey("language.id"), nullable=False
    )
    item_id = db.Column(
        db.Integer, db.ForeignKey("item.id", ondelete="SET NULL"), nullable=True
    )
    dictionary_entry_id = db.Column(
        db.Integer,
        db.ForeignKey("dictionary_entry.id", ondelete="SET NULL"),
        nullable=True,
    )
    # transcript | scene | teacher | dictionary | import | manual
    source = db.Column(db.String(24), nullable=False, default="manual")
    context_sentence = db.Column(db.Text, nullable=True)
    note = db.Column(db.Text, nullable=True)
    tags = db.Column(db.Text, nullable=True)  # JSON list
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=_utcnow, index=True
    )
    archived_at = db.Column(db.DateTime(timezone=True), nullable=True)

    item = db.relationship("Item")
    entry = db.relationship("DictionaryEntry")

    def __repr__(self):
        return f"<TermCard user={self.user_id} item={self.item_id}>"
