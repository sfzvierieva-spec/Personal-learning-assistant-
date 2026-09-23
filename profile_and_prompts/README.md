# Profile & Prompts module

Part 1 of the personalized study-agent project: profiles a learner via a short
questionnaire, turns the answers into a structured JSON profile, and generates a
personalized system prompt for the downstream generation agent.

_Full documentation is written in step 4 (deliverables report)._

## Pipeline

```
questionnaire answers
      -> build_profile()        -> Profile (validated JSON)
      -> summarize_profile()    -> warm-but-neutral summary  [user validates]
      -> generate_system_prompt() -> system prompt string     [-> downstream agent]
```

## Module boundaries

- No UI here (Streamlit/HTML is a teammate's job). This module is pure,
  importable logic.
- The downstream generation agent (flashcards/quizzes) is a separate module;
  we only produce the system prompt it receives.
- The contract between modules is the `Profile` JSON and the system prompt
  string.

_Status: skeleton. Modules are filled in step by step (3.1 -> 3.6)._
