"""End-to-end pipeline test with three contrasting fake users.

Runs each fake user through the full pipeline:

    questionnaire answers -> build_profile -> summarize_profile
                          -> generate_system_prompt

and prints the outputs side by side so the personalization is visibly
different across profiles.

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
    # A: MCQ crammer — wants flashcards + quiz, mainly testing, cheat-sheet
    # style, dense, definitions only, bullet lists.
    "User A - the MCQ crammer": {
        "q1_main_format": ["flashcards", "quiz"],
        "q2_density": "dense",
        "q3_explanation_style": "definition_only",
        "q4_struggle": ["hard_to_remember"],
        "q5_study_goal": "mcq_exam",
        "q6_self_testing": "mainly_testing",
        "q7_tone": "raw_notes",
        "q8_visual_layout": "bullet_lists",
    },
    # B: Practical applier — worked examples, step-by-step, teacher voice,
    # struggles with application.
    "User B - the practical applier": {
        "q1_main_format": ["worked_examples", "synthesis_sheet"],
        "q2_density": "balanced",
        "q3_explanation_style": "step_by_step",
        "q4_struggle": ["hard_to_apply", "too_abstract"],
        "q5_study_goal": "practical_application",
        "q6_self_testing": "reading_with_checks",
        "q7_tone": "teacher_voice",
        "q8_visual_layout": "mixed_with_diagrams",
    },
    # C: Curious reader — synthesis + mindmap, spacious, friend-explaining,
    # personal understanding, adds a free-text nuance.
    "User C - the curious reader": {
        "q1_main_format": ["synthesis_sheet", "mindmap"],
        "q2_density": "spacious",
        "q3_explanation_style": "definition_plus_analogy",
        "q4_struggle": ["too_abstract", "boring"],
        "q5_study_goal": "personal_understanding",
        "q6_self_testing": "mainly_reading",
        "q7_tone": "friend_explaining",
        "q8_visual_layout": {"value": "structured_paragraphs",
                             "other": "I get lost when there is too much jargon"},
    },
}


def _run(answers: dict):
    """Run one fake user through the whole pipeline."""
    profile = build_profile(answers)
    paragraph, bullets = summarize_profile(profile)
    system_prompt = generate_system_prompt(profile)
    return profile, paragraph, bullets, system_prompt


# --------------------------------------------------------------------------- #
# Pytest assertions.
# --------------------------------------------------------------------------- #
def test_pipeline_runs_for_all_users():
    for answers in FAKE_USERS.values():
        profile, paragraph, bullets, system_prompt = _run(answers)
        assert paragraph.startswith("Here's what I'm reading from your answers")
        assert bullets
        for tag in ("<role>", "<user_profile>", "<output_style>", "<forbidden>"):
            assert tag in system_prompt


def test_personalization_is_visible():
    prompts = [_run(a)[3] for a in FAKE_USERS.values()]
    assert len(set(prompts)) == len(prompts)


def test_free_text_other_is_preserved():
    profile, _, bullets, prompt = _run(FAKE_USERS["User C - the curious reader"])
    assert profile.free_text_notes
    assert any("jargon" in b for b in bullets)
    assert "jargon" in prompt


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
