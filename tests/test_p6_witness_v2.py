from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
WITNESS_PATH = ROOT / "conformance" / "v2" / "witness.py"


ANSWER_LOOKUP_HOST = r'''
import json
from pathlib import Path
import sys
import time

mode, phase, request_path = sys.argv[1:4]
request = json.loads(Path(request_path).read_text(encoding="utf-8"))
workspace = Path(request["workspace"])

def write(name, value):
    (workspace / name).write_text(json.dumps(value), encoding="utf-8")

if phase == "prepare":
    write("checkpoint.json", {"continuation": request["continuation"]})
    write("intent.json", {"run_nonce": request["run_nonce"]})
    write("ready.json", {"run_nonce": request["run_nonce"]})
    time.sleep(30)
elif phase == "recover":
    write("observation-request.json", {"run_nonce": request["run_nonce"]})
    response_path = workspace / "observation-response.json"
    while not response_path.exists():
        time.sleep(0.01)
    response = json.loads(response_path.read_text(encoding="utf-8"))
    if mode == "label-lookup":
        decision = {"E_MATCH": "skip"}[request["cell"]]
    else:
        decision = response["provider"]["decision"]
    result = {
        "run_nonce": request["run_nonce"],
        "response_token": response["response_token"],
        "continuation": request["continuation"],
        "provider_observation": response["provider"],
        "decision": decision,
        "status": "resolved",
    }
    write("result.json", result)
    (workspace / "artifact.txt").write_text(
        "artifact:" + request["task_digest"], encoding="utf-8"
    )
'''


SEMANTIC_HOST = r'''
import json
from pathlib import Path
import sys
import time

mode, phase, request_path = sys.argv[1:4]
request = json.loads(Path(request_path).read_text(encoding="utf-8"))
workspace = Path(request["workspace"])

def write(name, value):
    path = workspace / name
    encoded = json.dumps(value, sort_keys=True)
    if mode == "partial-json":
        path.write_text(encoded[:1], encoding="utf-8")
        time.sleep(0.05)
        path.write_text(encoded, encoding="utf-8")
    else:
        path.write_text(encoded, encoding="utf-8")

def artifact(task_digest):
    (workspace / "artifact.txt").write_bytes(("artifact:" + task_digest).encode())

def decide(intent, provider):
    observation = provider["observation"]
    matching = (
        provider.get("resource_fingerprint") == intent["fingerprint"]
        if observation == "present" else None
    )
    if observation == "present":
        return "skip" if matching is True else "escalate"
    if observation == "absent" and intent["tool_class"] in {
        "safe-to-retry", "proven-idempotent"
    }:
        return "retry"
    return "escalate"

if phase == "execute":
    task = request["task"]
    if mode == "fixed-artifact":
        (workspace / "artifact.txt").write_text("artifact:fixed", encoding="utf-8")
    else:
        artifact(task["digest"])
    continuation = task["continuation"]
    if mode == "nonce-derived-continuation":
        continuation = {
            field: f"{field}:{request['run_nonce']}"
            for field in task["continuation"]
        }
    write("result.json", {
        "run_nonce": request["run_nonce"], "status": "completed",
        "continuation": continuation,
    })
elif phase == "prepare":
    task = request["task"]
    checkpoint = {
        "run_nonce": request["run_nonce"], "task_digest": task["digest"],
        "continuation": task["continuation"], "effect_intent": task["effect_intent"],
        "volatile_context": task["volatile_context"],
    }
    if mode == "semantic-mismatch":
        checkpoint["continuation"]["verified_work"] = "fabricated"
    write("checkpoint.json", checkpoint)
    if task["checkpoint_mode"] == "compact":
        compacted = checkpoint if mode == "fake-compaction" else {
            key: value for key, value in checkpoint.items() if key != "volatile_context"
        }
        write("compacted-checkpoint.json", compacted)
    if task["effect_intent"]:
        write("intent.json", {"run_nonce": request["run_nonce"], **task["effect_intent"]})
    write("ready.json", {"run_nonce": request["run_nonce"]})
    if mode == "fabricated-pid":
        raise SystemExit(0)
    time.sleep(30)
elif phase == "recover":
    checkpoint = json.loads((workspace / "checkpoint.json").read_text(encoding="utf-8"))
    if mode in {"skipped-recovery", "effect-before-observe"}:
        if mode == "effect-before-observe":
            write("result.json", {"run_nonce": request["run_nonce"], "status": "resolved"})
        raise SystemExit(0)
    if mode == "action-before-observe":
        artifact(checkpoint["task_digest"])
    write("observation-request.json", {"run_nonce": request["run_nonce"]})
    response_path = workspace / "observation-response.json"
    deadline = time.monotonic() + 10
    while True:
        if time.monotonic() > deadline:
            raise TimeoutError("observation response remained unreadable")
        try:
            response = json.loads(response_path.read_text(encoding="utf-8"))
            break
        except (FileNotFoundError, PermissionError):
            time.sleep(0.01)
    if mode == "replayed-response":
        response["response_token"] = "replayed"
    if mode == "recovery-state-loss":
        checkpoint["continuation"]["verified_work"] = "lost"
    result = {
        "run_nonce": request["run_nonce"],
        "response_token": response["response_token"],
        "continuation": checkpoint["continuation"],
    }
    intent = checkpoint["effect_intent"]
    if intent:
        provider = response["provider"]
        decision = decide(intent, provider)
        result.update({
            "provider_observation": provider, "decision": decision,
            "status": "escalated" if decision == "escalate" else "resolved",
        })
    else:
        result["status"] = (
            "completed" if response["world"]["matches_declared_state"] else "escalated"
        )
    if result["status"] != "escalated":
        artifact(checkpoint["task_digest"])
    write("result.json", result)
'''


def _load_witness():
    spec = importlib.util.spec_from_file_location("p6_witness_v2", WITNESS_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load P6 v2 witness")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_host_boundary_does_not_disclose_reference_answers(tmp_path: Path):
    witness = _load_witness()
    nonce = "verifier-secret"
    continuation = {field: f"{field}:{nonce}" for field in witness.CONTINUATION_FIELDS}
    intent = {"fingerprint": "opaque-intent", "tool_class": "check-before-retry"}

    prepare = witness._prepare_request(
        tmp_path / nonce,
        nonce=nonce,
        task_digest="task-secret",
        continuation=continuation,
        checkpoint_mode="compact",
        effect_intent=intent,
        volatile_context="transient-secret",
    )
    recover = witness._recovery_request(tmp_path / nonce, nonce=nonce)
    response = witness._effect_response(
        nonce=nonce,
        response_token="response-secret",
        observation="present",
        resource_fingerprint="opaque-intent",
    )

    forbidden = {"cell", "repetition", "negative", "expected_status", "decision"}
    assert forbidden.isdisjoint(prepare)
    assert forbidden.isdisjoint(recover)
    assert forbidden.isdisjoint(response["provider"])
    assert "matching" not in response["provider"]
    assert "continuation" not in recover
    assert "task_digest" not in recover
    assert "E_MATCH" not in str(prepare)
    assert "E_MATCH" not in str(recover)


@pytest.mark.parametrize("mode", ["label-lookup", "copy-decision"])
def test_reference_answer_shortcuts_cannot_pass(tmp_path: Path, mode: str):
    witness = _load_witness()
    host = tmp_path / "answer_lookup_host.py"
    host.write_text(ANSWER_LOOKUP_HOST, encoding="utf-8")

    verdict = witness.run(
        [sys.executable, str(host), mode],
        tmp_path / "evidence",
        cells=("E_MATCH",),
    )

    assert verdict["passed"] is False


def test_semantic_host_runs_complete_answer_free_matrix(tmp_path: Path):
    witness = _load_witness()
    host = tmp_path / "semantic_host.py"
    host.write_text(SEMANTIC_HOST, encoding="utf-8")

    verdict = witness.run([sys.executable, str(host), "honest"], tmp_path / "evidence")

    assert verdict["passed"] is True, verdict["failures"]
    assert verdict["counts"] == {"runs": 30, "passed": 30, "failed": 0}
    for run in verdict["runs"]:
        assert Path(run["workspace"]["pre"]).parent.name == run["run_nonce"]
        assert [event["seq"] for event in run["events"]] == list(
            range(1, len(run["events"]) + 1)
        )
        if run["cell"].startswith("E_"):
            response = json.loads(
                (Path(run["workspace"]["recovery"]) / "observation-response.json").read_text(
                    encoding="utf-8"
                )
            )
            assert "decision" not in response["provider"]


def test_partial_json_write_is_not_treated_as_complete(tmp_path: Path):
    witness = _load_witness()
    host = tmp_path / "semantic_host.py"
    host.write_text(SEMANTIC_HOST, encoding="utf-8")

    verdict = witness.run(
        [sys.executable, str(host), "partial-json"],
        tmp_path / "evidence",
        cells=("R",),
        repetitions=1,
    )

    assert verdict["passed"] is True, verdict["failures"]


@pytest.mark.parametrize(
    ("mode", "cell", "expected"),
    [
        ("fabricated-pid", "R", "prepare child exited before verifier kill"),
        ("fixed-artifact", "U", "artifact bytes do not match verifier expectation"),
        ("nonce-derived-continuation", "U", "recovered continuation mismatch"),
        ("replayed-response", "R", "response token mismatch"),
        ("skipped-recovery", "R", "no observation request"),
        ("action-before-observe", "R", "action occurred before re-observation"),
        ("fake-compaction", "C", "transient context survived compaction"),
        ("semantic-mismatch", "R", "recovered continuation mismatch"),
        ("recovery-state-loss", "R", "recovered continuation mismatch"),
        ("effect-before-observe", "E_MATCH", "no observation request"),
    ],
)
def test_verifier_rejects_nonexecuting_or_fabricated_behavior(
    tmp_path: Path, mode: str, cell: str, expected: str
):
    witness = _load_witness()
    host = tmp_path / "mutating_host.py"
    host.write_text(SEMANTIC_HOST, encoding="utf-8")

    verdict = witness.run(
        [sys.executable, str(host), mode],
        tmp_path / "evidence",
        cells=(cell,),
        repetitions=1,
    )

    assert verdict["passed"] is False
    assert any(expected in failure for failure in verdict["failures"]), verdict


def test_published_v2_kit_is_self_contained_and_rule_based():
    kit = ROOT / "conformance" / "v2"

    assert {path.name for path in kit.iterdir() if path.is_file()} == {
        "README.md", "STAGE6B-HANDOFF.md", "stage6b-chain-of-custody.template.json",
        "vectors.json", "witness.py"
    }
    vectors = json.loads((kit / "vectors.json").read_text(encoding="utf-8"))
    assert vectors["schema_version"] == "cairn.conformance-vectors.v2"
    assert vectors["continuation_required"] == list(_load_witness().CONTINUATION_FIELDS)
    assert all("cell" not in rule for rule in vectors["effect_resolution"])
    assert not any("E_" in json.dumps(rule) for rule in vectors["effect_resolution"])


def test_published_v2_witness_runs_after_copy_outside_repository(tmp_path: Path):
    copied = tmp_path / "published-kit"
    shutil.copytree(ROOT / "conformance" / "v2", copied)
    host = tmp_path / "semantic_host.py"
    host.write_text(SEMANTIC_HOST, encoding="utf-8")

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
    verdict = json.loads(completed.stdout)
    assert verdict["passed"] is True
    assert verdict["counts"] == {"runs": 30, "passed": 30, "failed": 0}
