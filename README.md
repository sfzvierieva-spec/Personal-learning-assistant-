# Personalized Study Agent

An AI-powered study companion that reshapes a student's own course material
into revision content adapted to how that student actually learns. The same
course, uploaded by two different users, produces two visibly different
outputs — that is the point of the project.

Bachelor 2 group project · DAT32-91 Prompt Engineering & Git · 60% of the
final grade.

---

## Project

The app runs in six steps:

1. **Questionnaire** — 8 output-shaping questions presented one at a time
   (format, density, explanation style, blockers, study goal, self-testing
   balance, tone, visual layout).
2. **Profile validation** — a short *warm but neutral* summary of the detected
   profile is shown; the user validates or adjusts before continuing.
3. **Course upload** — PDF, DOCX, TXT or MD (long courses are split
   automatically, see *Context window* below).
4. **Format selection** — flashcards, synthesis sheet, quiz, revision plan,
   likely exam questions, mind map or worked examples.
5. **Generation** — the uploaded course is sent to the LLM through a system
   prompt built from the validated profile; the result comes back as
   structured JSON.
6. **Display + export** — results are rendered in the UI with Markdown, PDF,
   JSON and Anki CSV exports.

## Objective

Traditional revision tools treat every student the same. We wanted to make
*personalization visible*: the material the app returns changes **because of
your answers**, not just the content on the first page. The challenge was to
do that in 16 hours of class across 6 sessions.

## Team

| Pole | Member | Owns |
|---|---|---|
| 🧠 Profile & Prompts (the brain) | **Léna** | questionnaire, profile schema, personalized system prompt, 4 prompt iterations (v1→v4) |
| 📄 Ingestion & Generation (the engine) | **David** | file extraction, chunking, LLM calls, output formats |
| 🎨 Interface (the front) | **Sofiia** | Streamlit app: landing, questionnaire flow, profile validation, upload, results, exports |
| 🔬 Database & Docs (the memory) | **Hugo** | SQLite schema (profiles, courses, generations, feedbacks), evaluation reports, documentation |

Every Pull Request is reviewed by someone from a different pole — the course
grading explicitly checks this (25% Git).

## Tools

**Languages:** Python 3.10+, SQL (SQLite).

**Libraries:** pydantic 2 (profile validation), jinja2 (prompt templating),
Streamlit (interface), pytest (tests), fpdf2 (PDF export).

**LLM providers:** Google Gemini (free tier, the one we use) or Anthropic
Claude, selected with `LLM_PROVIDER` in the `.env` file.

**Collaboration:** Git + GitHub, with feature branches per pole and PR
reviews across poles.

**Development assistants:** Claude Code, ChatGPT and Microsoft Copilot were
used as pair-programmers; every AI-generated piece of code was reviewed via
Pull Request before being merged.

## Installation / Access

```bash
# 1. Clone
git clone https://github.com/sfzvierieva-spec/Personal-learning-assistant-.git
cd Personal-learning-assistant-

# 2. Install dependencies
pip install -r requirements.txt
pip install -r ingestion_generation/requirements.txt
pip install -r interface/requirements.txt   # once PR #2 (interface) is merged

# 3. Configure the LLM provider
cat > .env <<EOF
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
EOF
# Alternatively: LLM_PROVIDER=claude and ANTHROPIC_API_KEY=...

# 4. Run the tests
python3 -m pytest profile_and_prompts/tests
python3 -m pytest ingestion_generation/tests
python3 -m pytest interface/tests            # once PR #2 is merged

# 5. Launch the app (once PR #2 is merged)
streamlit run interface/app.py
```

The app opens at `http://localhost:8501`.

## Project Structure

```
Personal-learning-assistant-/
├── README.md
├── requirements.txt
│
├── profile_and_prompts/                # Léna — Pole 1
│   ├── questionnaire/questions.py      # the 8 questions
│   ├── profile/
│   │   ├── schema.py                   # pydantic Profile model (contract)
│   │   └── builder.py                  # build_profile(), summarize_profile()
│   ├── prompt_generator/
│   │   ├── generator.py                # generate_system_prompt()
│   │   └── templates/system_prompt.j2  # jinja2 template
│   ├── prompts/v1→v4.md + CHANGELOG.md # documented prompt iterations
│   └── tests/
│
├── ingestion_generation/               # David — Pole 2
│   ├── extraction.py                   # PDF / DOCX / TXT / MD -> text
│   ├── chunking.py                     # splits long documents into chunks
│   ├── llm_client.py                   # Gemini / Anthropic wrapper
│   ├── generator.py                    # generate_content(), map/reduce for long courses
│   ├── formats.py                      # the 7 structured output schemas
│   └── tests/
│
├── interface/                          # Sofiia — Pole 3
│   ├── app.py                          # Streamlit entry point
│   ├── ui/{screens,components,...}     # UI building blocks
│   └── tests/
│
├── evaluation_db/                      # Hugo — Pole 4
│   ├── schema.sql                      # the 4 tables (profiles, courses,
│   │                                   #   generations, feedbacks)
│   ├── create_database.py              # runs schema.sql into learning_platform.db
│   ├── README.md                       # how to run and inspect the DB
│   └── DATABASE.md                     # schema documentation
│
└── outputs/                            # Real sample outputs (users A and C
                                        # on a 12-page linear-algebra course)
```

**Contract between the modules (`profile_and_prompts` → the rest):**

```python
from profile_and_prompts.questionnaire.questions import QUESTIONS
from profile_and_prompts.profile.builder import build_profile, summarize_profile
from profile_and_prompts.prompt_generator.generator import generate_system_prompt

profile = build_profile(answers)
paragraph, bullets = summarize_profile(profile)   # shown to the user
system_prompt = generate_system_prompt(profile)   # passed to generate_content()
```

## AI Usage

Two very different uses:

- **AI as the product.** The core engine is an LLM: `generate_content()`
  calls Gemini or Anthropic with the system prompt built from the user's
  profile and returns structured JSON (flashcards, quiz items, summary
  sections, etc.).
- **AI as pair-programmer.** Claude Code, ChatGPT and Copilot were used
  throughout development to scaffold modules, review PRs, and iterate on
  prompts. Every piece of AI-generated code was read, tested and reviewed
  through a Pull Request before being merged — the Git history shows this.

## AI Failure Modes Addressed (grading criterion 12)

We address four known LLM failure modes, each mitigated in the code:

| Failure mode | How we address it |
|---|---|
| **Sycophancy** | Explicit `<forbidden>` block in the system prompt forbidding flattery or judgments about the user. The profile summary shown to the user is also template-based (no LLM) so it cannot drift into praise. |
| **Hallucination** | `<forbidden>` block tells the LLM to say *"the source does not contain this information"* explicitly when the course text is insufficient. The generator validates the returned JSON with pydantic and reports under-generation via `meta.warnings` (e.g. *"2 items produced instead of 10 requested"*). |
| **Prompt injection** | `<forbidden>` block states that any text inside the user's uploaded course is **data**, not instructions. The course text is wrapped in an unambiguous delimiter before being sent to the LLM. |
| **Context window** | Documents over ~40k tokens are chunked, summarized per chunk, then recombined (map-reduce). Prevents silent truncation on long courses. |

## Main Challenges

**Resisting the pseudo-science of "learning styles".** Our first draft of the
questionnaire probed VAK-style modalities (visual / auditory /
kinesthetic). We dropped them: the model is scientifically discredited
(Pashler et al., 2008). The questionnaire was rewritten to probe only
decisions that *change the generated output* — format, density, explanation
style, blockers — not personality traits. The commit history on
`lena/profile-and-prompts` shows the v1 → v2 refocus.

**Warmth vs. sycophancy.** The first version of the profile summary read
like a dry receipt — "based on your answers, you prefer X, Y, Z." Users
should feel understood, not acknowledged. We rebuilt the summary to combine
answers into short observations ("you don't trust that just reading is
enough — you want to remake the material yourself"), while still forbidding
compliments or character judgments.

**Quiz personalization gap.** David's first real runs on a 12-page linear
algebra course showed that *summaries* for users A and C were clearly
different, but *quizzes* were almost identical. The next prompt iteration
(v5) specifically targets quiz-shape personalization.

**Mock drift between modules.** Sofiia's `live_stub` of Léna's module was
based on an early contract and had to be re-synced with the real pydantic
Profile shape before merge — a reminder that stub-based parallel development
needs re-syncs to be scheduled.

**Non-standard Git workflow.** One teammate initially pushed files through
the GitHub web UI and onto another member's branch. We corrected this
mid-course to a clean *main → feature branch → PR → cross-pole review →
merge* workflow.

## Final Result

Works today:

- A pipeline from questionnaire → validated profile → generated system
  prompt → LLM call → structured output.
- 4 documented prompt iterations in `profile_and_prompts/prompts/` with a
  CHANGELOG explaining what changed and why between each.
- Real generated outputs committed under `outputs/` (quiz and summary for
  users A and C on a real course).
- A Streamlit UI covering the full user flow (landing, questionnaire,
  profile validation, upload, format selection, results, exports to
  Markdown / PDF / JSON / Anki CSV).
- A SQLite schema storing the Profile as JSON, plus courses, generations
  and feedbacks tables.

What is in progress:

- End-to-end integration (plugging the three live modules together through
  the UI).
- Prompt v5 to improve quiz personalization.
- Hugo's evaluation report comparing v1 vs v4 on the same course.

## Future Improvements

- Persistent user accounts and multi-course history.
- Memory of past sessions to apply spaced repetition over time.
- Letting the user choose the output language (today it follows the course
  language).
- More output formats (audio summary, animated mind map).
- Sharing of generated materials between study partners.
- Cloud deployment (currently local-only).

## License

Academic project — not licensed for redistribution.
