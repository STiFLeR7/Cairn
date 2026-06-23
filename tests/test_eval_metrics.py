"""AP-0030 — the five fidelity axes."""

from cairn.eval.metrics import RecoveryReport, no_regression, solution_quality
from cairn.eval.scenario import RunOutcome


class _Ref:
    final_digest = {"a.txt": "h1", "b.txt": "h2"}


def test_solution_quality_full_and_partial():
    full = RunOutcome(True, 0, {"a.txt": "h1", "b.txt": "h2"}, 0)
    half = RunOutcome(True, 0, {"a.txt": "h1", "b.txt": "WRONG"}, 0)
    assert solution_quality(full, _Ref()) == 1.0
    assert solution_quality(half, _Ref()) == 0.5


def test_no_regression_in_work_units():
    # AP-0044: no_regression is defined in WORK UNITS, not actions. 4-unit task, 2 units done
    # at the crash → 2 units genuinely remain.
    assert no_regression(recovery_units=4, work_at_crash=2, total_units=4) == 0.0  # B0 redid both
    assert no_regression(recovery_units=2, work_at_crash=2, total_units=4) == 1.0  # B3 redid none
    assert no_regression(recovery_units=3, work_at_crash=2, total_units=4) == 0.5  # redid one


def test_no_regression_is_action_granularity_robust():
    # The score depends only on work units, so a clean recovery (does exactly the genuinely
    # remaining units, redoes none) is 1.0 at any unit scale — independent of how many model
    # actions those units took. This is the property M1 lacked.
    assert no_regression(recovery_units=2, work_at_crash=2, total_units=4) == 1.0  # 2 remain, did 2
    assert no_regression(recovery_units=3, work_at_crash=3, total_units=6) == 1.0  # 3 remain, did 3
    # A from-scratch redo is full regression (0.0) at any unit scale.
    assert no_regression(recovery_units=4, work_at_crash=2, total_units=4) == 0.0  # redid the 2
    assert no_regression(recovery_units=5, work_at_crash=5, total_units=5) == 0.0  # redid all 5


def test_effect_safety_is_a_hard_gate():
    clean = RecoveryReport("B3", 2, True, 1.0, 1.0, 0, 2)
    dup = RecoveryReport("B0", 2, True, 1.0, 0.0, 1, 4)
    assert clean.passes_gate is True
    assert dup.passes_gate is False  # one duplicate fails the gate regardless of success
