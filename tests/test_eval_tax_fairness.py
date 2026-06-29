"""Success-conditioned recovery tax — AP-0048 (Milestone M3).

The fairness fix the M2 review flagged: `recovery_tax` measures the cost of a *successful
recovery*. A run that **fails** to complete the task never recovered, so its (often small)
work must NOT register as a cheap recovery and pull the tax down — otherwise a baseline could
"win" on tax by failing cheaply. These tests build `RecoveryReport`s directly so the property
is pinned independent of any model.
"""

from __future__ import annotations

from cairn.eval.metrics import RecoveryReport
from cairn.eval.runner import RepeatedRun, aggregate_repeated, verdict_c1


def _rep(reports) -> RepeatedRun:
    names = sorted({r.baseline for r in reports})
    return RepeatedRun(reports=reports, fired=len(reports), skipped=0, repeats=1,
                       steps=[3], baselines=names)


def _report(baseline, success, tax, *, no_regression=1.0):
    return RecoveryReport(
        baseline=baseline, failure_step=3, task_success=success,
        solution_quality=1.0 if success else 0.0, no_regression=no_regression,
        effect_duplicates=0, recovery_tax=tax,
    )


def test_recovery_tax_is_measured_over_successes_only():
    # One successful recovery (tax 4) and one cheap FAILURE (tax 1). The reported tax is the
    # cost of the recovery that actually happened (4), not the (4+1)/2 = 2.5 a naive mean gives.
    stats = aggregate_repeated(_rep([
        _report("B3", True, 4),
        _report("B3", False, 1),
    ]))
    assert stats["B3"]["recovery_tax"].mean == 4.0
    assert stats["B3"]["recovery_tax"].n == 1          # the failure is excluded
    assert stats["B3"]["n_success"] == 1
    assert stats["B3"]["recovery_tax_all"].mean == 2.5  # full distribution kept for transparency


def test_cheap_failures_do_not_suppress_a_real_win():
    # B3 recovers cheaply every time (tax 2). B0 has a genuine cold-restart recovery (tax 6) AND
    # a cheap crash that did ~no work (tax 0, FAILED). Comparing cost-of-success to cost-of-success
    # B3 clearly beats B0; the cheap B0 failure must not masquerade as a 0-tax "recovery" that
    # makes the no-overlap test fail.
    verdict = verdict_c1(aggregate_repeated(_rep([
        _report("B3", True, 2), _report("B3", True, 2),
        _report("B0", True, 6, no_regression=0.0),
        _report("B0", False, 0, no_regression=0.0),
    ])))
    assert verdict["supported"] is True


def test_competitor_that_never_recovers_is_not_a_cheap_win():
    # B0 never completes the recovery → it has no cost-of-recovery to compare. A baseline cannot
    # "win" (or be beaten) on a tax it never actually paid; the verdict declines rather than
    # reading B0's failed near-zero work as the cheapest possible recovery.
    verdict = verdict_c1(aggregate_repeated(_rep([
        _report("B3", True, 2),
        _report("B0", False, 0, no_regression=0.0),
    ])))
    assert verdict["supported"] is False
    assert "never completed" in verdict["reason"]


def test_deterministic_all_success_is_unchanged():
    # When every run succeeds (the deterministic chain case), success-conditioning is a no-op:
    # the headline tax equals the full-distribution tax.
    stats = aggregate_repeated(_rep([
        _report("B3", True, 2), _report("B3", True, 2),
        _report("B0", True, 6, no_regression=0.0), _report("B0", True, 6, no_regression=0.0),
    ]))
    assert stats["B3"]["recovery_tax"].mean == stats["B3"]["recovery_tax_all"].mean == 2.0
    assert stats["B0"]["recovery_tax"].mean == 6.0
    assert stats["B3"]["n_success"] == 2 and stats["B0"]["n_success"] == 2
