"""Output formats: what the LLM must return for each type of study material.

For every format we define:
- a pydantic model (used to VALIDATE the LLM answer before it reaches the UI);
- an instruction + a JSON example (shown to the LLM in the prompt).

This file is the contract with the interface: ``generate_content`` returns

    {
      "format": "flashcards",
      "title": "...",
      "language": "fr",
      "content": { ...one of the models below... },
      "meta": {...}
    }
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


# --------------------------------------------------------------------------- #
# Content models (one per format).
# --------------------------------------------------------------------------- #
class Flashcard(BaseModel):
    front: str
    back: str
    source_hint: str = ""        # e.g. "Page 4" — where the card comes from


class Flashcards(BaseModel):
    cards: list[Flashcard] = Field(min_length=1)


class QuizQuestion(BaseModel):
    question: str
    choices: list[str] = Field(min_length=2)
    answer_index: int
    explanation: str
    source_hint: str = ""

    @field_validator("answer_index")
    @classmethod
    def _index_in_range(cls, value: int, info) -> int:
        choices = info.data.get("choices", [])
        if not 0 <= value < len(choices):
            raise ValueError(f"answer_index {value} is not a valid choice index")
        return value


class Quiz(BaseModel):
    questions: list[QuizQuestion] = Field(min_length=1)


class SummarySection(BaseModel):
    heading: str
    points: list[str] = Field(min_length=1)


class KeyTerm(BaseModel):
    term: str
    definition: str


class Summary(BaseModel):
    sections: list[SummarySection] = Field(min_length=1)
    key_terms: list[KeyTerm] = Field(default_factory=list)


class RevisionDay(BaseModel):
    day: int
    focus: str
    tasks: list[str] = Field(min_length=1)
    duration_minutes: int


class RevisionPlan(BaseModel):
    days: list[RevisionDay] = Field(min_length=1)
    advice: str = ""


class ExamQuestion(BaseModel):
    question: str
    type: Literal["open", "mcq", "problem", "definition"]
    model_answer: str
    why_likely: str


class ExamQuestions(BaseModel):
    questions: list[ExamQuestion] = Field(min_length=1)


class MindMapNode(BaseModel):
    label: str
    children: list["MindMapNode"] = Field(default_factory=list)


class MindMap(BaseModel):
    root: MindMapNode


class WorkedExample(BaseModel):
    concept: str
    problem: str
    steps: list[str] = Field(min_length=1)
    answer: str


class WorkedExamples(BaseModel):
    examples: list[WorkedExample] = Field(min_length=1)


# --------------------------------------------------------------------------- #
# Registry: model + instruction + example for each format.
# --------------------------------------------------------------------------- #
FORMATS: dict[str, dict] = {
    "flashcards": {
        "model": Flashcards,
        "default_items": 15,
        "instruction": "Create {n} flashcards. Each card tests ONE idea. The front is a "
                       "question or a term, the back is the short answer.",
        "example": '{"cards": [{"front": "What is X?", "back": "X is ...", "source_hint": "Page 2"}]}',
    },
    "quiz": {
        "model": Quiz,
        "default_items": 10,
        "instruction": "Create a multiple-choice quiz of {n} questions with 4 choices each. "
                       "Wrong choices must be plausible. answer_index is 0-based. The "
                       "explanation says why the right answer is right.",
        "example": '{"questions": [{"question": "...", "choices": ["A", "B", "C", "D"], '
                   '"answer_index": 2, "explanation": "...", "source_hint": "Page 5"}]}',
    },
    "summary": {
        "model": Summary,
        "default_items": None,
        "instruction": "Write a structured summary sheet of the course, organized in "
                       "sections that follow the course plan, plus the key terms.",
        "example": '{"sections": [{"heading": "...", "points": ["...", "..."]}], '
                   '"key_terms": [{"term": "...", "definition": "..."}]}',
    },
    "revision_plan": {
        "model": RevisionPlan,
        "default_items": 7,
        "instruction": "Build a day-by-day revision plan over exactly {n} days covering "
                       "the whole course. Put active recall and practice before the "
                       "last day, and keep the last day for a light review.",
        "example": '{"days": [{"day": 1, "focus": "...", "tasks": ["...", "..."], '
                   '"duration_minutes": 45}], "advice": "..."}',
    },
    "exam_questions": {
        "model": ExamQuestions,
        "default_items": 8,
        "instruction": "List the {n} questions most likely to be asked at the exam on "
                       "this course, with a model answer. why_likely must refer to "
                       "something in the course (emphasis, repetition, a key definition).",
        "example": '{"questions": [{"question": "...", "type": "open", '
                   '"model_answer": "...", "why_likely": "..."}]}',
    },
    "mindmap": {
        "model": MindMap,
        "default_items": None,
        "instruction": "Build a mind map of the course: the root is the course topic, "
                       "then main themes, then sub-ideas. Maximum 3 levels below the "
                       "root, labels of a few words only.",
        "example": '{"root": {"label": "Topic", "children": [{"label": "Theme", '
                   '"children": [{"label": "Idea", "children": []}]}]}}',
    },
    "worked_examples": {
        "model": WorkedExamples,
        "default_items": 4,
        "instruction": "Create {n} worked examples that apply the main concepts of the "
                       "course, solved step by step.",
        "example": '{"examples": [{"concept": "...", "problem": "...", '
                   '"steps": ["...", "..."], "answer": "..."}]}',
    },
}

# Names used in Léna's profile (MainFormat) that map to one of ours.
ALIASES = {"synthesis_sheet": "summary"}

SUPPORTED_FORMATS = sorted(FORMATS)


def resolve_format(output_format: str) -> str:
    """Return the canonical format name, or raise ValueError."""
    name = ALIASES.get(output_format, output_format)
    if name not in FORMATS:
        raise ValueError(
            f"Unknown output format '{output_format}'. Supported: {', '.join(SUPPORTED_FORMATS)}"
        )
    return name
