"""Clicks through the whole app with mocks. Run from the repo root: pytest interface/tests"""
import os
from pathlib import Path

os.environ["STUDY_AGENT_MOCK"] = "1"
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def test_full_flow():
    at = AppTest.from_file(APP, default_timeout=30).run()
    at.button[0].click().run()                      # landing -> questionnaire
    for _ in range(8):                              # answer every question
        at.button[0].click().run()
    assert at.session_state.stage == "profile"
    next(b for b in at.button if b.label.startswith("Looks right")).click().run()
    assert at.session_state.stage == "space"
    at.text_area(key="paste_1").set_value("Cells produce energy in mitochondria.").run()
    next(b for b in at.button if b.label == "Generate study content").click().run()
    assert not at.exception
    assert set(at.session_state.sessions[1]["outputs"]) == {"flashcards", "quiz", "summary"}
