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


def write_preregistration(root: str = ".") -> dict:
    try:
        commit = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True,
                                text=True, check=False).stdout.strip() or None
    except FileNotFoundError:
        commit = None
    record = {"files": snapshot(root), "git_commit": commit,
              "created_utc": datetime.now(timezone.utc).isoformat()}
    path = os.path.join(root, PREREG)
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
    if sys.argv[1:] == ["write"]:
        print(json.dumps(write_preregistration(), indent=2))
    else:
        problems = verify()
        print("OK" if not problems else "\n".join(problems))
        sys.exit(1 if problems else 0)
