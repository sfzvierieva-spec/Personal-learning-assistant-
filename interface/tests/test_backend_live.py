"""Exercises normalize()/validate() against David's real output_format contract.

Uses local stubs under tests/fixtures/live_stub/ for both poles so the test
does not need network access or LLM credentials. The stubs now mirror the
REAL function names and data shapes merged into main (Lena's questions carry
`question`/`axis`/`multi_select` + options as `{"label","value"}` dicts).

Runs in a subprocess (not simple imports) so unsetting STUDY_AGENT_MOCK here
can't leak into test_smoke.py, which relies on it being set at the
pytest-process level.
"""
import os
import subprocess
import sys
from pathlib import Path

INTERFACE_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = INTERFACE_ROOT / "tests" / "fixtures" / "live_stub"

_SCRIPT = """
import sys
sys.path.insert(0, {interface!r})
sys.path.insert(0, {fixtures!r})
from ui import backend

assert backend.LIVE == {{"profile_and_prompts": True, "ingestion_generation": True,
                         "evaluation_db": False}}, backend.LIVE

for fmt in backend.FORMATS:
    data, err, meta = backend.generate(fmt, "course text", "sys prompt", {{"num_items": 3}}, "Demo")
    assert err is None, (fmt, err)
    assert data, fmt
    assert meta.get("strategy") == "single_pass", meta

qs = backend.get_questions()
answers = {{q["id"]: q["options"][0] for q in qs}}
profile = backend.build_profile(answers)
assert backend.summarize_profile(profile)
assert backend.generate_system_prompt(profile)
print("OK")
""".format(interface=str(INTERFACE_ROOT), fixtures=str(FIXTURES))


def test_live_modules_integrate_cleanly():
    # test_smoke.py sets STUDY_AGENT_MOCK=1 at collection time for the whole pytest process;
    # force it off for this subprocess only, so backend.py actually tries the real imports.
    env = {k: v for k, v in os.environ.items() if k != "STUDY_AGENT_MOCK"}
    result = subprocess.run([sys.executable, "-c", _SCRIPT], capture_output=True, text=True, env=env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK" in result.stdout
