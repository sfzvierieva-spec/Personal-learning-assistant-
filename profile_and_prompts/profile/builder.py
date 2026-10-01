"""Builds and summarizes the learner profile from questionnaire answers.

Two public functions:

- ``build_profile(answers: dict) -> Profile``
      Turns raw questionnaire answers into a validated ``Profile``. Free-text
      "Other" answers are handled explicitly and stored in ``free_text_notes``
      (never dropped silently).

- ``summarize_profile(profile: Profile) -> tuple[str, list[str]]``
      Returns ``(observations_paragraph, implication_bullets)`` for the single
      human-in-the-loop checkpoint: the user validates or corrects this summary
      before the system prompt is generated.

Summary design:
- Second person ("you"), not "the user".
- Combines several answers into short observations that feel like the tool
  actually listened (e.g. mainly_testing + mcq_exam + flashcards tells a
  richer story than any one of them alone).
- Every observation is grounded in the answers; nothing is invented.
- No character judgments (no "motivated", "smart", "lazy"). We describe
  MATERIAL decisions, not TRAITS.
- Bullets translate the profile into concrete material decisions ("your
  material will..."), so the user sees the link between what they said and
  what they will receive.
"""

from __future__ import annotations

from ..questionnaire.questions import QUESTIONS, QUESTIONNAIRE_VERSION, valid_values
from .schema import (
    FreeTextNote,
    Profile,
    ProfileMetadata,
)


# --------------------------------------------------------------------------- #
# Answer parsing helpers.
# --------------------------------------------------------------------------- #
def _split_answer(raw: object) -> tuple[object, str | None]:
    """Split a raw answer into ``(selection, other_text)``."""
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
    missing or invalid. Free-text "Other" nuance is preserved verbatim.
    """
    structured: dict[str, object] = {}
    notes: list[FreeTextNote] = []

    for question in QUESTIONS:
        qid = question["id"]
        axis = question["axis"]
        allowed = valid_values(qid)

        selection, other = _split_answer(answers.get(qid))

        if other:
            notes.append(FreeTextNote(question_id=qid, axis=axis, text=other))

        if question["multi_select"]:
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
            if selection not in allowed:
                raise ValueError(
                    f"Question {qid!r}: expected one of {sorted(allowed)}, "
                    f"got {selection!r}. A selection is required "
                    f"(free-text 'Other' is a nuance, not a substitute)."
                )
            structured[axis] = selection

    return Profile(
        **structured,
        free_text_notes=notes,
        metadata=ProfileMetadata(questionnaire_version=questionnaire_version),
    )


# --------------------------------------------------------------------------- #
# Summary generation. Every string is a fixed template: no LLM, no
# hallucination possible. Nothing describes the PERSON; everything describes
# the MATERIAL that will be produced.
# --------------------------------------------------------------------------- #

def _join(items: list[str]) -> str:
    """Join a list into an English phrase: 'a', 'a and b', 'a, b and c'."""
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return f"{', '.join(items[:-1])} and {items[-1]}"


_FORMAT_LABELS = {
    "synthesis_sheet": "a synthesis sheet",
    "flashcards": "flashcards",
    "quiz": "a quiz",
    "mindmap": "a mind map",
    "worked_examples": "worked examples",
    "revision_plan": "a revision plan",
    "exam_questions": "likely exam questions",
}
_STRUGGLE_LABELS = {
    "too_abstract": "things staying too abstract",
    "too_dense": "too much text at once",
    "hard_to_remember": "forgetting quickly",
    "hard_to_apply": "understanding but not knowing how to use it",
    "boring": "losing motivation",
}
_STRUGGLE_MOVES = {
    "too_abstract": "add concrete examples for every abstract concept",
    "too_dense": "keep passages short and airy",
    "hard_to_remember": "include mnemonics and quick recall prompts",
    "hard_to_apply": "add applied exercises after each concept",
    "boring": "keep the tone engaging and vary the format",
}
_GOAL_LABELS = {
    "mcq_exam": "an MCQ / short-answer exam",
    "essay_exam": "a written exam (essays or problem sets)",
    "oral_exam": "an oral exam or presentation",
    "practical_application": "practical application (project, code, real task)",
    "personal_understanding": "your own understanding, no exam pressure",
}
_GOAL_ASSESSMENT = {
    "mcq_exam": "MCQ-style questions with plausible distractors",
    "essay_exam": "open questions and mini-essay prompts with model answers",
    "oral_exam": "speaking prompts with talking points",
    "practical_application": "applied exercises grounded in real tasks",
    "personal_understanding": "reflection prompts rather than graded questions",
}
_TESTING_LABELS = {
    "mainly_reading": "content-heavy, few interruptions to test yourself",
    "reading_with_checks": "reading interleaved with small check-questions",
    "mainly_testing": "self-tests as the primary vehicle, content in between",
}
_EXPLANATION_LABELS = {
    "definition_only": "clean definitions on their own",
    "definition_plus_example": "each definition followed by a concrete example",
    "definition_plus_analogy": "each definition followed by an analogy",
    "step_by_step": "step-by-step logical derivations",
}
_DENSITY_LABELS = {
    "dense": "dense and concise, no filler",
    "balanced": "balanced — some structure, some breathing room",
    "spacious": "spacious, with examples and breathing room",
}
_TONE_LABELS = {
    "textbook": "formal, textbook-style",
    "teacher_voice": "clear and pedagogical, like a teacher speaking out loud",
    "friend_explaining": "friendly and vulgarized, like a friend explaining",
    "raw_notes": "raw and dense, no fluff, like a cheat sheet",
}
_LAYOUT_LABELS = {
    "structured_paragraphs": "structured paragraphs",
    "bullet_lists": "bullet lists throughout",
    "tables_when_comparative": "tables whenever content is comparative",
    "mixed_with_diagrams": "a mix, with ASCII diagrams when useful",
}


# ------------------- observation builders (insight, not mirror) ------------ #
def _format_observation(profile: Profile) -> str:
    fmts = profile.main_format
    goal = profile.study_goal.value
    testing = profile.self_testing.value
    if not fmts:
        return ("You didn't lock into a specific format — I'll default to a "
                "concise synthesis sheet plus a short quiz.")
    fmt_values = {f.value for f in fmts}
    if fmt_values == {"flashcards"} and testing == "mainly_testing" and goal == "mcq_exam":
        return ("You're aiming at MCQ-style mastery through repetition — "
                "flashcards, self-tests, exam-shaped questions. The material "
                "will be built entirely around active recall.")
    if "worked_examples" in fmt_values and goal == "practical_application":
        return ("You need to APPLY, not just understand — the material will "
                "lean heavily on worked examples that mirror the practical "
                "task you're preparing for.")
    if fmt_values == {"synthesis_sheet"} and goal == "personal_understanding":
        return ("You want a clear, standalone reference document — no drills, "
                "no exam simulation, just a synthesis you can come back to.")
    fmt_prose = _join([_FORMAT_LABELS[f] for f in fmt_values])
    return (f"You want your course reshaped as {fmt_prose}, aimed at "
            f"{_GOAL_LABELS[goal]}.")


def _shape_observation(profile: Profile) -> str:
    density = profile.density.value
    explanation = profile.explanation_style.value
    tone = profile.tone.value

    if density == "dense" and tone == "raw_notes":
        return ("You want zero fluff — dense, cheat-sheet style. The material "
                "will read like tight notes, not like a lesson.")
    if density == "spacious" and tone == "friend_explaining" and explanation.startswith("definition_plus"):
        return ("You want the material to explain like a friend would: room to "
                "breathe, real examples or analogies to make things click. "
                "It won't feel like a manual.")
    if explanation == "step_by_step" and tone == "teacher_voice":
        return ("You want a teacher's voice walking you through each concept "
                "step by step. The material will be built like a slow, "
                "structured explanation.")
    return (f"Overall shape: {_DENSITY_LABELS[density]}, with "
            f"{_EXPLANATION_LABELS[explanation]}, in a {_TONE_LABELS[tone]} "
            "voice.")


def _struggle_observation(profile: Profile) -> str | None:
    if not profile.struggle:
        return None
    labels = _join([_STRUGGLE_LABELS[s.value] for s in profile.struggle])
    moves = _join([_STRUGGLE_MOVES[s.value] for s in profile.struggle])
    return (f"You flagged {labels} as what tends to lose you in a course. "
            f"So the material will {moves}, not treat those as afterthoughts.")


# ------------------- implication bullets ----------------------------------- #
def _implication_format(profile: Profile) -> str:
    if not profile.main_format:
        return "Format: default to a concise synthesis sheet plus a short quiz."
    fmts = _join([_FORMAT_LABELS[f.value] for f in profile.main_format])
    return f"Format: your material will be produced as {fmts}."


def _implication_density(profile: Profile) -> str:
    return f"Density: {_DENSITY_LABELS[profile.density.value]}."


def _implication_explanation(profile: Profile) -> str:
    return f"Explanations: {_EXPLANATION_LABELS[profile.explanation_style.value]}."


def _implication_goal(profile: Profile) -> str:
    return (f"Assessment items: {_GOAL_ASSESSMENT[profile.study_goal.value]} "
            f"(you're preparing for {_GOAL_LABELS[profile.study_goal.value]}).")


def _implication_testing(profile: Profile) -> str:
    return f"Reading vs testing: {_TESTING_LABELS[profile.self_testing.value]}."


def _implication_tone(profile: Profile) -> str:
    return f"Voice: {_TONE_LABELS[profile.tone.value]}."


def _implication_layout(profile: Profile) -> str:
    return f"Layout: {_LAYOUT_LABELS[profile.visual_layout.value]}."


def _implication_struggle(profile: Profile) -> str | None:
    if not profile.struggle:
        return None
    moves = _join([_STRUGGLE_MOVES[s.value] for s in profile.struggle])
    return f"Against what loses you: {moves}."


def summarize_profile(profile: Profile) -> tuple[str, list[str]]:
    """Return an (observations_paragraph, implication_bullets) summary.

    The paragraph reads the profile back to the user — combining several
    answers into observations that feel like the tool actually listened.
    The bullets translate the profile into concrete material decisions.
    """
    obs = [_format_observation(profile), _shape_observation(profile)]
    struggle_obs = _struggle_observation(profile)
    if struggle_obs:
        obs.append(struggle_obs)
    paragraph = "Here's what I'm reading from your answers. " + " ".join(obs)

    bullets: list[str] = [
        _implication_format(profile),
        _implication_density(profile),
        _implication_explanation(profile),
        _implication_goal(profile),
        _implication_testing(profile),
        _implication_tone(profile),
        _implication_layout(profile),
    ]
    struggle_impl = _implication_struggle(profile)
    if struggle_impl:
        bullets.append(struggle_impl)

    for note in profile.free_text_notes:
        bullets.append(f'You added (on "{note.axis}"): "{note.text}"')

    return paragraph, bullets
