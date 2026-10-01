import streamlit as st

from ui import state


def render():
    _, mid, _ = st.columns([1, 2.4, 1])
    with mid:
        st.markdown("<div class='fn-agent'>YOUR PROFILE</div>", unsafe_allow_html=True)
        st.header("Here's how your agent sees you")
        with st.container(border=True):
            st.write(st.session_state.summary)
        st.caption("Read this critically. Your agent is only as useful as this description is accurate, "
                   "so correct anything that doesn't sound like you.")
        note = st.text_area("Anything wrong or missing? (optional)", value=st.session_state.profile_note,
                            placeholder="e.g. I focus better in the morning than this suggests.")
        with st.expander("See the system prompt built from your answers"):
            st.code(st.session_state.system_prompt, language="text", wrap_lines=True)
        a, b, _ = st.columns([1.4, 1.4, 2])
        if a.button("Looks right, continue", type="primary"):
            st.session_state.profile_note = note
            if not st.session_state.sessions:
                state.add_session("My first course")
            state.go("space")
        if b.button("Retake the questions"):
            state.restart_questionnaire()
