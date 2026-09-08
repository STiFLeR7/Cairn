"""Verifier-owned Phase 6A reference witness; it never imports Cairn."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import secrets
import signal
import shutil
import subprocess
import sys
import time
from typing import Any


CELLS = (
    "U",
    "R",
    "R_NEG",
    "C",
    "C_NEG",
    "E_MATCH",
    "E_ABSENT",
    "E_ESC_UNKNOWN",
    "E_ESC_MISMATCH",
    "E_ESC_NEVER",
)
CONTINUATION_FIELDS = (
    "task_intent",
    "active_subgoal",
    "accepted_decisions",
    "verified_work",
    "verification_state",
    "world_identity",
    "stop_conditions",
    "next_action_boundary",
)
EFFECTS = {
    "E_MATCH": {"observation": "present", "tool_class": "check-before-retry", "matching": True, "decision": "skip"},
    "E_ABSENT": {"observation": "absent", "tool_class": "safe-to-retry", "matching": None, "decision": "retry"},
    "E_ESC_UNKNOWN": {"observation": "unknown", "tool_class": "check-before-retry", "matching": None, "decision": "escalate"},
    "E_ESC_MISMATCH": {"observation": "present", "tool_class": "check-before-retry", "matching": False, "decision": "escalate"},
    "E_ESC_NEVER": {"observation": "absent", "tool_class": "never-retry", "matching": None, "decision": "escalate"},
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} is not an object")
    return value


def _wait_for(path: Path, child: subprocess.Popen[str], timeout: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.is_file():
            return True
        if child.poll() is not None:
            return False
        time.sleep(0.01)
    return path.is_file()


def _finish(child: subprocess.Popen[str]) -> int | None:
    try:
        return child.wait(timeout=4)
    except subprocess.TimeoutExpired:
        child.kill()
        return child.wait(timeout=4)


def _kill_and_confirm(child: subprocess.Popen[str]) -> tuple[bool, int | None]:
    """Kill a live child and confirm the OS-reported termination reason."""
    try:
        child.kill()
    except OSError:
        pass
    exit_code = _finish(child)
    expected = 1 if sys.platform == "win32" else -signal.SIGKILL
    return exit_code == expected, exit_code


def _new_process(command: list[str], phase: str, request: Path) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [*command, phase, str(request)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _continuation(nonce: str) -> dict[str, str]:
    return {field: f"{field}:{nonce}" for field in CONTINUATION_FIELDS}


def _failure(record: dict[str, Any], message: str) -> dict[str, Any]:
    record["passed"] = False
    record.setdefault("failures", []).append(message)
    return record


def _checkpoint(path: Path, expected: dict[str, str], label: str) -> tuple[dict[str, Any] | None, str | None]:
    if not path.is_file():
        return None, f"{label}: missing checkpoint"
    try:
        value = _read_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return None, f"{label}: invalid checkpoint ({error})"
    if value.get("continuation") != expected:
        return None, f"{label}: continuation mismatch"
    return value, None


def _request(
    workspace: Path,
    cell: str,
    repetition: int,
    nonce: str,
    task_digest: str,
    continuation: dict[str, str],
) -> dict[str, Any]:
    return {
        "protocol": "cairn.conformance-witness.v1",
        "workspace": str(workspace),
        "cell": cell,
        "repetition": repetition,
        "run_nonce": nonce,
        "task_digest": task_digest,
        "continuation": continuation,
        "effect": cell in EFFECTS,
        "negative": cell in {"R_NEG", "C_NEG"},
    }


def _expected_status(cell: str) -> str:
    if cell in {"R_NEG", "C_NEG"} or (cell in EFFECTS and EFFECTS[cell]["decision"] == "escalate"):
        return "escalated"
    return "resolved" if cell in EFFECTS else "completed"


def _record_path(output: Path, cell: str, repetition: int) -> Path:
    return output / "runs" / f"{cell.lower()}-{repetition}.json"


def _run_cell(
    command: list[str], output: Path, cell: str, repetition: int, task_digest: str
) -> dict[str, Any]:
    nonce = secrets.token_urlsafe(24)
    root = output / "work" / f"{cell.lower()}-{repetition}-{nonce[:8]}"
    pre = root / "pre"
    recovery = root / "recovery"
    pre.mkdir(parents=True)
    expected = _continuation(nonce)
    record: dict[str, Any] = {
        "cell": cell,
        "repetition": repetition,
        "run_nonce": nonce,
        "task_digest": task_digest,
        "verifier_owned": True,
        "passed": True,
        "failures": [],
        "process": {},
        "workspace": {"pre": str(pre), "recovery": str(recovery), "fresh_recovery": cell != "U"},
    }

    if cell == "U":
        request = _request(pre, cell, repetition, nonce, task_digest, expected)
        request_path = pre / "request.json"
        _write_json(request_path, request)
        child = _new_process(command, "execute", request_path)
        exit_code = _finish(child)
        record["process"]["execute"] = {"pid": child.pid, "exit_code": exit_code}
        return _validate_final(record, pre, cell, nonce, task_digest, None, None)

    prepare_request = _request(pre, cell, repetition, nonce, task_digest, expected)
    prepare_request_path = pre / "request.json"
    _write_json(prepare_request_path, prepare_request)
    prepare = _new_process(command, "prepare", prepare_request_path)
    record["process"]["prepare"] = {"pid": prepare.pid}
    ready = pre / "ready.json"
    if not _wait_for(ready, prepare):
        record["process"]["prepare"]["exit_code"] = _finish(prepare)
        return _failure(record, "prepare child exited before verifier kill")
    try:
        ready_value = _read_json(ready)
    except (OSError, ValueError, json.JSONDecodeError):
        ready_value = {}
    if ready_value.get("run_nonce") != nonce:
        prepare.kill()
        record["process"]["prepare"]["exit_code"] = _finish(prepare)
        return _failure(record, "prepare readiness nonce mismatch")
    _, error = _checkpoint(pre / "checkpoint.json", expected, "prepare")
    if error:
        prepare.kill()
        record["process"]["prepare"]["exit_code"] = _finish(prepare)
        return _failure(record, error)
    source = pre / "checkpoint.json"
    if cell in {"C", "C_NEG"}:
        compacted = pre / "compacted-checkpoint.json"
        _, error = _checkpoint(compacted, expected, "compaction")
        if error:
            prepare.kill()
            record["process"]["prepare"]["exit_code"] = _finish(prepare)
            return _failure(record, error.replace("missing checkpoint", "missing compacted checkpoint"))
        if _sha256(compacted) == _sha256(source):
            prepare.kill()
            record["process"]["prepare"]["exit_code"] = _finish(prepare)
            return _failure(record, "compaction: active state did not change")
        source = compacted
    if cell in EFFECTS:
        try:
            intent = _read_json(pre / "intent.json")
        except (OSError, ValueError, json.JSONDecodeError):
            intent = {}
        if intent.get("run_nonce") != nonce:
            prepare.kill()
            record["process"]["prepare"]["exit_code"] = _finish(prepare)
            return _failure(record, "effect: durable intent missing before crash")
    if prepare.poll() is not None:
        record["process"]["prepare"]["exit_code"] = prepare.returncode
        return _failure(record, "prepare child exited before verifier kill")
    killed, exit_code = _kill_and_confirm(prepare)
    record["process"]["prepare"]["exit_code"] = exit_code
    if not killed:
        return _failure(record, "prepare child exited before verifier kill")
    record["process"]["prepare"]["killed_by_verifier"] = True

    recovery.mkdir(parents=True)
    shutil.copy2(source, recovery / "checkpoint.json")
    recovery_request = _request(recovery, cell, repetition, nonce, task_digest, expected)
    recovery_request_path = recovery / "request.json"
    _write_json(recovery_request_path, recovery_request)
    recover = _new_process(command, "recover", recovery_request_path)
    record["process"]["recover"] = {"pid": recover.pid}
    observation_request = recovery / "observation-request.json"
    if not _wait_for(observation_request, recover):
        record["process"]["recover"]["exit_code"] = _finish(recover)
        return _failure(record, "recovery: no observation request before action")
    try:
        observed_request = _read_json(observation_request)
    except (OSError, ValueError, json.JSONDecodeError):
        observed_request = {}
    if observed_request.get("run_nonce") != nonce:
        recover.kill()
        record["process"]["recover"]["exit_code"] = _finish(recover)
        return _failure(record, "recovery: observation request nonce mismatch")
    response_token = secrets.token_urlsafe(24)
    response: dict[str, Any] = {"run_nonce": nonce, "response_token": response_token}
    if cell in EFFECTS:
        response["provider"] = EFFECTS[cell]
    else:
        response["world"] = {"workspace_fingerprint": _sha256(recovery / "checkpoint.json")}
    response_path = recovery / "observation-response.json"
    _write_json(response_path, response)
    result_path = recovery / "result.json"
    if not _wait_for(result_path, recover):
        record["process"]["recover"]["exit_code"] = _finish(recover)
        return _failure(record, "recovery: result missing after observation")
    record["process"]["recover"]["exit_code"] = _finish(recover)
    if recover.pid == prepare.pid:
        return _failure(record, "recovery: process identity was not fresh")
    return _validate_final(record, recovery, cell, nonce, task_digest, response, expected)


def _validate_final(
    record: dict[str, Any], workspace: Path, cell: str, nonce: str, task_digest: str,
    response: dict[str, Any] | None, expected_continuation: dict[str, str] | None,
) -> dict[str, Any]:
    try:
        result = _read_json(workspace / "result.json")
    except (OSError, ValueError, json.JSONDecodeError):
        return _failure(record, "result: missing or invalid")
    if result.get("run_nonce") != nonce:
        return _failure(record, "result: run nonce mismatch")
    if response is not None and result.get("response_token") != response["response_token"]:
        return _failure(record, "result: response token mismatch")
    if expected_continuation is not None and result.get("continuation") != expected_continuation:
        return _failure(record, "result: recovered continuation mismatch")
    if cell in EFFECTS:
        if result.get("provider_observation") != response["provider"]:
            return _failure(record, "effect: provider observation was not verifier-owned")
        if result.get("decision") != response["provider"]["decision"]:
            return _failure(record, "effect: decision does not reconcile observed provider state")
    if result.get("status") != _expected_status(cell):
        return _failure(record, "result: incorrect termination status")
    artifact = workspace / "artifact.txt"
    allowed = _expected_status(cell) != "escalated"
    if not allowed and artifact.exists():
        return _failure(record, "result: negative/escalation cell performed an unauthorized action")
    if allowed:
        expected_artifact = f"artifact:{task_digest}".encode("utf-8")
        if not artifact.is_file() or artifact.read_bytes() != expected_artifact:
            return _failure(record, "artifact bytes do not match verifier expectation")
        record["artifact_sha256"] = _sha256(artifact)
    record["result_sha256"] = _sha256(workspace / "result.json")
    if response is not None:
        record["observation_request_sha256"] = _sha256(workspace / "observation-request.json")
        record["observation_response_sha256"] = _sha256(workspace / "observation-response.json")
        if cell in EFFECTS:
            record["provider_observed"] = response["provider"]
    return record


def run(command: list[str], output: Path, *, cells: tuple[str, ...] = CELLS) -> dict[str, Any]:
    """Run the complete v1 reference matrix and write verifier-derived evidence."""
    if not command:
        raise ValueError("a host command is required")
    if output.exists() and any(output.iterdir()):
        raise ValueError("output directory must be empty to prevent evidence replay")
    output.mkdir(parents=True, exist_ok=True)
    (output / "runs").mkdir()
    records: list[dict[str, Any]] = []
    for repetition in range(1, 4):
        triplet_digest = secrets.token_hex(32)
        for cell in cells:
            task_digest = triplet_digest if cell in {"U", "R", "C"} else secrets.token_hex(32)
            record = _run_cell(command, output, cell, repetition, task_digest)
            _write_json(_record_path(output, cell, repetition), record)
            records.append(record)
            if not record["passed"]:
                break
        if records and not records[-1]["passed"]:
            break
    for repetition in range(1, 4):
        triplet = [record for record in records if record["repetition"] == repetition and record["cell"] in {"U", "R", "C"}]
        digests = {record.get("artifact_sha256") for record in triplet}
        if len(triplet) == 3 and len(digests) != 1:
            for record in triplet:
                _failure(record, "triplet: U/R/C artifact equivalence failed")
    failures = [failure for record in records for failure in record["failures"]]
    verdict = {
        "schema_version": "cairn.conformance-witness-verdict.v1",
        "passed": not failures,
        "counts": {"runs": len(records), "passed": sum(record["passed"] for record in records), "failed": sum(not record["passed"] for record in records)},
        "failures": failures,
        "runs": records,
    }
    _write_json(output / "manifest.json", verdict)
    return verdict


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--host", nargs=argparse.REMAINDER, required=True)
    args = parser.parse_args(argv)
    try:
        verdict = run(args.host, args.output)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        verdict = {"passed": False, "failures": [str(error)], "counts": {"runs": 0, "passed": 0, "failed": 0}}
        args.output.mkdir(parents=True, exist_ok=True)
        _write_json(args.output / "manifest.json", verdict)
    sys.stdout.write(json.dumps(verdict, indent=2, sort_keys=True) + "\n")
    return 0 if verdict["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
