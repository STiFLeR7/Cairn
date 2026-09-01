"""Phase 1 RecoveryBench worker entry point."""

import argparse
from dataclasses import asdict
from pathlib import Path

import _bootstrap  # noqa: F401

from cairn.eval.recoverybench import (
    deterministic_summary,
    LiveRunConfig,
    live_pilot_evidence,
    run_baseline_worker,
    run_crash_worker,
    run_deterministic_matrix,
    run_live_matrix,
    run_resume_worker,
    normalized_records_equal,
    write_records,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", choices=("baseline", "crash", "resume"))
    parser.add_argument("--run-root", type=Path)
    parser.add_argument("--control", action="store_true")
    parser.add_argument("--live", action="append", metavar="PROVIDER:MODEL")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-calls", type=int, default=12)
    parser.add_argument("--max-chars", type=int, default=100_000)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--compare", nargs=2, type=Path)
    args = parser.parse_args()
    if args.compare:
        equal = normalized_records_equal(*args.compare)
        print(equal)
        return 0 if equal else 1
    if args.control:
        if args.output is None:
            parser.error("--control requires --output")
        results = run_deterministic_matrix(args.output.parent / "runs", args.repeats)
        records = [result.to_record() for result in results]
        write_records(records, args.output)
        print(deterministic_summary(records))
        return 0
    if args.live:
        if args.output is None:
            parser.error("--live requires --output")
        try:
            configs = [
                LiveRunConfig(
                    provider=value.split(":", 1)[0],
                    model=value.split(":", 1)[1],
                    max_calls=args.max_calls,
                    max_chars=args.max_chars,
                    max_tokens=args.max_tokens,
                )
                for value in args.live
                if ":" in value and all(value.split(":", 1))
            ]
        except IndexError:  # pragma: no cover - guarded by the comprehension
            configs = []
        if len(configs) != len(args.live):
            parser.error("--live values must use PROVIDER:MODEL")
        records = run_live_matrix(args.output.parent / "runs", configs, args.repeats)
        write_records(records, args.output)
        print(asdict(live_pilot_evidence(records)))
        return 0
    if args.worker is None or args.run_root is None:
        parser.error("--worker and --run-root are required without --control")
    if args.worker == "baseline":
        return run_baseline_worker(args.run_root)
    if args.worker == "crash":
        return run_crash_worker(args.run_root)
    return run_resume_worker(args.run_root)


if __name__ == "__main__":
    raise SystemExit(main())
