"""Phase 4 hash freeze, reusing the admitted evidence hashing primitive."""

import argparse
import json
from pathlib import Path

from benchmarks.p3_freeze import freeze_manifest, frozen_paths_match


def freeze_phase4_inputs(paths: list[Path], metadata: dict) -> dict:
    manifest = freeze_manifest(paths, metadata)
    manifest["schema_version"] = "cairn.p4-freeze.v0.1"
    return manifest


def phase4_inputs_match(manifest: dict) -> bool:
    return manifest.get("schema_version") == "cairn.p4-freeze.v0.1" and frozen_paths_match(manifest)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    manifest = freeze_phase4_inputs(args.paths, {"phase": "P4.0", "purpose": "freeze admitted inputs"})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
