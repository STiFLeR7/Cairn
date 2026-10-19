"""M5 pre-registration (AP-0054): freeze protocol + verdict code hashes before any live call."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

FROZEN_FILES = [
    "results/m5/protocol.json",
    "src/cairn/eval/runner.py",
    "src/cairn/eval/calibration.py",
    "src/cairn/eval/scenario.py",
    "src/cairn/model_live.py",
    "benchmarks/scenarios.py",
    "benchmarks/m5_study.py",
]
PREREG = "results/m5/preregistration.json"


def _sha(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def snapshot(root: str = ".") -> dict:
    return {rel: _sha(os.path.join(root, rel)) for rel in FROZEN_FILES}


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
    for rel in FROZEN_FILES:
        full = os.path.join(root, rel)
        if not os.path.exists(full):
            problems.append(f"{rel}: missing")
        elif rel not in frozen or _sha(full) != frozen[rel]:
            problems.append(f"{rel}: hash differs from preregistration")
    return problems


if __name__ == "__main__":
    if sys.argv[1:] == ["write"]:
        print(json.dumps(write_preregistration(), indent=2))
    else:
        problems = verify()
        print("OK" if not problems else "\n".join(problems))
        sys.exit(1 if problems else 0)
