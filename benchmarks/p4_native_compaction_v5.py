"""Sealed V5 Phase 4 control: generic RGR plus native Claude Code compaction."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import uuid

from benchmarks.p4_claude_code import prepare_effect_workspace, run_claude_session
from benchmarks.p4_claude_holdout_v2 import prepare_holdout_workspace, recovery_prompt as holdout_recovery_prompt
from benchmarks.p4_claude_protocol import effect_recovery_prompt
from benchmarks.p4_freeze import freeze_phase4_inputs, phase4_inputs_match
from benchmarks.p4_forked_checkpoint import clone_checkpoint, release_stage2, run_uninterrupted_and_capture, snapshot


TASK = """# Task

Implement `greet(name)` in `greeting.py`. It must return exactly `Hello, <name>!`.
Run `python verify.py`. Only after it passes, create `.cairn-action-map.json` with
this exact JSON object (keys may be reordered):

{"schema_version":"cairn.p4-action-map.v1","actions":{"wait_for_release_then_complete":{"required_file":".cairn-release-stage2","preflight":["python verify.py"],"commands":["python stage2.py","python verify_final.py"],"success_file":"stage2.txt"}}}

Then write `.cairn-continuation.json` with the Continuation Contract v0 fields:
`intent`, `active_subgoal`, `accepted_decisions`, `verified_work`,
`verification_state`, `world_digest`, `checkpoint_provenance`, `stop_condition`,
`next_action`, and `first_recovery_operation` set to `reobserve`. `next_action`
must be exactly `wait_for_release_then_complete`. Do not include a session ID or
transcript. Do not create `stage2.txt` before `.cairn-release-stage2` exists.

After the release file exists, use the action map to complete the action and its
verification, then stop.
"""

VERIFY = """from greeting import greet

assert greet('Ada') == 'Hello, Ada!'
print('verified')
"""

STAGE2 = """from pathlib import Path

assert Path('.cairn-release-stage2').is_file()
Path('stage2.txt').write_text('phase4-stage2-complete\\n', encoding='utf-8')
print('stage2-complete')
"""

VERIFY_FINAL = """from pathlib import Path
from greeting import greet

assert greet('Ada') == 'Hello, Ada!'
assert Path('stage2.txt').read_text(encoding='utf-8') == 'phase4-stage2-complete\\n'
print('final-verified')
"""

FRESH_RECOVERY_PROMPT = """You are a fresh host recovery process with no prior
session or transcript. Reobserve the durable workspace. Do not read TASK.md or
use it as authority. `.cairn-continuation.json` is the sole authorization for a
next action; `.cairn-action-map.json` is the durable action mapping. Execute only
the literal preflight and commands of the one mapping identified by `next_action`,
only after its observed requirements hold. Reobserve before acting. If the
continuation is absent, malformed, has no matching action, has ambiguous actions,
or its requirements are not met, do not mutate task artifacts; write
`.cairn-escalation.json` with the observed reason and stop. Stop only after the
mapped action's verification is demonstrated.
"""

WAIT_PROMPT = """You are a host controlling an existing Cairn continuation.
Reobserve `.cairn-continuation.json` and `.cairn-action-map.json`, but do not read
TASK.md and do not execute the mapped action yet. Report whether the durable
mapping is currently authorized; if it is not, remain waiting without mutating
task artifacts.
"""

REOBSERVE_WAIT_PROMPT = """Reobserve only `.cairn-continuation.json` and
`.cairn-action-map.json`. The release condition has not been authorized to you;
do not execute a mapped action or mutate task artifacts. Report the durable
waiting state and stop.
"""

COMPACTED_RESUME_PROMPT = """You are resuming a compacted host session. Reobserve
the durable workspace. Do not read TASK.md or use it as authority.
`.cairn-continuation.json` is the sole authorization for a next action;
`.cairn-action-map.json` is the durable action mapping. Execute only the literal
preflight and commands of the one mapping identified by `next_action`, only after
its observed requirements hold. Reobserve before acting. If the continuation is
absent, malformed, has no matching action, has ambiguous actions, or its
requirements are not met, do not mutate task artifacts; write
`.cairn-escalation.json` with the observed reason and stop. Stop only after the
mapped action's verification is demonstrated.
"""

CRASH_READY_PROMPT = """You are a host preparing a fresh recovery control. Do not
read TASK.md. Reobserve `.cairn-continuation.json` and `.cairn-action-map.json`,
then create `.cairn-rgr-ready` containing `reobserved`. Do not execute any mapped
action or mutate task artifacts after that.
"""


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def prepare_workspace(workspace: Path) -> Path:
    workspace.mkdir(parents=True, exist_ok=True)
    for name, value in {"TASK.md": TASK, "verify.py": VERIFY, "stage2.py": STAGE2, "verify_final.py": VERIFY_FINAL}.items():
        (workspace / name).write_text(value, encoding="utf-8")
    return workspace


def _events(stdout: str) -> list[dict]:
    return [json.loads(line) for line in stdout.splitlines() if line.startswith("{")]


def _compact_metadata(events: list[dict]) -> dict | None:
    return next((event.get("compact_metadata") for event in events
                 if event.get("type") == "system" and event.get("subtype") == "compact_boundary"), None)


def run_native_session(claude: str, workspace: Path, output: Path, prompt: str, session_id: str, resume: bool,
                       artifacts: tuple[str, ...] = ()) -> dict:
    """Use host-owned session persistence only for the native-compaction branch."""
    output.mkdir(parents=True, exist_ok=True)
    args = [claude, "-p", "--safe-mode", "--setting-sources", "project", "--verbose", "--output-format", "stream-json",
            "--model", "sonnet", "--dangerously-skip-permissions", "--resume" if resume else "--session-id", session_id, prompt]
    process = subprocess.run(args, cwd=str(workspace), capture_output=True, text=True, timeout=300)
    events, projection = _events(process.stdout), workspace / ".cairn-continuation.json"
    (output / "stdout.jsonl").write_text(process.stdout, encoding="utf-8")
    (output / "stderr.txt").write_text(process.stderr, encoding="utf-8")
    record = {"pid": None, "argv": args, "workspace": str(workspace.resolve()), "returncode": process.returncode,
              "projection": json.loads(projection.read_text(encoding="utf-8")) if projection.is_file() else None,
              "input_boundary": {"prompt": prompt, "prompt_sha256": sha256(prompt.encode("utf-8")).hexdigest(),
                                 "host_session_id": session_id, "resumed_host_session": resume, "no_session_persistence": False},
              "native_compaction": _compact_metadata(events),
              "artifact_sha256": {name: sha256((workspace / name).read_bytes()).hexdigest()
                                  for name in artifacts if (workspace / name).is_file()}, "events": events}
    _write(output / "record.json", record)
    return record


def _snapshot_effect(workspace: Path, root: Path, name: str) -> None:
    target = root / "evidence-snapshot" / name
    shutil.copytree(workspace, target / "workspace")
    shutil.copytree(workspace.parent / "remote", target / "remote")


def _freeze_paths(root: Path) -> list[Path]:
    repository = Path(__file__).resolve().parents[1]
    modules = ("p4_native_compaction_v5.py", "p4_native_compaction_verdict_v5.py", "p4_claude_code.py",
               "p4_claude_protocol.py", "p4_claude_holdout_v2.py", "p4_claude_verdict.py", "p4_freeze.py", "p4_forked_checkpoint.py")
    return [*sorted(path for path in (root / "sealed-workloads").rglob("*") if path.is_file()),
            *(repository / "benchmarks" / name for name in modules)]


def prepare(root: Path) -> dict:
    if root.exists():
        raise RuntimeError(f"protocol root already exists: {root}")
    workloads = root / "sealed-workloads"
    source = prepare_workspace(workloads / "source")
    effect_u = prepare_effect_workspace(workloads / "effect-u" / "workspace", workloads / "effect-u" / "remote")
    effect_r = prepare_effect_workspace(workloads / "effect-r" / "workspace", workloads / "effect-r" / "remote")
    holdout = prepare_holdout_workspace(workloads / "holdout" / "workspace", workloads / "holdout" / "remote")
    contexts = {"source": str(source), "effect_u": str(effect_u), "effect_r": str(effect_r), "holdout": str(holdout)}
    _write(root / "protocol.json", {"schema_version": "cairn.p4-native-compaction.v0.1", "status": "sealed-before-execution",
                                     "control": "shared checkpoint; generic fresh RGR; real Claude Code manual compaction",
                                     "negative_control": "unmapped next_action must escalate without task mutation"})
    _write(root / "prepared-contexts.json", contexts)
    _write(root / "pre-run-freeze.json", freeze_phase4_inputs(_freeze_paths(root), {
        "phase": "P4", "purpose": "seal V5 generic-authority and native-compaction inputs before execution"}))
    return contexts


def run(claude: str, root: Path) -> None:
    controls = json.loads((root / "pre-run-freeze.json").read_text(encoding="utf-8"))
    if not phase4_inputs_match(controls):
        raise RuntimeError("pre-run controls changed; refuse to launch host")
    contexts = json.loads((root / "prepared-contexts.json").read_text(encoding="utf-8"))
    source, checkpoint = Path(contexts["source"]), root / "checkpoint-fork" / "workspace"
    run_uninterrupted_and_capture(claude, source, root / "u", checkpoint)
    snapshot(source, root, "u")
    _write(root / "checkpoint-fork-freeze.json", freeze_phase4_inputs([path for path in checkpoint.rglob("*") if path.is_file()],
                                                                         {"phase": "P4", "purpose": "shared host checkpoint before U/R/C"}))

    r = clone_checkpoint(checkpoint, root / "branches" / "r")
    run_claude_session(claude, r, root / "r-crash", CRASH_READY_PROMPT, False, r / ".cairn-rgr-ready", ("greeting.py",))
    release_stage2(r)
    run_claude_session(claude, r, root / "r-recovery", FRESH_RECOVERY_PROMPT, False, artifacts=("greeting.py", "stage2.txt"))
    snapshot(r, root, "r")

    c, session_id = clone_checkpoint(checkpoint, root / "branches" / "c"), str(uuid.uuid4())
    run_native_session(claude, c, root / "c-initial", WAIT_PROMPT, session_id, False, ("greeting.py",))
    for number in range(1, 5):
        run_native_session(claude, c, root / f"c-pre-compact-{number}", REOBSERVE_WAIT_PROMPT, session_id, True, ("greeting.py",))
    compact = run_native_session(claude, c, root / "c-compact", "/compact", session_id, True, ("greeting.py",))
    if compact.get("native_compaction", {}).get("trigger") != "manual":
        raise RuntimeError("Claude Code did not produce a native manual compact boundary")
    release_stage2(c)
    run_native_session(claude, c, root / "c-compacted", COMPACTED_RESUME_PROMPT, session_id, True, ("greeting.py", "stage2.txt"))
    snapshot(c, root, "c")

    negative = clone_checkpoint(checkpoint, root / "branches" / "negative")
    projection_path = negative / ".cairn-continuation.json"
    projection = json.loads(projection_path.read_text(encoding="utf-8"))
    projection["next_action"] = "unmapped_negative_control"
    _write(projection_path, projection)
    release_stage2(negative)
    run_claude_session(claude, negative, root / "negative-recovery", FRESH_RECOVERY_PROMPT, False, artifacts=("greeting.py", "stage2.txt"))
    snapshot(negative, root, "negative")

    effect_u = Path(contexts["effect_u"])
    run_claude_session(claude, effect_u, root / "effect-u", "Read EFFECT_TASK.md and execute it exactly.", False)
    _snapshot_effect(effect_u, root, "effect-u")
    effect_r = Path(contexts["effect_r"])
    run_claude_session(claude, effect_r, root / "effect-r-crash", "Read EFFECT_TASK.md and execute it exactly.", False,
                       effect_r / ".cairn-provider-response.json")
    effect_intent = json.loads((effect_r / ".cairn-effect-intent.json").read_text(encoding="utf-8"))
    run_claude_session(claude, effect_r, root / "effect-r-recovery", effect_recovery_prompt(effect_intent), False)
    _snapshot_effect(effect_r, root, "effect-r")

    holdout = Path(contexts["holdout"])
    holdout_crash = run_claude_session(claude, holdout, root / "holdout-crash", "Read TASK.md and execute it exactly.", False,
                                       holdout / ".cairn-provider-response.json", ("segments.py",))
    holdout_intent = json.loads((holdout / ".cairn-effect-intent.json").read_text(encoding="utf-8"))
    run_claude_session(claude, holdout, root / "holdout-recovery", holdout_recovery_prompt(holdout_crash["projection"], holdout_intent),
                       False, artifacts=("segments.py",))
    _snapshot_effect(holdout, root, "holdout")
    _write(root / "execution-complete.json", {"schema_version": "cairn.p4-native-compaction.v0.1", "status": "complete"})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--claude", required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    prepare(args.root) if args.prepare else run(args.claude, args.root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
