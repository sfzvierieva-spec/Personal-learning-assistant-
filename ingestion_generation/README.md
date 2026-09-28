# Ingestion & Generation module

Part 2 of the personalized study agent (owner: David). Reads the uploaded
course, sends it to the LLM together with the personalized system prompt from
`profile_and_prompts`, and returns structured study material as JSON ready to
display.

## Pipeline

```
uploaded file (PDF / DOCX / TXT / MD)
   -> extract_text()                    clean text, PDF pages marked [Page N]
   -> generate_content(course_text, system_prompt, output_format, user_context)
        short course -> 1 call with the full course            ("single_pass")
        long course  -> chunks -> notes per chunk -> 1 call    ("map_reduce")
        -> parse JSON -> validate (pydantic) -> 1 retry if invalid
   -> {format, title, language, content, meta}
```

## Usage (for the interface)

```python
from profile_and_prompts.prompt_generator.generator import generate_system_prompt
from ingestion_generation import extract_text, generate_content

course_text = extract_text(uploaded_file)          # Streamlit UploadedFile works directly
result = generate_content(
    course_text,
    system_prompt=generate_system_prompt(profile),
    output_format="quiz",
    user_context={"num_items": 10, "difficulty": "hard"},
)
```

Errors to catch and show to the user: `ExtractionError` (bad or empty file)
and `GenerationError` (API problem, invalid answer, course too long).

### `output_format`

| Format | `content` shape |
|---|---|
| `flashcards` | `{"cards": [{"front", "back", "source_hint"}]}` |
| `quiz` | `{"questions": [{"question", "choices": [4], "answer_index", "explanation", "source_hint"}]}` |
| `summary` (alias `synthesis_sheet`) | `{"sections": [{"heading", "points": []}], "key_terms": [{"term", "definition"}]}` |
| `revision_plan` | `{"days": [{"day", "focus", "tasks": [], "duration_minutes"}], "advice"}` |
| `exam_questions` | `{"questions": [{"question", "type", "model_answer", "why_likely"}]}` |
| `mindmap` | `{"root": {"label", "children": [ ...same node... ]}}` |
| `worked_examples` | `{"examples": [{"concept", "problem", "steps": [], "answer"}]}` |

The exact models are in [`formats.py`](formats.py).

### `user_context` (all keys optional)

| Key | Used for | Example |
|---|---|---|
| `num_items` | number of cards / questions / examples (max 50) | `15` |
| `difficulty` | all formats | `"hard"` |
| `focus` | chapter or topic to emphasize | `"chapter 3"` |
| `exam_date` | revision plan: number of days until the exam | `"2026-12-15"` |
| `days_available` | revision plan: overrides `exam_date` | `10` |
| `minutes_per_day` | revision plan | `45` |

Learning preferences (tone, density, study goal…) are **not** passed here: they
are already inside the system prompt built from the profile.

### `meta`

`strategy`, `chunks`, `input_tokens_estimate`, `model`, `retried`,
`user_context` (after cleaning) and `warnings` (e.g. fewer items than
requested). Useful for the evaluation / database part.

## Design choices

- **The system prompt is used as-is.** All the personalization comes from
  Léna's prompt; this module only adds a user message with the task, the JSON
  shape and the course. That keeps a clear boundary between the two modules.
- **Context-window limit → map/reduce.** Courses above ~40k tokens (estimated
  as characters / 4) are split into ~8k-token chunks on paragraph boundaries,
  with a small overlap. Each chunk is turned into faithful notes by a neutral,
  non-personalized prompt, and only the final call is personalized. If the
  notes are still too long, they are condensed again (max 3 rounds). The limit
  is deliberately lower than the model's context window: very long inputs cost
  more and the middle of a long input tends to be covered less well.
- **Hallucination.** The prompt asks to use only the course, to produce fewer
  items rather than invent, and to cite `[Page N]` in `source_hint` so an
  answer can be checked against the PDF. Revision-plan dates are computed in
  Python, not by the model.
- **Prompt injection.** The course is wrapped in `<course_material>` tags and
  the prompt says it is data, not instructions (Léna's system prompt says the
  same).
- **Invalid JSON.** The answer is parsed (markdown fences tolerated) and
  validated with pydantic, e.g. a quiz `answer_index` must point to an
  existing choice. If it fails, the model gets its own answer back with the
  error and one chance to fix it.
- **Testable without API key.** `generate_content` accepts an `llm` function;
  the tests use a fake one.

## Run

```bash
pip install -r ingestion_generation/requirements.txt
pytest ingestion_generation/tests
```

Real call on a course file, for two different profiles (`ANTHROPIC_API_KEY`
must be set, e.g. in a `.env` file at the root, which is git-ignored):

```bash
python -m ingestion_generation.demo my_course.pdf --format quiz --user A
python -m ingestion_generation.demo my_course.pdf --format quiz --user C
```

The model defaults to `claude-opus-5` and can be changed with the
`STUDY_AGENT_MODEL` environment variable.

## AI usage

Claude (Anthropic) was used as a coding assistant to draft this module and its
tests; the code was then run, tested and reviewed by me. Claude is also the
model called at runtime to generate the study material.

## Limits / next steps

- Scanned PDFs (images only) give no text: OCR would be needed.
- Token counts are estimated; the API's token-counting endpoint would be exact.
- Map/reduce calls run one after the other; they could run in parallel.
- The API's structured-output mode could replace the parse-and-retry step.
