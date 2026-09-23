"""End-to-end pipeline test with three contrasting fake users.

Runs each fake user through the full pipeline:

    questionnaire answers -> build_profile -> summarize_profile
                          -> generate_system_prompt

and prints the outputs side by side so the personalization is visibly
different across profiles (that is the point of the module).

Run it two ways:
    python -m profile_and_prompts.tests.test_end_to_end   # pretty-print report
    pytest profile_and_prompts/tests/test_end_to_end.py    # assertions only
"""

from __future__ import annotations

from ..profile.builder import build_profile, summarize_profile
from ..prompt_generator.generator import generate_system_prompt


# --------------------------------------------------------------------------- #
# Three deliberately contrasting fake users.
# --------------------------------------------------------------------------- #
FAKE_USERS: dict[str, dict] = {
    # A: self-testing, spaced, short sessions, easily blocked, wants why + cards.
    "User A - the spaced self-tester": {
        "q1_recall": "active_recall",
        "q2_spacing": "spaced",
        "q3_session_length": "short_25",
        "q4_chronotype": "morning",
        "q5_blockers": ["procrastination", "overload"],
        "q6_output_formats": ["flashcards", "quizzes"],
        "q7_elaboration": "deep_why",
        "q8_depth": "standard",
    },
    # B: re-reader, crams, long evening sessions, wants concise deep summaries.
    "User B - the deep-dive crammer": {
        "q1_recall": "passive_review",
        "q2_spacing": "massed",
        "q3_session_length": "long_90plus",
        "q4_chronotype": "evening",
        "q5_blockers": ["distraction"],
        "q6_output_formats": ["summaries", "worked_examples"],
        "q7_elaboration": "surface_facts",
        "q8_depth": "in_depth",
        # Non-cognitive UI preference, explicitly overridden here.
        "tone_preference": "warm",
    },
    # C: mixed everything, low confidence, overview only, adds a free-text note.
    "User C - the cautious generalist": {
        "q1_recall": "mixed",
        "q2_spacing": "mixed",
        "q3_session_length": "medium_50",
        "q4_chronotype": "variable",
        "q5_blockers": ["low_self_efficacy"],
        "q6_output_formats": ["quizzes"],
        "q7_elaboration": "mixed",
        "q8_depth": {"value": "overview", "other": "I get lost when there is too much jargon"},
    },
}


def _run(answers: dict):
    """Run one fake user through the whole pipeline."""
    profile = build_profile(answers)
    paragraph, bullets = summarize_profile(profile)
    system_prompt = generate_system_prompt(profile)
    return profile, paragraph, bullets, system_prompt


# --------------------------------------------------------------------------- #
# Pytest assertions: the pipeline runs, and personalization is actually visible.
# --------------------------------------------------------------------------- #
def test_pipeline_runs_for_all_users():
    for answers in FAKE_USERS.values():
        profile, paragraph, bullets, system_prompt = _run(answers)
        assert paragraph.startswith("Based on your answers")
        assert bullets
        for tag in ("<role>", "<user_profile>", "<output_style>", "<forbidden>"):
            assert tag in system_prompt


def test_personalization_is_visible():
    prompts = [_run(a)[3] for a in FAKE_USERS.values()]
    # All three generated prompts must differ from each other.
    assert len(set(prompts)) == len(prompts)


def test_free_text_other_is_preserved():
    profile, _, bullets, prompt = _run(FAKE_USERS["User C - the cautious generalist"])
    assert profile.free_text_notes  # captured, not dropped
    assert any("jargon" in b for b in bullets)  # surfaced to the user
    assert "jargon" in prompt  # carried into the system prompt


def test_guardrails_present_and_identical():
    prompts = [_run(a)[3] for a in FAKE_USERS.values()]
    for prompt in prompts:
        assert "Do not flatter the user" in prompt
        assert "Do not invent facts" in prompt
        assert "insufficient" in prompt
        assert "instruction to you" in prompt


# --------------------------------------------------------------------------- #
# Human-readable side-by-side report.
# --------------------------------------------------------------------------- #
def _print_report() -> None:
    for label, answers in FAKE_USERS.items():
        profile, paragraph, bullets, system_prompt = _run(answers)
        print("=" * 78)
        print(label)
        print("=" * 78)
        print("\n[SUMMARY PARAGRAPH shown to the user]\n")
        print(paragraph)
        print("\n[KEY BULLET POINTS]\n")
        for bullet in bullets:
            print(f"  - {bullet}")
        print("\n[GENERATED SYSTEM PROMPT sent to the downstream agent]\n")
        print(system_prompt)
        print()


if __name__ == "__main__":
    _print_report()
