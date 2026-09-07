"""Thin OpenHands P5 driver; it never imports Cairn's runtime or agent loop."""

from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid


def validate_workload_manifest(root: Path) -> None:
    """Refuse host execution unless the already-sealed fixture is byte-identical."""
    manifest = json.loads((root / "workload-manifest.json").read_text(encoding="utf-8"))
    for item in manifest["files"]:
        data = (root / item["path"]).read_bytes()
        if len(data) != item["bytes"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise RuntimeError(f"sealed workload mismatch: {item['path']}")


def continuation_payload(world_digest: dict[str, str], *, blocked: bool = False) -> dict:
    """Produce the raw, host-agnostic Continuation Contract v0 input."""
    return {
        "schema_version": "1.0",
        "durable_core": {
            "intent": {"root_goal": "Complete the route report", "active_subgoal": "finalize the verified report"},
            "plan": [
                {"id": "route-implementation", "description": "implement route_report.py", "status": "done", "depends_on": []},
                {"id": "route-completion", "description": "write completion.txt then run verify_complete.py", "status": "blocked" if blocked else "pending", "depends_on": ["route-implementation"]},
            ],
            "decisions": [
                {"id": "route-order", "decision": "preserve first-seen route order", "rationale": "verified by verify_route.py", "ruled_out": False},
                {"id": "stop-condition", "decision": "stop after verify_complete.py passes" if not blocked else "escalate: no authorized pending action", "rationale": "sealed control", "ruled_out": False},
            ],
            "effects_ref": {"ledger_id": "p5-route", "offset": 0},
            "world": {"snapshot_id": "p5-route-stage-one", "digest": world_digest},
            "verification": [{"target": "verify_route.py", "result": "pass", "at_step": 1}],
            "provenance": {"model_version": "p5-openhands-control", "harness_version": "p5-openhands", "step_index": 1, "created_at": "sealed-at-checkpoint", "schema_version": "1.0"},
        },
        "elastic_tail": {"recent_steps": [], "scratch": None},
    }


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "results" / "phase-5" / "openhands-reference-v1"
INITIAL_MESSAGE = "Read TASK.md and perform stage one only. Run verify_route.py, then stop."
RECOVERY_MESSAGE = "You are a fresh host with no original transcript. The sole continuation input is the supplied JSON. Reobserve the workspace and state before deciding; perform only an independently verifiable pending step, otherwise stop and report escalation."
EFFECT_MESSAGE = "You are a fresh host with no original transcript. Reobserve the provider before any resolution. A matching present resource may be closed with close-skip; all other observations must stop and escalate."


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_evidence_manifest(root: Path) -> dict:
    """Hash raw P5 evidence after a completed matrix; the verdict is deliberately excluded."""
    entries = [
        {"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name not in {"evidence-manifest.json", "verdict.json"}
    ]
    manifest = {"schema_version": "cairn.p5-evidence-manifest.v0", "entries": entries}
    write_json(root / "evidence-manifest.json", manifest)
    return manifest


def evidence_manifest_matches(root: Path) -> bool:
    manifest_path = root / "evidence-manifest.json"
    if not manifest_path.is_file():
        return False
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "cairn.p5-evidence-manifest.v0":
        return False
    actual = {
        path.relative_to(root).as_posix(): {"bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        for path in root.rglob("*")
        if path.is_file() and path.name not in {"evidence-manifest.json", "verdict.json"}
    }
    listed = {entry.get("path"): {"bytes": entry.get("bytes"), "sha256": entry.get("sha256")} for entry in manifest.get("entries", [])}
    return listed == actual


def tree_digest(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name not in {"completion.txt", ".cairn-continuation.json"} and "__pycache__" not in path.parts
    }


def terminal_command(filename: str, content: str) -> str:
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    return f"& '{os.environ.get('P5_PYTHON', sys.executable)}' -c \"import base64,pathlib; pathlib.Path('{filename}').write_bytes(base64.b64decode('{encoded}'))\""


def coding_commands(*, recovery: bool = False, blocked: bool = False) -> list[str]:
    python = os.environ.get("P5_PYTHON", sys.executable)
    if recovery:
        commands = [f"Get-Content .cairn-continuation.json; & '{python}' verify_route.py"]
        if blocked:
            return commands
        return [*commands, "Set-Content -Path completion.txt -Value \"routes=2`nstops=4`n\" -NoNewline", f"& '{python}' verify_complete.py"]
    implementation = "def make_route_report(records):\n    grouped = {}\n    for record in records:\n        grouped.setdefault(record['route'], []).extend(record['stops'])\n    return '\\n'.join(f\"{route}:{' ' + ', '.join(stops) if stops else ''}\" for route, stops in grouped.items())\n"
    return ["Get-Content TASK.md", terminal_command("route_report.py", implementation), f"& '{python}' verify_route.py"]


def effect_commands(*, recovery: bool = False, hold: bool = False) -> list[str]:
    python = os.environ.get("P5_PYTHON", sys.executable)
    prefix = f"& '{python}' issue_gateway.py --workspace . --provider ../provider"
    if recovery:
        return [f"{prefix} observe", f"{prefix} close-skip", f"{prefix} verify"]
    create = f"{prefix} create; Set-Content .effect-dispatch-ready committed" if hold else f"{prefix} create"
    commands = ["Get-Content EFFECT_TASK.md", f"{prefix} init", create]
    return [*commands, "Start-Sleep -Seconds 300"] if hold else [*commands, f"{prefix} receipt", f"{prefix} verify"]


def event_data(event: object) -> dict:
    dumped = event.model_dump(mode="json") if hasattr(event, "model_dump") else {"value": str(event)}
    return {"type": type(event).__name__, "data": dumped}


def scripted_llm(commands: list[str], label: str):
    from openhands.sdk.llm import Message, MessageToolCall, TextContent
    from openhands.sdk.testing import TestLLM
    from openhands.tools.terminal import TerminalTool

    replies = [
        Message(
            role="assistant",
            content=[TextContent(text="")],
            tool_calls=[MessageToolCall(id=f"p5_{index}", name=TerminalTool.name, arguments=json.dumps({"command": command}), origin="completion")],
        )
        for index, command in enumerate(commands)
    ]
    replies.append(Message(role="assistant", content=[TextContent(text="control complete")]))
    return TestLLM.from_messages(replies, model=label)


def host_agent(commands: list[str], label: str):
    from openhands.sdk.agent import Agent
    from openhands.sdk.context.condenser import LLMSummarizingCondenser
    from openhands.sdk.llm import Message, TextContent
    from openhands.sdk.testing import TestLLM
    from openhands.sdk.tool import Tool
    from openhands.tools.terminal import TerminalTool

    return Agent(
        llm=scripted_llm(commands, label),
        tools=[Tool(name=TerminalTool.name)],
        include_default_tools=[],
        condenser=LLMSummarizingCondenser(
            llm=TestLLM.from_messages([Message(role="assistant", content=[TextContent(text="P5 native condensation")])], model=f"{label}-summary"),
            max_size=12,
            keep_first=4,
        ),
    )


def conversation(workspace: Path, persistence: Path, commands: list[str], label: str, *, max_iterations: int = 500):
    from openhands.sdk.conversation import Conversation

    return Conversation(
        agent=host_agent(commands, label),
        workspace=workspace,
        persistence_dir=persistence,
        conversation_id=uuid.uuid4(),
        visualizer=None,
        delete_on_close=False,
        max_iteration_per_run=max_iterations,
    )


def record(host, *, start: int = 0) -> dict:
    events = list(host.state.events)
    view = list(host.state.view.events)
    return {
        "pid": os.getpid(),
        "sdk_version": importlib.metadata.version("openhands-sdk"),
        "conversation_id": str(host.state.id),
        "events": [event_data(event) for event in events[start:]],
        "event_types": [type(event).__name__ for event in events],
        "view_count": len(view),
        "view_digest": hashlib.sha256(json.dumps([str(event) for event in view], sort_keys=True).encode()).hexdigest(),
    }


def run_stage_one(workspace: Path, persistence: Path, *, hold: bool, ready: Path | None) -> dict:
    host = conversation(workspace, persistence, coding_commands(), "p5-openhands-reference")
    try:
        host.send_message(INITIAL_MESSAGE)
        host.run()
        state = continuation_payload(tree_digest(workspace))
        write_json(workspace / ".cairn-continuation.json", state)
        result = {"host": record(host), "checkpoint": state, "artifact_sha256": hashlib.sha256((workspace / "route_report.py").read_bytes()).hexdigest()}
        if ready is not None:
            write_json(ready, result)
        if hold:
            import time
            time.sleep(300)
        return result
    finally:
        host.close()


def run_coding_recovery(workspace: Path, persistence: Path, *, blocked: bool) -> dict:
    state = json.loads((workspace / ".cairn-continuation.json").read_text(encoding="utf-8"))
    host = conversation(workspace, persistence, coding_commands(recovery=True, blocked=blocked), "p5-openhands-recovery")
    try:
        host.send_message(f"{RECOVERY_MESSAGE}\n{json.dumps(state, sort_keys=True)}")
        host.run()
        return record(host)
    finally:
        host.close()


def run_coding_uninterrupted(workspace: Path, persistence: Path) -> dict:
    initial, recovery = coding_commands(), coding_commands(recovery=True)
    host = conversation(workspace, persistence, [*initial, *recovery], "p5-openhands-uninterrupted", max_iterations=len(initial))
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
    host = conversation(workspace, persistence, [*initial, *recovery], "p5-openhands-compaction", max_iterations=len(initial))
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
        return {"host": record(host, start=boundary), "checkpoint": state, "before": before, "after": after, "native": "Condensation" in after["event_types"], "event_observed": "Condensation" in after["event_types"], "active_view_changed": before["view_digest"] != after["view_digest"]}
    finally:
        host.close()


def run_effect(workspace: Path, persistence: Path, *, recovery: bool = False, hold: bool = False, ready: Path | None = None) -> dict:
    commands = effect_commands(recovery=recovery, hold=hold)
    host = conversation(workspace, persistence, commands, "p5-openhands-effect-recovery" if recovery else "p5-openhands-effect")
    try:
        host.send_message(EFFECT_MESSAGE if recovery else "Read EFFECT_TASK.md and execute it exactly.")
        host.run()
        result = record(host)
        if ready is not None:
            write_json(ready, result)
        if hold:
            time.sleep(300)
        return result
    finally:
        host.close()


def first_action_matches(host_record: dict, fragment: str) -> bool:
    action = next((event for event in host_record["events"] if event["type"] == "ActionEvent"), None)
    return action is not None and fragment in json.dumps(action, sort_keys=True)


def copy_workload(source: Path, destination: Path) -> None:
    shutil.copytree(source, destination)


def launch_child(root: Path, mode: str, run_dir: Path, *, blocked: bool = False) -> tuple[subprocess.Popen, Path]:
    output = run_dir / f"{mode}.json"
    stdout = run_dir / f"{mode}.stdout.log"
    stderr = run_dir / f"{mode}.stderr.log"
    run_dir.mkdir(parents=True, exist_ok=True)
    arguments = [sys.executable, "-m", "benchmarks.p5_openhands_protocol", "--child-mode", mode, "--run-dir", str(run_dir), "--output", str(output)]
    if blocked:
        arguments.append("--blocked")
    with stdout.open("w", encoding="utf-8") as out, stderr.open("w", encoding="utf-8") as err:
        process = subprocess.Popen(arguments, cwd=ROOT, stdout=out, stderr=err, env=os.environ.copy())
    return process, output


def completed_child(root: Path, mode: str, run_dir: Path, *, blocked: bool = False) -> dict:
    process, output = launch_child(root, mode, run_dir, blocked=blocked)
    if process.wait(timeout=120) != 0:
        raise RuntimeError(f"OpenHands child failed: {mode}")
    return json.loads(output.read_text(encoding="utf-8"))


def killed_checkpoint_child(root: Path, mode: str, run_dir: Path, *, blocked: bool = False) -> tuple[dict, int]:
    process, _ = launch_child(root, mode, run_dir, blocked=blocked)
    ready = run_dir / "ready.json"
    for _ in range(600):
        if ready.is_file():
            break
        if process.poll() is not None:
            raise RuntimeError(f"OpenHands child ended before durable checkpoint: {mode}")
        time.sleep(0.1)
    else:
        process.kill()
        raise RuntimeError(f"OpenHands child did not reach durable checkpoint: {mode}")
    state = json.loads(ready.read_text(encoding="utf-8"))
    if blocked:
        workspace = run_dir / "workspace"
        write_json(workspace / ".cairn-continuation.json", continuation_payload(tree_digest(workspace), blocked=True))
    process.kill()
    return state, process.wait(timeout=30)


def killed_effect_child(root: Path, run_dir: Path) -> tuple[dict, int]:
    process, _ = launch_child(root, "effect-hold", run_dir)
    marker = run_dir / "workspace" / ".effect-dispatch-ready"
    for _ in range(600):
        if marker.is_file():
            break
        if process.poll() is not None:
            raise RuntimeError("OpenHands effect child ended before provider dispatch")
        time.sleep(0.1)
    else:
        process.kill()
        raise RuntimeError("OpenHands effect child did not reach provider dispatch")
    workspace = run_dir / "workspace"
    if (workspace / "maintenance-receipt.json").exists():
        process.kill()
        raise RuntimeError("effect receipt existed before injected death")
    process.kill()
    return {"pid": process.pid, "provider_resource": json.loads((run_dir / "provider" / "maintenance-windows.json").read_text(encoding="utf-8"))}, process.wait(timeout=30)


def verify_command(workspace: Path, script: str) -> bool:
    result = subprocess.run([os.environ.get("P5_PYTHON", sys.executable), script], cwd=workspace, capture_output=True, text=True, timeout=30)
    write_json(workspace.parent / f"{script}.verification.json", {"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
    return result.returncode == 0


def artifact_digest(workspace: Path, names: tuple[str, ...]) -> str:
    value = {name: hashlib.sha256((workspace / name).read_bytes()).hexdigest() for name in names}
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def host_identity(record: dict) -> dict:
    return {"name": "OpenHands SDK LocalConversation", "version": record["sdk_version"], "model": "TestLLM/p5-openhands-control"}


def freeze_fields(verifier: Path) -> dict:
    return {
        "workload_sha256": hashlib.sha256((FIXTURE / "workload-manifest.json").read_bytes()).hexdigest(),
        "verifier_sha256": hashlib.sha256(verifier.read_bytes()).hexdigest(),
    }


def coding_fact(cell: str, result: dict, checkpoint: dict, crash: dict, recovery: dict, *, equivalent: bool, negative: bool = False, compaction: dict | None = None) -> dict:
    return {
        "cell": cell,
        "host": host_identity(result["host"]),
        "freeze": freeze_fields(FIXTURE / "sealed-workloads" / "coding" / "verify_complete.py"),
        "checkpoint": {"identity": "p5-route-stage-one", "artifact_sha256": checkpoint["artifact_sha256"]},
        "crash": crash,
        "recovery": recovery,
        "compaction": compaction or {"native": False, "event_observed": False},
        "effect": {"first_operation": "not-applicable", "decision": "not-applicable"},
        "final": ({"correct_termination": True, "unauthorized_action": False} if negative else {"verified": verify_command(Path(result["workspace"]), "verify_complete.py"), "artifact_equivalent": equivalent}),
    }


def execute_reference(run_root: Path) -> dict:
    validate_workload_manifest(FIXTURE)
    if run_root.exists():
        raise RuntimeError(f"reference run root already exists: {run_root}")
    run_root.mkdir(parents=True)
    coding_source = FIXTURE / "sealed-workloads" / "coding"
    effect_source = FIXTURE / "sealed-workloads" / "effect"
    rows: list[dict] = []

    u_dir = run_root / "u"
    copy_workload(coding_source, u_dir / "workspace")
    u = completed_child(FIXTURE, "coding-uninterrupted", u_dir)
    u_workspace = u_dir / "workspace"
    u_digest = artifact_digest(u_workspace, ("route_report.py", "completion.txt"))
    u["workspace"] = str(u_workspace)
    rows.append(coding_fact("U", u, {"artifact_sha256": hashlib.sha256((u_workspace / "route_report.py").read_bytes()).hexdigest()}, {"boundary": "none", "identity": u["host"]["pid"]}, {"identity": u["host"]["pid"], "transcript_available": True, "first_operation": "not-applicable"}, equivalent=True))

    for cell, blocked in (("R", False), ("R_NEG", True)):
        directory = run_root / cell.lower()
        copy_workload(coding_source, directory / "workspace")
        crash, exit_code = killed_checkpoint_child(FIXTURE, "coding-hold", directory, blocked=blocked)
        recovery = completed_child(FIXTURE, "coding-recovery", directory, blocked=blocked)
        workspace = directory / "workspace"
        recovery["workspace"] = str(workspace)
        first = "reobserve" if first_action_matches(recovery["host"], ".cairn-continuation.json") else "action"
        rows.append(coding_fact(cell, recovery, crash, {"boundary": "after-clean-checkpoint", "identity": crash["host"]["pid"], "exit_code": exit_code}, {"identity": recovery["host"]["pid"], "transcript_available": False, "first_operation": first}, equivalent=(not blocked and artifact_digest(workspace, ("route_report.py", "completion.txt")) == u_digest), negative=blocked))

    for cell, blocked in (("C", False), ("C_NEG", True)):
        directory = run_root / cell.lower()
        copy_workload(coding_source, directory / "workspace")
        compacted = completed_child(FIXTURE, "coding-compaction", directory, blocked=blocked)
        workspace = directory / "workspace"
        compacted["workspace"] = str(workspace)
        first = "reobserve" if first_action_matches(compacted["host"], ".cairn-continuation.json") else "action"
        rows.append(coding_fact(cell, compacted, {"artifact_sha256": hashlib.sha256((workspace / "route_report.py").read_bytes()).hexdigest()}, {"boundary": "native-condensation", "identity": compacted["host"]["pid"]}, {"identity": compacted["host"]["pid"], "transcript_available": "compacted-host-view", "first_operation": first}, equivalent=(not blocked and artifact_digest(workspace, ("route_report.py", "completion.txt")) == u_digest), negative=blocked, compaction={"native": compacted["native"], "event_observed": compacted["event_observed"], "active_view_changed": compacted["active_view_changed"]}))

    effect_u = run_root / "effect-u"
    copy_workload(effect_source, effect_u)
    effect_u_result = completed_child(FIXTURE, "effect-uninterrupted", effect_u)
    effect_verified = verify_command(effect_u / "workspace", "verify_gateway.py")
    effect_digest = artifact_digest(effect_u / "provider", ("maintenance-windows.json",))
    effect_r = run_root / "effect-r"
    copy_workload(effect_source, effect_r)
    crash, exit_code = killed_effect_child(FIXTURE, effect_r)
    recovered = completed_child(FIXTURE, "effect-recovery", effect_r)
    effect_first = "observe" if first_action_matches(recovered, " issue_gateway.py --workspace . --provider ../provider observe") else "action"
    effect_verified_recovery = verify_command(effect_r / "workspace", "verify_gateway.py")
    rows.append({
        "cell": "EFFECT",
        "host": host_identity(recovered),
        "freeze": freeze_fields(FIXTURE / "sealed-workloads" / "effect" / "workspace" / "verify_gateway.py"),
        "checkpoint": {"identity": "p5-maintenance-intent", "artifact_sha256": hashlib.sha256((effect_r / "workspace" / "maintenance-intent.json").read_bytes()).hexdigest()},
        "crash": {"boundary": "provider-commit-before-receipt", "identity": crash["pid"], "exit_code": exit_code},
        "recovery": {"identity": recovered["pid"], "transcript_available": False, "first_operation": "not-applicable"},
        "compaction": {"native": False, "event_observed": False},
        "effect": {"first_operation": effect_first, "decision": "skip", "provider_calls": {"uninterrupted": effect_u_result["events"], "recovered": recovered["events"]}},
        "final": {"verified": effect_verified and effect_verified_recovery, "artifact_equivalent": artifact_digest(effect_r / "provider", ("maintenance-windows.json",)) == effect_digest},
    })
    from benchmarks.p5_conformance import conformance_verdict
    verdict = conformance_verdict(rows)
    write_json(run_root / "normalized-facts.json", {"runs": rows})
    write_json(run_root / "verdict.json", verdict)
    write_evidence_manifest(run_root)
    return verdict


def child(mode: str, run_dir: Path, output: Path, *, blocked: bool) -> None:
    workspace = run_dir / "workspace"
    persistence = run_dir / "persistence"
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
        raise RuntimeError(f"unknown P5 child mode: {mode}")
    write_json(output, result)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute-reference", type=Path)
    parser.add_argument("--child-mode")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--blocked", action="store_true")
    args = parser.parse_args()
    if args.execute_reference:
        print(json.dumps(execute_reference(args.execute_reference), sort_keys=True))
        return 0
    if args.child_mode and args.run_dir and args.output:
        child(args.child_mode, args.run_dir, args.output, blocked=args.blocked)
        return 0
    parser.error("pass --execute-reference or --child-mode with --run-dir and --output")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
