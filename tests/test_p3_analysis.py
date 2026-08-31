from benchmarks.p3_analysis import analyze_records


def test_duplicate_free_skip_is_not_success_when_the_intended_effect_is_absent():
    result = analyze_records(
        [
            {
                "cell": {"expected_decision": "skip", "expected_intended_effect": True, "normal": False},
                "processes": {"crash_pid": 1, "recovery_pid": 2},
                "recovery": {"first_operation": "observe", "restore_attempts": 0},
                "resolution": {"decision": "skip"},
                "provider": {"duplicate_count": 0},
                "outcome": {"intended_effect_exists": False, "successful_recovery": False},
            }
        ]
    )

    assert result["duplicate_free"] == 1
    assert result["correct_decisions"] == 1
    assert result["successful_recoveries"] == 0
    assert result["silent_losses"] == 1
