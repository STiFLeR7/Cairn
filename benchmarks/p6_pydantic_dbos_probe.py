"""Host-only capability gate for the Pydantic AI/DBOS Phase 6 target."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

CAPABILITIES = (
    "fresh_process",
    "durable_workspace",
    "durable_journal",
    "compaction_completed",
    "active_context_changed",
    "ordered_effect_events",
    "ambiguous_effect_window",
)


def capability_verdict(observations: dict[str, bool]) -> dict:
    """Return the target gate without importing Pydantic AI, DBOS, or Cairn."""
    unknown = sorted(set(observations) - set(CAPABILITIES))
    missing = sorted(set(CAPABILITIES) - set(observations))
    if unknown:
        raise ValueError(f"unknown capabilities: {', '.join(unknown)}")
    if missing:
        raise ValueError(f"missing capabilities: {', '.join(missing)}")
    absent = [name for name in CAPABILITIES if observations[name] is not True]
    return {
        "schema_version": "cairn.p6-capability-verdict.v0",
        "passed": not absent,
        "state": "TARGET_CAPABLE" if not absent else "TARGET_STOPPED",
        "missing": absent,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("verdict",), required=True)
    parser.add_argument("--observations", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    observations = json.loads(args.observations.read_text(encoding="utf-8"))
    verdict = capability_verdict(observations)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if verdict["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
