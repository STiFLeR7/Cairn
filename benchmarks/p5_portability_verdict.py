"""Derive P5's narrow two-host verdict from already sealed host evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from benchmarks.p4_claude_verdict import evidence_manifest_matches as p4_evidence_manifest_matches
from benchmarks.p5_conformance import conformance_verdict
from benchmarks.p5_openhands_protocol import evidence_manifest_matches


def _all_true(value: dict) -> bool:
    return all(item is True for item in value.values())


def _openhands_run(root: Path) -> bool:
    facts = json.loads((root / "normalized-facts.json").read_text(encoding="utf-8"))["runs"]
    by_cell = {row["cell"]: row for row in facts}
    return bool(
        evidence_manifest_matches(root)
        and conformance_verdict(facts)["passed"]
        and all(by_cell[cell]["compaction"].get("active_view_changed") is True for cell in ("C", "C_NEG"))
    )


def _claude_run(v5_root: Path, v6_root: Path) -> bool:
    v5 = json.loads((v5_root / "verdict.json").read_text(encoding="utf-8"))
    v6 = json.loads((v6_root / "verdict.json").read_text(encoding="utf-8"))
    shared = v5["reference"]["shared_checkpoint_urc"]
    effect = v5["reference"]["effect_crash_recovery"]
    return bool(
        v5.get("passed") and v6.get("passed")
        and p4_evidence_manifest_matches(v5_root) and p4_evidence_manifest_matches(v6_root)
        and _all_true({key: shared[key] for key in ("uninterrupted_baseline", "fresh_process_recovery", "fresh_recovery_transcript_free", "fresh_recovery_reobserves_before_action", "fresh_recovery_verified", "artifact_equivalence", "native_compaction_manual", "native_compaction_reduces_context", "compacted_host_reobserves_before_action", "compacted_host_verified", "causal_negative_escalates")})
        and _all_true({key: effect[key] for key in ("injected_crash", "fresh_process", "transcript_free_input", "first_operation_observes", "decision_skip", "single_commit", "single_resource", "ledger_closed")})
        and _all_true(v6["independent_holdout_generic_urc"])
        and _all_true(v6["post_compaction_causal_negative"])
    )


def build_verdict(claude_v5: Path, claude_v6: Path, openhands_reference: Path, openhands_holdout: Path) -> dict:
    claude_ok = _claude_run(claude_v5, claude_v6)
    reference_ok = _openhands_run(openhands_reference)
    holdout_ok = _openhands_run(openhands_holdout)
    passed = claude_ok and reference_ok and holdout_ok
    return {
        "schema_version": "cairn.p5-two-host-portability.v0",
        "passed": passed,
        "hosts": ["Claude Code", "OpenHands SDK LocalConversation"],
        "claude_code_admission_evidence": claude_ok,
        "openhands_reference_conformance": reference_ok,
        "openhands_independent_holdout_conformance": holdout_ok,
        "claim": "Two independently implemented coding-agent hosts satisfied the existing recovery, continuation, and receipt/reconciliation semantics through host-owned boundaries.",
        "boundary": "This is deterministic, evidence-scoped two-host portability; it is not universal compatibility, a host-native Cairn implementation, exactly-once delivery, or an ecosystem standard.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--claude-v5", type=Path, required=True)
    parser.add_argument("--claude-v6", type=Path, required=True)
    parser.add_argument("--openhands-reference", type=Path, required=True)
    parser.add_argument("--openhands-holdout", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    verdict = build_verdict(args.claude_v5, args.claude_v6, args.openhands_reference, args.openhands_holdout)
    args.output.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if verdict["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
