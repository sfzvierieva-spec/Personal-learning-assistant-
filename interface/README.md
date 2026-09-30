# interface/ : The Front (Sofiia)

Streamlit app: landing, conversational questionnaire, profile validation, personal space
(sessions sidebar, upload, results, exports).

```bash
pip install -r interface/requirements.txt
streamlit run interface/app.py                    # from the repo root
STUDY_AGENT_MOCK=1 streamlit run interface/app.py  # force mocks (demo without other poles)
pytest interface/tests                             # click-through smoke test
```

## How it plugs into the other poles
Everything goes through `interface/ui/backend.py`. A module is used live only once every piece
it needs resolves cleanly (see `LIVE` / `PROFILE_LIVE` in that file); otherwise a mock stands in,
so the UI stays demoable at every stage. Force mocks regardless with `STUDY_AGENT_MOCK=1`.

This is wired against what's actually in the two open PRs as of Sep 29:

| Pole | Module (PR) | The UI calls |
|---|---|---|
| Léna | `profile_and_prompts` (`lena/profile-and-prompts`, folded into PR #1) | `profile.builder.build_profile`, `.summarize_profile`; `prompt_generator.generator.generate_system_prompt`; `questionnaire.questions.QUESTIONS` |
| David | `ingestion_generation` (PR #1, `David/Ingestion-&-Generation`) | `extract_text(source, filename=None)`, `generate_content(course_text, system_prompt, output_format, user_context)` |
| Hugo | `evaluation_db` | not opened yet — `backend.record(kind, payload)` is called for `profile`, `course`, `generation`, `feedback` and currently just logs in-memory |

**One open question for Léna:** `questionnaire/questions.py` wasn't in the diff yet, so
`backend._normalize_questions()` assumes each question is `{"id", "text", "options"}`. If her real
shape differs, that's the one function to adjust — everything downstream (answers dict, profile
building) already matches her `build_profile` signature.

David's `generate_content` returns `{format, title, language, content, meta}` with a `content`
shape that's different per `output_format` (7 formats, see his README). `backend.normalize()`
converts each of those into one of four shapes the UI actually renders:
- `flashcards`: `{"cards": [{"front", "back"}]}`
- `quiz`: `{"questions": [{"question", "options": [..], "answer": <index>, "explanation"}]}`
- `summary` (also used for `exam_questions`, `worked_examples`, `mindmap`): `{"sections": [{"heading", "body"}]}`
- `revision_plan`: `{"days": [{"label", "tasks": [..]}]}`

`backend.validate()` then sanity-checks that shape; a malformed generation shows a warning
instead of crashing, and is logged with `ok=false` (plus David's `meta`, e.g. chunking strategy
and warnings) for Hugo's failure-mode tracking once his module exists.

### Trying it against the real modules
The two PRs aren't merged yet, so `profile_and_prompts/` and `ingestion_generation/` aren't on
`main`. To try the interface against them before that happens: checkout `David/Ingestion-&-Generation`
(it already contains Léna's commits), copy or symlink both packages next to `interface/` at the
repo root, then run normally (no `STUDY_AGENT_MOCK`). `interface/tests/test_backend_live.py` does
exactly this against lightweight stand-ins, as a template for that check.

## Layout
`app.py` (router) · `ui/screens/` (one file per screen) · `ui/components/` (flashcards, results) ·
`ui/exporters.py` (Markdown, PDF, JSON, Anki CSV) · `assets/style.css` (design tokens).
