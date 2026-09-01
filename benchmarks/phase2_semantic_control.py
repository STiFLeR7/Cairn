"""Deterministic compaction control for the Phase 2 semantic boundary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:  # Script execution puts benchmarks/ on sys.path.
    import _bootstrap  # noqa: F401
except ModuleNotFoundError:  # Package import is used by the test suite.
    from benchmarks import _bootstrap  # noqa: F401

from cairn.eval.phase2 import run_live_urc
from cairn.eval.recoverybench import LiveRunConfig, load_fixture
from cairn.runtime.digest import world_digest


FIXTURES = ("bugfix", "config", "tests", "followup")


def run_semantic_control(base_dir: Path, *, output: Path | None = None) -> dict:
    """Exercise every non-terminal split with a deterministic fake coding agent."""
    base_dir.mkdir(parents=True, exist_ok=True)
    config = LiveRunConfig(provider="fake", model="control")
    records = []
    for fixture_name in FIXTURES:
        fixture = load_fixture(fixture_name)
        for split_step in range(fixture.work_units - 1):
            record = run_live_urc(
                base_dir,
                fixture_name,
                split_step=split_step,
                config=config,
                prefix_mode="control",
                prompt_composition="legacy",
                verification_mode="empty",
            )
            run_root = base_dir / record["run_id"]
            for branch in ("U", "R", "C"):
                root = run_root / branch / fixture_name
                record["branches"][branch]["final_digest"] = world_digest(str(root))
            records.append(record)

    complete = [
        record for record in records
        if all(record["branches"][branch].get("success") for branch in ("U", "R", "C"))
    ]
    mismatches = sum(
        len({
            tuple(record["branches"][branch].get("final_digest", {}).items())
            for branch in ("U", "R", "C")
        }) > 1
        for record in complete
    )
    evidence = {
        "schema_version": "cairn.phase-2-semantic-control.v0.1",
        "control": {
            "provider": "fake",
            "model": "control",
            "prefix_mode": "control",
            "prompt_composition": "legacy",
            "verification_mode": "empty",
        },
        "fixtures": list(FIXTURES),
        "cells": len(records),
        "complete_triplets": len(complete),
        "digest_mismatches": mismatches,
        "records": records,
    }
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-dir", type=Path)
    args = parser.parse_args()
    run_semantic_control(args.base_dir or args.output.parent / "semantic-control-runs", output=args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
