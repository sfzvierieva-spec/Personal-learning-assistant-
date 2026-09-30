"""Turn generated content into downloadable files (Markdown, JSON, CSV, PDF)."""
import csv
import io
import json

from ui.backend import FORMATS, KIND


def blocks(fmt, data):
    """Neutral (heading, lines) structure shared by the Markdown and PDF exporters."""
    kind = KIND[fmt]
    if kind == "flashcards":
        return [(f"Card {i}", [f"Q: {c['front']}", f"A: {c['back']}"]) for i, c in enumerate(data["cards"], 1)]
    if kind == "quiz":
        out = []
        for i, q in enumerate(data["questions"], 1):
            lines = [f"- {o}" for o in q["options"]]
            lines.append(f"Answer: {q['options'][q['answer']]}")
            if q.get("explanation"):
                lines.append(q["explanation"])
            out.append((f"{i}. {q['question']}", lines))
        return out
    if kind == "summary":
        return [(s["heading"], [s["body"]]) for s in data["sections"]]
    return [(d["label"], [f"- {t}" for t in d["tasks"]]) for d in data["days"]]


def to_markdown(title, parts):
    out = [f"# {title}", ""]
    for fmt, data in parts:
        out += [f"## {FORMATS[fmt]}", ""]
        for heading, lines in blocks(fmt, data):
            out += [f"### {heading}", *lines, ""]
    return "\n".join(out)


def to_json(parts):
    return json.dumps({fmt: data for fmt, data in parts}, indent=2, ensure_ascii=False)


def flashcards_csv(data):
    """Two columns, no header: imports directly into Anki."""
    buf = io.StringIO()
    csv.writer(buf).writerows([[c["front"], c["back"]] for c in data["cards"]])
    return buf.getvalue()


def _latin(text):  # built-in PDF fonts are Latin-1 only
    return str(text).encode("latin-1", "replace").decode("latin-1")


def to_pdf(title, parts):
    from fpdf import FPDF
    pdf = FPDF()
    pdf.set_auto_page_break(True, 15)
    pdf.add_page()

    def write(text, style="", size=11, gap=6):
        pdf.set_font("Helvetica", style, size)
        pdf.multi_cell(0, gap, _latin(text), new_x="LMARGIN", new_y="NEXT")

    write(title, "B", 20, 10)
    for fmt, data in parts:
        pdf.ln(4)
        write(FORMATS[fmt], "B", 15, 8)
        for heading, lines in blocks(fmt, data):
            pdf.ln(2)
            write(heading, "B", 11)
            for line in lines:
                write(line)
    return bytes(pdf.output())
