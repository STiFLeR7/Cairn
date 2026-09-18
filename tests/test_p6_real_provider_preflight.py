from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "results" / "phase-6" / "stage-6a-haiku-candidate-7" / "candidate.bundle"
PREFLIGHT = ROOT / "conformance" / "v2" / "stage6a_real_provider.py"


PROVIDER_ENVELOPE_HOST = r'''
import json
from pathlib import Path
import sys
import time


def write(path, value):
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


phase, request_path = sys.argv[1:]
request = json.loads(Path(request_path).read_text(encoding="utf-8"))
workspace = Path(request["workspace"])
if phase == "prepare":
    task = request["task"]
    checkpoint = {
        "run_nonce": request["run_nonce"],
        "task_digest": task["digest"],
        "continuation": task["continuation"],
        "effect_intent": task["effect_intent"],
        "volatile_context": task["volatile_context"],
    }
    write(workspace / "checkpoint.json", checkpoint)
    write(workspace / "intent.json", {
        "run_nonce": request["run_nonce"],
        "fingerprint": task["effect_intent"]["fingerprint"],
        "tool_class": task["effect_intent"]["tool_class"],
    })
    write(workspace / "ready.json", {"run_nonce": request["run_nonce"]})
    while True:
        time.sleep(0.1)

checkpoint = json.loads((workspace / "checkpoint.json").read_text(encoding="utf-8"))
write(workspace / "observation-request.json", {"run_nonce": request["run_nonce"]})
response_path = workspace / "observation-response.json"
deadline = time.monotonic() + 10
while not response_path.is_file() and time.monotonic() < deadline:
    time.sleep(0.01)
response = json.loads(response_path.read_text(encoding="utf-8"))
provider = response["provider"]
intent = checkpoint["effect_intent"]
state = provider["state"]
matching = state == "present" and provider["request_fingerprint"] == intent["fingerprint"]
decision = "skip" if matching else "escalate"
write(workspace / "result.json", {
    "run_nonce": request["run_nonce"],
    "continuation": checkpoint["continuation"],
    "response_token": response["response_token"],
    "provider_observation": provider,
    "decision": decision,
    "status": "resolved" if decision != "escalate" else "escalated",
})
'''


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


def test_real_provider_preflight_exposes_a_ledger_grounded_observation_to_fresh_recovery(tmp_path: Path):
    host = tmp_path / "host.py"
    host.write_text(PROVIDER_ENVELOPE_HOST, encoding="utf-8")
    output = tmp_path / "preflight"

    completed = subprocess.run(
        [sys.executable, str(PREFLIGHT), "--output", str(output), "--host", sys.executable, str(host)],
        cwd=ROOT, capture_output=True, text=True,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    verdict = json.loads((output / "verdict.json").read_text(encoding="utf-8"))
    assert verdict["passed"] is True
    observed = verdict["provider"]["observation"]
    result = json.loads((output / "recovery" / "result.json").read_text(encoding="utf-8"))
    candidate_observation = result["provider_observation"]
    assert candidate_observation["state"] == candidate_observation["observation"] == "present"
    assert candidate_observation["resource_id"] == observed["resource_id"]
    assert candidate_observation["request_fingerprint"] == observed["request_fingerprint"]
    assert candidate_observation["resource_fingerprint"] == observed["request_fingerprint"]
    assert candidate_observation["idempotency_key"] == observed["idempotency_key"]
    assert candidate_observation["receipt_id"]
    ledger = json.loads((output / "provider-ledger" / "provider-ledger.json").read_text(encoding="utf-8"))
    assert ledger["resources"][observed["idempotency_key"]]["create_count"] == 1
