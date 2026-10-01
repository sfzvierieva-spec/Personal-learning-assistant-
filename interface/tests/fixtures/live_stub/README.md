Minimal stand-ins for `profile_and_prompts` and `ingestion_generation`, matching the function
names and JSON shapes documented in their real PRs. Used only by `test_backend_live.py` so the
interface/backend integration can be checked before those PRs are merged. Not real logic — do
not use as a reference for how those modules should work internally, only for their public shape.
