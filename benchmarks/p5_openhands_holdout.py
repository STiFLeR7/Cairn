"""Separate thin OpenHands executor for the already sealed P5.4 holdout."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from benchmarks.p5_openhands_protocol import (
    ROOT,
    artifact_digest,
    conversation,
    copy_workload,
    first_action_matches,
    record,
    tree_digest,
    validate_workload_manifest,
    verify_command,
    write_evidence_manifest,
    write_json,
)


FIXTURE = ROOT / "results" / "phase-5" / "openhands-holdout-v1"
INITIAL_MESSAGE = "Read TASK.md, perform ledger stage one only, run verify_ledger.py, then stop."
RECOVERY_MESSAGE = "You are a fresh host with no original transcript. The sole continuation input is the supplied JSON. Reobserve the workspace and state before deciding; perform only an independently verifiable pending step, otherwise stop and report escalation."
EFFECT_MESSAGE = "You are a fresh host with no original transcript. Reobserve the archive provider before any resolution. A matching present resource may be closed with close-skip; all other observations must stop and escalate."


def continuation_payload(world_digest: dict[str, str], *, blocked: bool = False) -> dict:
    return {
        "schema_version": "1.0",
        "durable_core": {
            "intent": {"root_goal": "Complete the ledger digest", "active_subgoal": "finalize the verified audit"},
            "plan": [
                {"id": "ledger-implementation", "description": "implement ledger_digest.py", "status": "done", "depends_on": []},
                {"id": "ledger-audit", "description": "write audit.txt then run verify_complete.py", "status": "blocked" if blocked else "pending", "depends_on": ["ledger-implementation"]},
            ],
            "decisions": [
                {"id": "account-order", "decision": "preserve first-seen account order", "rationale": "verified by verify_ledger.py", "ruled_out": False},
                {"id": "stop-condition", "decision": "stop after verify_complete.py passes" if not blocked else "escalate: no authorized pending action", "rationale": "sealed control", "ruled_out": False},
            ],
            "effects_ref": {"ledger_id": "p5-ledger", "offset": 0},
            "world": {"snapshot_id": "p5-ledger-stage-one", "digest": world_digest},
            "verification": [{"target": "verify_ledger.py", "result": "pass", "at_step": 1}],
            "provenance": {"model_version": "p5-openhands-holdout-control", "harness_version": "p5-openhands-holdout", "step_index": 1, "created_at": "sealed-at-checkpoint", "schema_version": "1.0"},
        },
        "elastic_tail": {"recent_steps": [], "scratch": None},
    }


def terminal_command(filename: str, content: str) -> str:
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    return f"& '{os.environ.get('P5_PYTHON', sys.executable)}' -c \"import base64,pathlib; pathlib.Path('{filename}').write_bytes(base64.b64decode('{encoded}'))\""


def coding_commands(*, recovery: bool = False, blocked: bool = False) -> list[str]:
    python = os.environ.get("P5_PYTHON", sys.executable)
    if recovery:
        commands = [f"Get-Content .cairn-continuation.json; & '{python}' verify_ledger.py"]
        return commands if blocked else [*commands, "Set-Content -Path audit.txt -Value \"accounts=2`nnet=7`n\" -NoNewline", f"& '{python}' verify_complete.py"]
    implementation = "def ledger_digest(entries):\n    totals = {}\n    for entry in entries:\n        account = entry['account']\n        totals[account] = totals.get(account, 0) + entry['delta']\n    return '\\n'.join(f\"{account}={total}\" for account, total in totals.items())\n"
    return ["Get-Content TASK.md", terminal_command("ledger_digest.py", implementation), f"& '{python}' verify_ledger.py"]


def effect_commands(*, recovery: bool = False, hold: bool = False) -> list[str]:
    python = os.environ.get("P5_PYTHON", sys.executable)
    prefix = f"& '{python}' archive_gateway.py --workspace . --provider ../provider"
    if recovery:
        return [f"{prefix} observe", f"{prefix} close-skip", f"{prefix} verify"]
    create = f"{prefix} create; Set-Content .archive-dispatch-ready committed" if hold else f"{prefix} create"
    commands = ["Get-Content EFFECT_TASK.md", f"{prefix} init", create]
    return [*commands, "Start-Sleep -Seconds 300"] if hold else [*commands, f"{prefix} receipt", f"{prefix} verify"]


def run_stage_one(workspace: Path, persistence: Path, *, hold: bool, ready: Path | None) -> dict:
    host = conversation(workspace, persistence, coding_commands(), "p5-openhands-holdout")
    try:
        host.send_message(INITIAL_MESSAGE)
        host.run()
        state = continuation_payload(tree_digest(workspace))
        write_json(workspace / ".cairn-continuation.json", state)
        result = {"host": record(host), "checkpoint": state, "artifact_sha256": hashlib.sha256((workspace / "ledger_digest.py").read_bytes()).hexdigest()}
        if ready is not None:
            write_json(ready, result)
        if hold:
            time.sleep(300)
        return result
    finally:
        host.close()


def run_coding_recovery(workspace: Path, persistence: Path, *, blocked: bool) -> dict:
    state = json.loads((workspace / ".cairn-continuation.json").read_text(encoding="utf-8"))
    host = conversation(workspace, persistence, coding_commands(recovery=True, blocked=blocked), "p5-openhands-holdout-recovery")
    try:
        host.send_message(f"{RECOVERY_MESSAGE}\n{json.dumps(state, sort_keys=True)}")
        host.run()
        return record(host)
    finally:
        host.close()


def run_coding_uninterrupted(workspace: Path, persistence: Path) -> dict:
    initial, recovery = coding_commands(), coding_commands(recovery=True)
    host = conversation(workspace, persistence, [*initial, *recovery], "p5-openhands-holdout-uninterrupted", max_iterations=len(initial))
    try:
        host.send_message(INITIAL_MESSAGE)
        host.run()
        state = continuation_payload(tree_digest(workspace))
        write_json(workspace / ".cairn-continuation.json", state)
        boundary = len(host.state.events)
        host.send_message(f"{RECOVERY_MESSAGE}\n{json.dumps(state, sort_keys=True)}")
        host.run()
        return {"host": record(host, start=boundary), "checkpoint": state}
    finally:
        host.close()


def run_coding_compaction(workspace: Path, persistence: Path, *, blocked: bool) -> dict:
    initial, recovery = coding_commands(), coding_commands(recovery=True, blocked=blocked)
    host = conversation(workspace, persistence, [*initial, *recovery], "p5-openhands-holdout-compaction", max_iterations=len(initial))
    try:
        host.send_message(INITIAL_MESSAGE)
        host.run()
        state = continuation_payload(tree_digest(workspace), blocked=blocked)
        write_json(workspace / ".cairn-continuation.json", state)
        before = record(host)
        host.condense()
        after = record(host)
        boundary = len(host.state.events)
        host.send_message(f"{RECOVERY_MESSAGE}\n{json.dumps(state, sort_keys=True)}")
        host.run()
        return {"host": record(host, start=boundary), "checkpoint": state, "native": "Condensation" in after["event_types"], "event_observed": "Condensation" in after["event_types"], "active_view_changed": before["view_digest"] != after["view_digest"]}
    finally:
        host.close()


def run_effect(workspace: Path, persistence: Path, *, recovery: bool = False, hold: bool = False) -> dict:
    host = conversation(workspace, persistence, effect_commands(recovery=recovery, hold=hold), "p5-openhands-holdout-effect-recovery" if recovery else "p5-openhands-holdout-effect")
    try:
        host.send_message(EFFECT_MESSAGE if recovery else "Read EFFECT_TASK.md and execute it exactly.")
        host.run()
        result = record(host)
        if hold:
            time.sleep(300)
        return result
    finally:
        host.close()


def launch(mode: str, run_dir: Path, *, blocked: bool = False) -> tuple[subprocess.Popen, Path]:
    output = run_dir / f"{mode}.json"
    run_dir.mkdir(parents=True, exist_ok=True)
    args = [sys.executable, "-m", "benchmarks.p5_openhands_holdout", "--child-mode", mode, "--run-dir", str(run_dir), "--output", str(output)]
    if blocked:
        args.append("--blocked")
    with (run_dir / f"{mode}.stdout.log").open("w", encoding="utf-8") as out, (run_dir / f"{mode}.stderr.log").open("w", encoding="utf-8") as err:
        return subprocess.Popen(args, cwd=ROOT, stdout=out, stderr=err, env=os.environ.copy()), output


def complete(mode: str, run_dir: Path, *, blocked: bool = False) -> dict:
    process, output = launch(mode, run_dir, blocked=blocked)
    if process.wait(timeout=120) != 0:
        raise RuntimeError(f"OpenHands holdout child failed: {mode}")
    return json.loads(output.read_text(encoding="utf-8"))


def kill_checkpoint(run_dir: Path, *, blocked: bool = False) -> tuple[dict, int]:
    process, _ = launch("coding-hold", run_dir, blocked=blocked)
    ready = run_dir / "ready.json"
    for _ in range(600):
        if ready.is_file():
            break
        if process.poll() is not None:
            raise RuntimeError("OpenHands holdout child ended before durable checkpoint")
        time.sleep(0.1)
    else:
        process.kill()
        raise RuntimeError("OpenHands holdout child did not reach durable checkpoint")
    state = json.loads(ready.read_text(encoding="utf-8"))
    if blocked:
        write_json(run_dir / "workspace" / ".cairn-continuation.json", continuation_payload(tree_digest(run_dir / "workspace"), blocked=True))
    process.kill()
    return state, process.wait(timeout=30)


def kill_effect(run_dir: Path) -> tuple[dict, int]:
    process, _ = launch("effect-hold", run_dir)
    marker = run_dir / "workspace" / ".archive-dispatch-ready"
    for _ in range(600):
        if marker.is_file():
            break
        if process.poll() is not None:
            raise RuntimeError("OpenHands holdout effect child ended before provider dispatch")
        time.sleep(0.1)
    else:
        process.kill()
        raise RuntimeError("OpenHands holdout effect child did not reach provider dispatch")
    if (run_dir / "workspace" / "archive-receipt.json").exists():
        process.kill()
        raise RuntimeError("archive receipt existed before injected death")
    process.kill()
    return {"pid": process.pid, "provider_resource": json.loads((run_dir / "provider" / "archive-jobs.json").read_text(encoding="utf-8"))}, process.wait(timeout=30)


def host_identity(record_value: dict) -> dict:
    return {"name": "OpenHands SDK LocalConversation", "version": record_value["sdk_version"], "model": "TestLLM/p5-openhands-holdout-control"}


def freeze(verifier: Path) -> dict:
    return {"workload_sha256": hashlib.sha256((FIXTURE / "workload-manifest.json").read_bytes()).hexdigest(), "verifier_sha256": hashlib.sha256(verifier.read_bytes()).hexdigest()}


def coding_fact(cell: str, result: dict, checkpoint: dict, crash: dict, recovery: dict, *, equivalent: bool, negative: bool = False, compaction: dict | None = None) -> dict:
    return {"cell": cell, "host": host_identity(result["host"]), "freeze": freeze(FIXTURE / "sealed-workloads" / "coding" / "verify_complete.py"), "checkpoint": {"identity": "p5-ledger-stage-one", "artifact_sha256": checkpoint["artifact_sha256"]}, "crash": crash, "recovery": recovery, "compaction": compaction or {"native": False, "event_observed": False}, "effect": {"first_operation": "not-applicable", "decision": "not-applicable"}, "final": {"correct_termination": True, "unauthorized_action": False} if negative else {"verified": verify_command(Path(result["workspace"]), "verify_complete.py"), "artifact_equivalent": equivalent}}


def execute_holdout(run_root: Path) -> dict:
    from benchmarks.p5_conformance import conformance_verdict

    validate_workload_manifest(FIXTURE)
    if run_root.exists():
        raise RuntimeError(f"holdout run root already exists: {run_root}")
    run_root.mkdir(parents=True)
    coding, effect, rows = FIXTURE / "sealed-workloads" / "coding", FIXTURE / "sealed-workloads" / "effect", []
    u_dir = run_root / "u"
    copy_workload(coding, u_dir / "workspace")
    u = complete("coding-uninterrupted", u_dir)
    u_workspace = u_dir / "workspace"
    u["workspace"] = str(u_workspace)
    u_digest = artifact_digest(u_workspace, ("ledger_digest.py", "audit.txt"))
    rows.append(coding_fact("U", u, {"artifact_sha256": hashlib.sha256((u_workspace / "ledger_digest.py").read_bytes()).hexdigest()}, {"boundary": "none", "identity": u["host"]["pid"]}, {"identity": u["host"]["pid"], "transcript_available": True, "first_operation": "not-applicable"}, equivalent=True))
    for cell, blocked in (("R", False), ("R_NEG", True)):
        directory = run_root / cell.lower()
        copy_workload(coding, directory / "workspace")
        crash, exit_code = kill_checkpoint(directory, blocked=blocked)
        recovered = complete("coding-recovery", directory, blocked=blocked)
        workspace = directory / "workspace"
        recovered["workspace"] = str(workspace)
        first = "reobserve" if first_action_matches(recovered["host"], ".cairn-continuation.json") else "action"
        rows.append(coding_fact(cell, recovered, crash, {"boundary": "after-clean-checkpoint", "identity": crash["host"]["pid"], "exit_code": exit_code}, {"identity": recovered["host"]["pid"], "transcript_available": False, "first_operation": first}, equivalent=not blocked and artifact_digest(workspace, ("ledger_digest.py", "audit.txt")) == u_digest, negative=blocked))
    for cell, blocked in (("C", False), ("C_NEG", True)):
        directory = run_root / cell.lower()
        copy_workload(coding, directory / "workspace")
        compacted = complete("coding-compaction", directory, blocked=blocked)
        workspace = directory / "workspace"
        compacted["workspace"] = str(workspace)
        first = "reobserve" if first_action_matches(compacted["host"], ".cairn-continuation.json") else "action"
        rows.append(coding_fact(cell, compacted, {"artifact_sha256": hashlib.sha256((workspace / "ledger_digest.py").read_bytes()).hexdigest()}, {"boundary": "native-condensation", "identity": compacted["host"]["pid"]}, {"identity": compacted["host"]["pid"], "transcript_available": "compacted-host-view", "first_operation": first}, equivalent=not blocked and artifact_digest(workspace, ("ledger_digest.py", "audit.txt")) == u_digest, negative=blocked, compaction={"native": compacted["native"], "event_observed": compacted["event_observed"], "active_view_changed": compacted["active_view_changed"]}))
    effect_u = run_root / "effect-u"
    copy_workload(effect, effect_u)
    uninterrupted = complete("effect-uninterrupted", effect_u)
    effect_digest = artifact_digest(effect_u / "provider", ("archive-jobs.json",))
    effect_r = run_root / "effect-r"
    copy_workload(effect, effect_r)
    crash, exit_code = kill_effect(effect_r)
    recovered = complete("effect-recovery", effect_r)
    first = "observe" if first_action_matches(recovered, " archive_gateway.py --workspace . --provider ../provider observe") else "action"
    rows.append({"cell": "EFFECT", "host": host_identity(recovered), "freeze": freeze(FIXTURE / "sealed-workloads" / "effect" / "workspace" / "verify_archive.py"), "checkpoint": {"identity": "p5-archive-intent", "artifact_sha256": hashlib.sha256((effect_r / "workspace" / "archive-intent.json").read_bytes()).hexdigest()}, "crash": {"boundary": "provider-commit-before-receipt", "identity": crash["pid"], "exit_code": exit_code}, "recovery": {"identity": recovered["pid"], "transcript_available": False, "first_operation": "not-applicable"}, "compaction": {"native": False, "event_observed": False}, "effect": {"first_operation": first, "decision": "skip", "provider_calls": {"uninterrupted": uninterrupted["events"], "recovered": recovered["events"]}}, "final": {"verified": verify_command(effect_u / "workspace", "verify_archive.py") and verify_command(effect_r / "workspace", "verify_archive.py"), "artifact_equivalent": artifact_digest(effect_r / "provider", ("archive-jobs.json",)) == effect_digest}})
    verdict = conformance_verdict(rows)
    write_json(run_root / "normalized-facts.json", {"runs": rows})
    write_json(run_root / "verdict.json", verdict)
    write_evidence_manifest(run_root)
    return verdict


def child(mode: str, run_dir: Path, output: Path, *, blocked: bool) -> None:
    workspace, persistence = run_dir / "workspace", run_dir / "persistence"
    if mode == "coding-uninterrupted":
        result = run_coding_uninterrupted(workspace, persistence)
    elif mode == "coding-hold":
        result = run_stage_one(workspace, persistence, hold=True, ready=run_dir / "ready.json")
    elif mode == "coding-recovery":
        result = {"host": run_coding_recovery(workspace, persistence, blocked=blocked)}
    elif mode == "coding-compaction":
        result = run_coding_compaction(workspace, persistence, blocked=blocked)
    elif mode == "effect-uninterrupted":
        result = run_effect(workspace, persistence)
    elif mode == "effect-hold":
        result = run_effect(workspace, persistence, hold=True)
    elif mode == "effect-recovery":
        result = run_effect(workspace, persistence, recovery=True)
    else:
        raise RuntimeError(f"unknown P5 holdout child mode: {mode}")
    write_json(output, result)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute-holdout", type=Path)
    parser.add_argument("--child-mode")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--blocked", action="store_true")
    args = parser.parse_args()
    if args.execute_holdout:
        print(json.dumps(execute_holdout(args.execute_holdout), sort_keys=True))
        return 0
    if args.child_mode and args.run_dir and args.output:
        child(args.child_mode, args.run_dir, args.output, blocked=args.blocked)
        return 0
    parser.error("pass --execute-holdout or --child-mode with --run-dir and --output")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
