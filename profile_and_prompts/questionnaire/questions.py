"""Question bank for the learner-profiling questionnaire.

This module holds the 8 questions of the questionnaire as structured Python
data (no UI, no I/O). Each question probes a DIRECT output-shaping decision:
if a question does not visibly change the study material the app produces,
it does not belong here.

Design principles (agreed with the module owner):
- 8 questions (questionnaire-fatigue research: Galesic & Bosnjak 2009).
- Linear order (no adaptive branching in v1).
- Neutral tone: a well-designed research questionnaire, not a chatbot.
- Every question is multiple choice (3-4 options) + an optional free-text
  "Other" field, so users can nuance their answer.
- Every question changes the OUTPUT — format, density, explanation style,
  what the material pre-empts, goal, self-check density, tone, layout.

The value strings below are the ONLY contract with the profile builder: they
must stay in sync with the enums in ``profile/schema.py``.
"""

from __future__ import annotations

# Bumped whenever the question set changes; stored in every profile's metadata
# so a profile can always be traced back to the exact instrument that produced it.
QUESTIONNAIRE_VERSION = "2.0"


# Each question is a dict with a stable shape so the UI can render it generically:
#   - id             : stable string key (used as the answer key)
#   - axis           : the profile field this question feeds
#   - question       : the English text shown to the user (neutral tone)
#   - options        : 3-4 dicts, each {"label": <shown>, "value": <stored>}
#   - multi_select   : True if the user may pick several options (-> list field)
#   - allow_other    : always True; free-text nuance captured as "Other"
#   - rationale      : what concrete output decision this answer drives
QUESTIONS: list[dict] = [
    # -------------------------------------------------------------------------
    # Q1 - Primary output format(s) the learner wants to receive.
    # OUTPUT DECISION: which artifact(s) the downstream agent produces.
    # -------------------------------------------------------------------------
    {
        "id": "q1_main_format",
        "axis": "main_format",
        "question": (
            "What kind of study material do you want to receive most? "
            "(Select all that apply.)"
        ),
        "options": [
            {"label": "A synthesis sheet (the course condensed into structured sections).",
             "value": "synthesis_sheet"},
            {"label": "Flashcards (question / answer pairs).",
             "value": "flashcards"},
            {"label": "A quiz with corrections and explanations.",
             "value": "quiz"},
            {"label": "A mind map (concepts and their links).",
             "value": "mindmap"},
            {"label": "Worked examples (fully solved problems, step by step).",
             "value": "worked_examples"},
            {"label": "A revision plan (study sessions split across several days).",
             "value": "revision_plan"},
            {"label": "Likely exam questions (anticipated questions with answers).",
             "value": "exam_questions"},
        ],
        "multi_select": True,
        "allow_other": True,
        "rationale": "Directly selects which artifact(s) the downstream agent "
                     "produces as the primary output.",
    },
    # -------------------------------------------------------------------------
    # Q2 - Content density.
    # OUTPUT DECISION: how long/aired-out the produced material is.
    # -------------------------------------------------------------------------
    {
        "id": "q2_density",
        "axis": "density",
        "question": "Do you prefer material that is dense, or spacious?",
        "options": [
            {"label": "Dense and concise — get to the point.",
             "value": "dense"},
            {"label": "Balanced — some structure, some breathing room.",
             "value": "balanced"},
            {"label": "Spacious — more breathing room, more examples, easier to skim.",
             "value": "spacious"},
        ],
        "multi_select": False,
        "allow_other": True,
        "rationale": "Sets the length and pacing of the generated material.",
    },
    # -------------------------------------------------------------------------
    # Q3 - How each concept should be explained.
    # OUTPUT DECISION: the shape of every concept explanation.
    # -------------------------------------------------------------------------
    {
        "id": "q3_explanation_style",
        "axis": "explanation_style",
        "question": "When a concept is explained, what helps you most?",
        "options": [
            {"label": "The definition on its own, stated clearly.",
             "value": "definition_only"},
            {"label": "The definition plus a concrete example.",
             "value": "definition_plus_example"},
            {"label": "The definition plus an analogy with something familiar.",
             "value": "definition_plus_analogy"},
            {"label": "A step-by-step logical derivation.",
             "value": "step_by_step"},
        ],
        "multi_select": False,
        "allow_other": True,
        "rationale": "Determines how each concept explanation is structured in "
                     "the generated material.",
    },
    # -------------------------------------------------------------------------
    # Q4 - What tends to lose the learner in a course. MULTI-SELECT.
    # OUTPUT DECISION: which flaw the material actively compensates for.
    # -------------------------------------------------------------------------
    {
        "id": "q4_struggle",
        "axis": "struggle",
        "question": (
            "What tends to lose you in a course? (Select all that apply.)"
        ),
        "options": [
            {"label": "It feels too abstract — I can't picture it.",
             "value": "too_abstract"},
            {"label": "It feels too dense — too much text at once.",
             "value": "too_dense"},
            {"label": "It's hard to remember — I forget quickly.",
             "value": "hard_to_remember"},
            {"label": "It's hard to apply — I understand it but can't use it.",
             "value": "hard_to_apply"},
            {"label": "It's boring — I lose motivation.",
             "value": "boring"},
        ],
        "multi_select": True,
        "allow_other": True,
        "rationale": "Tells the agent which specific weakness to compensate for "
                     "(more examples, denser summarization, mnemonics, exercises, "
                     "hooks).",
    },
    # -------------------------------------------------------------------------
    # Q5 - What the learner is preparing for.
    # OUTPUT DECISION: shape of assessment items produced (MCQ vs essay vs oral).
    # -------------------------------------------------------------------------
    {
        "id": "q5_study_goal",
        "axis": "study_goal",
        "question": "What are you mainly preparing for?",
        "options": [
            {"label": "A multiple-choice / short-answer exam.",
             "value": "mcq_exam"},
            {"label": "A written exam (essays, problem sets).",
             "value": "essay_exam"},
            {"label": "An oral exam / presentation.",
             "value": "oral_exam"},
            {"label": "Practical application (project, code, real task).",
             "value": "practical_application"},
            {"label": "Personal understanding — no specific exam.",
             "value": "personal_understanding"},
        ],
        "multi_select": False,
        "allow_other": True,
        "rationale": "Shapes assessment items: MCQ vs open questions vs speaking "
                     "prompts vs practical exercises.",
    },
    # -------------------------------------------------------------------------
    # Q6 - Balance between reading and self-testing in the material.
    # OUTPUT DECISION: proportion of content vs check questions.
    # -------------------------------------------------------------------------
    {
        "id": "q6_self_testing",
        "axis": "self_testing",
        "question": "What do you want the material to be, mostly?",
        "options": [
            {"label": "Mostly to read — I don't want to be quizzed constantly.",
             "value": "mainly_reading"},
            {"label": "Reading with small check-questions along the way.",
             "value": "reading_with_checks"},
            {"label": "Mostly self-tests — I want to be quizzed as I go.",
             "value": "mainly_testing"},
        ],
        "multi_select": False,
        "allow_other": True,
        "rationale": "Sets the proportion of prose vs. self-check questions in "
                     "the material.",
    },
    # -------------------------------------------------------------------------
    # Q7 - Preferred tone / register of the material.
    # OUTPUT DECISION: the voice / register of the generated text.
    # -------------------------------------------------------------------------
    {
        "id": "q7_tone",
        "axis": "tone",
        "question": "How do you want the material to sound?",
        "options": [
            {"label": "Like a textbook — formal and academic.",
             "value": "textbook"},
            {"label": "Like a teacher explaining out loud — clear and pedagogical.",
             "value": "teacher_voice"},
            {"label": "Like a friend explaining — friendly and vulgarized.",
             "value": "friend_explaining"},
            {"label": "Like raw notes — a dense cheat-sheet, no fluff.",
             "value": "raw_notes"},
        ],
        "multi_select": False,
        "allow_other": True,
        "rationale": "Sets the register / voice of the generated text.",
    },
    # -------------------------------------------------------------------------
    # Q8 - Preferred visual layout of the text.
    # OUTPUT DECISION: the visual structure of the generated document.
    # -------------------------------------------------------------------------
    {
        "id": "q8_visual_layout",
        "axis": "visual_layout",
        "question": "How do you like text to be laid out?",
        "options": [
            {"label": "Structured paragraphs.",
             "value": "structured_paragraphs"},
            {"label": "Bullet lists as much as possible.",
             "value": "bullet_lists"},
            {"label": "Tables when things are comparative.",
             "value": "tables_when_comparative"},
            {"label": "A mix, with ASCII diagrams when useful.",
             "value": "mixed_with_diagrams"},
        ],
        "multi_select": False,
        "allow_other": True,
        "rationale": "Determines the visual structure of the generated document "
                     "(prose vs bullets vs tables vs diagrams).",
    },
]


def get_question(question_id: str) -> dict:
    """Return the question dict with the given id (raises KeyError if unknown)."""
    for question in QUESTIONS:
        if question["id"] == question_id:
            return question
    raise KeyError(f"Unknown question id: {question_id!r}")


def valid_values(question_id: str) -> set[str]:
    """Return the set of allowed option values for a question (excludes 'Other')."""
    return {option["value"] for option in get_question(question_id)["options"]}
