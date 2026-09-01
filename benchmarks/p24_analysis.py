"""Deterministic structural and outcome analysis for P2.4 records."""

from __future__ import annotations


def _structural_ok(record: dict) -> bool:
    parent = record.get("parent_pid")
    branches = record.get("branches", {})
    if not all(name in branches for name in ("U", "R", "C")):
        return False
    recovery, compacted = branches["R"], branches["C"]
    if recovery.get("worker_pid") == parent or compacted.get("worker_pid") == parent:
        return False
    if recovery.get("used_in_memory_history") or compacted.get("used_in_memory_history"):
        return False
    if compacted.get("original_transcript_available") or not compacted.get("state_serialized"):
        return False
    for branch in branches.values():
        start = branch.get("start_progress")
        final = branch.get("final_progress")
        if not isinstance(start, int) or final != 4:
            return False
        if branch.get("accepted_progress") != list(range(start + 1, final + 1)):
            return False
        if not branch.get("verified") or len(branch.get("accepted_actions", [])) != final - start:
            return False
    return True


def analyze_p24_records(records: list[dict]) -> dict:
    """Count conditional U/R/C outcomes without conflating them with structural validity."""
    outcome = {
        "attempts": len(records), "complete_records": 0, "eligible": 0,
        "recovery_successes": 0, "compaction_successes": 0, "complete_triplets": 0,
        "structural_failures": 0,
    }
    for record in records:
        branches = record.get("branches", {})
        if not all(name in branches for name in ("U", "R", "C")):
            continue
        outcome["complete_records"] += 1
        if not _structural_ok(record):
            outcome["structural_failures"] += 1
        if not branches["U"].get("success"):
            continue
        outcome["eligible"] += 1
        recovered = branches["R"].get("success") is True
        compacted = branches["C"].get("success") is True
        outcome["recovery_successes"] += recovered
        outcome["compaction_successes"] += compacted
        outcome["complete_triplets"] += recovered and compacted
    return outcome
