"""Fresh-process U/R/C runner for the sealed P2.4 holdout."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid
import re

try:
    import _bootstrap  # noqa: F401
except ModuleNotFoundError:
    from benchmarks import _bootstrap  # noqa: F401

from cairn.eval.phase2 import compacted_continuation, continuation_prompt
from cairn.eval.recoverybench import (
    CheckpointStore,
    EffectLedger,
    _live_goal,
    _live_provider,
    _live_world,
    load_fixture,
    run_control_step,
    run_live_step,
)
from cairn.recovery import recover
from cairn.state import ContinuationState

from benchmarks.p24_fixture import NAME, register_fixture


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _wire(cell: dict) -> dict:
    return {"live": {"provider": cell["provider"], "model": cell["model"]}}


def _continue(*, name: str, fixture, root: Path, world, store, ledger, goal: str, history: list, split_step: int, cell: dict) -> dict:
    provider = _live_provider(_wire(cell), fixture, root.parent / "continuation.transcript.jsonl")
    accepted = []
    accepted_actions = []
    start = fixture.progress(root)
    for step in range(split_step + 1, fixture.work_units):
        run_live_step(goal, fixture, world, store, ledger, provider, run_id=name, step=step, history=history, model_version=cell["model"])
        accepted.append(fixture.progress(root))
        accepted_actions.append({"step": step, "kind": history[-1].action.kind, "code": history[-1].action.code})
    verified = fixture.verify(root).passed
    return {
        "start_progress": start,
        "accepted_progress": accepted,
        "accepted_actions": accepted_actions,
        "final_progress": fixture.progress(root),
        "verified": verified,
        "success": verified,
        "final_digest": world.digest(),
    }


def _worker(payload: dict) -> dict:
    register_fixture()
    fixture = load_fixture(payload["cell"]["fixture"])
    branch_dir = Path(payload["branch_dir"])
    root = branch_dir / fixture.name
    cell = payload["cell"]
    world = _live_world(root, branch_dir, _wire(cell))
    store = CheckpointStore(str(branch_dir / "checkpoints"))
    ledger = EffectLedger(str(branch_dir / "effects.jsonl"), payload["branch"])
    loaded = store.load_latest()
    if loaded is None:
        raise RuntimeError("durable checkpoint missing")
    state = loaded[0]
    if payload["branch"] == "R":
        history = recover(world, store, ledger).history
        goal = continuation_prompt(state)
        metadata = {"used_in_memory_history": False, "original_transcript_available": False, "state_serialized": False}
    else:
        compacted = compacted_continuation(ContinuationState.from_json(state.to_json()))
        history = compacted.history
        goal = compacted.prompt
        metadata = {"used_in_memory_history": False, "original_transcript_available": False, "state_serialized": True}
    record = _continue(
        name=payload["branch"], fixture=fixture, root=root, world=world, store=store, ledger=ledger,
        goal=goal, history=history, split_step=payload["cell"]["split_step"], cell=cell,
    )
    return record | metadata | {"worker_pid": os.getpid(), "parent_pid": payload["parent_pid"]}


def _run_worker(branch: str, branch_dir: Path, cell: dict, parent_pid: int) -> dict:
    request = branch_dir / "worker-input.json"
    response = branch_dir / "worker-output.json"
    _write_json(request, {"branch": branch, "branch_dir": str(branch_dir), "cell": cell, "parent_pid": parent_pid})
    command = [sys.executable, str(Path(__file__).resolve()), "--branch-worker", "--input", str(request), "--output", str(response)]
    completed = subprocess.run(command, cwd=str(Path(__file__).resolve().parents[1]), capture_output=True, text=True)
    if completed.returncode != 0:
        return {"success": False, "invalid": completed.stderr.strip() or "worker failed", "worker_pid": None}
    return json.loads(response.read_text(encoding="utf-8"))


def p24_cells(protocol: dict) -> list[dict]:
    """Enumerate the sealed two-model, three-split, ten-repetition matrix."""
    register_fixture()
    fixture = load_fixture(NAME)
    return [
        {"provider": model["provider"], "model": model["model"], "fixture": NAME, "split_step": split_step, "repetition": repetition}
        for model in protocol["matrix"]["models"]
        for repetition in range(1, protocol["matrix"]["repetitions_per_model_fixture_split"] + 1)
        for split_step in range(fixture.work_units - 1)
    ]


def _cell_stem(cell: dict) -> str:
    model = re.sub(r"[^A-Za-z0-9_.-]", "_", cell["model"])
    return f"{model}-{cell['fixture']}-s{cell['split_step']}-r{cell['repetition']:02d}"


def run_p24_cell(cell: dict, protocol: dict, output_dir: Path) -> dict:
    """Run a shared control prefix, parent U, and fresh-process R/C continuations."""
    del protocol
    register_fixture()
    fixture = load_fixture(cell["fixture"])
    split_step = cell["split_step"]
    if not 0 <= split_step < fixture.work_units - 1:
        raise ValueError("split_step must be non-terminal")
    run_dir = Path(output_dir) / f"p24-{uuid.uuid4().hex}"
    prefix_dir = run_dir / "prefix"
    root = fixture.copy_to(prefix_dir)
    wire = _wire(cell)
    world = _live_world(root, prefix_dir, wire)
    store = CheckpointStore(str(prefix_dir / "checkpoints"))
    ledger = EffectLedger(str(prefix_dir / "effects.jsonl"), "prefix")
    goal = _live_goal(fixture)
    history = []
    for step in range(split_step + 1):
        run_control_step(goal, fixture, world, store, ledger, run_id="prefix", step=step, history=history)

    parent_pid = os.getpid()
    u_dir = run_dir / "U"
    shutil.copytree(prefix_dir, u_dir)
    u_root = u_dir / fixture.name
    u_world = _live_world(u_root, u_dir, wire)
    u_store = CheckpointStore(str(u_dir / "checkpoints"))
    u_ledger = EffectLedger(str(u_dir / "effects.jsonl"), "U")
    branches = {
        "U": _continue(
            name="U", fixture=fixture, root=u_root, world=u_world, store=u_store, ledger=u_ledger,
            goal=goal, history=list(history), split_step=split_step, cell=cell,
        ) | {"worker_pid": parent_pid, "parent_pid": parent_pid, "used_in_memory_history": True, "original_transcript_available": True, "state_serialized": False},
    }
    for branch in ("R", "C"):
        branch_dir = run_dir / branch
        shutil.copytree(prefix_dir, branch_dir)
        branches[branch] = _run_worker(branch, branch_dir, cell, parent_pid)
    record = {"schema_version": "cairn.p24-urc.v0.1", "cell": cell, "run_dir": str(run_dir), "parent_pid": parent_pid, "prefix": {"progress": split_step + 1}, "branches": branches}
    _write_json(run_dir / "record.json", record)
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--branch-worker", action="store_true")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--protocol", type=Path)
    parser.add_argument("--model")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    if args.branch_worker:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        _write_json(args.output, _worker(payload))
        return 0
    if not args.protocol or not args.model or not args.output_dir:
        parser.error("--protocol, --model, and --output-dir are required")
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for cell in p24_cells(protocol):
        if cell["model"] != args.model:
            continue
        evidence = args.output_dir / f"{_cell_stem(cell)}.json"
        if evidence.exists():
            continue
        try:
            record = run_p24_cell(cell, protocol, args.output_dir / "runs")
        except Exception as exc:
            record = {"cell": cell, "invalid": f"{type(exc).__name__}: {exc}"}
        _write_json(evidence, record)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
