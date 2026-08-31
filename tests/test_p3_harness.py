from pathlib import Path

from benchmarks.p3_harness import run_p3_cell, run_uninterrupted_cell


def test_committed_effect_without_durable_receipt_is_observed_then_skipped(tmp_path: Path):
    record = run_p3_cell(
        {"id": "commit-skip", "tool_class": "check-before-retry", "boundary": "commit"},
        tmp_path,
    )

    assert record["crash"]["fired"] is True
    assert record["processes"]["crash_pid"] != record["processes"]["recovery_pid"]
    assert record["recovery"]["first_operation"] == "observe"
    assert record["recovery"]["restore_attempts"] == 0
    assert record["resolution"]["decision"] == "skip"
    assert record["provider"]["commit_count"] == 1
    assert record["ledger"]["closed"] is True
    assert record["outcome"]["successful_recovery"] is True


def test_absent_effect_is_observed_then_retried_once(tmp_path: Path):
    record = run_p3_cell(
        {"id": "dispatch-retry", "tool_class": "check-before-retry", "boundary": "dispatch"},
        tmp_path,
    )

    assert record["recovery"]["first_operation"] == "observe"
    assert record["resolution"]["decision"] == "retry"
    assert record["provider"]["commit_count"] == 1
    assert record["provider"]["duplicate_count"] == 0
    assert record["outcome"] == {"intended_effect_exists": True, "successful_recovery": True}


def test_unknown_effect_escalates_without_retry(tmp_path: Path):
    record = run_p3_cell(
        {
            "id": "unknown-escalate",
            "tool_class": "check-before-retry",
            "boundary": "dispatch",
            "unknown_on_recovery": True,
        },
        tmp_path,
    )

    assert record["recovery"]["first_operation"] == "observe"
    assert record["resolution"]["decision"] == "escalate"
    assert record["provider"]["commit_count"] == 0
    assert record["ledger"]["closed"] is False
    assert record["outcome"] == {"intended_effect_exists": False, "successful_recovery": False}


def test_uninterrupted_effect_writes_receipt_and_closes_ledger(tmp_path: Path):
    record = run_uninterrupted_cell(
        {"id": "normal-control", "tool_class": "check-before-retry", "boundary": "normal"},
        tmp_path,
    )

    assert record["cell"]["normal"] is True
    assert record["crash"]["fired"] is False
    assert record["resolution"]["decision"] == "complete"
    assert record["provider"]["commit_count"] == 1
    assert record["ledger"]["closed"] is True
    assert record["outcome"] == {"intended_effect_exists": True, "successful_recovery": True}
