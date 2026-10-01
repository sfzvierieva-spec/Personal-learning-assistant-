"""The ONLY file that talks to the other three poles.

Real modules are used when they import cleanly with the expected names; otherwise mocks keep
the UI demoable. Force mocks with:  STUDY_AGENT_MOCK=1

Contracts (as found in the open PRs):

  profile_and_prompts (Lena)   -> profile.builder.build_profile / summarize_profile,
                                  prompt_generator.generator.generate_system_prompt,
                                  questionnaire.questions  (question format still to confirm)
  ingestion_generation (David) -> extract_text(source, filename=None) -> str
                                  generate_content(course_text, system_prompt, output_format,
                                  user_context) -> {format, title, language, content, meta}
                                  raises ExtractionError / GenerationError
  evaluation_db (Hugo)         -> record(kind, payload)   (proposal, not merged yet)

David's JSON shapes are converted to the UI's internal shapes in normalize() below,
so screens and exporters only ever see one shape per kind.
"""
import importlib
import io
import json
import os

MOCK = os.getenv("STUDY_AGENT_MOCK") == "1"

# output_format -> (label, kind). The UI renders by kind; several formats share the summary layout.
FORMATS = {"flashcards": "Flashcards", "quiz": "Quiz", "summary": "Summary sheet",
           "revision_plan": "Revision plan", "exam_questions": "Likely exam questions",
           "worked_examples": "Worked examples", "mindmap": "Mind map (outline)"}
KIND = {"flashcards": "flashcards", "quiz": "quiz", "summary": "summary", "revision_plan": "revision_plan",
        "exam_questions": "summary", "worked_examples": "summary", "mindmap": "summary"}
FORMAT_KEY = {"flashcards": "cards", "quiz": "questions", "summary": "sections", "revision_plan": "days"}
DEFAULT_FORMATS = ["flashcards", "quiz", "summary"]
CONTEXT_KEYS = {"num_items", "difficulty", "focus", "exam_date", "days_available", "minutes_per_day"}


def _resolve(module, attr=None):
    if MOCK:
        return None
    try:
        mod = importlib.import_module(module)
        return getattr(mod, attr) if attr else mod
    except (ImportError, AttributeError):
        return None


_ig = _resolve("ingestion_generation")
if _ig is not None and not hasattr(_ig, "generate_content"):
    _ig = None
_db = _resolve("evaluation_db")
_build = _resolve("profile_and_prompts.profile.builder", "build_profile")
_summarize = _resolve("profile_and_prompts.profile.builder", "summarize_profile")
_sysprompt = _resolve("profile_and_prompts.prompt_generator.generator", "generate_system_prompt")
_raw_questions = _resolve("profile_and_prompts.questionnaire.questions", "QUESTIONS")


def _normalize_questions(raw):
    """Turn Lena's question objects into [{"id","text","options","multi_select"}].

    Lena's real shape (now on main):
      {"id": str, "axis": str, "question": str,
       "options": [{"label": str, "value": str}, ...],
       "multi_select": bool, "allow_other": True, ...}

    We keep the option dicts intact so screens can show `opt["label"]` to the
    user and store `opt["value"]` as the answer that `build_profile` expects.
    Returns None if the shape doesn't match.
    """
    try:
        return [{"id": q["id"],
                 "text": q["question"],
                 "options": [{"label": o["label"], "value": o["value"]} for o in q["options"]],
                 "multi_select": q.get("multi_select", False)}
                for q in raw]
    except (TypeError, KeyError):
        return None


_questions = _normalize_questions(_raw_questions) if _raw_questions else None
# Profile pole is only "live" if every piece (incl. questions) is usable; mixing real and
# placeholder pieces would feed the wrong answer format to build_profile().
PROFILE_LIVE = all([_build, _summarize, _sysprompt, _questions])
LIVE = {"profile_and_prompts": PROFILE_LIVE, "ingestion_generation": _ig is not None,
        "evaluation_db": _db is not None}

# ---------------------------------------------------------------- profile (Lena)
_PLACEHOLDER_QUESTIONS = [
    ("input", "When you need to remember something, what do you reach for first?",
     ["A diagram or picture", "Saying it out loud", "Writing it by hand", "Testing myself"]),
    ("focus", "How long can you focus before your brain asks for a break?",
     ["About 15 minutes", "25 minutes", "45 minutes", "It depends on the day"]),
    ("structure", "How do you like new material to be organised?",
     ["Big picture first, details later", "Step by step, in order", "Through examples", "Through questions"]),
    ("pace", "How do you prefer to pace a study week?",
     ["A little every day", "Long sessions, fewer days", "Mostly the last week", "No fixed pattern"]),
    ("testing", "How do you feel about being quizzed?",
     ["Love it, it shows gaps", "Fine, if it's low-pressure", "Stressful", "Only right before exams"]),
    ("environment", "What usually derails a session?",
     ["My phone", "Not knowing where to start", "Boredom", "Doubting what I know"]),
    ("motivation", "What keeps you going?",
     ["Seeing progress", "Deadlines", "Curiosity", "Not falling behind others"]),
    ("blocker", "What's hardest for you?",
     ["Starting", "Stopping", "Staying consistent", "Trusting that I know it"]),
]


def get_questions():
    """Return questions in the uniform shape used by screens.

    Each option is always a {"label", "value"} dict so screens render the
    label and store the value. In mock mode (no real Lena module), label and
    value are the same string.
    """
    if PROFILE_LIVE:
        return _questions
    return [{"id": i, "text": t,
             "options": [{"label": o, "value": o} for o in opts],
             "multi_select": False}
            for i, t, opts in _PLACEHOLDER_QUESTIONS]


def build_profile(answers):
    if PROFILE_LIVE:
        return _build(answers)
    return {"answers": answers}


def summarize_profile(profile):
    if PROFILE_LIVE:
        return _summarize(profile)
    lines = [f"- {v}" for v in profile["answers"].values()]
    return "Placeholder summary (Lena's module not connected). You told us:\n" + "\n".join(lines)


def generate_system_prompt(profile):
    if PROFILE_LIVE:
        return _sysprompt(profile)
    return "You are a study assistant. Adapt to this learner: " + json.dumps(profile["answers"])


# ------------------------------------------------------------ ingestion (David)
def extract_text(uploaded_file):
    """Accepts a Streamlit UploadedFile (David's extract_text takes it directly)."""
    if _ig:
        return _ig.extract_text(uploaded_file)
    name, data = uploaded_file.name.lower(), uploaded_file.getvalue()
    if name.endswith(".pdf"):
        from pypdf import PdfReader
        return "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(data)).pages)
    if name.endswith(".docx"):
        import docx
        return "\n".join(p.text for p in docx.Document(io.BytesIO(data)).paragraphs)
    return data.decode("utf-8", errors="replace")


def _bullets(items):
    return "\n".join(f"- {i}" for i in items)


def _mind(node, depth=0):
    lines = ["  " * depth + "- " + node["label"]]
    for child in node.get("children", []):
        lines += _mind(child, depth + 1)
    return lines


def _src(text, item):
    hint = item.get("source_hint")
    return f"{text} ({hint})" if hint else text


def normalize(fmt, c):
    """David's `content` -> the UI's internal shape for this kind."""
    kind = KIND[fmt]
    if kind == "flashcards":
        return {"cards": [{"front": x["front"], "back": _src(x["back"], x)} for x in c["cards"]]}
    if kind == "quiz":
        return {"questions": [{"question": q["question"], "options": q["choices"], "answer": q["answer_index"],
                               "explanation": _src(q.get("explanation", ""), q)} for q in c["questions"]]}
    if kind == "revision_plan":
        days = []
        for d in c["days"]:
            label = f"Day {d['day']}" if str(d["day"]).isdigit() else str(d["day"])
            tasks = list(d["tasks"]) + ([f"About {d['duration_minutes']} min"] if d.get("duration_minutes") else [])
            days.append({"label": f"{label}: {d['focus']}" if d.get("focus") else label, "tasks": tasks})
        if c.get("advice"):
            days.append({"label": "Advice", "tasks": [c["advice"]]})
        return {"days": days}
    if fmt == "exam_questions":
        return {"sections": [{"heading": q["question"], "body": f"{q['model_answer']}\n\n*Why it's likely:* "
                              f"{q['why_likely']}"} for q in c["questions"]]}
    if fmt == "worked_examples":
        return {"sections": [{"heading": e["concept"], "body": f"**Problem:** {e['problem']}\n\n"
                              + "\n".join(f"{n}. {s}" for n, s in enumerate(e["steps"], 1))
                              + f"\n\n**Answer:** {e['answer']}"} for e in c["examples"]]}
    if fmt == "mindmap":
        root = c["root"]
        return {"sections": [{"heading": root["label"], "body": "\n".join(
            line for ch in root.get("children", []) for line in _mind(ch))}]}
    sections = [{"heading": s["heading"], "body": _bullets(s["points"])} for s in c["sections"]]
    if c.get("key_terms"):
        sections.append({"heading": "Key terms", "body": _bullets(
            f"**{t['term']}**: {t['definition']}" for t in c["key_terms"])})
    return {"sections": sections}


def validate(fmt, data):
    """Parse and sanity-check output so the UI never crashes on a bad generation."""
    kind = KIND[fmt]
    if isinstance(data, str):
        data = json.loads(data.strip().removeprefix("```json").removesuffix("```").strip())
    items = data.get(FORMAT_KEY[kind])
    if not isinstance(items, list) or not items:
        raise ValueError(f"missing or empty '{FORMAT_KEY[kind]}' list")
    for it in items:
        if kind == "flashcards" and not {"front", "back"} <= it.keys():
            raise ValueError("a flashcard lacks front/back")
        if kind == "quiz" and not (it.get("options") and isinstance(it.get("answer"), int)
                                   and 0 <= it["answer"] < len(it["options"])):
            raise ValueError("a quiz question has no valid options/answer index")
    return data


def _mock(fmt, name):
    kind = KIND[fmt]
    if kind == "flashcards":
        return {"cards": [{"front": f"Key idea #{i} of {name}?", "back": f"Placeholder answer {i}."}
                          for i in range(1, 6)]}
    if kind == "quiz":
        return {"questions": [{"question": f"Sample question {i} about {name}?",
                               "options": ["Option A", "Option B", "Option C"], "answer": i % 3,
                               "explanation": "Placeholder explanation."} for i in range(1, 4)]}
    if kind == "summary":
        return {"sections": [{"heading": f"Section {i}", "body": "- Placeholder point\n- Another point"}
                             for i in range(1, 4)]}
    return {"days": [{"label": f"Day {i}", "tasks": ["Review notes", "Do 10 practice questions"]}
                     for i in range(1, 5)]}


def generate(fmt, course_text, system_prompt, user_context=None, session_name="your course"):
    """-> (data, None, meta) on success, (None, message, {}) on failure."""
    ctx = {k: v for k, v in (user_context or {}).items() if k in CONTEXT_KEYS and v not in (None, "")}
    try:
        if _ig:
            result = _ig.generate_content(course_text, system_prompt, fmt, ctx)
            return validate(fmt, normalize(fmt, result["content"])), None, result.get("meta", {})
        return validate(fmt, _mock(fmt, session_name)), None, {}
    except Exception as exc:  # ExtractionError / GenerationError / bad shape: show it, don't crash
        return None, f"{type(exc).__name__}: {exc}", {}


# ----------------------------------------------------------------- database (Hugo)
LOG = []  # in-memory fallback, visible in tests


def record(kind, payload):
    LOG.append((kind, payload))
    if _db and hasattr(_db, "record"):
        try:
            _db.record(kind, payload)
        except Exception:
            pass  # logging must never break the app
