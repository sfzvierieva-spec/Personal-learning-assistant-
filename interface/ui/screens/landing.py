import streamlit as st

from ui import state
from ui.components import flashcards


def render():
    st.markdown("<div class='fn-brand'>field<span>note</span></div>", unsafe_allow_html=True)
    left, right = st.columns([1.15, 0.85], gap="large", vertical_alignment="center")
    with left:
        st.markdown("""<div class='fn-hero'><h1>Two students. One textbook. Two different study plans.</h1>
        <p class='fn-sub'>Answer a few questions once. Your agent studies your course the way you
        actually think, not the way a generic app assumes everyone learns.</p></div>""",
                    unsafe_allow_html=True)
        if st.button("Build my study agent", type="primary"):
            state.go("questionnaire")
        st.markdown("<span class='fn-note'>Takes about 4 minutes</span>", unsafe_allow_html=True)
    with right:
        flashcards.render([{"front": "What's the powerhouse of the cell?",
                            "back": "The mitochondria, explained the way you said you learn best."},
                           {"front": "Why does the same course feel different to two people?",
                            "back": "Because your agent is built from how you study, not from the course."}],
                          height=330)
    st.markdown("""<div class='fn-steps'>
      <div><b>Tell it how you study</b><p>A short conversation on focus, habits and blockers builds your agent.</p></div>
      <div><b>Upload your course</b><p>Drop in slides, PDFs or notes for whatever you're learning now.</p></div>
      <div><b>Study your way</b><p>Flashcards, quizzes, summaries and plans shaped around your profile.</p></div>
    </div>""", unsafe_allow_html=True)
