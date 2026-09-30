class ExtractionError(Exception): pass
class GenerationError(Exception): pass

def extract_text(source, filename=None):
    if hasattr(source, "getvalue"):
        return source.getvalue().decode("utf-8", errors="replace")
    raise ExtractionError("stub extractor: only text-like uploads supported here")

def generate_content(course_text, system_prompt, output_format, user_context):
    # Minimal stand-in for David's real generate_content, matching his documented `content` shapes.
    n = (user_context or {}).get("num_items") or 3
    content = {
        "flashcards": {"cards": [{"front": f"Q{i}", "back": f"A{i}", "source_hint": "[Page 1]"} for i in range(1, n+1)]},
        "quiz": {"questions": [{"question": f"Q{i}?", "choices": ["a", "b", "c", "d"], "answer_index": 0,
                                "explanation": "because", "source_hint": "[Page 1]"} for i in range(1, n+1)]},
        "summary": {"sections": [{"heading": "Overview", "points": ["point one", "point two"]}],
                    "key_terms": [{"term": "Term", "definition": "Definition"}]},
        "synthesis_sheet": {"sections": [{"heading": "Overview", "points": ["point"]}], "key_terms": []},
        "revision_plan": {"days": [{"day": 1, "focus": "Basics", "tasks": ["Read", "Quiz"], "duration_minutes": 30}],
                          "advice": "Space it out."},
        "exam_questions": {"questions": [{"question": "Explain X", "type": "open", "model_answer": "Because Y",
                                          "why_likely": "Core concept"}]},
        "mindmap": {"root": {"label": "Course", "children": [{"label": "Topic", "children": []}]}},
        "worked_examples": {"examples": [{"concept": "C", "problem": "P", "steps": ["s1", "s2"], "answer": "42"}]},
    }[output_format]
    return {"format": output_format, "title": "Course", "language": "en", "content": content,
            "meta": {"strategy": "single_pass", "chunks": 1}}
