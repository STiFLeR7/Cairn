"""Shared-checkpoint Claude Code control for Phase 4.

The host creates one verified checkpoint.  The U, crash/restart, and compacted
paths then start from byte-identical copies of that observed state, so model
generation variance cannot masquerade as recovery variance.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import threading
import time

from benchmarks.p4_claude_code import run_claude_session


TASK = """# Task

Implement `greet(name)` in `greeting.py`. It must return exactly `Hello, <name>!`.
Run `python verify.py`. Only after it passes, write `.cairn-continuation.json` with
the Continuation Contract v0 fields: `intent`, `active_subgoal`, `accepted_decisions`,
`verified_work`, `verification_state`, `world_digest`, `checkpoint_provenance`,
`stop_condition`, `next_action`, and `first_recovery_operation` set to `reobserve`.
Do not include a session ID or transcript.

Then wait until `.cairn-release-stage2` exists. After it exists, run `python stage2.py`,
then `python verify_final.py`, and stop. Do not create `stage2.txt` before the release file exists.
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


def prepare_workspace(workspace: Path) -> Path:
    workspace.mkdir(parents=True, exist_ok=True)
    for name, value in {
        "TASK.md": TASK,
        "verify.py": VERIFY,
        "stage2.py": STAGE2,
        "verify_final.py": VERIFY_FINAL,
    }.items():
        (workspace / name).write_text(value, encoding="utf-8")
    return workspace


def recovery_prompt(projection: dict, compacted: bool = False) -> str:
    mode = "compacted continuation" if compacted else "recovery process"
    return (
        f"You are a fresh {mode} with no prior session or transcript. The sole continuation input is:\n"
        + json.dumps(projection, sort_keys=True)
        + "\nFirst reobserve the workspace by reading TASK.md and running python verify.py. Then, because the "
        "release file is present, run python stage2.py and python verify_final.py. Preserve greeting.py and "
        "the continuation file. Stop after the final verifier passes."
    )


def run_uninterrupted_and_capture(claude: str, workspace: Path, output: Path, checkpoint: Path) -> dict:
    """Capture the host-produced clean checkpoint before releasing its final stage."""
    process = subprocess.Popen(
        [claude, "-p", "--safe-mode", "--setting-sources", "project", "--verbose", "--output-format", "stream-json",
         "--model", "sonnet", "--dangerously-skip-permissions", "--no-session-persistence", "Read TASK.md and execute it exactly."],
        cwd=str(workspace), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    projection = workspace / ".cairn-continuation.json"
    captured = False

    def release() -> None:
        nonlocal captured
        while process.poll() is None:
            if projection.is_file() and not captured:
                shutil.copytree(workspace, checkpoint)
                captured = True
                (workspace / ".cairn-release-stage2").write_text("release\n", encoding="utf-8")
                return
            time.sleep(0.005)

    watcher = threading.Thread(target=release, daemon=True)
    watcher.start()
    stdout, stderr = process.communicate(timeout=300)
    watcher.join(timeout=1)
    if not captured:
        raise RuntimeError("host did not produce a checkpoint for the shared fork")
    output.mkdir(parents=True, exist_ok=True)
    events = [json.loads(line) for line in stdout.splitlines() if line.startswith("{")]
    record = {
        "pid": process.pid,
        "argv": process.args,
        "returncode": process.returncode,
        "workspace": str(workspace.resolve()),
        "checkpoint_captured_before_stage2": captured,
        "projection": json.loads(projection.read_text(encoding="utf-8")),
        "input_boundary": {"prompt": "Read TASK.md and execute it exactly.", "no_session_persistence": True},
        "events": events,
    }
    (output / "stdout.jsonl").write_text(stdout, encoding="utf-8")
    (output / "stderr.txt").write_text(stderr, encoding="utf-8")
    (output / "record.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record


def clone_checkpoint(checkpoint: Path, target: Path) -> Path:
    shutil.copytree(checkpoint, target)
    return target


def release_stage2(workspace: Path) -> None:
    (workspace / ".cairn-release-stage2").write_text("release\n", encoding="utf-8")


def snapshot(workspace: Path, root: Path, name: str) -> None:
    shutil.copytree(workspace, root / "evidence-snapshot" / name / "workspace")

