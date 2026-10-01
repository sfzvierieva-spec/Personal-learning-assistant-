"""Renderers for each output format, plus the export and feedback row under each."""
import streamlit as st

from ui import backend, exporters
from ui.components import flashcards


def _quiz(data, key):
    score = 0
    for i, q in enumerate(data["questions"]):
        picked = st.radio(f"{i + 1}. {q['question']}", q["options"], index=None, key=f"{key}_q{i}")
        if picked is None:
            continue
        if q["options"].index(picked) == q["answer"]:
            score += 1
            st.success("Correct. " + q.get("explanation", ""))
        else:
            st.error(f"Not quite. Answer: {q['options'][q['answer']]}. " + q.get("explanation", ""))
    st.caption(f"Score so far: {score} / {len(data['questions'])}")


def _summary(data):
    if data.get("title"):
        st.subheader(data["title"])
    for s in data["sections"]:
        st.markdown(f"**{s['heading']}**")
        st.write(s["body"])


def _plan(data):
    html = "".join(f"<div class='d'>{d['label']}</div>" + "".join(f"<div>{t}</div>" for t in d["tasks"])
                   for d in data["days"])
    st.markdown(f"<div class='fn-plan'>{html}</div>", unsafe_allow_html=True)


def _export_row(fmt, data, title, key):
    parts = [(fmt, data)]
    cols = st.columns(4)
    cols[0].download_button("Markdown", exporters.to_markdown(title, parts), f"{key}.md", key=f"{key}_md")
    cols[1].download_button("PDF", exporters.to_pdf(title, parts), f"{key}.pdf", key=f"{key}_pdf")
    cols[2].download_button("JSON", exporters.to_json(parts), f"{key}.json", key=f"{key}_json")
    if backend.KIND[fmt] == "flashcards":
        cols[3].download_button("Anki CSV", exporters.flashcards_csv(data), f"{key}.csv", key=f"{key}_csv")


def _feedback_row(fmt, key, session_name):
    a, b, _ = st.columns([1, 1.3, 4])
    for col, label, verdict in ((a, "Useful", "useful"), (b, "Flag an error", "inaccurate")):
        if col.button(label, key=f"{key}_{verdict}"):
            backend.record("feedback", {"session": session_name, "format": fmt, "verdict": verdict})
            st.toast("Thanks, noted." if verdict == "useful" else "Flagged for review.")


def render(fmt, data, session_name, key):
    kind = backend.KIND[fmt]
    if kind == "flashcards":
        flashcards.render(data["cards"])
    elif kind == "quiz":
        _quiz(data, key)
    elif kind == "summary":
        _summary(data)
    else:
        _plan(data)
    st.divider()
    _export_row(fmt, data, f"{session_name}: {backend.FORMATS[fmt]}", key)
    _feedback_row(fmt, key, session_name)
