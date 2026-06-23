"""World digest — a content fingerprint of the workspace (taxonomy layer 1).

Used by `distill` to record `world.digest` at checkpoint time and by the resume
protocol to detect torn/divergent writes (a file whose content no longer matches the
cairn). Hashing keeps the cairn small and the resume-time check O(files).
"""

from __future__ import annotations

import hashlib
import os


def world_digest(workspace_dir: str) -> dict[str, str]:
    """Return {relative_posix_path: sha256_hex} for every file under ``workspace_dir``.

    Deterministic and order-stable (sorted keys). Directories are implied by their
    files; empty directories are not recorded. Missing dir → empty digest.

    Python bytecode caches (``__pycache__`` dirs, ``.pyc``/``.pyo`` files) are excluded:
    they are *derived* artifacts (created when the harness imports a workspace module like a
    planted tool) with non-reproducible headers, never task output — counting them would
    corrupt solution-quality and trigger spurious torn-write detection on resume.
    """
    out: dict[str, str] = {}
    if not os.path.isdir(workspace_dir):
        return out
    for root, dirs, files in os.walk(workspace_dir):
        dirs[:] = [d for d in dirs if d != "__pycache__"]  # prune bytecode caches
        for name in files:
            if name.endswith((".pyc", ".pyo")):
                continue
            full = os.path.join(root, name)
            rel = os.path.relpath(full, workspace_dir).replace(os.sep, "/")
            out[rel] = _hash_file(full)
    return dict(sorted(out.items()))


def _hash_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
