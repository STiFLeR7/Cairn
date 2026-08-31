"""Execute only the public cases of the independently authored P3 holdout."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    import _bootstrap  # noqa: F401
except ModuleNotFoundError:
    from benchmarks import _bootstrap  # noqa: F401

from benchmarks.p3_harness import run_p3_cell


def _fault(observation: str) -> dict:
    return {
        "absent": {"boundary": "dispatch", "expected_intended_effect": True},
        "present": {"boundary": "commit", "expected_intended_effect": True},
        "unknown": {"boundary": "dispatch", "unknown_on_recovery": True, "expected_intended_effect": False},
        "mismatch": {"boundary": "commit", "seed_mismatch": True, "expected_intended_effect": False},
    }[observation]


def holdout_cells(author: dict, repetitions: int) -> list[dict]:
    cells = []
    for repetition in range(1, repetitions + 1):
        for index, case in enumerate(author["acceptance_cases"], start=1):
            observation = case["observation"]
            fault = _fault(observation)
            cells.append(
                fault | {
                    "id": f"holdout-case-{index}-r{repetition}",
                    "row": f"holdout-case-{index}",
                    "repetition": repetition,
                    "tool_class": case["tool_class"],
                    "expected_decision": case["decision"],
                    "holdout": True,
                }
            )
    return cells


def run_holdout(author: dict, repetitions: int, output_dir: Path) -> list[dict]:
    records = []
    for cell in holdout_cells(author, repetitions):
        evidence = Path(output_dir) / f"{cell['row']}-r{cell['repetition']}.json"
        if evidence.exists():
            records.append(json.loads(evidence.read_text(encoding="utf-8")))
            continue
        record = run_p3_cell(cell, output_dir)
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        records.append(record)
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--author", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    run_holdout(json.loads(args.author.read_text(encoding="utf-8")), args.repetitions, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
