"""Pydantic schemas for AI request and model-output validation."""

from typing import Literal

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

__all__ = [
    "ConversationLine",
    "ConversationRequest",
    "ConversationScenario",
    "TranslationRequest",
    "ValidationError",
    "contains_hangul",
]


def contains_hangul(text):
    """Return True when ``text`` contains at least one precomposed Hangul syllable."""
    return any("\uac00" <= char <= "\ud7a3" for char in text)


def _required_text(value, field_name):
    if not isinstance(value, str):
        raise ValueError(  # noqa: TRY004 - pydantic validators use ValueError
            f"{field_name} must be a string"
        )
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{field_name} must not be empty")
    return stripped


class TranslationRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    text: str = Field(min_length=1, max_length=500)
    addressee: Literal["male", "female", "group", "any"] = "any"
    # The response and database call this "register"; accept both names on the
    # wire. A field literally named ``register`` shadows an ABCMeta member and
    # makes Pydantic warn, so the internal field is ``formality``.
    formality: Literal["casual", "polite", "formal"] | None = Field(
        default=None,
        validation_alias=AliasChoices("register", "formality"),
    )

    @field_validator("text", mode="before")
    @classmethod
    def _strip_text(cls, value):
        return _required_text(value, "text")


class VariantAudioRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    item_id: int = Field(gt=0)
    text: str = Field(min_length=1, max_length=300)


class GenericTranslationResponse(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    translation: str = Field(min_length=1, max_length=500)
    romanization: str | None = Field(default=None, max_length=500)

    @field_validator("translation", mode="before")
    @classmethod
    def _strip_translation(cls, value):
        return _required_text(value, "translation")

    @field_validator("romanization", mode="before")
    @classmethod
    def _strip_romanization(cls, value):
        if value is None:
            return None
        text = str(value).strip()
        return text or None


class ConversationRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    prompt: str = Field(min_length=1, max_length=200)

    @field_validator("prompt", mode="before")
    @classmethod
    def _strip_prompt(cls, value):
        return _required_text(value, "prompt")


class ConversationLine(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    speaker: Literal[1, 2]
    source_text: str = Field(min_length=1, max_length=300)
    target_text: str = Field(min_length=1, max_length=300)

    @field_validator("source_text", mode="before")
    @classmethod
    def _strip_english(cls, value):
        return _required_text(value, "source_text")

    @field_validator("target_text", mode="before")
    @classmethod
    def _strip_korean(cls, value):
        return _required_text(value, "target_text")

    @field_validator("target_text")
    @classmethod
    def _require_hangul(cls, value):
        if not contains_hangul(value):
            raise ValueError("target_text must contain at least one Hangul character")
        return value


class ConversationScenario(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    lines: list[ConversationLine] = Field(min_length=2, max_length=4)

    @field_validator("title", mode="before")
    @classmethod
    def _strip_title(cls, value):
        return _required_text(value, "title")

    @model_validator(mode="after")
    def _speakers_alternate(self):
        for previous, current in zip(self.lines, self.lines[1:]):
            if previous.speaker == current.speaker:
                raise ValueError(
                    "consecutive lines must use different speakers; "
                    f"got speaker {current.speaker} twice in a row"
                )
        return self
