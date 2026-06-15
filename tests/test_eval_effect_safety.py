"""AP-0030 / C3 — with-WAL (RGR) vs without-WAL (cold restart) effect safety."""

from benchmarks.scenarios import effectful_scenario
from cairn.eval.baselines import ColdRestart, RGR
from cairn.eval.runner import run_matrix


def test_c3_rgr_zero_duplicates_cold_restart_duplicates(tmp_path):
    # Effect fires at step 2; the failure is injected at step 2 (torn — INTENT, no COMPLETE).
    scenario = effectful_scenario(n=4, effect_step=2)
    counter = {"i": 0}

    def base_factory():
        counter["i"] += 1
        return str(tmp_path / f"b{counter['i']}")

    reports = run_matrix(scenario, steps=[2],
                         baselines=[ColdRestart(), RGR()], base_factory=base_factory)
    by = {r.baseline: r for r in reports}

    # C3: the write-ahead ledger + danger-window resolution → zero duplicate effects.
    assert by["B3"].effect_duplicates == 0
    assert by["B3"].passes_gate is True
    # Without the WAL, cold restart re-fires the irreversible effect → duplicate, gate fails.
    assert by["B0"].effect_duplicates >= 1
    assert by["B0"].passes_gate is False
