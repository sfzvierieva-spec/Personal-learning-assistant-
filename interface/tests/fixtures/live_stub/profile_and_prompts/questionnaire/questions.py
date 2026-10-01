"""Minimal stand-in for Lena's real QUESTIONS list, matching the shape
documented on main (profile_and_prompts/questionnaire/questions.py).

Each question has: id, axis, question (NOT 'text'), options as a list of
{"label","value"} dicts, multi_select (bool), allow_other (bool).
"""

QUESTIONS = [
    {
        "id": "q1_main_format",
        "axis": "main_format",
        "question": "What kind of study material do you want to receive most?",
        "options": [
            {"label": "Flashcards.", "value": "flashcards"},
            {"label": "A quiz.", "value": "quiz"},
            {"label": "A synthesis sheet.", "value": "synthesis_sheet"},
        ],
        "multi_select": True,
        "allow_other": True,
    },
    {
        "id": "q2_density",
        "axis": "density",
        "question": "Do you prefer dense material or spacious material?",
        "options": [
            {"label": "Dense and concise.", "value": "dense"},
            {"label": "Balanced.", "value": "balanced"},
            {"label": "Spacious.", "value": "spacious"},
        ],
        "multi_select": False,
        "allow_other": True,
    },
]
