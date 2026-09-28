"""Pydantic schema for the structured learner profile.

Defines the ``Profile`` model and its typed enums. This is the *contract*
between my module and the rest of the app: the profile builder produces a
validated ``Profile``, and the prompt generator consumes it.

Every enum value here MUST match an option ``value`` in
``questionnaire/questions.py``.

Every field encodes a DIRECT output-shaping decision — no meta questions
about how the person learns in general, only decisions that change what the
generated study material looks like.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Typed enums. String values are the storage/contract format shared with
# questions.py. str-based enums keep JSON serialization human-readable.
# --------------------------------------------------------------------------- #
class MainFormat(str, Enum):
    """Primary output format the learner wants to receive."""

    SYNTHESIS_SHEET = "synthesis_sheet"
    FLASHCARDS = "flashcards"
    QUIZ = "quiz"
    MINDMAP = "mindmap"
    WORKED_EXAMPLES = "worked_examples"


class Density(str, Enum):
    """Content density — how long / aired out the material is."""

    DENSE = "dense"
    BALANCED = "balanced"
    SPACIOUS = "spacious"


class ExplanationStyle(str, Enum):
    """How each concept should be explained."""

    DEFINITION_ONLY = "definition_only"
    DEFINITION_PLUS_EXAMPLE = "definition_plus_example"
    DEFINITION_PLUS_ANALOGY = "definition_plus_analogy"
    STEP_BY_STEP = "step_by_step"


class Struggle(str, Enum):
    """What tends to lose the learner in a course (multi-select)."""

    TOO_ABSTRACT = "too_abstract"
    TOO_DENSE = "too_dense"
    HARD_TO_REMEMBER = "hard_to_remember"
    HARD_TO_APPLY = "hard_to_apply"
    BORING = "boring"


class StudyGoal(str, Enum):
    """What the learner is preparing for — shapes assessment items."""

    MCQ_EXAM = "mcq_exam"
    ESSAY_EXAM = "essay_exam"
    ORAL_EXAM = "oral_exam"
    PRACTICAL_APPLICATION = "practical_application"
    PERSONAL_UNDERSTANDING = "personal_understanding"


class SelfTesting(str, Enum):
    """Balance between reading and self-testing."""

    MAINLY_READING = "mainly_reading"
    READING_WITH_CHECKS = "reading_with_checks"
    MAINLY_TESTING = "mainly_testing"


class Tone(str, Enum):
    """Preferred voice / register of the generated text."""

    TEXTBOOK = "textbook"
    TEACHER_VOICE = "teacher_voice"
    FRIEND_EXPLAINING = "friend_explaining"
    RAW_NOTES = "raw_notes"


class VisualLayout(str, Enum):
    """Preferred visual layout of the text."""

    STRUCTURED_PARAGRAPHS = "structured_paragraphs"
    BULLET_LISTS = "bullet_lists"
    TABLES_WHEN_COMPARATIVE = "tables_when_comparative"
    MIXED_WITH_DIAGRAMS = "mixed_with_diagrams"


# --------------------------------------------------------------------------- #
# Sub-models.
# --------------------------------------------------------------------------- #
class FreeTextNote(BaseModel):
    """A single free-text ("Other") answer, kept verbatim so it is never lost.

    ``axis`` records which profile field the note relates to, so the UI and the
    prompt generator can surface the nuance next to the right structured field.
    """

    question_id: str
    axis: str
    text: str


class ProfileMetadata(BaseModel):
    """Traceability metadata attached to every profile."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    questionnaire_version: str


# --------------------------------------------------------------------------- #
# The profile itself.
# --------------------------------------------------------------------------- #
class Profile(BaseModel):
    """Validated, structured learner profile.

    Single source of truth passed to the prompt generator. Every field is a
    typed enum guaranteed valid by pydantic; list fields may be empty but are
    never ``None``.
    """

    main_format: list[MainFormat] = Field(default_factory=list)
    density: Density
    explanation_style: ExplanationStyle
    struggle: list[Struggle] = Field(default_factory=list)
    study_goal: StudyGoal
    self_testing: SelfTesting
    tone: Tone
    visual_layout: VisualLayout

    free_text_notes: list[FreeTextNote] = Field(default_factory=list)
    metadata: ProfileMetadata

    model_config = {"extra": "forbid"}
