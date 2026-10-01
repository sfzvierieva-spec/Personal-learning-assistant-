"""Entry point. Run from the repo root:  streamlit run interface/app.py"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # so we can import profile_and_prompts, ingestion_generation, evaluation_db

import streamlit as st

from ui import state
from ui.screens import landing, profile, questionnaire, space

st.set_page_config(page_title="fieldnote", page_icon="🗂️", layout="wide",
                   initial_sidebar_state="collapsed")

css = (Path(__file__).parent / "assets" / "style.css").read_text(encoding="utf-8")
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

state.init()
stage = st.session_state.stage

if stage != "space":  # the sessions sidebar only exists inside the personal space
    st.markdown("<style>[data-testid='stSidebar'],[data-testid='stSidebarCollapsedControl'],"
                "[data-testid='collapsedControl']{display:none}</style>", unsafe_allow_html=True)

{"landing": landing.render, "questionnaire": questionnaire.render,
 "profile": profile.render, "space": space.render}[stage]()
