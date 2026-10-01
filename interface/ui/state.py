"""Session-state helpers. Everything the UI remembers lives in st.session_state."""
import copy

import streamlit as st

DEFAULTS = dict(stage="landing", q_index=0, answers={}, profile=None, summary="",
                system_prompt="", profile_note="", sessions={}, active=None, next_id=1)


def init():
    for key, value in DEFAULTS.items():
        st.session_state.setdefault(key, copy.deepcopy(value))


def go(stage: str):
    st.session_state.stage = stage
    st.rerun()


def restart_questionnaire():
    for key in ("q_index", "answers", "profile", "summary", "system_prompt", "profile_note"):
        st.session_state[key] = copy.deepcopy(DEFAULTS[key])
    go("questionnaire")


def add_session(name: str) -> int:
    sid = st.session_state.next_id
    st.session_state.next_id += 1
    from ui.backend import DEFAULT_FORMATS
    st.session_state.sessions[sid] = dict(name=name.strip() or f"Session {sid}", course_text="",
                                          formats=list(DEFAULT_FORMATS),
                                          outputs={}, errors={}, meta={})
    st.session_state.active = sid
    return sid


def current():
    return st.session_state.sessions.get(st.session_state.active)
