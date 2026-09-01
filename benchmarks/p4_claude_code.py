"""Thin Claude Code host harness for the Phase 4 recovery proof."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
import subprocess
import threading
import time


TASK = """# Task

Implement `greet(name)` in `greeting.py`. It must return exactly `Hello, <name>!`.
Run `python verify.py`. Only after it passes, write `.cairn-continuation.json` containing:
`intent`, `active_subgoal`, `accepted_decisions`, `verified_work`, `verification_state`,
`world_digest`, `checkpoint_provenance`, `stop_condition`, `next_action`, and
`first_recovery_operation` set to `reobserve`. Do not include a session ID or transcript.
Then stop.
"""

VERIFY = """from greeting import greet

assert greet('Ada') == 'Hello, Ada!'
print('verified')
"""

EFFECT_TASK = """# External-effect task

Use only the provided `effect_tool.py` commands. First run `python effect_tool.py init`, then
`python effect_tool.py create`. The latter durably commits one external create-once resource but
does not store a durable receipt. If it returns normally, run `python effect_tool.py receipt` to
persist the receipt and close the effect. Do not invent a retry policy.

For recovery, re-observe with `python effect_tool.py observe` before any retry decision. A
matching present resource must be closed with `python effect_tool.py close-skip`; do not call
`create` again.
"""


def prepare_claude_workspace(workspace: Path) -> Path:
    workspace = Path(workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "TASK.md").write_text(TASK, encoding="utf-8")
    (workspace / "verify.py").write_text(VERIFY, encoding="utf-8")
    return workspace


def prepare_effect_workspace(workspace: Path, remote: Path) -> Path:
    """Expose the admitted P3 reference provider as a host-owned terminal command."""
    workspace = Path(workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    repository = Path(__file__).resolve().parents[1]
    tool = f'''import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path[:0] = [{str(repository)!r}, {str(repository / "src")!r}]
from benchmarks.p3_effect_service import CreateOnceProvider, Intent, Receipt
from cairn.runtime.effect_ledger import EffectLedger

WORKSPACE = Path(__file__).resolve().parent
REMOTE = Path({str(Path(remote).resolve())!r})
INTENT_PATH = WORKSPACE / ".cairn-effect-intent.json"
RESPONSE_PATH = WORKSPACE / ".cairn-provider-response.json"
OBSERVATION_PATH = WORKSPACE / ".cairn-effect-observation.json"
RECEIPT_PATH = WORKSPACE / ".cairn-effect-receipt.json"
RESOLUTION_PATH = WORKSPACE / ".cairn-effect-resolution.json"
LEDGER = WORKSPACE / ".cairn-effects.jsonl"

def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\\n", encoding="utf-8")

def intent():
    return Intent("p4-claude-create-once", "p4-claude-key", "p4-claude-request", "create-once")

def load_intent():
    return Intent(**json.loads(INTENT_PATH.read_text(encoding="utf-8")))

def main(command):
    provider = CreateOnceProvider(REMOTE)
    if command == "init":
        value = intent()
        write(INTENT_PATH, asdict(value))
        EffectLedger(str(LEDGER), "p4-claude").append_effect("create-once", value.idempotency_key, value.tool_class)
        print("intent-durable")
    elif command == "create":
        value = load_intent()
        provider.dispatch(value)
        write(RESPONSE_PATH, asdict(provider.commit(value)))
        print("provider-committed-without-durable-receipt")
    elif command == "observe":
        value = load_intent()
        observation = provider.observe(value)
        write(OBSERVATION_PATH, asdict(observation))
        print(observation.state)
    elif command in {{"receipt", "close-skip"}}:
        value = load_intent()
        observation = provider.observe(value)
        if observation.state != "present" or observation.request_fingerprint != value.request_fingerprint:
            raise SystemExit("cannot close without matching observed resource")
        receipt = Receipt(value.effect_id, value.idempotency_key, value.request_fingerprint, observation.resource_id, "commit" if command == "receipt" else "reobserve")
        write(RECEIPT_PATH, asdict(receipt))
        EffectLedger(str(LEDGER), "p4-claude").complete_effect(value.idempotency_key)
        write(RESOLUTION_PATH, {{"decision": "complete" if command == "receipt" else "skip", "observation": asdict(observation)}})
        print("closed")
    else:
        raise SystemExit("usage: effect_tool.py init|create|observe|receipt|close-skip")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) == 2 else "")
'''
    (workspace / "EFFECT_TASK.md").write_text(EFFECT_TASK, encoding="utf-8")
    (workspace / "effect_tool.py").write_text(tool, encoding="utf-8")
    return workspace


def stream_has_tool(events: list[dict], tool: str) -> bool:
    return any(
        part.get("name") == tool
        for event in events
        if event.get("type") == "assistant"
        for part in event.get("message", {}).get("content", [])
        if part.get("type") == "tool_use"
    )


def run_claude_session(
    claude: str, workspace: Path, output: Path, prompt: str, crash_after_projection: bool,
    crash_marker: Path | None = None, artifacts: tuple[str, ...] = ()
) -> dict:
    """Run a fresh Claude process; optionally kill it after its durable boundary file exists."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    projection = Path(workspace) / ".cairn-continuation.json"
    process = subprocess.Popen(
        [
            claude,
            "-p",
            "--safe-mode",
            "--setting-sources",
            "project",
            "--verbose",
            "--output-format",
            "stream-json",
            "--model",
            "sonnet",
            "--dangerously-skip-permissions",
            "--no-session-persistence",
            prompt,
        ],
        cwd=str(workspace),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    killed = False
    boundary_state = None

    def watch() -> None:
        nonlocal boundary_state, killed
        while process.poll() is None:
            if (crash_after_projection and projection.exists()) or (crash_marker is not None and crash_marker.exists()):
                boundary_state = {
                    "marker": str(crash_marker.resolve()) if crash_marker else str(projection.resolve()),
                    "marker_exists": True,
                    "receipt_exists": (Path(workspace) / ".cairn-effect-receipt.json").exists(),
                }
                process.kill()
                killed = True
                return
            time.sleep(0.005)

    watcher = threading.Thread(target=watch, daemon=True)
    watcher.start()
    stdout, stderr = process.communicate(timeout=300)
    watcher.join(timeout=1)
    events = [json.loads(line) for line in stdout.splitlines() if line.startswith("{")]
    (output / "stdout.jsonl").write_text(stdout, encoding="utf-8")
    (output / "stderr.txt").write_text(stderr, encoding="utf-8")
    record = {
        "pid": process.pid,
        "argv": process.args,
        "workspace": str(Path(workspace).resolve()),
        "returncode": process.returncode,
        "killed_after_projection": killed and crash_after_projection,
        "killed_after_marker": killed and crash_marker is not None,
        "killed_after_boundary": killed,
        "crash_marker": str(crash_marker.resolve()) if crash_marker else None,
        "boundary_state": boundary_state,
        "projection": json.loads(projection.read_text(encoding="utf-8")) if projection.exists() else None,
        "input_boundary": {
            "prompt": prompt,
            "prompt_sha256": sha256(prompt.encode("utf-8")).hexdigest(),
            "no_session_persistence": True,
            # The recovery instruction may say "no prior transcript".  Only an
            # actual session/transcript payload, not that warning, is forbidden.
            "contains_original_session_or_transcript": (
                "original_session_id" in prompt.lower()
                or "session_id=" in prompt.lower()
                or "original_transcript=" in prompt.lower()
                or "\ntranscript=" in prompt.lower()
            ),
        },
        "artifact_sha256": {
            name: sha256((Path(workspace) / name).read_bytes()).hexdigest()
            for name in artifacts if (Path(workspace) / name).is_file()
        },
        "events": events,
    }
    (output / "record.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record
