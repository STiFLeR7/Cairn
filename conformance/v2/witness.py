"""Verifier-owned Phase 6A witness with answer-free host inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import time
from typing import Any


CELLS = (
    "U", "R", "R_NEG", "C", "C_NEG", "E_MATCH", "E_ABSENT",
    "E_ESC_UNKNOWN", "E_ESC_MISMATCH", "E_ESC_NEVER",
)
CONTINUATION_FIELDS = (
    "task_intent", "active_subgoal", "accepted_decisions", "verified_work",
    "verification_state", "world_identity", "stop_conditions", "next_action_boundary",
)
EFFECT_FACTS = {
    "E_MATCH": {"tool_class": "check-before-retry", "observation": "present", "matching": True},
    "E_ABSENT": {"tool_class": "safe-to-retry", "observation": "absent", "matching": None},
    "E_ESC_UNKNOWN": {"tool_class": "check-before-retry", "observation": "unknown", "matching": None},
    "E_ESC_MISMATCH": {"tool_class": "check-before-retry", "observation": "present", "matching": False},
    "E_ESC_NEVER": {"tool_class": "never-retry", "observation": "absent", "matching": None},
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> None:
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


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


def _new_process(command: list[str], phase: str, request: Path) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [*command, phase, str(request)], stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )


def _continuation(nonce: str) -> dict[str, str]:
    return {field: f"{field}:{nonce}" for field in CONTINUATION_FIELDS}


def _prepare_request(
    workspace: Path, *, nonce: str, task_digest: str,
    continuation: dict[str, str], checkpoint_mode: str,
    effect_intent: dict[str, Any] | None, volatile_context: str,
) -> dict[str, Any]:
    return {
        "protocol": "cairn.conformance-witness.v2", "workspace": str(workspace),
        "run_nonce": nonce,
        "task": {
            "digest": task_digest, "continuation": continuation,
            "checkpoint_mode": checkpoint_mode, "effect_intent": effect_intent,
            "volatile_context": volatile_context,
        },
    }


def _recovery_request(workspace: Path, *, nonce: str) -> dict[str, str]:
    return {
        "protocol": "cairn.conformance-witness.v2",
        "workspace": str(workspace), "run_nonce": nonce,
    }


def _effect_response(
    *, nonce: str, response_token: str, observation: str,
    resource_fingerprint: str | None,
) -> dict[str, Any]:
    return {
        "run_nonce": nonce, "response_token": response_token,
        "provider": {
            "observation": observation,
            "resource_fingerprint": resource_fingerprint,
        },
    }


def _world_response(
    *, nonce: str, response_token: str, fingerprint: str, matches: bool,
) -> dict[str, Any]:
    return {
        "run_nonce": nonce, "response_token": response_token,
        "world": {"workspace_fingerprint": fingerprint, "matches_declared_state": matches},
    }


def _failure(record: dict[str, Any], message: str) -> dict[str, Any]:
    record["passed"] = False
    record.setdefault("failures", []).append(message)
    return record


def _event(record: dict[str, Any], kind: str, **facts: Any) -> None:
    record.setdefault("events", []).append({
        "seq": len(record.get("events", [])) + 1,
        "kind": kind, "time_ns": time.time_ns(), **facts,
    })


def _checkpoint(
    path: Path, *, continuation: dict[str, str], nonce: str, task_digest: str,
    effect_intent: dict[str, Any] | None, volatile_context: str, compacted: bool,
) -> tuple[dict[str, Any] | None, str | None]:
    if not path.is_file():
        return None, f"{path.name}: missing checkpoint"
    try:
        value = _read_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return None, f"{path.name}: invalid checkpoint ({error})"
    expected = {
        "continuation": continuation, "run_nonce": nonce,
        "task_digest": task_digest, "effect_intent": effect_intent,
    }
    for key, wanted in expected.items():
        if value.get(key) != wanted:
            return None, f"{path.name}: recovered {key} mismatch"
    if compacted and "volatile_context" in value:
        return None, "compaction: transient context survived compaction"
    if not compacted and value.get("volatile_context") != volatile_context:
        return None, "checkpoint: volatile context missing before compaction"
    return value, None


def _effect_decision(tool_class: str, observation: str, matching: bool | None) -> str:
    if observation == "present":
        return "skip" if matching is True else "escalate"
    if observation == "absent" and tool_class in {"safe-to-retry", "proven-idempotent"}:
        return "retry"
    return "escalate"


def _expected_status(cell: str) -> str:
    if cell in {"R_NEG", "C_NEG"}:
        return "escalated"
    if cell in EFFECT_FACTS:
        facts = EFFECT_FACTS[cell]
        decision = _effect_decision(
            str(facts["tool_class"]), str(facts["observation"]), facts["matching"]
        )
        return "escalated" if decision == "escalate" else "resolved"
    return "completed"


def _validate_final(
    record: dict[str, Any], workspace: Path, *, cell: str, nonce: str,
    task_digest: str, continuation: dict[str, str],
    response: dict[str, Any] | None, effect_intent: dict[str, Any] | None,
) -> dict[str, Any]:
    try:
        result = _read_json(workspace / "result.json")
    except (OSError, ValueError, json.JSONDecodeError):
        return _failure(record, "result: missing or invalid")
    if result.get("run_nonce") != nonce:
        return _failure(record, "result: run nonce mismatch")
    if result.get("continuation") != continuation:
        return _failure(record, "result: recovered continuation mismatch")
    if response is not None and result.get("response_token") != response["response_token"]:
        return _failure(record, "result: response token mismatch")
    if effect_intent:
        provider = response["provider"]
        if result.get("provider_observation") != provider:
            return _failure(record, "effect: provider observation was not verifier-owned")
        observation = str(provider["observation"])
        matching = (
            provider.get("resource_fingerprint") == effect_intent["fingerprint"]
            if observation == "present"
            else None
        )
        expected_decision = _effect_decision(
            str(effect_intent["tool_class"]), observation, matching
        )
        if result.get("decision") != expected_decision:
            return _failure(record, "effect: incorrect reconciliation of observed provider state")
    expected_status = _expected_status(cell)
    if result.get("status") != expected_status:
        return _failure(record, "result: incorrect termination status")
    artifact = workspace / "artifact.txt"
    allowed = expected_status != "escalated"
    if not allowed and artifact.exists():
        return _failure(record, "result: negative/escalation cell performed an unauthorized action")
    if allowed:
        expected_artifact = f"artifact:{task_digest}".encode()
        if not artifact.is_file() or artifact.read_bytes() != expected_artifact:
            return _failure(record, "artifact bytes do not match verifier expectation")
        record["artifact_sha256"] = _sha256(artifact)
    record["result_sha256"] = _sha256(workspace / "result.json")
    if response is not None:
        record["observation_request_sha256"] = _sha256(workspace / "observation-request.json")
        record["observation_response_sha256"] = _sha256(workspace / "observation-response.json")
        if effect_intent:
            record["provider_observed"] = response["provider"]
    _event(record, "result_observed", sha256=record["result_sha256"])
    return record


def _run_cell(
    command: list[str], output: Path, cell: str, repetition: int, task_digest: str,
) -> dict[str, Any]:
    nonce = secrets.token_urlsafe(24)
    root = output / "work" / nonce
    pre, recovery = root / "pre", root / "recovery"
    pre.mkdir(parents=True)
    continuation = _continuation(nonce)
    volatile_context = secrets.token_hex(2048)
    effect_facts = EFFECT_FACTS.get(cell)
    effect_intent = None if not effect_facts else {
        "fingerprint": secrets.token_hex(32), "tool_class": effect_facts["tool_class"],
    }
    checkpoint_mode = "compact" if cell in {"C", "C_NEG"} else "full"
    request = _prepare_request(
        pre, nonce=nonce, task_digest=task_digest, continuation=continuation,
        checkpoint_mode=checkpoint_mode, effect_intent=effect_intent,
        volatile_context=volatile_context,
    )
    record: dict[str, Any] = {
        "cell": cell, "repetition": repetition, "run_nonce": nonce,
        "task_digest": task_digest, "verifier_owned": True, "passed": True,
        "failures": [], "process": {}, "events": [],
        "workspace": {"pre": str(pre), "recovery": str(recovery), "fresh_recovery": cell != "U"},
    }
    request_path = pre / "request.json"
    _write_json(request_path, request)

    if cell == "U":
        child = _new_process(command, "execute", request_path)
        record["process"]["execute"] = {"pid": child.pid}
        _event(record, "process_started", phase="execute", pid=child.pid)
        exit_code = _finish(child)
        record["process"]["execute"]["exit_code"] = exit_code
        _event(record, "process_exited", phase="execute", pid=child.pid, exit_code=exit_code)
        return _validate_final(
            record, pre, cell=cell, nonce=nonce, task_digest=task_digest,
            continuation=continuation, response=None, effect_intent=None,
        )

    prepare = _new_process(command, "prepare", request_path)
    record["process"]["prepare"] = {"pid": prepare.pid}
    _event(record, "process_started", phase="prepare", pid=prepare.pid)
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
    source = pre / "checkpoint.json"
    _, error = _checkpoint(
        source, continuation=continuation, nonce=nonce, task_digest=task_digest,
        effect_intent=effect_intent, volatile_context=volatile_context, compacted=False,
    )
    if error:
        prepare.kill()
        record["process"]["prepare"]["exit_code"] = _finish(prepare)
        return _failure(record, error)
    _event(record, "checkpoint_observed", sha256=_sha256(source))
    if checkpoint_mode == "compact":
        compacted_path = pre / "compacted-checkpoint.json"
        _, error = _checkpoint(
            compacted_path, continuation=continuation, nonce=nonce, task_digest=task_digest,
            effect_intent=effect_intent, volatile_context=volatile_context, compacted=True,
        )
        if error:
            prepare.kill()
            record["process"]["prepare"]["exit_code"] = _finish(prepare)
            return _failure(record, error)
        if compacted_path.stat().st_size >= source.stat().st_size:
            prepare.kill()
            record["process"]["prepare"]["exit_code"] = _finish(prepare)
            return _failure(record, "compaction: active context was not reduced")
        source = compacted_path
        _event(record, "compaction_observed", sha256=_sha256(source), bytes=source.stat().st_size)
    if effect_intent:
        try:
            intent = _read_json(pre / "intent.json")
        except (OSError, ValueError, json.JSONDecodeError):
            intent = {}
        expected_intent = {"run_nonce": nonce, **effect_intent}
        if any(intent.get(key) != value for key, value in expected_intent.items()):
            prepare.kill()
            record["process"]["prepare"]["exit_code"] = _finish(prepare)
            return _failure(record, "effect: durable intent missing before crash")
        _event(record, "intent_observed", sha256=_sha256(pre / "intent.json"))
    if prepare.poll() is not None:
        record["process"]["prepare"]["exit_code"] = prepare.returncode
        return _failure(record, "prepare child exited before verifier kill")
    prepare.kill()
    record["process"]["prepare"]["exit_code"] = _finish(prepare)
    record["process"]["prepare"]["killed_by_verifier"] = True
    _event(record, "process_killed", phase="prepare", pid=prepare.pid)

    recovery.mkdir(parents=True)
    shutil.copy2(source, recovery / "checkpoint.json")
    recovery_request_path = recovery / "request.json"
    _write_json(recovery_request_path, _recovery_request(recovery, nonce=nonce))
    recover = _new_process(command, "recover", recovery_request_path)
    record["process"]["recover"] = {"pid": recover.pid}
    _event(record, "process_started", phase="recover", pid=recover.pid)
    observation_request = recovery / "observation-request.json"
    if not _wait_for(observation_request, recover):
        record["process"]["recover"]["exit_code"] = _finish(recover)
        return _failure(record, "recovery: no observation request before action")
    unexpected = {p.name for p in recovery.iterdir()} - {
        "checkpoint.json", "request.json", "observation-request.json",
    }
    if unexpected:
        recover.kill()
        record["process"]["recover"]["exit_code"] = _finish(recover)
        return _failure(record, f"recovery: action occurred before re-observation ({sorted(unexpected)})")
    try:
        observed_request = _read_json(observation_request)
    except (OSError, ValueError, json.JSONDecodeError):
        observed_request = {}
    if observed_request.get("run_nonce") != nonce:
        recover.kill()
        record["process"]["recover"]["exit_code"] = _finish(recover)
        return _failure(record, "recovery: observation request nonce mismatch")
    _event(record, "observation_requested", sha256=_sha256(observation_request))
    response_token = secrets.token_urlsafe(24)
    if effect_facts:
        resource_fingerprint = None
        if effect_facts["observation"] == "present":
            resource_fingerprint = (
                effect_intent["fingerprint"]
                if effect_facts["matching"] is True
                else secrets.token_hex(32)
            )
        response = _effect_response(
            nonce=nonce, response_token=response_token,
            observation=str(effect_facts["observation"]),
            resource_fingerprint=resource_fingerprint,
        )
    else:
        response = _world_response(
            nonce=nonce, response_token=response_token,
            fingerprint=_sha256(recovery / "checkpoint.json"),
            matches=cell not in {"R_NEG", "C_NEG"},
        )
    response_path = recovery / "observation-response.json"
    _write_json(response_path, response)
    _event(record, "observation_responded", sha256=_sha256(response_path))
    result_path = recovery / "result.json"
    if not _wait_for(result_path, recover):
        record["process"]["recover"]["exit_code"] = _finish(recover)
        return _failure(record, "recovery: result missing after observation")
    record["process"]["recover"]["exit_code"] = _finish(recover)
    _event(record, "process_exited", phase="recover", pid=recover.pid,
           exit_code=record["process"]["recover"]["exit_code"])
    if recover.pid == prepare.pid:
        return _failure(record, "recovery: process identity was not fresh")
    return _validate_final(
        record, recovery, cell=cell, nonce=nonce, task_digest=task_digest,
        continuation=continuation, response=response, effect_intent=effect_intent,
    )


def run(
    command: list[str], output: Path, *, cells: tuple[str, ...] = CELLS,
    repetitions: int = 3,
) -> dict[str, Any]:
    if not command:
        raise ValueError("a host command is required")
    if output.exists() and any(output.iterdir()):
        raise ValueError("output directory must be empty to prevent evidence replay")
    unknown = set(cells) - set(CELLS)
    if unknown:
        raise ValueError(f"unknown cells: {sorted(unknown)}")
    if repetitions < 1:
        raise ValueError("repetitions must be positive")
    output.mkdir(parents=True, exist_ok=True)
    (output / "runs").mkdir()
    records: list[dict[str, Any]] = []
    for repetition in range(1, repetitions + 1):
        triplet_digest = secrets.token_hex(32)
        for cell in cells:
            task_digest = triplet_digest if cell in {"U", "R", "C"} else secrets.token_hex(32)
            record = _run_cell(command, output, cell, repetition, task_digest)
            records.append(record)
            if not record["passed"]:
                break
        if records and not records[-1]["passed"]:
            break
    for repetition in range(1, repetitions + 1):
        triplet = [r for r in records if r["repetition"] == repetition and r["cell"] in {"U", "R", "C"}]
        digests = {r.get("artifact_sha256") for r in triplet}
        if len(triplet) == 3 and len(digests) != 1:
            for record in triplet:
                _failure(record, "triplet: U/R/C artifact equivalence failed")
    for record in records:
        _write_json(output / "runs" / f"{record['cell'].lower()}-{record['repetition']}.json", record)
    failures = [failure for record in records for failure in record["failures"]]
    verdict = {
        "schema_version": "cairn.conformance-witness-verdict.v2",
        "passed": not failures,
        "counts": {"runs": len(records), "passed": sum(r["passed"] for r in records),
                   "failed": sum(not r["passed"] for r in records)},
        "failures": failures, "runs": records,
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
        verdict = {
            "schema_version": "cairn.conformance-witness-verdict.v2",
            "passed": False, "failures": [str(error)],
            "counts": {"runs": 0, "passed": 0, "failed": 0},
        }
        args.output.mkdir(parents=True, exist_ok=True)
        _write_json(args.output / "manifest.json", verdict)
    sys.stdout.write(json.dumps(verdict, indent=2, sort_keys=True) + "\n")
    return 0 if verdict["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
