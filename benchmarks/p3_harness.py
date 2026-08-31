"""Crash-in-place reference harness for Phase 3 effect reconciliation."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

try:
    import _bootstrap  # noqa: F401
except ModuleNotFoundError:
    from benchmarks import _bootstrap  # noqa: F401

from cairn.runtime.effect_ledger import COMPLETE, EffectLedger

from benchmarks.p3_effect_service import CreateOnceProvider, Intent, Receipt


CRASH_EXIT = 86


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _append_trace(run_dir: Path, value: dict) -> None:
    with (run_dir / "trace.jsonl").open("a", encoding="utf-8") as output:
        output.write(json.dumps(value, sort_keys=True) + "\n")


def _intent(cell: dict) -> Intent:
    return Intent(
        effect_id=cell["id"],
        idempotency_key="key-" + cell["id"],
        request_fingerprint=cell.get("request_fingerprint", "request-" + cell["id"]),
        tool_class=cell["tool_class"],
    )


def _crash_worker(payload: dict) -> None:
    run_dir = Path(payload["run_dir"])
    cell = payload["cell"]
    intent = _intent(cell)
    workspace = run_dir / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    _write_json(workspace / "before-effect.json", {"effect_id": intent.effect_id})
    _write_json(run_dir / "intent.json", asdict(intent))
    ledger = EffectLedger(str(run_dir / "effects.jsonl"), "p3")
    ledger.append_effect("create-once", intent.idempotency_key, intent.tool_class)
    _append_trace(run_dir, {"operation": "intent", **asdict(intent), "pid": os.getpid()})
    provider = CreateOnceProvider(run_dir / "remote")
    if cell.get("seed_mismatch"):
        provider.commit(Intent("seed", intent.idempotency_key, "conflicting-request", intent.tool_class))
    boundary = cell["boundary"]
    if boundary != "intent":
        provider.dispatch(intent)
    if boundary in {"commit", "response", "receipt"}:
        receipt = provider.commit(intent)
        if boundary == "response":
            _append_trace(run_dir, {"operation": "response", **asdict(receipt), "pid": os.getpid()})
        if boundary == "receipt":
            _append_trace(run_dir, {"operation": "receipt", **asdict(receipt), "pid": os.getpid()})
    if cell.get("unknown_on_recovery"):
        provider.set_unknown(True)
    _write_json(run_dir / "failure_fired.json", {"fired": True, "boundary": boundary, "pid": os.getpid()})
    os._exit(CRASH_EXIT)


def _load_intent(run_dir: Path) -> Intent:
    return Intent(**json.loads((run_dir / "intent.json").read_text(encoding="utf-8")))


def _recovery_worker(payload: dict) -> dict:
    run_dir = Path(payload["run_dir"])
    cell = payload["cell"]
    intent = _load_intent(run_dir)
    provider = CreateOnceProvider(run_dir / "remote")
    _append_trace(run_dir, {"operation": "observe", "effect_id": intent.effect_id, "pid": os.getpid()})
    observation = provider.observe(intent)
    _append_trace(run_dir, {"operation": "observation", **asdict(observation), "pid": os.getpid()})
    ledger = EffectLedger(str(run_dir / "effects.jsonl"), "p3")
    if intent.tool_class == "never-retry" or observation.state in {"unknown", "mismatch"}:
        decision = "escalate"
        receipt = None
    elif observation.state == "present":
        decision = "skip"
        receipt = Receipt(intent.effect_id, intent.idempotency_key, intent.request_fingerprint, observation.resource_id, "reobserve")
    else:
        decision = "retry"
        provider.dispatch(intent)
        receipt = provider.commit(intent)
    if receipt is not None:
        _append_trace(run_dir, {"operation": "receipt", **asdict(receipt), "pid": os.getpid()})
        ledger.complete_effect(intent.idempotency_key)
    _append_trace(run_dir, {"operation": "resolution", "decision": decision, "effect_id": intent.effect_id, "pid": os.getpid()})
    state = provider._state()
    actual = state["resources"].get(intent.idempotency_key)
    intended_effect_exists = bool(actual and actual["request_fingerprint"] == intent.request_fingerprint)
    closed = any(record["type"] == COMPLETE and record["idempotency_key"] == intent.idempotency_key for record in ledger.list_effects_since(0))
    return {
        "pid": os.getpid(),
        "first_operation": "observe",
        "restore_attempts": 0,
        "observation": asdict(observation),
        "decision": decision,
        "receipt": asdict(receipt) if receipt else None,
        "closed": closed,
        "intended_effect_exists": intended_effect_exists,
        "successful_recovery": decision in {"retry", "skip"} and intended_effect_exists and closed,
        "commit_count": provider.commit_count,
        "call_count": provider.call_count,
    }


def _child(mode: str, run_dir: Path, cell: dict) -> subprocess.CompletedProcess:
    request = run_dir / f"{mode}-input.json"
    _write_json(request, {"run_dir": str(run_dir), "cell": cell})
    command = [sys.executable, str(Path(__file__).resolve()), f"--{mode}-worker", "--input", str(request)]
    return subprocess.run(command, cwd=str(Path(__file__).resolve().parents[1]), capture_output=True, text=True)


def run_p3_cell(cell: dict, output_dir: Path) -> dict:
    """Crash a real child at one effect boundary; reconcile in a fresh child."""
    run_dir = Path(output_dir) / "runs" / f"p3-{uuid.uuid4().hex}"
    crash = _child("crash", run_dir, cell)
    fired = json.loads((run_dir / "failure_fired.json").read_text(encoding="utf-8"))
    if crash.returncode != CRASH_EXIT or not fired["fired"]:
        raise RuntimeError("injected crash did not fire")
    recovered = _child("recovery", run_dir, cell)
    if recovered.returncode != 0:
        raise RuntimeError(recovered.stderr or "recovery worker failed")
    recovery = json.loads(recovered.stdout)
    duplicate_count = max(0, recovery["commit_count"] - 1)
    record = {
        "schema_version": "cairn.p3-effect-cell.v0.1",
        "cell": cell,
        "run_dir": str(run_dir),
        "crash": fired,
        "processes": {"parent_pid": os.getpid(), "crash_pid": fired["pid"], "recovery_pid": recovery["pid"]},
        "intent": asdict(_intent(cell)),
        "recovery": {key: recovery[key] for key in ("first_operation", "restore_attempts", "observation")},
        "resolution": {"decision": recovery["decision"], "receipt": recovery["receipt"]},
        "provider": {"call_count": recovery["call_count"], "commit_count": recovery["commit_count"], "duplicate_count": duplicate_count},
        "ledger": {"closed": recovery["closed"]},
        "outcome": {"intended_effect_exists": recovery["intended_effect_exists"], "successful_recovery": recovery["successful_recovery"]},
    }
    _write_json(run_dir / "record.json", record)
    return record


def run_uninterrupted_cell(cell: dict, output_dir: Path) -> dict:
    """Control path for a normal intent -> effect -> receipt -> closure trace."""
    run_dir = Path(output_dir) / "runs" / f"p3-{uuid.uuid4().hex}"
    run_dir.mkdir(parents=True, exist_ok=True)
    intent = _intent(cell)
    _write_json(run_dir / "intent.json", asdict(intent))
    ledger = EffectLedger(str(run_dir / "effects.jsonl"), "p3")
    ledger.append_effect("create-once", intent.idempotency_key, intent.tool_class)
    _append_trace(run_dir, {"operation": "intent", **asdict(intent), "pid": os.getpid()})
    provider = CreateOnceProvider(run_dir / "remote")
    provider.dispatch(intent)
    receipt = provider.commit(intent)
    _append_trace(run_dir, {"operation": "receipt", **asdict(receipt), "pid": os.getpid()})
    ledger.complete_effect(intent.idempotency_key)
    _append_trace(run_dir, {"operation": "resolution", "decision": "complete", "effect_id": intent.effect_id, "pid": os.getpid()})
    record = {
        "schema_version": "cairn.p3-effect-cell.v0.1",
        "cell": cell | {"normal": True},
        "run_dir": str(run_dir),
        "crash": {"fired": False, "boundary": "normal", "pid": os.getpid()},
        "processes": {"parent_pid": os.getpid(), "crash_pid": None, "recovery_pid": None},
        "intent": asdict(intent),
        "recovery": {"first_operation": "not-applicable", "restore_attempts": 0, "observation": None},
        "resolution": {"decision": "complete", "receipt": asdict(receipt)},
        "provider": {"call_count": provider.call_count, "commit_count": provider.commit_count, "duplicate_count": 0},
        "ledger": {"closed": True},
        "outcome": {"intended_effect_exists": True, "successful_recovery": True},
    }
    _write_json(run_dir / "record.json", record)
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--crash-worker", action="store_true")
    parser.add_argument("--recovery-worker", action="store_true")
    parser.add_argument("--input", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    if args.crash_worker:
        _crash_worker(payload)
    if args.recovery_worker:
        print(json.dumps(_recovery_worker(payload), sort_keys=True))
        return 0
    parser.error("choose a worker mode")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
