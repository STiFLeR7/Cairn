"""Repetition + statistics harness — AP-0045 (Milestone M2).

A non-deterministic real model produces a distribution per cell, so evidence must carry its
spread, and vacuous cells (the M1 injection-fired bug) must never enter the statistics. These
tests use the deterministic chain task: repeats reproduce identical results (spread 0), which
lets us assert exact means while exercising the same machinery a live model will use.
"""

from __future__ import annotations

from benchmarks.scenarios import batching_chain_transport, chain_scenario, live_chain_scenario
from cairn.eval.baselines import ColdRestart, RGR
from cairn.eval.runner import (
    aggregate_repeated,
    format_repeated_table,
    run_repeated,
    verdict_c1,
)

BASELINES = [ColdRestart(), RGR()]


def test_run_repeated_runs_every_cell_n_times():
    run = run_repeated(chain_scenario(6), steps=[2, 3], baselines=BASELINES, repeats=3)
    # 3 repeats x 2 steps x 2 baselines = 12 fired reports, nothing skipped.
    assert run.fired == 12
    assert run.skipped == 0
    assert run.repeats == 3


def test_deterministic_model_has_zero_spread():
    run = run_repeated(chain_scenario(6), steps=[3], baselines=BASELINES, repeats=4)
    stats = aggregate_repeated(run)
    # Deterministic chain => every repetition identical => stdev 0 on every axis.
    assert stats["B3"]["recovery_tax"].stdev == 0.0
    assert stats["B0"]["recovery_tax"].stdev == 0.0
    assert stats["B3"]["task_success"].mean == 1.0
    assert stats["B3"]["recovery_tax"].n == 4  # 4 repetitions of the single cell


def test_aggregate_repeated_means_are_work_units():
    # n=6 chain, crash at step 3 -> 4 links committed; B3 redoes 2, B0 redoes all 6 (AP-0044).
    run = run_repeated(chain_scenario(6), steps=[3], baselines=BASELINES, repeats=5)
    stats = aggregate_repeated(run)
    assert stats["B3"]["recovery_tax"].mean == 2.0
    assert stats["B0"]["recovery_tax"].mean == 6.0
    assert stats["B3"]["no_regression"].mean == 1.0
    assert stats["B0"]["no_regression"].mean == 0.0


def test_vacuous_cells_are_skipped_not_scored():
    # A batching model finishes before the crash -> every cell is vacuous (M1 fix carried forward).
    skipped: list = []
    run = run_repeated(
        live_chain_scenario(4, batching_chain_transport(4)),
        steps=[2], baselines=BASELINES, repeats=3,
        on_skip=lambda k, name: skipped.append((k, name)),
    )
    assert run.fired == 0
    assert run.skipped == 3 * 2          # 3 repeats x 2 baselines, all skipped
    assert len(skipped) == 6
    assert aggregate_repeated(run) == {}  # no statistics fabricated from non-failures


def test_verdict_c1_supported_with_consistent_evidence():
    run = run_repeated(chain_scenario(6), steps=[2, 3], baselines=BASELINES, repeats=5)
    verdict = verdict_c1(aggregate_repeated(run))
    assert verdict["claim"] == "C1"
    assert verdict["supported"] is True


def test_verdict_c1_not_supported_when_no_cells_fire():
    run = run_repeated(
        live_chain_scenario(4, batching_chain_transport(4)),
        steps=[2], baselines=BASELINES, repeats=3,
    )
    verdict = verdict_c1(aggregate_repeated(run))
    assert verdict["supported"] is False
    assert "batchable" in verdict["reason"]


def test_before_repeat_hook_is_called_per_repeat():
    seen: list = []
    run_repeated(chain_scenario(4), steps=[2], baselines=[RGR()], repeats=3,
                 before_repeat=lambda i: seen.append(i))
    assert seen == [0, 1, 2]


def test_format_repeated_table_renders():
    run = run_repeated(chain_scenario(4), steps=[2], baselines=BASELINES, repeats=2)
    table = format_repeated_table(aggregate_repeated(run))
    assert "baseline" in table and "B3" in table and "recovery_tax" in table
