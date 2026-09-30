def build_profile(answers):
    return {"answers": answers}

def summarize_profile(profile):
    return "Stub summary: " + ", ".join(profile["answers"].values())
