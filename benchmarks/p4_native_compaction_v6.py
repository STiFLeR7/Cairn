"""V6 supplements sealed V5 evidence with the two missing Phase 4 controls."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import uuid

from benchmarks.p4_claude_code import run_claude_session
from benchmarks.p4_freeze import freeze_phase4_inputs, phase4_inputs_match
from benchmarks.p4_forked_checkpoint import clone_checkpoint, release_stage2, run_uninterrupted_and_capture, snapshot
from benchmarks.p4_native_compaction_v5 import (COMPACTED_RESUME_PROMPT, CRASH_READY_PROMPT,
                                                FRESH_RECOVERY_PROMPT, REOBSERVE_WAIT_PROMPT, WAIT_PROMPT,
                                                run_native_session)


HOLDOUT_TASK = """# Sealed V6 independent coding holdout

Implement `normalize_label(value)` in `labels.py`. It must strip whitespace, collapse internal
whitespace to one hyphen, and lowercase the result. Run `python verify.py`. Only after it passes,
create `.cairn-action-map.json` with exactly this object (keys may be reordered):

{"schema_version":"cairn.p4-action-map.v1","actions":{"release_to_finalize":{"required_file":".cairn-release-stage2","preflight":["python verify.py"],"commands":["python advance.py","python verify_final.py"],"success_file":"release.txt"}}}

Then write `.cairn-continuation.json` with Continuation Contract v0 fields `intent`,
`active_subgoal`, `accepted_decisions`, `verified_work`, `verification_state`, `world_digest`,
`checkpoint_provenance`, `stop_condition`, `next_action`, and `first_recovery_operation` set to
`reobserve`. Set `next_action` exactly to `release_to_finalize`. Do not include a session ID or
transcript, and do not create `release.txt` before `.cairn-release-stage2` exists. Once released,
use the action map and stop after its final verifier passes.
"""

HOLDOUT_VERIFY = """from labels import normalize_label

assert normalize_label('  Blue   Sky ') == 'blue-sky'
assert normalize_label('One') == 'one'
print('verified')
"""

HOLDOUT_ADVANCE = """from pathlib import Path

assert Path('.cairn-release-stage2').is_file()
Path('release.txt').write_text('holdout-release-complete\\n', encoding='utf-8')
print('advanced')
"""

HOLDOUT_FINAL = """from pathlib import Path
from labels import normalize_label

assert normalize_label('  Blue   Sky ') == 'blue-sky'
assert Path('release.txt').read_text(encoding='utf-8') == 'holdout-release-complete\\n'
print('final-verified')
"""


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def prepare_holdout(workspace: Path) -> Path:
    workspace.mkdir(parents=True, exist_ok=True)
    for name, value in {"TASK.md": HOLDOUT_TASK, "verify.py": HOLDOUT_VERIFY,
                        "advance.py": HOLDOUT_ADVANCE, "verify_final.py": HOLDOUT_FINAL}.items():
        (workspace / name).write_text(value, encoding="utf-8")
    return workspace


def _freeze_paths(root: Path) -> list[Path]:
    repo = Path(__file__).resolve().parents[1]
    modules = ("p4_native_compaction_v6.py", "p4_native_compaction_v6_verdict.py",
               "p4_native_compaction_v5.py", "p4_claude_code.py", "p4_forked_checkpoint.py", "p4_freeze.py")
    return [*sorted(path for path in (root / "sealed-workloads").rglob("*") if path.is_file()),
            *(repo / "benchmarks" / name for name in modules)]


def _native_wait_then_compact(claude: str, workspace: Path, root: Path, label: str) -> str:
    session_id = str(uuid.uuid4())
    run_native_session(claude, workspace, root / f"{label}-initial", WAIT_PROMPT, session_id, False)
    for number in range(1, 5):
        run_native_session(claude, workspace, root / f"{label}-pre-compact-{number}", REOBSERVE_WAIT_PROMPT, session_id, True)
    compact = run_native_session(claude, workspace, root / f"{label}-compact", "/compact", session_id, True)
    if compact.get("native_compaction", {}).get("trigger") != "manual":
        raise RuntimeError("Claude Code did not produce a native manual compact boundary")
    return session_id


def prepare(root: Path) -> dict:
    if root.exists():
        raise RuntimeError(f"protocol root already exists: {root}")
    from benchmarks.p4_native_compaction_v5 import prepare_workspace
    reference = prepare_workspace(root / "sealed-workloads" / "reference-source")
    holdout = prepare_holdout(root / "sealed-workloads" / "holdout-source")
    _write(root / "protocol.json", {"schema_version": "cairn.p4-native-compaction.v0.2",
                                     "status": "sealed-before-execution",
                                     "purpose": "V6: post-compaction causal negative plus independent generic U/R/C holdout"})
    _write(root / "prepared-contexts.json", {"reference": str(reference), "holdout": str(holdout)})
    _write(root / "pre-run-freeze.json", freeze_phase4_inputs(_freeze_paths(root),
        {"phase": "P4", "purpose": "seal V6 causal-compaction and independent holdout controls"}))
    return {"reference": str(reference), "holdout": str(holdout)}


def _mutate_next_action(workspace: Path, value: str) -> None:
    path = workspace / ".cairn-continuation.json"
    projection = json.loads(path.read_text(encoding="utf-8"))
    projection["next_action"] = value
    _write(path, projection)


def run(claude: str, root: Path, v5_root: Path) -> None:
    controls = json.loads((root / "pre-run-freeze.json").read_text(encoding="utf-8"))
    if not phase4_inputs_match(controls):
        raise RuntimeError("pre-run controls changed; refuse to launch host")
    if not (v5_root / "evidence-manifest.json").is_file():
        raise RuntimeError("V5 evidence manifest is required as the fixed reference/effect control")

    # Same persisted host session knows the original task; only durable next_action is made incompatible after compacting.
    reference_source = Path(json.loads((root / "prepared-contexts.json").read_text(encoding="utf-8"))["reference"])
    reference_checkpoint = root / "reference-checkpoint" / "workspace"
    run_uninterrupted_and_capture(claude, reference_source, root / "reference-u", reference_checkpoint)
    snapshot(reference_source, root, "reference-u")
    c_negative = clone_checkpoint(reference_checkpoint, root / "branches" / "reference-c-negative")
    session_id = _native_wait_then_compact(claude, c_negative, root, "reference-c-negative")
    _mutate_next_action(c_negative, "unmapped_post_compaction_control")
    release_stage2(c_negative)
    run_native_session(claude, c_negative, root / "reference-c-negative-resume", COMPACTED_RESUME_PROMPT, session_id, True)
    snapshot(c_negative, root, "reference-c-negative")

    holdout_source = Path(json.loads((root / "prepared-contexts.json").read_text(encoding="utf-8"))["holdout"])
    holdout_checkpoint = root / "holdout-checkpoint" / "workspace"
    run_uninterrupted_and_capture(claude, holdout_source, root / "holdout-u", holdout_checkpoint)
    snapshot(holdout_source, root, "holdout-u")
    holdout_r = clone_checkpoint(holdout_checkpoint, root / "branches" / "holdout-r")
    run_claude_session(claude, holdout_r, root / "holdout-r-crash", CRASH_READY_PROMPT, False,
                       holdout_r / ".cairn-rgr-ready", ("labels.py",))
    release_stage2(holdout_r)
    run_claude_session(claude, holdout_r, root / "holdout-r-recovery", FRESH_RECOVERY_PROMPT, False,
                       artifacts=("labels.py", "release.txt"))
    snapshot(holdout_r, root, "holdout-r")
    holdout_c = clone_checkpoint(holdout_checkpoint, root / "branches" / "holdout-c")
    session_id = _native_wait_then_compact(claude, holdout_c, root, "holdout-c")
    release_stage2(holdout_c)
    run_native_session(claude, holdout_c, root / "holdout-c-resume", COMPACTED_RESUME_PROMPT, session_id, True,
                       ("labels.py", "release.txt"))
    snapshot(holdout_c, root, "holdout-c")
    _write(root / "execution-complete.json", {"schema_version": "cairn.p4-native-compaction.v0.2", "status": "complete"})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--claude", required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--v5-root", type=Path, required=True)
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    prepare(args.root) if args.prepare else run(args.claude, args.root, args.v5_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
