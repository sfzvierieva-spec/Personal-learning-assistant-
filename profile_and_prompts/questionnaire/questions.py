"""Question bank for the learner-profiling questionnaire.

This module holds the 8 questions of the questionnaire as structured Python
data (no UI, no I/O). Each question maps to a single cognitive-science axis and
carries a short research reference so every item can be defended at the oral
exam. The UI teammate renders this data; the profile builder consumes the
collected answers.

Design decisions (agreed with the module owner):
- 8 questions, one cognitive-science construct each
  (questionnaire-fatigue research: Galesic & Bosnjak 2009).
- Linear order (no adaptive branching in v1).
- Neutral tone: a well-designed research questionnaire, not a chatbot.
- Every question is multiple choice (3-4 options) + an optional free-text
  "Other" field, so users can nuance their answer.

The value strings below are the ONLY contract with the profile builder: they
must stay in sync with the enums in ``profile/schema.py``.

IMPORTANT (evidence base): questions are grounded in cognitive science, NOT in
the discredited "learning styles" / VAK model (Pashler et al. 2008).
"""

from __future__ import annotations

# Bumped whenever the question set changes; stored in every profile's metadata
# so a profile can always be traced back to the exact instrument that produced it.
QUESTIONNAIRE_VERSION = "1.0"


# Each question is a dict with a stable shape so the UI can render it generically:
#   - id             : stable string key (used as the answer key)
#   - axis           : the profile field this question feeds
#   - research_ref   : the cognitive-science concept behind the question
#   - question       : the English text shown to the user (neutral tone)
#   - options        : 3-4 dicts, each {"label": <shown>, "value": <stored>}
#   - multi_select   : True if the user may pick several options (-> list field)
#   - allow_other    : always True; free-text nuance captured as "Other"
#   - rationale      : what the answer tells us about the learner
QUESTIONS: list[dict] = [
    # -------------------------------------------------------------------------
    # Q1 - Retrieval practice (active recall) vs. passive review.
    # research_ref: Roediger & Karpicke (2006), the "testing effect": retrieving
    # information strengthens memory more than re-reading it.
    # rationale: tells us whether to lead with self-testing (flashcards, quizzes)
    # or with review material (summaries) as the primary study format.
    # -------------------------------------------------------------------------
    {
        "id": "q1_recall",
        "axis": "recall_preference",
        "research_ref": "Roediger & Karpicke 2006 (testing effect)",
        "question": (
            "When you want to make sure you have really learned something, "
            "what do you usually do?"
        ),
        "options": [
            {"label": "I test myself (recall it from memory, do practice questions).",
             "value": "active_recall"},
            {"label": "I re-read or review my notes and the material.",
             "value": "passive_review"},
            {"label": "I do both, depending on the subject.",
             "value": "mixed"},
        ],
        "multi_select": False,
        "allow_other": True,
        "rationale": "Chooses whether generated material leads with retrieval "
                     "(self-testing) or with review artifacts.",
    },
    # -------------------------------------------------------------------------
    # Q2 - Spaced practice vs. massed practice (cramming).
    # research_ref: Cepeda et al. (2006) meta-analysis; Ebbinghaus forgetting
    # curve: distributing study over time beats cramming for long-term retention.
    # rationale: tells us whether to package material for spaced review
    # (small sets over days) or as one dense block.
    # -------------------------------------------------------------------------
    {
        "id": "q2_spacing",
        "axis": "spacing_preference",
        "research_ref": "Cepeda et al. 2006; Ebbinghaus (spacing effect)",
        "question": "How do you usually schedule your studying before a deadline?",
        "options": [
            {"label": "A little at a time, spread across several days or weeks.",
             "value": "spaced"},
            {"label": "In one or a few long sessions close to the deadline.",
             "value": "massed"},
            {"label": "It varies a lot depending on the workload.",
             "value": "mixed"},
        ],
        "multi_select": False,
        "allow_other": True,
        "rationale": "Chooses whether material is chunked for spaced repetition "
                     "or delivered as a single dense block.",
    },
    # -------------------------------------------------------------------------
    # Q3 - Sustainable focus span / cognitive load per session.
    # research_ref: Sweller (cognitive load theory); ultradian rhythms: sustained
    # focus degrades over long unbroken sessions.
    # rationale: sizes the chunks of generated material to the user's session
    # length so a single sitting is completable.
    # -------------------------------------------------------------------------
    {
        "id": "q3_session_length",
        "axis": "session_length",
        "research_ref": "Sweller (cognitive load); ultradian focus rhythms",
        "question": "How long can you usually stay focused before you need a real break?",
        "options": [
            {"label": "About 25 minutes or less.", "value": "short_25"},
            {"label": "Around 45-60 minutes.", "value": "medium_50"},
            {"label": "90 minutes or more.", "value": "long_90plus"},
        ],
        "multi_select": False,
        "allow_other": True,
        "rationale": "Sizes each unit of generated material to a completable "
                     "single sitting.",
    },
    # -------------------------------------------------------------------------
    # Q4 - Chronotype / time-of-day performance.
    # research_ref: chronotype research: cognitive performance peaks at different
    # times of day for different people (morning vs. evening types).
    # rationale: lets the downstream agent suggest scheduling and frame the
    # workload for the user's peak window (advisory only).
    # -------------------------------------------------------------------------
    {
        "id": "q4_chronotype",
        "axis": "chronotype",
        "research_ref": "Chronotype / time-of-day performance research",
        "question": "At what time of day do you concentrate best?",
        "options": [
            {"label": "Morning.", "value": "morning"},
            {"label": "Afternoon.", "value": "afternoon"},
            {"label": "Evening or night.", "value": "evening"},
            {"label": "It changes from day to day.", "value": "variable"},
        ],
        "multi_select": False,
        "allow_other": True,
        "rationale": "Advises scheduling and workload framing for the user's "
                     "peak-focus window.",
    },
    # -------------------------------------------------------------------------
    # Q5 - Sources of disengagement / study blockers. MULTI-SELECT.
    # research_ref: task aversiveness & procrastination (Steel 2007); cognitive
    # overload (Sweller); self-efficacy (Bandura 1997).
    # rationale: the downstream agent can pre-empt the user's specific blockers
    # (e.g. smaller steps for overload, quick wins for low self-efficacy).
    # -------------------------------------------------------------------------
    {
        "id": "q5_blockers",
        "axis": "blockers",
        "research_ref": "Steel 2007 (procrastination); Sweller; Bandura 1997 (self-efficacy)",
        "question": (
            "What most often gets in the way of your studying? "
            "(Select all that apply.)"
        ),
        "options": [
            {"label": "I put it off / struggle to get started.",
             "value": "procrastination"},
            {"label": "It feels like too much at once / overwhelming.",
             "value": "overload"},
            {"label": "I get distracted (phone, noise, environment).",
             "value": "distraction"},
            {"label": "I doubt I can do it / lose confidence.",
             "value": "low_self_efficacy"},
        ],
        "multi_select": True,
        "allow_other": True,
        "rationale": "Lets generated material pre-empt the user's specific "
                     "blockers (smaller steps, quick wins, focus cues).",
    },
    # -------------------------------------------------------------------------
    # Q6 - Preferred output formats. MULTI-SELECT.
    # research_ref: dual coding (Paivio) and worked examples (Sweller & Cooper
    # 1985) as effective study formats. NOTE: this is about *material format*,
    # NOT the debunked "learning styles" claim that people have a fixed modality.
    # rationale: directly tells the downstream agent which artifacts to generate.
    # -------------------------------------------------------------------------
    {
        "id": "q6_output_formats",
        "axis": "preferred_output_formats",
        "research_ref": "Paivio (dual coding); Sweller & Cooper 1985 (worked examples)",
        "question": (
            "Which study materials help you the most? (Select all that apply.)"
        ),
        "options": [
            {"label": "Flashcards (question/answer pairs).", "value": "flashcards"},
            {"label": "Summaries and condensed notes.", "value": "summaries"},
            {"label": "Practice quizzes and tests.", "value": "quizzes"},
            {"label": "Worked examples (step-by-step solved problems).",
             "value": "worked_examples"},
        ],
        "multi_select": True,
        "allow_other": True,
        "rationale": "Directly selects which artifacts the downstream agent "
                     "produces for this user.",
    },
    # -------------------------------------------------------------------------
    # Q7 - Elaboration / self-explanation depth ("why" vs. facts).
    # research_ref: Chi et al. (1994), self-explanation effect: explaining *why*
    # and connecting ideas produces deeper understanding than memorizing facts.
    # rationale: tells the agent whether to include causal/"why" explanations and
    # connections, or to stay closer to concise factual statements.
    # -------------------------------------------------------------------------
    {
        "id": "q7_elaboration",
        "axis": "elaboration_preference",
        "research_ref": "Chi et al. 1994 (self-explanation / elaboration)",
        "question": "When you learn something new, what helps it stick best?",
        "options": [
            {"label": "Understanding WHY it works and how it connects to other ideas.",
             "value": "deep_why"},
            {"label": "Having the key facts stated clearly and concisely.",
             "value": "surface_facts"},
            {"label": "A mix of both.", "value": "mixed"},
        ],
        "multi_select": False,
        "allow_other": True,
        "rationale": "Controls whether generated material includes causal 'why' "
                     "explanations and cross-links or stays concise and factual.",
    },
    # -------------------------------------------------------------------------
    # Q8 - Preferred depth / level of detail.
    # research_ref: Sweller (cognitive load theory): the right amount of detail
    # avoids both under-explaining and overloading working memory.
    # rationale: sets the default verbosity/detail of generated material.
    # -------------------------------------------------------------------------
    {
        "id": "q8_depth",
        "axis": "depth_preference",
        "research_ref": "Sweller (cognitive load / level of detail)",
        "question": "How much detail do you usually want when studying a topic?",
        "options": [
            {"label": "A high-level overview of the essentials.", "value": "overview"},
            {"label": "A balanced, standard level of detail.", "value": "standard"},
            {"label": "In-depth coverage, including nuances and edge cases.",
             "value": "in_depth"},
        ],
        "multi_select": False,
        "allow_other": True,
        "rationale": "Sets the default level of detail / verbosity of generated "
                     "material.",
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
