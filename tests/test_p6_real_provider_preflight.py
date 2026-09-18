from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "results" / "phase-6" / "stage-6a-haiku-candidate-7" / "candidate.bundle"
PREFLIGHT = ROOT / "conformance" / "v2" / "stage6a_real_provider.py"


def test_frozen_candidate_7_fails_the_real_provider_preflight(tmp_path: Path):
    candidate = tmp_path / "candidate"
    subprocess.run(["git", "clone", str(BUNDLE), str(candidate)], check=True, capture_output=True)
    output = tmp_path / "preflight"
    completed = subprocess.run(
        [sys.executable, str(PREFLIGHT), "--output", str(output), "--host", sys.executable, str(candidate / "host.py")],
        cwd=ROOT, capture_output=True, text=True,
    )

    assert completed.returncode == 1
    verdict = json.loads((output / "verdict.json").read_text(encoding="utf-8"))
    assert verdict["passed"] is False
    assert verdict["failure"] == "recovery did not produce a result after real provider observation"
    assert verdict["provider"]["observation_before_response"] is True
    assert verdict["provider"]["observation"]["state"] == "present"
    assert verdict["process"]["recover"]["exit_code"] == 1
