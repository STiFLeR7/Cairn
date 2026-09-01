"""Hash-pinned freeze helpers for the isolated P2.4 evidence program."""

from __future__ import annotations

import hashlib
from pathlib import Path


def _fingerprint(path: Path) -> dict:
    content = path.read_bytes()
    return {
        "path": str(path),
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
    }


def freeze_manifest(paths: list[Path], metadata: dict) -> dict:
    """Capture exact bytes for the fixed P2.4 boundary."""
    return {
        "schema_version": "cairn.p24-freeze.v0.1",
        "metadata": dict(metadata),
        "files": [_fingerprint(Path(path)) for path in paths],
    }


def frozen_paths_match(manifest: dict) -> bool:
    """Return whether every recorded path still has identical bytes."""
    try:
        return all(
            _fingerprint(Path(item["path"])) == item
            for item in manifest["files"]
        )
    except (KeyError, OSError):
        return False
