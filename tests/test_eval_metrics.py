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


def test_no_regression_cold_restart_vs_rgr():
    # task of 4 steps, failure after k=2 → 2 steps genuinely remain.
    assert no_regression(executed=4, n_steps=4, k=2) == 0.0   # B0 redid both pre-failure steps
    assert no_regression(executed=2, n_steps=4, k=2) == 1.0   # B3 redid none
    assert no_regression(executed=3, n_steps=4, k=2) == 0.5   # redid one


def test_effect_safety_is_a_hard_gate():
    clean = RecoveryReport("B3", 2, True, 1.0, 1.0, 0, 2)
    dup = RecoveryReport("B0", 2, True, 1.0, 0.0, 1, 4)
    assert clean.passes_gate is True
    assert dup.passes_gate is False  # one duplicate fails the gate regardless of success
