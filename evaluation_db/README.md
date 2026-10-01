# evaluation_db — Evaluation, Docs & Database (Pole 4)

This folder contains everything related to the SQLite database used by the
Personalized Learning Platform.

## Contents

| File | Role |
|------|------|
| `schema.sql` | The table definitions (single source of truth). |
| `create_database.py` | Creates `learning_platform.db` by executing `schema.sql`. |
| `DATABASE.md` | Full documentation: schema, tables, relationships, design choices. |
| `PROMPT_EVALUATION.md` | Evaluation of the prompts v1 vs v4 and of the personalization (users A vs C), based on the real runs in `outputs/`. |

The failure log of the project is in `docs/failure_log.md`.

## Usage

From the repo root:

```bash
python evaluation_db/create_database.py
```

This creates `evaluation_db/learning_platform.db` (git-ignored). The script is
idempotent: re-running it does not drop existing data.

## Database structure

Four tables:

```text
profiles      the learner Profile (stored as JSON)
courses       uploaded course files
generations   AI-generated study material
feedbacks     user ratings and comments on a generation
```

The `profiles` table stores the `Profile` produced by
`profile_and_prompts/profile/schema.py` serialized with
`Profile.model_dump_json()`; read it back with `Profile.model_validate_json()`.
See `DATABASE.md` for details.

## Technology

- SQLite
- Python (`sqlite3` standard library)
