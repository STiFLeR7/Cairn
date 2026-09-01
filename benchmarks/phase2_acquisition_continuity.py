"""Offline acquisition-versus-continuity analysis for Phase 2 U/R/C records."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

try:  # Script execution puts benchmarks/ on sys.path.
    import _bootstrap  # noqa: F401
except ModuleNotFoundError:  # Package import is used by the test suite.
    from benchmarks import _bootstrap  # noqa: F401

from cairn.eval.phase2 import matrix_cell_stem, matrix_cells


def _failure_class(branch: dict) -> str:
    detail = branch.get("invalid", "")
    if not isinstance(detail, str):
        return ""
    return detail.rsplit(": ", 1)[-1].strip()


def analyze_records(records: list[dict]) -> dict:
    """Report checkpoint acquisition separately from conditional R/C outcomes."""
    failures = {name: Counter() for name in ("U", "R", "C")}
    terminal_failures = Counter()
    acquisition_eligible = 0
    recovery_successes = compaction_successes = complete_triplets = 0
    recovery_only = compaction_only = both_fail = 0
    incomplete = 0
    for record in records:
        branches = record.get("branches", {})
        if not all(name in branches for name in ("U", "R", "C")):
            invalid = record.get("invalid")
            if invalid:
                failure = _failure_class({"invalid": invalid.get("detail", "")})
                if failure:
                    terminal_failures[failure] += 1
            else:
                incomplete += 1
            continue
        for name in ("U", "R", "C"):
            if branches[name].get("success") is not True:
                failure = _failure_class(branches[name])
                if failure:
                    failures[name][failure] += 1
        if branches["U"].get("success") is not True:
            continue
        acquisition_eligible += 1
        recovered = branches["R"].get("success") is True
        compacted = branches["C"].get("success") is True
        recovery_successes += recovered
        compaction_successes += compacted
        complete_triplets += recovered and compacted
        if not recovered and compacted:
            recovery_only += 1
        elif recovered and not compacted:
            compaction_only += 1
        elif not recovered and not compacted:
            both_fail += 1
    return {
        "attempts": len(records),
        "incomplete": incomplete,
        "terminal_invalid": sum(terminal_failures.values()),
        "acquisition": {
            "eligible": acquisition_eligible,
            "ineligible": len(records) - incomplete - acquisition_eligible,
        },
        "continuity": {
            "eligible": acquisition_eligible,
            "recovery_successes": recovery_successes,
            "compaction_successes": compaction_successes,
            "complete_triplets": complete_triplets,
        },
        "conditional_divergence": {
            "recovery_only_failures": recovery_only,
            "compaction_only_failures": compaction_only,
            "both_failures": both_fail,
        },
        "failure_classes": {
            name: dict(sorted(counts.items())) for name, counts in failures.items()
        },
        "terminal_failure_classes": dict(sorted(terminal_failures.items())),
    }


def select_matrix_records(matrix_dir: Path, protocol: dict) -> tuple[list[dict], list[str], list[str]]:
    """Select one durable record per registered cell, preferring exact retries."""
    records = []
    sources = []
    missing = []
    for cell in matrix_cells(protocol):
        stem = matrix_cell_stem(cell)
        candidates = (matrix_dir / f"{stem}.retry.json", matrix_dir / f"{stem}-complete.json", matrix_dir / f"{stem}.json")
        selected = next((path for path in candidates if path.is_file()), None)
        if selected is None:
            missing.append(stem)
            continue
        sources.append(selected.name)
        records.append(json.loads(selected.read_text(encoding="utf-8")))
    return records, sources, missing


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix-dir", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    records, sources, missing = select_matrix_records(args.matrix_dir, protocol)
    evidence = {
        "schema_version": "cairn.phase-2-acquisition-continuity.v0.1",
        "protocol": args.protocol.name,
        "matrix_dir": str(args.matrix_dir),
        "selected_sources": sources,
        "missing_cells": missing,
        **analyze_records(records),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
