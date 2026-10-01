"""Minimal stand-in for Lena's real builder, matching the shape documented
on main (profile_and_prompts/profile/builder.py)."""


class _ProfileStub:
    """Mimics a pydantic BaseModel enough for the backend/UI code paths that
    treat the profile as an opaque object with attribute access."""

    def __init__(self, answers):
        self._answers = dict(answers)
        # Expose typical real-Profile attributes so caller code doesn't crash.
        self.main_format = _value_of(answers.get("q1_main_format", []))
        self.density = _value_of(answers.get("q2_density"))
        self.explanation_style = _value_of(answers.get("q3_explanation_style"))
        self.struggle = _value_of(answers.get("q4_struggle", []))
        self.study_goal = _value_of(answers.get("q5_study_goal"))
        self.self_testing = _value_of(answers.get("q6_self_testing"))
        self.tone = _value_of(answers.get("q7_tone"))
        self.visual_layout = _value_of(answers.get("q8_visual_layout"))

    def model_dump(self):
        return {"answers": self._answers}


def _value_of(x):
    """Accept raw value, {'value': ...} dict, or list; return a usable value."""
    if isinstance(x, dict):
        return x.get("value")
    return x


def build_profile(answers):
    return _ProfileStub(answers)


def summarize_profile(profile):
    # Real function returns (paragraph, bullets); stub keeps the same shape.
    return ("Stub paragraph for an assembled profile.",
            [f"- stub bullet derived from {k}" for k in profile._answers])
