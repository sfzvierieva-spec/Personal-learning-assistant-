"""Builds and summarizes the learner profile from questionnaire answers.

Two public functions:

- ``build_profile(answers: dict) -> Profile``
      Turns raw questionnaire answers into a validated ``Profile``. Free-text
      "Other" answers are handled explicitly and stored in ``free_text_notes``
      (never dropped silently).

- ``summarize_profile(profile: Profile) -> tuple[str, list[str]]``
      Returns ``(short_paragraph, key_bullet_points)`` for the *single*
      human-in-the-loop checkpoint: the user validates or corrects this summary
      before the system prompt is generated.

Summary tone (agreed): warm but neutral. Strictly grounded in the answers,
"based on your answers" framing, no sycophancy, and no character judgments
(we describe methods and tendencies, never traits like "motivated"/"smart").

Input contract (``answers``)
----------------------------
A dict keyed by question id. Each value is one of:
  - a plain option value            -> "active_recall"
  - a list of values (multi-select) -> ["flashcards", "quizzes"]
  - a dict with explicit nuance     -> {"value": "spaced", "other": "..."}
    (``value`` is the selected option(s); ``other`` is the free-text nuance)

The multiple-choice selection is always required. The free-text "Other" is an
optional nuance *on top of* the selection (per the questionnaire design), and is
preserved verbatim in ``free_text_notes`` regardless of what was selected.
"""

from __future__ import annotations

from ..questionnaire.questions import QUESTIONS, QUESTIONNAIRE_VERSION, valid_values
from .schema import (
    FreeTextNote,
    Profile,
    ProfileMetadata,
    TonePreference,
)


# --------------------------------------------------------------------------- #
# Answer parsing helpers.
# --------------------------------------------------------------------------- #
def _split_answer(raw: object) -> tuple[object, str | None]:
    """Split a raw answer into ``(selection, other_text)``.

    Accepts a plain value, a list, or a ``{"value": ..., "other": ...}`` dict.
    Returns the selection (str, list, or None) and the optional free-text nuance.
    """
    if isinstance(raw, dict):
        other = raw.get("other")
        other = other.strip() if isinstance(other, str) and other.strip() else None
        return raw.get("value"), other
    return raw, None


def build_profile(
    answers: dict,
    questionnaire_version: str = QUESTIONNAIRE_VERSION,
) -> Profile:
    """Validate raw questionnaire answers into a ``Profile``.

    Raises ``ValueError`` (loudly, never silently) when a required selection is
    missing or is not one of the allowed option values for its question. Any
    free-text "Other" nuance is preserved in ``free_text_notes``.
    """
    structured: dict[str, object] = {}
    notes: list[FreeTextNote] = []

    for question in QUESTIONS:
        qid = question["id"]
        axis = question["axis"]
        allowed = valid_values(qid)

        selection, other = _split_answer(answers.get(qid))

        # Preserve any free-text nuance, whatever was selected.
        if other:
            notes.append(FreeTextNote(question_id=qid, axis=axis, text=other))

        if question["multi_select"]:
            # Multi-select -> list. Accept a bare string as a one-item list.
            if selection is None:
                selected = []
            elif isinstance(selection, str):
                selected = [selection]
            else:
                selected = list(selection)
            invalid = [v for v in selected if v not in allowed]
            if invalid:
                raise ValueError(
                    f"Question {qid!r}: invalid option(s) {invalid}; "
                    f"allowed values are {sorted(allowed)}."
                )
            structured[axis] = selected
        else:
            # Single-select -> exactly one allowed value is required.
            if selection not in allowed:
                raise ValueError(
                    f"Question {qid!r}: expected one of {sorted(allowed)}, "
                    f"got {selection!r}. A selection is required "
                    f"(free-text 'Other' is a nuance, not a substitute)."
                )
            structured[axis] = selection

    # tone_preference has no v1 question; default to neutral, allow explicit override.
    tone = answers.get("tone_preference", TonePreference.NEUTRAL.value)

    # Axis names deliberately match Profile field names, so we can splat them.
    return Profile(
        **structured,
        tone_preference=tone,
        free_text_notes=notes,
        metadata=ProfileMetadata(questionnaire_version=questionnaire_version),
    )


# --------------------------------------------------------------------------- #
# Summary generation (warm but neutral, strictly grounded, no sycophancy).
#
# Each phrase describes a METHOD or TENDENCY, never a character trait. There are
# no evaluative adjectives about the person. Wording is fixed (template-based),
# so the summary can never hallucinate a trait that is not in the answers.
# --------------------------------------------------------------------------- #
_RECALL = {
    "active_recall": "you tend to check your understanding by testing yourself "
                     "rather than by re-reading",
    "passive_review": "you tend to study by reviewing and re-reading your material",
    "mixed": "you mix self-testing and reviewing depending on the subject",
}
_SPACING = {
    "spaced": "you usually spread your studying across several sessions",
    "massed": "you usually study in longer sessions close to the deadline",
    "mixed": "your scheduling varies with the workload",
}
_SESSION = {
    "short_25": "you stay focused best in short blocks of around 25 minutes",
    "medium_50": "you stay focused best in sessions of about 45-60 minutes",
    "long_90plus": "you can stay focused for long sessions of 90 minutes or more",
}
_CHRONO = {
    "morning": "you concentrate best in the morning",
    "afternoon": "you concentrate best in the afternoon",
    "evening": "you concentrate best in the evening",
    "variable": "your best time to concentrate changes from day to day",
}
_ELAB = {
    "deep_why": "material sticks best when it explains why things work and how "
                "they connect",
    "surface_facts": "material sticks best when the key facts are stated clearly "
                     "and concisely",
    "mixed": "a mix of clear facts and deeper explanations works best",
}
_DEPTH = {
    "overview": "you usually want a high-level overview of the essentials",
    "standard": "you usually want a balanced, standard level of detail",
    "in_depth": "you usually want in-depth coverage, including nuances",
}
_BLOCKERS = {
    "procrastination": "getting started / putting it off",
    "overload": "feeling overwhelmed by too much at once",
    "distraction": "getting distracted",
    "low_self_efficacy": "losing confidence in your ability to do it",
}
_FORMATS = {
    "flashcards": "flashcards",
    "summaries": "summaries",
    "quizzes": "practice quizzes",
    "worked_examples": "worked examples",
}


def _join(items: list[str]) -> str:
    """Join a list into an English phrase: 'a', 'a and b', 'a, b and c'."""
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return f"{', '.join(items[:-1])} and {items[-1]}"


def summarize_profile(profile: Profile) -> tuple[str, list[str]]:
    """Return a (short_paragraph, key_bullet_points) summary for user validation.

    The text is factual, grounded strictly in the profile, warm but neutral, and
    contains no compliments or character judgments. The "Based on your answers"
    framing signals that it is derived from the questionnaire, not divined.
    """
    # --- short paragraph -------------------------------------------------- #
    paragraph = (
        "Based on your answers, "
        f"{_RECALL[profile.recall_preference.value]}, and "
        f"{_SPACING[profile.spacing_preference.value]}. "
        f"You reported that {_SESSION[profile.session_length.value]}, and "
        f"{_CHRONO[profile.chronotype.value]}. "
        f"For you, {_ELAB[profile.elaboration_preference.value]}, and "
        f"{_DEPTH[profile.depth_preference.value]}."
    )

    # --- key bullet points ------------------------------------------------ #
    bullets: list[str] = [
        f"Recall: {_RECALL[profile.recall_preference.value]}.",
        f"Scheduling: {_SPACING[profile.spacing_preference.value]}.",
        f"Focus span: {_SESSION[profile.session_length.value]}.",
        f"Best time: {_CHRONO[profile.chronotype.value]}.",
        f"Understanding: {_ELAB[profile.elaboration_preference.value]}.",
        f"Detail: {_DEPTH[profile.depth_preference.value]}.",
    ]

    if profile.blockers:
        blocker_text = _join([_BLOCKERS[b.value] for b in profile.blockers])
        bullets.append(f"Reported obstacles: {blocker_text}.")
    else:
        bullets.append("Reported obstacles: none selected.")

    if profile.preferred_output_formats:
        fmt_text = _join([_FORMATS[f.value] for f in profile.preferred_output_formats])
        bullets.append(f"Preferred study materials: {fmt_text}.")
    else:
        bullets.append("Preferred study materials: none selected.")

    # Surface every free-text nuance verbatim so the user can confirm it.
    for note in profile.free_text_notes:
        bullets.append(f'You added (on "{note.axis}"): "{note.text}"')

    return paragraph, bullets
