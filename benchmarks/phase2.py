"""Phase 2 evidence commands; no benchmark or runtime semantics live here."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:  # Script execution puts benchmarks/ on sys.path.
    import _bootstrap  # noqa: F401
except ModuleNotFoundError:  # Package import is used by the test suite.
    from benchmarks import _bootstrap  # noqa: F401

from cairn.eval.phase2 import freeze_phase_one_controls
from cairn.eval.phase2 import capture_live_urc
from cairn.eval.recoverybench import LiveRunConfig


def write_control_freeze(paths: list[Path], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(freeze_phase_one_controls(paths), indent=2) + "\n", encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", nargs="+", type=Path)
    parser.add_argument("--urc", metavar="PROVIDER:MODEL")
    parser.add_argument("--fixture", default="bugfix")
    parser.add_argument("--split-step", type=int, default=0)
    parser.add_argument("--ablate", choices=("intent", "plan", "decisions", "verification", "world"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.freeze:
        write_control_freeze(args.freeze, args.output)
    elif args.urc and ":" in args.urc:
        provider, model = args.urc.split(":", 1)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(capture_live_urc(
            args.output.parent / "runs", args.fixture, split_step=args.split_step,
            config=LiveRunConfig(provider=provider, model=model), ablate=args.ablate or "",
            evidence_path=args.output,
        ), indent=2) + "\n", encoding="utf-8")
    else:
        parser.error("use --freeze PATH... or --urc PROVIDER:MODEL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
