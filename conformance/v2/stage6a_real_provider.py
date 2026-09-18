"""Public pre-freeze real-provider qualification for a Stage 6A host.

This is not a Stage 6B holdout.  It proves only that a candidate can wait for
a verifier response that is derived from a separate, durable HTTP provider
after a fresh-process recovery.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import secrets
import shutil
import signal
import subprocess
import sys
import time
from typing import Any

try:  # Supports both ``python stage6a_real_provider.py`` and package imports.
    from stage6b_provider import launch_provider, verify_effect_evidence
except ModuleNotFoundError:  # pragma: no cover - import mode only
    from conformance.v2.stage6b_provider import launch_provider, verify_effect_evidence


CONTINUATION_FIELDS = (
    "task_intent", "active_subgoal", "accepted_decisions", "verified_work",
    "verification_state", "world_identity", "stop_conditions", "next_action_boundary",
)


def _write_json(path: Path, value: object) -> None:
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} is not an object")
    return value


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _wait_for(path: Path, child: subprocess.Popen[str], timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.is_file():
            try:
                _read_json(path)
                return True
            except (OSError, ValueError, json.JSONDecodeError):
                pass
        if child.poll() is not None:
            return False
        time.sleep(0.01)
    return False


def _finish(child: subprocess.Popen[str]) -> tuple[int | None, str, str]:
    try:
        child.wait(timeout=3)
    except subprocess.TimeoutExpired:
        child.kill()
        child.wait(timeout=3)
    stdout, stderr = child.communicate()
    return child.returncode, stdout, stderr


def _run(command: list[str], phase: str, request: Path) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [*command, phase, str(request)], stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )


def _fail(record: dict[str, Any], message: str) -> dict[str, Any]:
    record.update(passed=False, failure=message)
    return record


def run(command: list[str], output: Path, *, response_delay_ms: int = 100) -> dict[str, Any]:
    """Exercise an actual process death and a delayed, ledger-backed response."""
    if not command:
        raise ValueError("a host command is required")
    if output.exists() and any(output.iterdir()):
        raise ValueError("output directory must be empty to prevent evidence replay")
    if response_delay_ms < 0:
        raise ValueError("response delay must be non-negative")

    output.mkdir(parents=True)
    pre, recovery = output / "pre", output / "recovery"
    nonce = secrets.token_urlsafe(24)
    digest = secrets.token_hex(32)
    continuation = {field: secrets.token_urlsafe(24) for field in CONTINUATION_FIELDS}
    fingerprint = secrets.token_hex(32)
    intent = {"fingerprint": fingerprint, "tool_class": "check-before-retry"}
    record: dict[str, Any] = {
        "schema_version": "cairn.phase6a-real-provider-preflight.v1",
        "passed": True,
        "run_nonce": nonce,
        "task_digest": digest,
        "response_delay_ms": response_delay_ms,
        "workspace": {"pre": str(pre), "recovery": str(recovery), "fresh_recovery": True},
        "process": {},
        "provider": {},
    }
    request = {
        "protocol": "cairn.conformance-witness.v2", "workspace": str(pre), "run_nonce": nonce,
        "task": {"digest": digest, "continuation": continuation, "checkpoint_mode": "full",
                 "effect_intent": intent, "volatile_context": secrets.token_hex(3072)},
    }
    pre.mkdir(parents=True)
    _write_json(pre / "request.json", request)

    with launch_provider(output / "provider-ledger") as provider:
        record["provider"].update(pid=provider.pid, ledger=str(output / "provider-ledger"))
        prepare = _run(command, "prepare", pre / "request.json")
        record["process"]["prepare"] = {"pid": prepare.pid}
        if not _wait_for(pre / "ready.json", prepare):
            record["process"]["prepare"]["exit_code"], _, _ = _finish(prepare)
            return _fail(record, "prepare did not become ready")
        checkpoint = pre / "checkpoint.json"
        if not checkpoint.is_file() or not (pre / "intent.json").is_file():
            prepare.kill()
            record["process"]["prepare"]["exit_code"], _, _ = _finish(prepare)
            return _fail(record, "durable checkpoint or effect intent missing")

        key, foreign = secrets.token_urlsafe(28), secrets.token_hex(32)
        provider.dispatch(idempotency_key=key, request_fingerprint=fingerprint, request_id=secrets.token_urlsafe(16))
        provider.create(idempotency_key=key, request_fingerprint=foreign, request_id=secrets.token_urlsafe(16))
        prepare.kill()
        code, _, _ = _finish(prepare)
        record["process"]["prepare"].update(exit_code=code, killed_by_verifier=True)
        expected_kill = 1 if sys.platform == "win32" else -signal.SIGKILL
        if code != expected_kill:
            return _fail(record, "verifier did not confirm process death")

        recovery.mkdir(parents=True)
        shutil.copy2(checkpoint, recovery / "checkpoint.json")
        _write_json(recovery / "request.json", {
            "protocol": "cairn.conformance-witness.v2", "workspace": str(recovery), "run_nonce": nonce,
        })
        recover = _run(command, "recover", recovery / "request.json")
        record["process"]["recover"] = {"pid": recover.pid}
        observation_request = recovery / "observation-request.json"
        if not _wait_for(observation_request, recover):
            record["process"]["recover"]["exit_code"], _, stderr = _finish(recover)
            record["process"]["recover"]["stderr"] = stderr
            return _fail(record, "recovery did not request observation")
        observed_request = _read_json(observation_request)
        if observed_request.get("run_nonce") != nonce:
            recover.kill()
            record["process"]["recover"]["exit_code"], _, _ = _finish(recover)
            return _fail(record, "recovery observation request nonce mismatch")

        actual = provider.observe(key)
        record["provider"].update(observation=actual, observation_before_response=True)
        # The external provider has replied; publication remains asynchronous to the host.
        time.sleep(response_delay_ms / 1000)
        token = secrets.token_urlsafe(24)
        response = {"run_nonce": nonce, "response_token": token, "provider": {
            "observation": actual["state"], "resource_fingerprint": actual["request_fingerprint"],
        }}
        response_path = recovery / "observation-response.json"
        _write_json(response_path, response)
        record["observation_response_sha256"] = _hash(response_path)

        result_path = recovery / "result.json"
        if not _wait_for(result_path, recover):
            code, stdout, stderr = _finish(recover)
            record["process"]["recover"].update(exit_code=code, stdout=stdout, stderr=stderr)
            return _fail(record, "recovery did not produce a result after real provider observation")
        code, stdout, stderr = _finish(recover)
        record["process"]["recover"].update(exit_code=code, stdout=stdout, stderr=stderr)
        if recover.pid == prepare.pid:
            return _fail(record, "recovery process identity was not fresh")
        result = _read_json(result_path)
        candidate_observation = result.get("provider_observation")
        if result.get("continuation") != continuation or result.get("decision") != "escalate" or result.get("status") != "escalated":
            return _fail(record, "recovery did not preserve state and escalate foreign provider resource")
        if (recovery / "artifact.txt").exists():
            return _fail(record, "escalation performed an unauthorized artifact action")
        try:
            effect = verify_effect_evidence(
                provider=provider, idempotency_key=key, expected_fingerprint=fingerprint,
                candidate_observation=candidate_observation, candidate_decision="escalate",
                observation_event_sequence=("reobservation-request", "provider-observation", "candidate-result"),
                provider_observation=actual, candidate_root=output / "candidate-placeholder",
            )
        except ValueError as error:
            return _fail(record, f"provider-backed effect evidence rejected: {error}")
        record.update(result_sha256=_hash(result_path), effect_verdict=effect, passed=True)
        return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--host", nargs="+", required=True)
    parser.add_argument("--response-delay-ms", type=int, default=100)
    args = parser.parse_args()
    verdict = run(args.host, args.output, response_delay_ms=args.response_delay_ms)
    _write_json(args.output / "verdict.json", verdict)
    print(json.dumps({"passed": verdict["passed"], "failure": verdict.get("failure")}, sort_keys=True))
    return 0 if verdict["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
