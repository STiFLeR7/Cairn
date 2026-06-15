"""AP-0029 / AP-0033 — baselines + matrix; claim C1 (RGR beats cold restart)."""

from benchmarks.scenarios import multi_file_scenario
from cairn.eval.baselines import ColdRestart, RGR
from cairn.eval.runner import aggregate, run_matrix


def test_all_baselines_complete_the_task(tmp_path):
    scenario = multi_file_scenario(n=4)
    counter = {"i": 0}

    def base_factory():
        counter["i"] += 1
        d = str(tmp_path / f"b{counter['i']}")
        return d

    reports = run_matrix(scenario, steps=[1, 2, 3], base_factory=base_factory)
    assert all(r.task_success for r in reports)  # every baseline finishes the task


def test_c1_rgr_beats_cold_restart(tmp_path):
    scenario = multi_file_scenario(n=4)
    counter = {"i": 0}

    def base_factory():
        counter["i"] += 1
        return str(tmp_path / f"b{counter['i']}")

    reports = run_matrix(scenario, steps=[1, 2, 3],
                         baselines=[ColdRestart(), RGR()], base_factory=base_factory)
    summary = aggregate(reports)

    # C1: RGR (B3) imposes less recovery tax and preserves more pre-failure work than B0.
    assert summary["B3"]["recovery_tax"] < summary["B0"]["recovery_tax"]
    assert summary["B3"]["no_regression"] > summary["B0"]["no_regression"]
    assert summary["B0"]["no_regression"] == 0.0   # cold restart redoes everything
    assert summary["B3"]["no_regression"] == 1.0   # RGR redoes nothing
    assert summary["B3"]["task_success"] == 1.0
