"""Derive the narrow Phase 4 Claude Code integration verdict from sealed raw evidence."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

from benchmarks.p4_claude_holdout_v2 import recovery_prompt as holdout_recovery_prompt
from benchmarks.p4_claude_protocol import coding_recovery_prompt, effect_recovery_prompt
from benchmarks.p4_freeze import phase4_inputs_match


FIELDS = {"intent", "active_subgoal", "accepted_decisions", "verified_work", "verification_state", "world_digest", "checkpoint_provenance", "stop_condition", "next_action", "first_recovery_operation"}


def projection_is_valid(projection: dict | None) -> bool:
    return bool(isinstance(projection, dict) and FIELDS <= set(projection)
                and projection.get("first_recovery_operation") == "reobserve"
                and not {"session_id", "original_session_id", "transcript", "original_transcript"} & set(projection)
                and projection.get("accepted_decisions") and projection.get("verified_work")
                and ("passed" in str(projection.get("verification_state", "")).lower() or "verified" in str(projection.get("verification_state", "")).lower()))


def _record(path: Path) -> dict:
    return json.loads((path / "record.json").read_text(encoding="utf-8"))


def _tools(record: dict) -> list[dict]:
    return [{"name": part.get("name"), "command": part.get("input", {}).get("command", "")}
            for event in record["events"] if event.get("type") == "assistant"
            for part in event.get("message", {}).get("content", []) if part.get("type") == "tool_use"]


def _verify(workspace: Path) -> bool:
    return subprocess.run([sys.executable, "verify.py"], cwd=workspace, capture_output=True, text=True).returncode == 0


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _all_true(value: dict) -> bool:
    return all(item for key, item in value.items() if key not in {"tools", "detail"})


def input_is_transcript_free(record: dict, expected_prompt: str) -> bool:
    boundary, argv = record.get("input_boundary", {}), record.get("argv", [])
    return bool(boundary.get("prompt") == expected_prompt
                and boundary.get("prompt_sha256") == sha256(expected_prompt.encode("utf-8")).hexdigest()
                and boundary.get("no_session_persistence") and not boundary.get("contains_original_session_or_transcript")
                and "--no-session-persistence" in argv and "--resume" not in argv)


def snapshot_matches_record(record: dict, snapshot: Path, artifact: str, require_projection: bool = True) -> bool:
    artifact_path, projection = snapshot / artifact, snapshot / ".cairn-continuation.json"
    return bool(artifact_path.is_file() and record.get("artifact_sha256", {}).get(artifact) == _sha(artifact_path)
                and (not require_projection or (projection.is_file() and json.loads(projection.read_text(encoding="utf-8")) == record.get("projection"))))


def artifact_equivalent(records: list[dict], artifact: str) -> bool:
    values = [record.get("artifact_sha256", {}).get(artifact) for record in records]
    return bool(values and all(values) and len(set(values)) == 1)


def write_evidence_manifest(root: Path) -> dict:
    """Hash the completed raw record set; the verdict deliberately excludes itself."""
    root = Path(root)
    entries = [
        {"path": str(path.relative_to(root)).replace("\\", "/"), "bytes": path.stat().st_size, "sha256": _sha(path)}
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name not in {"evidence-manifest.json", "verdict.json"}
    ]
    manifest = {"schema_version": "cairn.p4-evidence-manifest.v0.2", "entries": entries}
    (root / "evidence-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def evidence_manifest_matches(root: Path) -> bool:
    root = Path(root)
    manifest_path = root / "evidence-manifest.json"
    if not manifest_path.is_file():
        return False
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "cairn.p4-evidence-manifest.v0.2":
        return False
    listed = {entry.get("path"): entry for entry in manifest.get("entries", [])}
    actual = {
        str(path.relative_to(root)).replace("\\", "/"): path
        for path in root.rglob("*")
        if path.is_file() and path.name not in {"evidence-manifest.json", "verdict.json"}
    }
    return set(listed) == set(actual) and all(
        entry.get("bytes") == actual[name].stat().st_size and entry.get("sha256") == _sha(actual[name])
        for name, entry in listed.items()
    )


def receipt_matches_intent_and_observation(receipt: dict, intent: dict, observation: dict) -> bool:
    return bool(
        all(receipt.get(key) == intent.get(key) for key in ("effect_id", "idempotency_key", "request_fingerprint"))
        and receipt.get("resource_id") == observation.get("resource_id")
        and observation.get("request_fingerprint") == intent.get("request_fingerprint")
    )


def _coding(crash: dict, recovery: dict, snapshot: Path, expected_prompt: str) -> dict:
    tools, first = _tools(recovery), {}
    if tools:
        first = tools[0]
    return {"injected_crash": crash["killed_after_projection"] and crash["returncode"] != 0,
            "fresh_process": crash["pid"] != recovery["pid"], "projection_valid": projection_is_valid(crash.get("projection")),
            "snapshot_bound": snapshot_matches_record(crash, snapshot, "greeting.py"),
            "transcript_free_input": input_is_transcript_free(recovery, expected_prompt),
            "first_operation_reobserves": first.get("name") in {"Read", "Glob"} or first.get("command", "") in {"ls", "dir"},
            "verifier_passes": _verify(snapshot), "recovery_returncode": recovery["returncode"] == 0, "tools": tools}


def _compaction(initial: dict, compacted: dict, snapshot: Path, expected_prompt: str) -> dict:
    tools, first = _tools(compacted), {}
    if tools:
        first = tools[0]
    return {"fresh_process": initial["pid"] != compacted["pid"], "projection_valid": projection_is_valid(initial.get("projection")),
            "snapshot_bound": snapshot_matches_record(initial, snapshot, "greeting.py"),
            "transcript_free_input": input_is_transcript_free(compacted, expected_prompt),
            "first_operation_reobserves": first.get("name") in {"Read", "Glob"} or first.get("command", "") in {"ls", "dir"},
            "verifier_passes": _verify(snapshot), "recovery_returncode": compacted["returncode"] == 0, "tools": tools}


def _effect(crash: dict, recovery: dict, snapshot: Path, expected_prompt: str, require_projection: bool = False) -> dict:
    workspace, remote, tools = snapshot / "workspace", snapshot / "remote", _tools(recovery)
    provider = json.loads((remote / "provider.json").read_text(encoding="utf-8"))
    events = [json.loads(line) for line in (remote / "provider-events.jsonl").read_text(encoding="utf-8").splitlines()]
    intent = json.loads((workspace / ".cairn-effect-intent.json").read_text(encoding="utf-8"))
    observation = json.loads((workspace / ".cairn-effect-observation.json").read_text(encoding="utf-8"))
    resolution = json.loads((workspace / ".cairn-effect-resolution.json").read_text(encoding="utf-8"))
    receipt = json.loads((workspace / ".cairn-effect-receipt.json").read_text(encoding="utf-8"))
    return {"injected_crash": crash["killed_after_marker"] and crash["returncode"] != 0,
            "receipt_absent_at_crash": not crash["boundary_state"]["receipt_exists"], "fresh_process": crash["pid"] != recovery["pid"],
            "projection_valid": projection_is_valid(crash.get("projection")) if require_projection else True,
            "snapshot_bound": snapshot_matches_record(crash, workspace, "segments.py") if require_projection else True,
            "transcript_free_input": input_is_transcript_free(recovery, expected_prompt),
            "first_operation_observes": bool(tools and tools[0]["command"] == "python effect_tool.py observe"),
            "single_resource": len(provider["resources"]) == 1, "single_commit": sum(event["kind"] == "commit" for event in events) == 1,
            "decision_skip": resolution["decision"] == "skip", "receipt_from_reobserve": receipt["observed_from"] == "reobserve",
            "receipt_matches_intent_and_observation": receipt_matches_intent_and_observation(receipt, intent, observation),
            "ledger_closed": any(json.loads(line).get("type") == "COMPLETE" for line in (workspace / ".cairn-effects.jsonl").read_text(encoding="utf-8").splitlines()),
            "coding_verifier_passes": _verify(workspace) if require_projection else True,
            "recovery_returncode": recovery["returncode"] == 0, "tools": tools}


def _effect_baseline(record: dict, snapshot: Path) -> dict:
    workspace, remote = snapshot / "workspace", snapshot / "remote"
    provider = json.loads((remote / "provider.json").read_text(encoding="utf-8"))
    events = [json.loads(line) for line in (remote / "provider-events.jsonl").read_text(encoding="utf-8").splitlines()]
    return {"returncode": record["returncode"] == 0, "single_resource": len(provider["resources"]) == 1,
            "single_commit": sum(event["kind"] == "commit" for event in events) == 1,
            "receipt_persisted": (workspace / ".cairn-effect-receipt.json").is_file()}


def build_verdict(root: Path) -> dict:
    root, snapshots = Path(root), Path(root) / "evidence-snapshot"
    controls = json.loads((root / "pre-run-freeze.json").read_text(encoding="utf-8"))
    u, r_crash, r_recovery, c_initial, c_compacted = (_record(root / name) for name in ("u", "r-crash", "r-recovery", "c-initial", "c-compacted"))
    effect_u, effect_crash, effect_recovery = (_record(root / name) for name in ("effect-u", "effect-r-crash", "effect-r-recovery"))
    holdout_crash, holdout_recovery = (_record(root / name) for name in ("holdout-crash", "holdout-recovery"))
    coding = _coding(r_crash, r_recovery, snapshots / "r" / "workspace", coding_recovery_prompt(r_crash["projection"]))
    compacted = _compaction(c_initial, c_compacted, snapshots / "c" / "workspace", coding_recovery_prompt(c_initial["projection"], True))
    effect_intent = json.loads((snapshots / "effect-r" / "workspace" / ".cairn-effect-intent.json").read_text(encoding="utf-8"))
    effect = _effect(effect_crash, effect_recovery, snapshots / "effect-r", effect_recovery_prompt(effect_intent))
    holdout_intent = json.loads((snapshots / "holdout" / "workspace" / ".cairn-effect-intent.json").read_text(encoding="utf-8"))
    holdout = _effect(holdout_crash, holdout_recovery, snapshots / "holdout", holdout_recovery_prompt(holdout_crash["projection"], holdout_intent), True)
    baseline = _effect_baseline(effect_u, snapshots / "effect-u")
    artifact_parity = artifact_equivalent([u, r_crash, r_recovery, c_initial, c_compacted], "greeting.py")
    baseline_coding = _verify(snapshots / "u" / "workspace") and snapshot_matches_record(u, snapshots / "u" / "workspace", "greeting.py", False)
    evidence_matches = evidence_manifest_matches(root)
    passed = all((phase4_inputs_match(controls), evidence_matches, baseline_coding, artifact_parity, _all_true(coding), _all_true(compacted), _all_true(baseline), _all_true(effect), _all_true(holdout)))
    return {"schema_version": "cairn.p4-claude-code-verdict.v0.2", "verdict": "PASS — thin Claude Code integration proof" if passed else "FAIL — do not admit Phase 4", "passed": passed,
            "host": {"name": "Claude Code", "requested_flags": ["--safe-mode", "--setting-sources project", "--model sonnet", "--no-session-persistence"]},
            "pre_run_control_freeze_matches": phase4_inputs_match(controls), "evidence_manifest_matches": evidence_matches,
            "reference": {"uninterrupted_baseline": baseline_coding, "artifact_equivalence": artifact_parity, "coding_crash_recovery": coding, "compaction": compacted, "effect_uninterrupted_baseline": baseline, "effect_crash_recovery": effect},
            "sealed_holdout": {"combined_crash_recovery": holdout},
            "claim": "One external coding-agent host retained execution control while consuming Cairn continuation and receipt/reconciliation semantics through workspace files and native terminal operations.",
            "boundary": "This is one deterministic host/provider integration, not an adapter API, framework integration, exactly-once claim, or interoperability standard."}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--write-evidence-manifest", action="store_true")
    args = parser.parse_args()
    if args.write_evidence_manifest:
        write_evidence_manifest(args.root)
        return 0
    verdict = build_verdict(args.root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if verdict["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
