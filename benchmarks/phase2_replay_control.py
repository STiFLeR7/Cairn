"""Offline replay control for causal compaction analysis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

try:  # Script execution puts benchmarks/ on sys.path.
    import _bootstrap  # noqa: F401
except ModuleNotFoundError:  # Package import is used by the test suite.
    from benchmarks import _bootstrap  # noqa: F401

from cairn.eval.phase2 import compacted_continuation, continuation_prompt
from cairn.eval.recoverybench import load_fixture, run_live_step
from cairn.model_live import LiveModelProvider
from cairn.recovery import regrounded_history
from cairn.runtime.checkpoint_store import CheckpointStore
from cairn.runtime.digest import world_digest
from cairn.runtime.effect_ledger import EffectLedger
from cairn.worlds import TerminalWorld


def replay_continuation_branch(
    run_root: Path,
    fixture_name: str,
    *,
    split_step: int,
    replies: list[str],
    output_dir: Path,
    target_branch: str,
) -> dict:
    """Replay recorded replies through a fresh recovery or compacted continuation."""
    fixture = load_fixture(fixture_name)
    loaded = CheckpointStore(str(run_root / "prefix" / "checkpoints")).load_latest()
    if loaded is None:
        raise ValueError("prefix checkpoint is missing")
    if target_branch == "C":
        branch = compacted_continuation(loaded[0])
        prompt, history = branch.prompt, list(branch.history)
    elif target_branch == "R":
        prompt = continuation_prompt(loaded[0])
        history = regrounded_history(loaded[0].durable_core.plan)
    else:
        raise ValueError(f"unknown replay target: {target_branch}")
    replay_root = output_dir / run_root.name
    workspace = replay_root / fixture_name
    shutil.copytree(run_root / "prefix" / fixture_name, workspace)
    world = TerminalWorld(str(workspace), str(replay_root / "snapshots"))
    store = CheckpointStore(str(replay_root / "checkpoints"))
    ledger = EffectLedger(str(replay_root / "effects.jsonl"), "replay")
    remaining = iter(replies)
    provider = LiveModelProvider(lambda _prompt: next(remaining, "TASK_COMPLETE"))
    result = {
        "run_id": run_root.name,
        "fixture": fixture_name,
        "split_step": split_step,
        "target_branch": target_branch,
        "replayed_replies": len(replies),
        "workspace": str(workspace),
    }
    try:
        for step in range(split_step + 1, fixture.work_units):
            run_live_step(
                prompt,
                fixture,
                world,
                store,
                ledger,
                provider,
                run_id="replay",
                step=step,
                history=history,
                model_version="replay",
            )
        result["verified"] = fixture.verify(workspace).passed
        result["success"] = result["verified"]
    except Exception as exc:  # preserve a failed replay as evidence
        result["success"] = False
        result["verified"] = False
        result["invalid"] = f"{type(exc).__name__}: {exc}"
    result["final_digest"] = world_digest(str(workspace))
    return result


def replay_compacted_branch(
    run_root: Path,
    fixture_name: str,
    *,
    split_step: int,
    replies: list[str],
    output_dir: Path,
) -> dict:
    """Backward-compatible compacted replay entry point."""
    return replay_continuation_branch(
        run_root,
        fixture_name,
        split_step=split_step,
        replies=replies,
        output_dir=output_dir,
        target_branch="C",
    )


def _transcript_replies(run_root: Path, branch: str) -> list[str]:
    transcript = run_root / branch / "continuation.transcript.jsonl"
    return [json.loads(line)["reply"] for line in transcript.read_text(encoding="utf-8").splitlines()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix-dir", type=Path, required=True)
    parser.add_argument("--records", nargs="+", type=Path, required=True)
    parser.add_argument("--source-branch", default="R", choices=("U", "R", "C"))
    parser.add_argument("--target-branch", default="C", choices=("R", "C"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    replay_dir = args.output.parent / f"{args.output.stem}-runs"
    for record_path in args.records:
        record = json.loads(record_path.read_text(encoding="utf-8"))
        run_root = next(
            (path for path in args.matrix_dir.rglob(record["run_id"]) if path.is_dir()),
            None,
        )
        if run_root is None:
            rows.append({"record": record_path.name, "success": False, "invalid": "run_root_missing"})
            continue
        rows.append(replay_continuation_branch(
            run_root,
            record["fixture"]["name"],
            split_step=record["split_step"],
            replies=_transcript_replies(run_root, args.source_branch),
            output_dir=replay_dir,
            target_branch=args.target_branch,
        ))
    evidence = {
        "schema_version": "cairn.phase-2-replay-control.v0.1",
        "source_branch": args.source_branch,
        "target_branch": args.target_branch,
        "records": rows,
        "replayed": len(rows),
        "verified": sum(row.get("verified") is True for row in rows),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
