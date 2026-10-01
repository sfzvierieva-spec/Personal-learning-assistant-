import streamlit as st

from ui import backend, state


def _finish(answers):
    profile = backend.build_profile(answers)
    st.session_state.profile = profile
    st.session_state.summary = backend.summarize_profile(profile)
    st.session_state.system_prompt = backend.generate_system_prompt(profile)
    backend.record("profile", {"answers": answers, "profile": profile})
    state.go("profile")


def render():
    qs = backend.get_questions()
    i = st.session_state.q_index
    _, mid, _ = st.columns([1, 2.4, 1])
    with mid:
        ticks = "".join(f"<i class='{'done' if n < i else ''}'></i>" for n in range(len(qs)))
        st.markdown(f"<div class='fn-ruler'>{ticks}</div><div class='fn-mono'>Question {i + 1} of {len(qs)}</div>",
                    unsafe_allow_html=True)
        q = qs[i]
        with st.container(border=True):
            st.markdown(f"<div class='fn-agent'>YOUR AGENT IS ASKING</div><div class='fn-q'>{q['text']}</div>",
                        unsafe_allow_html=True)
            with st.container(key="options"):
                # Each option is {"label": shown, "value": stored}. The label is
                # the human-readable text; the value is what we send to build_profile.
                # Multi-select questions (q.get("multi_select")) are not yet handled
                # by this single-click flow — see TODO at bottom of file.
                for opt in q["options"]:
                    if st.button(opt["label"], key=f"q{i}_{opt['value']}", use_container_width=True):
                        st.session_state.answers[q["id"]] = opt["value"]
                        st.session_state.q_index += 1
                        if st.session_state.q_index >= len(qs):
                            _finish(st.session_state.answers)
                        st.rerun()
        if st.button("Back", disabled=i == 0):
            st.session_state.q_index -= 1
            st.rerun()
