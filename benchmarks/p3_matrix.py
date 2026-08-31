"""Fixed twelve-row Phase 3 reference matrix runner."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    import _bootstrap  # noqa: F401
except ModuleNotFoundError:
    from benchmarks import _bootstrap  # noqa: F401

from benchmarks.p3_harness import run_p3_cell, run_uninterrupted_cell


ROWS = (
    {"row": "intent-absent-retry", "tool_class": "check-before-retry", "boundary": "intent", "expected_decision": "retry", "expected_intended_effect": True},
    {"row": "dispatch-absent-retry", "tool_class": "check-before-retry", "boundary": "dispatch", "expected_decision": "retry", "expected_intended_effect": True},
    {"row": "commit-skip", "tool_class": "check-before-retry", "boundary": "commit", "expected_decision": "skip", "expected_intended_effect": True},
    {"row": "response-skip", "tool_class": "check-before-retry", "boundary": "response", "expected_decision": "skip", "expected_intended_effect": True},
    {"row": "receipt-skip", "tool_class": "check-before-retry", "boundary": "receipt", "expected_decision": "skip", "expected_intended_effect": True},
    {"row": "unknown-escalate", "tool_class": "check-before-retry", "boundary": "dispatch", "unknown_on_recovery": True, "expected_decision": "escalate", "expected_intended_effect": False},
    {"row": "mismatch-escalate", "tool_class": "check-before-retry", "boundary": "commit", "seed_mismatch": True, "expected_decision": "escalate", "expected_intended_effect": False},
    {"row": "never-retry-escalate", "tool_class": "never-retry", "boundary": "commit", "expected_decision": "escalate", "expected_intended_effect": True},
    {"row": "safe-retry-convergent", "tool_class": "safe-to-retry", "boundary": "dispatch", "expected_decision": "retry", "expected_intended_effect": True},
    {"row": "normal-check-before-retry", "tool_class": "check-before-retry", "boundary": "normal", "normal": True, "expected_decision": "complete", "expected_intended_effect": True},
    {"row": "normal-safe-to-retry", "tool_class": "safe-to-retry", "boundary": "normal", "normal": True, "expected_decision": "complete", "expected_intended_effect": True},
    {"row": "normal-never-retry", "tool_class": "never-retry", "boundary": "normal", "normal": True, "expected_decision": "complete", "expected_intended_effect": True},
)


def reference_cells(protocol: dict) -> list[dict]:
    return [
        row | {"id": f"{row['row']}-r{repetition}", "repetition": repetition}
        for repetition in range(1, protocol["matrix"]["repetitions"] + 1)
        for row in ROWS
    ]


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def run_reference_matrix(protocol: dict, output_dir: Path) -> list[dict]:
    records = []
    for cell in reference_cells(protocol):
        evidence = Path(output_dir) / f"{cell['row']}-r{cell['repetition']}.json"
        if evidence.exists():
            records.append(json.loads(evidence.read_text(encoding="utf-8")))
            continue
        record = run_uninterrupted_cell(cell, output_dir) if cell.get("normal") else run_p3_cell(cell, output_dir)
        _write(evidence, record)
        records.append(record)
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    run_reference_matrix(protocol, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
