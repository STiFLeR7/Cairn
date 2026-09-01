"""U/R/C control for the independently authored non-batchable chain task."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

try:  # Script execution puts benchmarks/ on sys.path.
    import _bootstrap  # noqa: F401
except ModuleNotFoundError:  # Package import is used by the test suite.
    from benchmarks import _bootstrap  # noqa: F401

from cairn.app import build_harness
from cairn.eval.phase2 import compacted_continuation
from cairn.harness.agent_loop import regrounded_history
from cairn.model_live import LiveModelProvider, render_prompt
from cairn.runtime.digest import world_digest
from benchmarks.scenarios import ChainTask, fake_chain_transport


def _model(n: int) -> LiveModelProvider:
    return LiveModelProvider(fake_chain_transport(n))


def _compacted_model(n: int, prompt: str) -> LiveModelProvider:
    return LiveModelProvider(
        fake_chain_transport(n),
        render=lambda _goal, history: prompt + "\n\n" + render_prompt("", history),
    )


def _branch(base_dir: Path, branch: str, n: int, split_step: int, *, compact: bool = False) -> dict:
    branch_dir = base_dir / branch
    task = ChainTask(n, f"chain-{n}-neutral")
    harness, runtime = build_harness(
        model=_model(n),
        base_dir=str(branch_dir),
        model_version="fake/control",
        max_steps=n + 2,
    )
    loaded = runtime.load_latest()
    if loaded is None:
        raise ValueError("branch checkpoint is missing")
    state = loaded[0]
    if compact:
        continuation = compacted_continuation(state)
        harness = build_harness(
            model=_compacted_model(n, continuation.prompt),
            base_dir=str(branch_dir),
            model_version="fake/compacted-control",
            max_steps=n + 2,
        )[0]
        result = harness.continue_from(task, continuation.history)
    elif branch == "R":
        result = harness.resume(task)
    else:
        result = harness.continue_from(task, regrounded_history(state.durable_core.plan))
    digest = world_digest(runtime.workspace_dir)
    return {
        "success": task.is_complete(runtime.workspace_dir),
        "work_units": task.progress(runtime.workspace_dir),
        "final_digest": digest,
        "resumed": result.resumed,
    }


def run_chain_urc(base_dir: Path, *, n: int = 6, model_factory: str = "fake", output: Path | None = None) -> dict:
    """Run deterministic U/R/C branches from one clean chain checkpoint."""
    if model_factory != "fake":
        raise ValueError("only the deterministic fake model is supported by this control")
    if n < 2:
        raise ValueError("n must be at least 2")
    base_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for split_step in range(n - 1):
        cell_dir = base_dir / f"split-{split_step}"
        prefix_dir = cell_dir / "prefix"
        task = ChainTask(n, f"chain-{n}-neutral")
        harness, runtime = build_harness(
            model=_model(n),
            base_dir=str(prefix_dir),
            model_version="fake/control",
            max_steps=split_step + 1,
        )
        result = harness.run(task)
        if not result.final_state or task.progress(runtime.workspace_dir) != split_step + 1:
            raise ValueError("deterministic prefix did not produce the registered checkpoint")
        branches = {}
        for name in ("U", "R", "C"):
            branch_dir = cell_dir / name
            shutil.copytree(prefix_dir, branch_dir)
            branches[name] = _branch(
                cell_dir,
                name,
                n,
                split_step,
                compact=name == "C",
            )
        records.append({
            "fixture": f"chain-{n}",
            "split_step": split_step,
            "prefix_work_units": split_step + 1,
            "branches": branches,
            "digests_equal": len({tuple(branches[name]["final_digest"].items()) for name in branches}) == 1,
        })
    evidence = {
        "schema_version": "cairn.phase-2-chain-urc.v0.1",
        "control": {"model": model_factory, "task": f"chain-{n}", "prefix": "clean checkpoint"},
        "cells": len(records),
        "complete_triplets": sum(all(row["branches"][name]["success"] for name in ("U", "R", "C")) for row in records),
        "records": records,
    }
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=6)
    parser.add_argument("--base-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run_chain_urc(args.base_dir, n=args.n, output=args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
