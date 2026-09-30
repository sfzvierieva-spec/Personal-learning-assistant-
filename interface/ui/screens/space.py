import streamlit as st

from ui import backend, state
from ui.components import results


def _sidebar():
    with st.sidebar:
        st.markdown("<div class='fn-brand' style='margin-bottom:1rem'>field<span>note</span></div>",
                    unsafe_allow_html=True)
        st.markdown("<div class='fn-mono'>SESSIONS</div>", unsafe_allow_html=True)
        for sid, s in st.session_state.sessions.items():
            ready = "●" if s["outputs"] else "○"
            if st.button(f"{ready}  {s['name']}", key=f"tab_{sid}", use_container_width=True,
                         type="primary" if sid == st.session_state.active else "secondary"):
                st.session_state.active = sid
                st.rerun()
        with st.form("new_session", clear_on_submit=True, border=False):
            name = st.text_input("New session", placeholder="Subject or course name",
                                 label_visibility="collapsed")
            if st.form_submit_button("+ New session", use_container_width=True):
                state.add_session(name)
                st.rerun()
        st.caption("● has study content   ○ needs materials")
        if st.button("Edit my profile", use_container_width=True):
            state.go("profile")


def _materials(sid, s):
    files = st.file_uploader("Course files (PDF, DOCX, TXT, MD)", type=["pdf", "docx", "txt", "md"],
                             accept_multiple_files=True, key=f"up_{sid}")
    pasted = st.text_area("Or paste your notes", height=130, key=f"paste_{sid}")
    s["formats"] = st.multiselect("What do you want from it?", list(backend.FORMATS),
                                  default=s["formats"], format_func=backend.FORMATS.get, key=f"fmt_{sid}")
    with st.expander("Fine-tune the request (optional)"):
        c1, c2 = st.columns(2)
        num_items = c1.number_input("Items per format", min_value=3, max_value=50, value=10, key=f"n_{sid}")
        exam_date = c2.date_input("Exam date (for the revision plan)", value=None, key=f"exam_{sid}")

    extracted, bad = [], []
    for f in files:
        try:
            extracted.append(backend.extract_text(f))
        except Exception as exc:
            bad.append(f"{f.name}: {exc}")
    for msg in bad:
        st.warning(f"Couldn't read {msg}")
    text = "\n\n".join(extracted + [pasted]).strip()
    if text:
        st.caption(f"{len(text.split()):,} words ready")

    if st.button("Generate study content", type="primary", disabled=not (text and s["formats"]),
                 key=f"gen_{sid}"):
        s["course_text"], s["outputs"], s["errors"], s["meta"] = text, {}, {}, {}
        ctx = {"num_items": num_items, "exam_date": str(exam_date) if exam_date else None}
        backend.record("course", {"session": s["name"], "words": len(text.split())})
        for fmt in s["formats"]:
            with st.spinner(f"Building {backend.FORMATS[fmt].lower()}…"):
                data, err, meta = backend.generate(fmt, text, st.session_state.system_prompt, ctx, s["name"])
            if data:
                s["outputs"][fmt], s["meta"][fmt] = data, meta
            else:
                s["errors"][fmt] = err
            backend.record("generation", {"session": s["name"], "format": fmt, "ok": data is not None,
                                          "error": err, "meta": meta})
        st.rerun()


def _results(sid, s):
    if not s["outputs"] and not s["errors"]:
        st.markdown("<div class='fn-empty'>Nothing here yet. Add materials in the first tab and "
                    "generate your study content.</div>", unsafe_allow_html=True)
        return
    for fmt, err in s["errors"].items():
        st.warning(f"{backend.FORMATS[fmt]} couldn't be built ({err}). Try generating again.")
    if s["outputs"]:
        tabs = st.tabs([backend.FORMATS[f] for f in s["outputs"]])
        for tab, (fmt, data) in zip(tabs, s["outputs"].items()):
            with tab:
                meta = s["meta"].get(fmt, {})
                if meta.get("strategy") == "map_reduce":
                    st.caption(f"Long course: processed in {meta.get('chunks', '?')} chunks, then combined.")
                for w in meta.get("warnings", []):
                    st.caption(f"⚠ {w}")
                results.render(fmt, data, s["name"], f"s{sid}_{fmt}")
        with st.expander("How your agent shaped this"):
            st.write(st.session_state.summary)


def render():
    _sidebar()
    s = state.current()
    if s is None:
        st.markdown("<div class='fn-empty'>Create your first session in the sidebar.</div>",
                    unsafe_allow_html=True)
        return
    sid = st.session_state.active
    st.title(s["name"])
    t1, t2 = st.tabs(["Materials", "Study content"])
    with t1:
        _materials(sid, s)
    with t2:
        _results(sid, s)
