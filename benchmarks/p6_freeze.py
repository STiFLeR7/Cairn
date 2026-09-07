"""Portable hash freeze for the P6 conformance proof boundary."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path
import subprocess
import sys
from typing import Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
BASELINE_COMMIT = "4db80e0b9f0b6ba01ec92a50060c4b8d6a6e97fb"
FROZEN_PATHS = (
    "docs/design/continuation-contract-v0.md",
    "docs/design/receipt-reconciliation-contract-v0.md",
    "results/phase-1/REPORT.md",
    "results/phase-2/p24-verdict.json",
    "results/phase-3/p3-verdict.json",
    "results/phase-4/reconstitution-v6/verdict.json",
    "results/phase-5/two-host-portability-verdict.json",
    "benchmarks/p5_conformance.py",
    "docs/superpowers/specs/2026-09-07-p6-independent-ecosystem-conformance-design.md",
)


def _fingerprint(root: Path, path: Path) -> dict:
    root = root.resolve()
    path = path.resolve()
    relative = path.relative_to(root)
    content = path.read_bytes()
    return {
        "path": relative.as_posix(),
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def freeze_manifest(
    root: Path,
    paths: Sequence[Path],
    metadata: Mapping[str, object],
) -> dict:
    """Capture byte-identical inputs using paths relative to ``root``."""
    return {
        "schema_version": "cairn.p6-freeze.v0",
        "metadata": dict(metadata),
        "files": [_fingerprint(root, path) for path in paths],
    }


def frozen_paths_match(root: Path, manifest: Mapping[str, object]) -> bool:
    """Return whether every recorded path still has identical bytes."""
    try:
        files = manifest["files"]
        return all(
            _fingerprint(root, root / item["path"]) == item
            for item in files
        )
    except (KeyError, OSError, TypeError, ValueError):
        return False


def _branch(root: Path) -> str:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output", type=Path)
    mode.add_argument("--check", type=Path)
    args = parser.parse_args()

    if args.check:
        manifest = json.loads(args.check.read_text(encoding="utf-8"))
        return 0 if (
            manifest.get("schema_version") == "cairn.p6-freeze.v0"
            and frozen_paths_match(ROOT, manifest)
        ) else 1

    manifest = freeze_manifest(
        ROOT,
        [ROOT / path for path in FROZEN_PATHS],
        {
            "state": "FROZEN_OBLIGATIONS",
            "baseline_commit": BASELINE_COMMIT,
            "branch": _branch(ROOT),
            "python": sys.version,
            "platform": platform.platform(),
        },
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(manifest, stream, indent=2, sort_keys=True)
        stream.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
