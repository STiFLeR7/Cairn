"""Regression tests for failure-injection integrity (root-cause fix, 2026-06-16).

Bug found via the M1 live run: a model that finishes a batchable task before step `k`
means the injected crash never fires, yet the matrix scored the resulting *non-failure*
as a valid (even perfect) recovery. The benchmark must detect a vacuous injection and
refuse to score it, rather than fabricating a recovery result.
"""

from __future__ import annotations

import tempfile

from benchmarks.scenarios import batching_multifile_transport, live_multi_file_scenario
from cairn.eval.baselines import ColdRestart, RGR
from cairn.eval.runner import run_matrix
from cairn.eval.scenario import run_until_failure

NAMES = [f"step{i}.txt" for i in range(4)]


def test_run_until_failure_reports_fired_true_for_well_behaved_model():
    # One-file-per-step model takes 4 steps, so a crash at k=2 actually fires.
    inj = run_until_failure(live_multi_file_scenario(4), tempfile.mkdtemp(), 2)
    assert inj.fired is True


def test_run_until_failure_reports_fired_false_when_model_finishes_first():
    # A batching model finishes in one action; the crash at k=2 never fires.
    scenario = live_multi_file_scenario(4, batching_multifile_transport(NAMES))
    inj = run_until_failure(scenario, tempfile.mkdtemp(), 2)
    assert inj.fired is False
    assert inj.completed is True


def test_matrix_skips_cells_where_injection_did_not_fire():
    scenario = live_multi_file_scenario(4, batching_multifile_transport(NAMES))
    skipped = []
    reports = run_matrix(
        scenario, steps=[2], baselines=[ColdRestart(), RGR()],
        on_skip=lambda k, name: skipped.append((k, name)),
    )
    assert reports == []                       # nothing fabricated from a non-failure
    assert set(skipped) == {(2, "B0"), (2, "B3")}


def test_matrix_still_scores_when_injection_fires():
    # Regression guard: a well-behaved model still produces scored cells.
    reports = run_matrix(live_multi_file_scenario(4), steps=[2], baselines=[ColdRestart(), RGR()])
    assert {r.baseline for r in reports} == {"B0", "B3"}
