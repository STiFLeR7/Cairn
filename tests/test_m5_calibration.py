from __future__ import annotations

from benchmarks.scenarios import live_chain_effect_scenario, live_chain_scenario
from cairn.eval.baselines import ColdRestart, RGR
from cairn.eval.calibration import run_calibration
from cairn.eval.runner import aggregate_repeated, run_repeated


def test_effect_scenario_tears_effect_at_crash_step():
    s = live_chain_effect_scenario(6, 2)
    assert s.effect.key == "send-report" and s.effect.at_step == 2
    run = run_repeated(s, steps=[2], baselines=[ColdRestart(), RGR()], repeats=2)
    stats = aggregate_repeated(run)
    assert stats["B3"]["effect_duplicates_total"] == 0
    assert stats["B0"]["effect_duplicates_total"] >= 1


def test_calibration_on_reliable_fake_is_eligible():
    cal = run_calibration(live_chain_scenario(6), runs=10)
    assert cal["completed"] == 10 and cal["successes"] == 10
    assert cal["calibration_rate"] == 1.0 and cal["eligible"] is True


def test_calibration_counts_transport_errors_against_eligibility():
    calls = {"n": 0}
    base = live_chain_scenario(6)
    inner = base.model_factory

    class Boom(RuntimeError):
        pass

    def flaky_factory():
        calls["n"] += 1
        if calls["n"] in (1, 2):  # two runs lose their transport
            raise Boom("429")
        return inner()

    base.model_factory = flaky_factory
    cal = run_calibration(base, runs=10)
    assert cal["completed"] == 8 and len(cal["errors"]) == 2
    assert cal["calibration_rate"] == 1.0
    assert cal["eligible"] is False  # needs >= 9 of 10 completed
