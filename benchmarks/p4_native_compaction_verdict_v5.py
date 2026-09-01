"""Verdict for the V5 generic-authority and native-host-compaction control."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

from benchmarks.p4_claude_holdout_v2 import recovery_prompt as holdout_recovery_prompt
from benchmarks.p4_claude_protocol import effect_recovery_prompt
from benchmarks.p4_claude_verdict import (_all_true, _effect, _effect_baseline, evidence_manifest_matches,
                                          input_is_transcript_free, projection_is_valid, write_evidence_manifest)
from benchmarks.p4_freeze import phase4_inputs_match
from benchmarks.p4_native_compaction_v5 import FRESH_RECOVERY_PROMPT


def _record(root: Path, name: str) -> dict:
    return json.loads((root / name / "record.json").read_text(encoding="utf-8"))


def _tools(record: dict) -> list[dict]:
    return [{"name": part.get("name"), "command": part.get("input", {}).get("command", "")}
            for event in record.get("events", []) if event.get("type") == "assistant"
            for part in event.get("message", {}).get("content", []) if part.get("type") == "tool_use"]


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _verify_final(workspace: Path) -> bool:
    return subprocess.run([sys.executable, "verify_final.py"], cwd=workspace, capture_output=True, text=True).returncode == 0


def _reobserves_before_action(record: dict) -> bool:
    tools = _tools(record)
    action_at = next((index for index, tool in enumerate(tools) if "python stage2.py" in tool["command"]), None)
    if action_at is None:
        return False
    return any(tool["name"] in {"Read", "Glob"} or ".cairn-continuation" in tool["command"] or ".cairn-action-map" in tool["command"]
               for tool in tools[:action_at])


def _matching_map(workspace: Path, projection: dict) -> bool:
    try:
        action = json.loads((workspace / ".cairn-action-map.json").read_text(encoding="utf-8"))["actions"][projection["next_action"]]
    except (KeyError, TypeError, json.JSONDecodeError, FileNotFoundError):
        return False
    return action == {"required_file": ".cairn-release-stage2", "preflight": ["python verify.py"],
                      "commands": ["python stage2.py", "python verify_final.py"], "success_file": "stage2.txt"}


def _first_effect_operation_is_observe(record: dict) -> bool:
    tools = _tools(record)
    return bool(tools and tools[0]["name"] == "Bash" and tools[0]["command"].strip().endswith("python effect_tool.py observe"))


def build_verdict(root: Path) -> dict:
    root, snapshots = Path(root), Path(root) / "evidence-snapshot"
    controls = json.loads((root / "pre-run-freeze.json").read_text(encoding="utf-8"))
    fork = json.loads((root / "checkpoint-fork-freeze.json").read_text(encoding="utf-8"))
    u, r_crash, r_recovery = (_record(root, name) for name in ("u", "r-crash", "r-recovery"))
    c_initial, c_compact, c_recovery = (_record(root, name) for name in ("c-initial", "c-compact", "c-compacted"))
    negative = _record(root, "negative-recovery")
    u_ws, r_ws, c_ws, negative_ws = (snapshots / name / "workspace" for name in ("u", "r", "c", "negative"))
    projection = r_crash["projection"]
    greeting_hashes = [_sha(path / "greeting.py") for path in (u_ws, r_ws, c_ws)] + [r_crash["artifact_sha256"]["greeting.py"], c_initial["artifact_sha256"]["greeting.py"]]
    coding = {
        "uninterrupted_baseline": u["returncode"] == 0 and u["checkpoint_captured_before_stage2"] and _verify_final(u_ws),
        "checkpoint_fork_matches": phase4_inputs_match(fork),
        "shared_projection": projection_is_valid(projection) and c_initial["projection"] == projection,
        "action_map_binds_next_action": _matching_map(r_ws, projection) and _matching_map(c_ws, projection),
        "artifact_equivalence": len(set(greeting_hashes)) == 1 and len({_sha(path / "stage2.txt") for path in (u_ws, r_ws, c_ws)}) == 1,
        "injected_crash_after_reobserve": r_crash["killed_after_marker"] and r_crash["returncode"] != 0,
        "fresh_process_recovery": r_crash["pid"] != r_recovery["pid"],
        "fresh_recovery_transcript_free": input_is_transcript_free(r_recovery, FRESH_RECOVERY_PROMPT),
        "fresh_recovery_reobserves_before_action": _reobserves_before_action(r_recovery),
        "fresh_recovery_verified": r_recovery["returncode"] == 0 and _verify_final(r_ws),
        "native_compaction_manual": c_compact.get("native_compaction", {}).get("trigger") == "manual",
        "native_compaction_reduces_context": c_compact.get("native_compaction", {}).get("pre_tokens", 0) > c_compact.get("native_compaction", {}).get("post_tokens", 0),
        "native_compaction_same_host_session": all(record["input_boundary"].get("host_session_id") == c_initial["input_boundary"].get("host_session_id")
                                                   for record in (c_compact, c_recovery)) and c_recovery["input_boundary"].get("resumed_host_session"),
        "compacted_host_reobserves_before_action": _reobserves_before_action(c_recovery),
        "compacted_host_verified": c_recovery["returncode"] == 0 and _verify_final(c_ws),
        "causal_negative_escalates": negative["returncode"] == 0 and not (negative_ws / "stage2.txt").exists()
                                      and (negative_ws / ".cairn-escalation.json").is_file()
                                      and "unmapped_negative_control" in (negative_ws / ".cairn-escalation.json").read_text(encoding="utf-8")
                                      and not any("stage2.py" in tool["command"] for tool in _tools(negative)),
    }
    effect_u, effect_crash, effect_recovery = (_record(root, name) for name in ("effect-u", "effect-r-crash", "effect-r-recovery"))
    effect_intent = json.loads((snapshots / "effect-r" / "workspace" / ".cairn-effect-intent.json").read_text(encoding="utf-8"))
    effect = _effect(effect_crash, effect_recovery, snapshots / "effect-r", effect_recovery_prompt(effect_intent))
    effect["first_operation_observes"] = _first_effect_operation_is_observe(effect_recovery)
    baseline = _effect_baseline(effect_u, snapshots / "effect-u")
    holdout_crash, holdout_recovery = (_record(root, name) for name in ("holdout-crash", "holdout-recovery"))
    holdout_intent = json.loads((snapshots / "holdout" / "workspace" / ".cairn-effect-intent.json").read_text(encoding="utf-8"))
    holdout = _effect(holdout_crash, holdout_recovery, snapshots / "holdout", holdout_recovery_prompt(holdout_crash["projection"], holdout_intent), True)
    holdout["first_operation_observes"] = _first_effect_operation_is_observe(holdout_recovery)
    passed = all((phase4_inputs_match(controls), evidence_manifest_matches(root), _all_true(coding),
                  _all_true(baseline), _all_true(effect), _all_true(holdout)))
    return {"schema_version": "cairn.p4-native-compaction-verdict.v0.1", "passed": passed,
            "verdict": "PASS — thin Claude Code integration proof" if passed else "FAIL — do not admit Phase 4",
            "pre_run_control_freeze_matches": phase4_inputs_match(controls),
            "evidence_manifest_matches": evidence_manifest_matches(root),
            "reference": {"shared_checkpoint_urc": coding, "effect_uninterrupted_baseline": baseline,
                          "effect_crash_recovery": effect},
            "sealed_holdout": {"combined_crash_recovery": holdout},
            "boundary": "One Claude Code host/provider only; native compaction is host-owned. No framework adapter, exactly-once, or interoperability claim."}


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
    args.output.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if verdict["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
