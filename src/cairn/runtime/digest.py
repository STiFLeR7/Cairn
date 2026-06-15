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
    """
    out: dict[str, str] = {}
    if not os.path.isdir(workspace_dir):
        return out
    for root, _dirs, files in os.walk(workspace_dir):
        for name in files:
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
