"""Fixed verdict for the two V6 Phase 4 admission controls."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

from benchmarks.p4_claude_verdict import evidence_manifest_matches, write_evidence_manifest
from benchmarks.p4_freeze import phase4_inputs_match
from benchmarks.p4_native_compaction_v5 import FRESH_RECOVERY_PROMPT


def _record(root: Path, name: str) -> dict:
    return json.loads((root / name / "record.json").read_text(encoding="utf-8"))


def _tools(record: dict) -> list[dict]:
    return [{"name": part.get("name"), "command": part.get("input", {}).get("command", "")}
            for event in record.get("events", []) if event.get("type") == "assistant"
            for part in event.get("message", {}).get("content", []) if part.get("type") == "tool_use"]


def _native_compact(record: dict) -> bool:
    value = record.get("native_compaction") or {}
    return value.get("trigger") == "manual" and value.get("pre_tokens", 0) > value.get("post_tokens", 0)


def _verify(workspace: Path) -> bool:
    return subprocess.run([sys.executable, "verify_final.py"], cwd=workspace, capture_output=True, text=True).returncode == 0


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _reobserves_before(record: dict, command: str) -> bool:
    tools = _tools(record)
    at = next((index for index, tool in enumerate(tools) if command in tool["command"]), None)
    return at is not None and any(tool["name"] in {"Read", "Glob"} or ".cairn-continuation" in tool["command"]
                                 or ".cairn-action-map" in tool["command"] for tool in tools[:at])


def build_verdict(root: Path, v5_root: Path) -> dict:
    root, v5_root = Path(root), Path(v5_root)
    controls = json.loads((root / "pre-run-freeze.json").read_text(encoding="utf-8"))
    v5 = json.loads((v5_root / "verdict.json").read_text(encoding="utf-8"))
    ref_compact = _record(root, "reference-c-negative-compact")
    ref_resume = _record(root, "reference-c-negative-resume")
    ref_ws = root / "evidence-snapshot" / "reference-c-negative" / "workspace"
    hu, hr_crash, hr, hc_compact, hc = (_record(root, name) for name in
        ("holdout-u", "holdout-r-crash", "holdout-r-recovery", "holdout-c-compact", "holdout-c-resume"))
    hu_ws, hr_ws, hc_ws = (root / "evidence-snapshot" / name / "workspace" for name in ("holdout-u", "holdout-r", "holdout-c"))
    holdout = {
        "uninterrupted_baseline": hu["returncode"] == 0 and hu["checkpoint_captured_before_stage2"] and _verify(hu_ws),
        "fresh_crash": hr_crash["killed_after_marker"] and hr_crash["returncode"] != 0 and hr_crash["pid"] != hr["pid"],
        "fresh_prompt_generic": hr["input_boundary"]["prompt"] == FRESH_RECOVERY_PROMPT and hr["input_boundary"]["no_session_persistence"],
        "fresh_reobserves_and_verifies": _reobserves_before(hr, "python advance.py") and hr["returncode"] == 0 and _verify(hr_ws),
        "native_compaction": _native_compact(hc_compact),
        "compacted_same_session": hc["input_boundary"]["resumed_host_session"] and hc["input_boundary"]["host_session_id"] == hc_compact["input_boundary"]["host_session_id"],
        "compacted_reobserves_and_verifies": _reobserves_before(hc, "python advance.py") and hc["returncode"] == 0 and _verify(hc_ws),
        "artifact_equivalence": len({_sha(path / "labels.py") for path in (hu_ws, hr_ws, hc_ws)}) == 1
                                and len({_sha(path / "release.txt") for path in (hu_ws, hr_ws, hc_ws)}) == 1,
    }
    post_compaction_negative = {
        "native_compaction": _native_compact(ref_compact),
        "same_host_session_resumed": ref_resume["input_boundary"]["resumed_host_session"]
                                    and ref_resume["input_boundary"]["host_session_id"] == ref_compact["input_boundary"]["host_session_id"],
        "escalates_without_stage_action": ref_resume["returncode"] == 0 and not (ref_ws / "stage2.txt").exists()
                                          and (ref_ws / ".cairn-escalation.json").is_file()
                                          and "unmapped_post_compaction_control" in (ref_ws / ".cairn-escalation.json").read_text(encoding="utf-8")
                                          and not any("stage2.py" in tool["command"] for tool in _tools(ref_resume)),
    }
    all_true = lambda values: all(values.values())
    passed = all((phase4_inputs_match(controls), evidence_manifest_matches(root),
                  evidence_manifest_matches(v5_root), v5.get("passed") is True,
                  all_true(post_compaction_negative), all_true(holdout)))
    return {"schema_version": "cairn.p4-native-compaction-v6-verdict.v0.1", "passed": passed,
            "verdict": "PASS — Phase 4 admission evidence" if passed else "FAIL — do not admit Phase 4",
            "v5_reference_effect_evidence_manifest_matches": evidence_manifest_matches(v5_root),
            "v6_pre_run_control_freeze_matches": phase4_inputs_match(controls),
            "v6_evidence_manifest_matches": evidence_manifest_matches(root),
            "post_compaction_causal_negative": post_compaction_negative,
            "independent_holdout_generic_urc": holdout,
            "boundary": "Cumulative V5/V6 evidence for one host/provider; no adapter, exactly-once, or interoperability claim."}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--v5-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--write-evidence-manifest", action="store_true")
    args = parser.parse_args()
    if args.write_evidence_manifest:
        write_evidence_manifest(args.root)
        return 0
    verdict = build_verdict(args.root, args.v5_root)
    args.output.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if verdict["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
