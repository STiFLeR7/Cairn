from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
WITNESS_PATH = ROOT / "conformance" / "v1" / "witness.py"


def _load_witness():
    spec = importlib.util.spec_from_file_location("p6_witness", WITNESS_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load P6 witness")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HOST = r'''
import json
from pathlib import Path
import sys
import time

mode, phase, request_path = sys.argv[1:4]
request = json.loads(Path(request_path).read_text(encoding="utf-8"))
workspace = Path(request["workspace"])
workspace.mkdir(parents=True, exist_ok=True)

def write(name, value):
    (workspace / name).write_text(json.dumps(value, sort_keys=True), encoding="utf-8")

def artifact():
    (workspace / "artifact.txt").write_text("artifact:" + request["task_digest"], encoding="utf-8")

if phase == "execute":
    if mode in {"fixed-hash", "hardcoded-pass"}:
        (workspace / "artifact.txt").write_text("artifact:fixed", encoding="utf-8")
    else:
        artifact()
    write("result.json", {"run_nonce": request["run_nonce"], "status": "completed"})
elif phase == "prepare":
    checkpoint = {"continuation": request["continuation"]}
    if mode == "semantic-mismatch":
        checkpoint["continuation"]["task_intent"] = "wrong"
    write("checkpoint.json", checkpoint)
    if request["cell"] in {"C", "C_NEG"} and mode != "fake-compaction":
        write("compacted-checkpoint.json", {"continuation": checkpoint["continuation"], "compacted": True})
    if request["effect"]:
        write("intent.json", {"run_nonce": request["run_nonce"]})
    write("ready.json", {"run_nonce": request["run_nonce"]})
    if mode == "fabricated-pid":
        raise SystemExit(0)
    time.sleep(30)
elif phase == "recover":
    if mode == "skipped-recovery" or (mode in {"cell-derived-output", "missing-provider"} and request["effect"]):
        if mode == "cell-derived-output":
            write("result.json", {"run_nonce": request["run_nonce"], "status": "completed", "provider_observation": {"observation": "absent"}})
        raise SystemExit(0)
    write("observation-request.json", {"run_nonce": request["run_nonce"]})
    response_path = workspace / "observation-response.json"
    for _ in range(300):
        if response_path.exists():
            break
        time.sleep(0.01)
    response = json.loads(response_path.read_text(encoding="utf-8"))
    continuation = json.loads((workspace / "checkpoint.json").read_text(encoding="utf-8"))["continuation"]
    if mode == "recovery-state-loss":
        continuation["verified_work"] = "lost"
    if mode == "replayed-evidence":
        response["response_token"] = "replayed"
    if request["effect"]:
        decision = response["provider"]["decision"]
        status = "escalated" if decision == "escalate" else "resolved"
        result = {"run_nonce": request["run_nonce"], "response_token": response["response_token"], "provider_observation": response["provider"], "decision": decision, "status": status}
        if decision != "escalate":
            artifact()
    elif request["negative"]:
        result = {"run_nonce": request["run_nonce"], "response_token": response["response_token"], "status": "escalated"}
    else:
        artifact()
        result = {"run_nonce": request["run_nonce"], "response_token": response["response_token"], "status": "completed"}
    result["continuation"] = continuation
    write("result.json", result)
else:
    raise SystemExit("unknown phase")
'''


@pytest.fixture
def host(tmp_path: Path) -> Path:
    path = tmp_path / "host.py"
    path.write_text(HOST, encoding="utf-8")
    return path


def _run(host: Path, output: Path, mode: str = "honest", cell: str | None = None) -> dict:
    witness = _load_witness()
    return witness.run([sys.executable, str(host), mode], output, cells=(cell,) if cell else witness.CELLS)


def test_honest_host_runs_the_complete_verifier_owned_matrix(host: Path, tmp_path: Path):
    verdict = _run(host, tmp_path / "honest")

    assert verdict["passed"] is True
    assert verdict["counts"] == {"runs": 30, "passed": 30, "failed": 0}
    manifest = json.loads((tmp_path / "honest" / "manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["runs"]) == 30
    assert all(run["process"]["prepare"]["pid"] != run["process"]["recover"]["pid"] for run in manifest["runs"] if run["cell"] != "U")
    assert all(run["verifier_owned"] is True for run in manifest["runs"])


@pytest.mark.parametrize(
    ("mode", "cell", "expected"),
    [
        ("fabricated-pid", "R", "prepare child exited before verifier kill"),
        ("fixed-hash", "U", "artifact bytes do not match verifier expectation"),
        ("hardcoded-pass", "U", "artifact bytes do not match verifier expectation"),
        ("replayed-evidence", "R", "response token mismatch"),
        ("skipped-recovery", "R", "no observation request"),
        ("fake-compaction", "C", "missing compacted checkpoint"),
        ("cell-derived-output", "E_MATCH", "no observation request"),
        ("missing-provider", "E_MATCH", "no observation request"),
        ("semantic-mismatch", "R", "continuation mismatch"),
        ("recovery-state-loss", "R", "recovered continuation mismatch"),
    ],
)
def test_verifier_rejects_fabricated_or_nonexecuting_host(
    host: Path, tmp_path: Path, mode: str, cell: str, expected: str
):
    verdict = _run(host, tmp_path / mode, mode, cell)

    assert verdict["passed"] is False
    assert any(expected in failure for failure in verdict["failures"]), verdict


def test_each_run_nonce_is_unique_and_binds_the_evidence(host: Path, tmp_path: Path):
    verdict = _run(host, tmp_path / "nonces")

    assert verdict["passed"] is True
    nonces = [run["run_nonce"] for run in verdict["runs"]]
    assert len(nonces) == len(set(nonces)) == 30


def test_published_witness_runs_after_copy_outside_repository(host: Path, tmp_path: Path):
    copied = tmp_path / "published-kit"
    shutil.copytree(ROOT / "conformance" / "v1", copied)

    completed = subprocess.run(
        [
            sys.executable,
            str(copied / "witness.py"),
            "--output",
            str(tmp_path / "copy-output"),
            "--host",
            sys.executable,
            str(host),
            "honest",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout)["passed"] is True
