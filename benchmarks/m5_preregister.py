"""M5 pre-registration (AP-0054): freeze protocol + verdict code hashes before any live call."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

PROTOCOL = "results/m5/protocol.json"
FROZEN_GLOBS = ["src/cairn/**/*.py", "benchmarks/*.py"]
PREREG = "results/m5/preregistration.json"


def _sha(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def frozen_paths(root: str = ".") -> list[str]:
    base = Path(root)
    found = {p.relative_to(base).as_posix() for g in FROZEN_GLOBS for p in base.glob(g)
             if p.is_file() and "__pycache__" not in p.parts}
    if (base / PROTOCOL).is_file():
        found.add(PROTOCOL)
    return sorted(found)


def snapshot(root: str = ".") -> dict:
    return {rel: _sha(os.path.join(root, rel)) for rel in frozen_paths(root)}


def preregistration_digest(root: str = ".") -> str | None:
    """sha256 of the preregistration file's bytes (what every live record is bound to), or None."""
    path = os.path.join(root, PREREG)
    return _sha(path) if os.path.exists(path) else None


def _git(root: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", root, *args], capture_output=True, check=False)


def uncommitted_frozen(root: str = ".") -> list[str]:
    """Frozen paths whose working-tree bytes are not exactly the committed HEAD bytes.

    The freeze must equal what a clean checkout of the recorded commit contains. Empty when
    ``root`` is not inside a git work tree (e.g. a tmp dir in tests).
    """
    try:
        inside = _git(root, "rev-parse", "--is-inside-work-tree").stdout.strip() == b"true"
    except FileNotFoundError:
        inside = False
    if not inside:
        return []
    paths = frozen_paths(root)
    tracked = set(_git(root, "ls-files", "-z", "--", *paths).stdout.decode("utf-8").split("\0"))
    problems = []
    for rel in paths:
        if rel not in tracked:
            problems.append(f"{rel}: untracked")
            continue
        head = _git(root, "cat-file", "blob", f"HEAD:./{rel}")
        with open(os.path.join(root, rel), "rb") as f:
            if head.returncode or head.stdout != f.read():
                problems.append(f"{rel}: working-tree bytes differ from HEAD")
    return problems


def write_preregistration(root: str = ".", force: bool = False) -> dict:
    path = os.path.join(root, PREREG)
    if os.path.exists(path) and not force:
        raise FileExistsError(f"{PREREG} exists; pass force=True (write --force) to supersede it")
    problems = uncommitted_frozen(root)
    if problems:
        raise RuntimeError("refusing to freeze uncommitted bytes:\n  " + "\n  ".join(problems))
    try:
        commit = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True,
                                text=True, check=False).stdout.strip() or None
    except FileNotFoundError:
        commit = None
    record = {"files": snapshot(root), "git_commit": commit,
              "created_utc": datetime.now(timezone.utc).isoformat()}
    if os.path.exists(path):
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        os.replace(path, f"{path}.superseded-{stamp}")  # never delete
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(record, f, indent=2)
        f.write("\n")
    return record


def verify(root: str = ".") -> list[str]:
    path = os.path.join(root, PREREG)
    if not os.path.exists(path):
        return [f"no preregistration at {PREREG}"]
    with open(path, encoding="utf-8") as f:
        frozen = json.load(f)["files"]
    problems = []
    for rel, digest in sorted(frozen.items()):
        full = os.path.join(root, rel)
        if not os.path.exists(full):
            problems.append(f"{rel}: missing")
        elif _sha(full) != digest:
            problems.append(f"{rel}: hash differs from preregistration")
    for rel in frozen_paths(root):
        if rel not in frozen:
            problems.append(f"{rel}: not in preregistration")
    return problems


if __name__ == "__main__":
    if sys.argv[1:2] == ["write"]:
        print(json.dumps(write_preregistration(force="--force" in sys.argv[2:]), indent=2))
    else:
        problems = verify()
        print("OK" if not problems else "\n".join(problems))
        sys.exit(1 if problems else 0)
