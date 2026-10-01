# Prompt CHANGELOG

This folder documents four iterations of the personalized system prompt. Each
`.md` file is a **complete, standalone** prompt (not a diff); this changelog
explains what changed between versions and why, in prompt-engineering terms.

All four target the same task — generating study material from a learner's own
course, adapted to their profile — so the differences are purely about prompt
technique, not about the use case.

---

## v1 — Initial prompt (zero-shot, minimal)

A single unstructured paragraph. It is **zero-shot** (no examples) and has no
sections, no explicit output format, and no guardrails. It states the task and a
few profile facts in prose and hopes the model does the right thing. This is the
naive baseline: it works for easy cases but gives the model no reliable structure
to follow and no protection against bad behaviour.

## v2 — Structured prompt (sectioning + format constraints)

Introduces **structure**: the prompt is split into XML-style sections
(`<role>`, `<user_profile>`, `<output_style>`) so the model can locate each kind
of information reliably, and the `<output_style>` block turns vague wishes into
explicit, checkable constraints (formats to produce, question-first ordering,
unit size, tone). Sectioning also makes the prompt machine-parseable and easier
to generate programmatically. Still no examples and no guardrails.

## v3 — Few-shot prompt (examples added)

Adds an `<examples>` section with a few **few-shot** demonstrations. The examples
pin down the exact output format (question-first flashcards) and, crucially, show
the desired *behaviour* on a hard case — answering "the source does not contain
this information" instead of guessing. Demonstrations steer models more reliably
than instructions alone, so this version is the first that reliably refuses to
fabricate. The anti-fabrication rule is still only *shown*, not *stated*.

## v4 — Final prompt (structure + few-shot + guardrails)

Adds an explicit `<forbidden>` section that **states** the guardrails the earlier
versions only implied. It directly targets the two failure modes the module must
defend at the oral: **sycophancy** (no flattery or character judgments) and
**hallucination** (no invented facts; say so when the source is insufficient). It
also adds a **prompt-injection** guardrail — text inside the uploaded course is
data, never an instruction to the agent. Combining structure + few-shot +
explicit guardrails, v4 is the version the generator reproduces automatically
from any profile.
