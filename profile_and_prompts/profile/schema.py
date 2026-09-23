"""Pydantic schema for the structured learner profile.

Defines the ``Profile`` model and its typed enums. This is the *contract*
between my module and the rest of the app: the profile builder produces a
validated ``Profile``, and the prompt generator consumes it. Fields are typed
enums wherever possible so downstream code never has to parse free strings.

Every enum value here MUST match an option ``value`` in
``questionnaire/questions.py`` (or a default set in ``profile/builder.py``).

Fields and the cognitive-science axis each one encodes:
- recall_preference        (Roediger & Karpicke, testing effect)
- spacing_preference       (Cepeda et al.; Ebbinghaus forgetting curve)
- session_length           (Sweller cognitive load; ultradian rhythms)
- chronotype               (time-of-day performance)
- blockers (list)          (Steel procrastination; Bandura self-efficacy)
- preferred_output_formats (list) (Paivio dual coding; worked examples)
- elaboration_preference   (Chi et al., self-explanation)
- tone_preference          (user preference; NOT a cognitive construct)
- depth_preference         (Sweller cognitive load / level of detail)
- free_text_notes (list)   (captures every "Other" answer; never dropped)
- metadata                 (timestamp, questionnaire_version)
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Typed enums. The string values are the storage/contract format shared with
# questions.py. Using str-based enums keeps JSON serialization human-readable.
# --------------------------------------------------------------------------- #
class RecallPreference(str, Enum):
    """Retrieval practice vs. passive review (Roediger & Karpicke 2006)."""

    ACTIVE_RECALL = "active_recall"
    PASSIVE_REVIEW = "passive_review"
    MIXED = "mixed"


class SpacingPreference(str, Enum):
    """Spaced vs. massed practice (Cepeda et al. 2006; Ebbinghaus)."""

    SPACED = "spaced"
    MASSED = "massed"
    MIXED = "mixed"


class SessionLength(str, Enum):
    """Sustainable focus span per session (Sweller; ultradian rhythms)."""

    SHORT_25 = "short_25"
    MEDIUM_50 = "medium_50"
    LONG_90PLUS = "long_90plus"


class Chronotype(str, Enum):
    """Time of day of best concentration (chronotype research)."""

    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    VARIABLE = "variable"


class Blocker(str, Enum):
    """Sources of disengagement (Steel 2007; Sweller; Bandura 1997)."""

    PROCRASTINATION = "procrastination"
    OVERLOAD = "overload"
    DISTRACTION = "distraction"
    LOW_SELF_EFFICACY = "low_self_efficacy"


class OutputFormat(str, Enum):
    """Preferred study-material formats (Paivio; Sweller & Cooper 1985)."""

    FLASHCARDS = "flashcards"
    SUMMARIES = "summaries"
    QUIZZES = "quizzes"
    WORKED_EXAMPLES = "worked_examples"


class ElaborationPreference(str, Enum):
    """Depth of elaboration / self-explanation (Chi et al. 1994)."""

    DEEP_WHY = "deep_why"
    SURFACE_FACTS = "surface_facts"
    MIXED = "mixed"


class TonePreference(str, Enum):
    """Preferred tone of generated material.

    Not a cognitive-science construct: this is a pure user/UI preference. It
    has no dedicated questionnaire item in v1 and defaults to ``NEUTRAL``.
    """

    NEUTRAL = "neutral"
    WARM = "warm"
    DIRECT = "direct"


class DepthPreference(str, Enum):
    """Preferred level of detail (Sweller, cognitive load)."""

    OVERVIEW = "overview"
    STANDARD = "standard"
    IN_DEPTH = "in_depth"


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

    # Default factory stamps creation time in UTC at build time.
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    questionnaire_version: str


# --------------------------------------------------------------------------- #
# The profile itself.
# --------------------------------------------------------------------------- #
class Profile(BaseModel):
    """Validated, structured learner profile.

    This object is the single source of truth passed to the prompt generator.
    All enum fields are guaranteed valid by pydantic; list fields may be empty
    (e.g. a user who reports no blockers) but are never ``None``.
    """

    # Single-choice cognitive axes.
    recall_preference: RecallPreference
    spacing_preference: SpacingPreference
    session_length: SessionLength
    chronotype: Chronotype
    elaboration_preference: ElaborationPreference
    depth_preference: DepthPreference

    # Multi-choice axes (order-insensitive; may be empty).
    blockers: list[Blocker] = Field(default_factory=list)
    preferred_output_formats: list[OutputFormat] = Field(default_factory=list)

    # Non-cognitive user preference; defaults to neutral (no v1 question).
    tone_preference: TonePreference = TonePreference.NEUTRAL

    # Free-text nuance and traceability.
    free_text_notes: list[FreeTextNote] = Field(default_factory=list)
    metadata: ProfileMetadata

    # Reject unknown fields so a malformed answer set fails loudly, not silently.
    model_config = {"extra": "forbid"}
