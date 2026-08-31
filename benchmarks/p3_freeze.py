"""Hash-based external baseline freeze for the Phase 3 proof harness."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path


def _entry(path: Path) -> dict:
    data = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(data), "sha256": sha256(data).hexdigest()}


def freeze_manifest(paths: list[Path], metadata: dict) -> dict:
    return {"schema_version": "cairn.p3-freeze.v0.1", "metadata": metadata, "entries": [_entry(path) for path in paths]}


def frozen_paths_match(manifest: dict) -> bool:
    return all(Path(entry["path"]).is_file() and _entry(Path(entry["path"])) == entry for entry in manifest["entries"])
