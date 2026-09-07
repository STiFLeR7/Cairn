"""Deterministic provider-like create-once archive-job service."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


INTENT = {
    "effect_id": "archive-job",
    "idempotency_key": "p5-archive-917",
    "request_fingerprint": "sha256:bb63c1f3e6f8d0aa",
    "tool_class": "check-before-retry",
}


def read(path: Path, default: object) -> object:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--provider", type=Path, required=True)
    parser.add_argument("command", choices=("init", "create", "observe", "receipt", "close-skip", "verify"))
    args = parser.parse_args()
    intent_path = args.workspace / "archive-intent.json"
    receipt_path = args.workspace / "archive-receipt.json"
    resolution_path = args.workspace / "archive-resolution.json"
    resources_path = args.provider / "archive-jobs.json"
    if args.command == "init":
        write(intent_path, INTENT)
        result = INTENT
    else:
        intent = read(intent_path, None)
        if intent != INTENT:
            raise SystemExit("intent is absent or mismatched")
        resources = read(resources_path, [])
        matching = [resource for resource in resources if resource["request_fingerprint"] == INTENT["request_fingerprint"]]
        observation = {"status": "present", "resource": matching[0]} if len(matching) == 1 else {"status": "absent" if not resources else "mismatch"}
        if args.command == "create":
            if observation["status"] != "absent":
                raise SystemExit("create refused: resource is not absent")
            resource = INTENT | {"resource_id": "archive-917", "period": "2026-Q3"}
            write(resources_path, [resource])
            result = {"status": "committed", "resource": resource}
        elif args.command == "observe":
            result = observation
        elif args.command in {"receipt", "close-skip"}:
            if observation["status"] != "present":
                raise SystemExit("resolution refused: provider observation is not a matching present resource")
            receipt = INTENT | {"resource_id": observation["resource"]["resource_id"], "observed_from": "reobserve" if args.command == "close-skip" else "response"}
            write(receipt_path, receipt)
            result = {"decision": "skip" if args.command == "close-skip" else "complete", "receipt": receipt}
            write(resolution_path, result)
        else:
            receipt = read(receipt_path, None)
            resolution = read(resolution_path, None)
            result = {"verified": len(resources) == 1 and observation["status"] == "present" and receipt is not None and resolution is not None}
            if not result["verified"]:
                raise SystemExit("effect verification failed")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
