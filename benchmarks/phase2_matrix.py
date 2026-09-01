"""Run one model's pre-registered Phase 2 U/R/C matrix, resuming from raw files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    import _bootstrap  # noqa: F401
except ModuleNotFoundError:
    from benchmarks import _bootstrap  # noqa: F401

from cairn.eval.phase2 import capture_live_urc, matrix_cell_stem, matrix_cells
from cairn.eval.recoverybench import LiveRunConfig


def next_evidence_path(output: Path) -> Path | None:
    """Preserve interrupted evidence and resume once through the registered retry path."""
    retry = output.with_suffix(".retry.json")
    for candidate in (output, retry):
        if not candidate.exists():
            return candidate
        record = json.loads(candidate.read_text(encoding="utf-8"))
        if record.get("invalid") or all(name in record.get("branches", {}) for name in ("U", "R", "C")):
            return None
    raise RuntimeError(f"both primary and retry evidence are incomplete: {output.name}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    output_dir = args.output_dir or args.protocol.parent / protocol["matrix"]["output_directory"]
    output_dir.mkdir(parents=True, exist_ok=True)
    for cell in matrix_cells(protocol):
        if cell["model"] != args.model:
            continue
        output = next_evidence_path(output_dir / f"{matrix_cell_stem(cell)}.json")
        if output is None:
            continue
        capture_live_urc(
            output_dir / "runs", cell["fixture"], split_step=cell["split_step"],
            config=LiveRunConfig(provider=cell["provider"], model=cell["model"]), evidence_path=output,
            prefix_mode=protocol["matrix"].get("prefix_mode", "live"),
            prompt_composition=protocol["matrix"].get("prompt_composition", "legacy"),
            verification_mode=protocol["matrix"].get("verification_mode", "empty"),
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
