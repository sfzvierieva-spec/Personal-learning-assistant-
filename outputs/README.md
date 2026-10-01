# Example outputs

Real runs of `ingestion_generation.demo` on the same course (Linear Algebra II
problem set, 12-page PDF, ~4.9k tokens, so `single_pass`), with the Gemini
free tier (`gemini-flash-latest`), for two opposite profiles from
`profile_and_prompts/tests/test_end_to_end.py`:

- **User A** (MCQ crammer): dense, definitions only, raw notes, bullet lists.
- **User C** (curious reader): spacious, analogies, friendly tone, paragraphs.

| File | What it shows |
|---|---|
| `summary_linear_algebra_user_A.json` | 5 sections, 30 short bullets (~135 chars each), cheat-sheet style |
| `summary_linear_algebra_user_C.json` | 5 sections, 10 long paragraphs (~620 chars each), explanations with examples and a reflection question |
| `quiz_linear_algebra_user_A.json` / `_C.json` | 5 MCQs each, all valid JSON, `source_hint` with page numbers |

## First observations

- The **summary** shows the personalization clearly: same sections (they follow
  the course plan), but completely different density and tone.
- The **quiz** shows much less difference between A and C: questions and
  explanations are similar and short for both. The quiz format (fixed JSON,
  4 choices) leaves little room for tone. User C's "friendly / analogy"
  preferences are not visible in the explanations → to discuss with Léna
  (prompt iteration) and Hugo (evaluation).
- In the quiz questions we checked, the page numbers in `source_hint` match the PDF
  and the answers are stated in the course. A systematic hallucination check
  is still to be done (evaluation part).
- Free tier: one run failed with a 503 "high demand" error → retry added in
  `llm_client.py`.
