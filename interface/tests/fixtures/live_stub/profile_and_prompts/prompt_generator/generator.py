"""Minimal stand-in for Lena's real generate_system_prompt.

The real function takes a Profile object (pydantic BaseModel) and returns a
string. This stub keeps the same signature.
"""


def generate_system_prompt(profile):
    return "Stub system prompt for an assembled profile: " + str(profile.model_dump())
