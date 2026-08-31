"""Semantic analysis for Phase 3 raw effect-recovery records."""

from __future__ import annotations


def _structural(record: dict) -> bool:
    if record["cell"].get("normal"):
        return record.get("crash", {}).get("fired") is False and record.get("ledger", {}).get("closed") is True
    processes = record.get("processes", {})
    return (
        record.get("crash", {}).get("fired") is True
        and processes.get("crash_pid") not in {processes.get("parent_pid"), processes.get("recovery_pid")}
        and processes.get("recovery_pid") != processes.get("parent_pid")
        and record.get("recovery", {}).get("first_operation") == "observe"
        and record.get("recovery", {}).get("restore_attempts") == 0
    )


def analyze_records(records: list[dict]) -> dict:
    result = {
        "attempts": len(records), "structural_failures": 0, "correct_decisions": 0,
        "duplicate_free": 0, "successful_recoveries": 0, "silent_losses": 0,
        "semantic_failures": 0,
    }
    for record in records:
        cell = record["cell"]
        structural = _structural(record)
        correct_decision = record["resolution"]["decision"] == cell["expected_decision"]
        duplicate_free = record["provider"]["duplicate_count"] == 0
        successful = record["outcome"]["successful_recovery"] is True
        silent_loss = bool(cell["expected_intended_effect"] and not record["outcome"]["intended_effect_exists"])
        result["structural_failures"] += not structural
        result["correct_decisions"] += correct_decision
        result["duplicate_free"] += duplicate_free
        result["successful_recoveries"] += successful
        result["silent_losses"] += silent_loss
        result["semantic_failures"] += not (structural and correct_decision and duplicate_free and not silent_loss)
    return result
