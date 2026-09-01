"""Pre-pinned Phase 4 Claude Code reconstitution protocol."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

from benchmarks.p4_claude_code import prepare_claude_workspace, prepare_effect_workspace, run_claude_session
from benchmarks.p4_claude_holdout_v2 import prepare_holdout_workspace, recovery_prompt as holdout_recovery_prompt
from benchmarks.p4_freeze import phase4_inputs_match


TASK_PROMPT = "Read TASK.md and execute it exactly."
SCHEMA = "cairn.p4-claude-code-reconstitution.v0.1"


def coding_recovery_prompt(projection: dict, compacted: bool = False) -> str:
    mode = "compacted continuation" if compacted else "recovery process"
    return (
        f"You are a fresh {mode} with no prior session or transcript. The sole continuation input is:\n"
        + json.dumps(projection, sort_keys=True)
        + "\nFirst reobserve the workspace by reading TASK.md and running python verify.py. If it passes, "
        "preserve the verified work and stop. Do not write or change the continuation file."
    )


def effect_recovery_prompt(intent: dict) -> str:
    return (
        "You are a fresh recovery process with no prior session or transcript. The sole external continuity input is:\n"
        + json.dumps(intent, sort_keys=True)
        + "\nYour first command must be python effect_tool.py observe. Do not inspect files first. If its output is "
        "present, run python effect_tool.py close-skip, do not run init, create, or receipt, then stop. If it is "
        "absent, unknown, or mismatch, stop without retry and report escalation."
    )


def _snapshot(workspace: Path, root: Path, name: str) -> None:
    target = root / "evidence-snapshot" / name
    shutil.copytree(workspace, target / "workspace")
    remote = workspace.parent / "remote"
    if remote.is_dir():
        shutil.copytree(remote, target / "remote")


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def prepare(root: Path) -> dict:
    """Materialize and seal every public workload before a host process runs."""
    root.mkdir(parents=True, exist_ok=True)
    if (root / "prepared-contexts.json").exists():
        raise RuntimeError(f"prepared protocol already exists: {root}")
    workloads = root / "sealed-workloads"
    u, r, c = workloads / "u", workloads / "r", workloads / "c"
    effect_u_root, effect_r_root, holdout_root = workloads / "effect-u", workloads / "effect-r", workloads / "holdout"
    prepare_claude_workspace(u)
    prepare_claude_workspace(r)
    prepare_claude_workspace(c)
    prepare_effect_workspace(effect_u_root / "workspace", effect_u_root / "remote")
    prepare_effect_workspace(effect_r_root / "workspace", effect_r_root / "remote")
    prepare_holdout_workspace(holdout_root / "workspace", holdout_root / "remote")
    contexts = {
        "u": str(u), "r": str(r), "c": str(c),
        "effect_u": str(effect_u_root / "workspace"),
        "effect_r": str(effect_r_root / "workspace"),
        "holdout": str(holdout_root / "workspace"),
    }
    _write_json(root / "protocol.json", {
        "schema_version": SCHEMA,
        "status": "sealed-before-execution",
        "task_prompt": TASK_PROMPT,
        "coding_recovery_template": "fresh process; sole continuation input; reobserve TASK.md and verify.py; preserve verified work; stop",
        "effect_recovery_template": "fresh process; sole external input; first command observe; matching present closes skip; all other observations escalate",
    })
    _write_json(root / "prepared-contexts.json", contexts)
    return contexts


def run(claude: str, root: Path) -> None:
    freeze_path = root / "pre-run-freeze.json"
    if not freeze_path.is_file() or not phase4_inputs_match(json.loads(freeze_path.read_text(encoding="utf-8"))):
        raise RuntimeError("pre-run controls are absent or changed; refuse to launch host")
    contexts = json.loads((root / "prepared-contexts.json").read_text(encoding="utf-8"))
    u = Path(contexts["u"])
    run_claude_session(claude, u, root / "u", TASK_PROMPT, False, artifacts=("greeting.py",))
    _snapshot(u, root, "u")

    r = Path(contexts["r"])
    crash = run_claude_session(claude, r, root / "r-crash", TASK_PROMPT, True, artifacts=("greeting.py",))
    run_claude_session(claude, r, root / "r-recovery", coding_recovery_prompt(crash["projection"]), False, artifacts=("greeting.py",))
    _snapshot(r, root, "r")

    c = Path(contexts["c"])
    initial = run_claude_session(claude, c, root / "c-initial", TASK_PROMPT, False, artifacts=("greeting.py",))
    run_claude_session(claude, c, root / "c-compacted", coding_recovery_prompt(initial["projection"], True), False, artifacts=("greeting.py",))
    _snapshot(c, root, "c")

    effect_u = Path(contexts["effect_u"])
    run_claude_session(claude, effect_u, root / "effect-u", "Read EFFECT_TASK.md and execute it exactly.", False)
    _snapshot(effect_u, root, "effect-u")
    effect_r = Path(contexts["effect_r"])
    crash = run_claude_session(claude, effect_r, root / "effect-r-crash", "Read EFFECT_TASK.md and execute it exactly.", False, effect_r / ".cairn-provider-response.json")
    intent = json.loads((effect_r / ".cairn-effect-intent.json").read_text(encoding="utf-8"))
    run_claude_session(claude, effect_r, root / "effect-r-recovery", effect_recovery_prompt(intent), False)
    _snapshot(effect_r, root, "effect-r")

    holdout = Path(contexts["holdout"])
    crash = run_claude_session(claude, holdout, root / "holdout-crash", TASK_PROMPT, False, holdout / ".cairn-provider-response.json", ("segments.py",))
    intent = json.loads((holdout / ".cairn-effect-intent.json").read_text(encoding="utf-8"))
    run_claude_session(claude, holdout, root / "holdout-recovery", holdout_recovery_prompt(crash["projection"], intent), False, artifacts=("segments.py",))
    _snapshot(holdout, root, "holdout")
    _write_json(root / "execution-complete.json", {"schema_version": SCHEMA, "status": "complete"})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--claude", required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        prepare(args.root)
    else:
        run(args.claude, args.root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
