"""Smoke test for examples/byom_recovery.py — the CI-run, offline, mock-model path.

Loads the example by file path (examples/ is not an importable package) and asserts each
deterministic demo's outcome. The optional Ollama path is never exercised here (no network in CI).
"""

import importlib.util
import os

_EX = os.path.join(os.path.dirname(__file__), "..", "examples", "byom_recovery.py")
_spec = importlib.util.spec_from_file_location("byom_recovery", _EX)
byom = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(byom)


def test_primitives_demo_regrounds_and_finishes(tmp_path):
    out = byom.demo_primitives(str(tmp_path))
    assert out["regrounded"] == 1               # step 0 re-grounded from the cairn
    assert out["new_steps"] == 1                 # only the un-done step redone (not a cold restart of 2)
    assert out["files"] == ["a.txt", "b.txt"]    # the task got finished


def test_agent_demo_resumes_with_recovery_tax_one(tmp_path):
    out = byom.demo_agent(str(tmp_path))
    assert out["resumed"] is True                # took the recover() path
    assert out["recovery_tax"] == 1             # only one new step after resume
    assert out["finished"] is True
    assert out["files"] == ["a.txt", "b.txt"]


def test_effect_demo_is_exactly_once(tmp_path):
    out = byom.demo_effect_once(str(tmp_path))
    assert out["resolutions"] == [("send-1", "skip")]   # verify saw it done -> not re-executed
    assert out["outbox_lines_before"] == 1
    assert out["outbox_lines_after"] == 1               # no duplicate effect (claim C3)
