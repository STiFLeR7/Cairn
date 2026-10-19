from __future__ import annotations

from cairn.eval.runner import AxisStat, verdict_c1_capability, verdict_c3_live, verdict_v1_gate


def ax(mean, lo=None, hi=None, n=8):
    return AxisStat(mean=mean, stdev=0.0, min=mean if lo is None else lo, max=mean if hi is None else hi, n=n)


def summary(b3_succ=0.9, b0_succ=0.7, b3_tax=(2, 4), b0_tax=(6, 9), b3_reg=1.0, b0_reg=0.5,
            b3_dup=0, b0_dup=3, b0_nsucc=5, n=16):
    return {
        "B3": {"n": n, "n_success": int(b3_succ * n), "task_success": ax(b3_succ, 0.0, 1.0),
               "no_regression": ax(b3_reg), "recovery_tax": ax(sum(b3_tax) / 2, *b3_tax),
               "effect_duplicates_total": b3_dup},
        "B0": {"n": n, "n_success": b0_nsucc, "task_success": ax(b0_succ, 0.0, 1.0),
               "no_regression": ax(b0_reg), "recovery_tax": ax(sum(b0_tax) / 2, *b0_tax),
               "effect_duplicates_total": b0_dup},
    }


def test_c1_capability_supported_when_all_checks_hold():
    v = verdict_c1_capability(summary(), calibration_rate=0.95)
    assert v["supported"] is True and all(v["checks"].values())


def test_c1_capability_tolerates_flaky_b3_within_ten_points():
    assert verdict_c1_capability(summary(b3_succ=0.875), 0.95)["supported"] is True
    v = verdict_c1_capability(summary(b3_succ=0.8), 0.95)
    assert v["supported"] is False and v["checks"]["b3_within_capability"] is False


def test_c1_capability_rejects_overlapping_tax_and_regression_and_b0_better():
    assert verdict_c1_capability(summary(b3_tax=(2, 7)), 0.95)["supported"] is False
    assert verdict_c1_capability(summary(b3_reg=0.4), 0.95)["supported"] is False
    assert verdict_c1_capability(summary(b0_succ=0.95), 0.95)["supported"] is False


def test_c1_capability_needs_fired_cells_and_a_b0_success():
    assert verdict_c1_capability({}, 0.95)["supported"] is False
    assert verdict_c1_capability(summary(b0_nsucc=0), 0.95)["supported"] is False


def test_c3_live():
    assert verdict_c3_live(summary())["supported"] is True
    assert verdict_c3_live(summary(b3_dup=1))["supported"] is False
    assert verdict_c3_live(summary(b0_dup=0))["supported"] is False  # torn effect never shown
    assert verdict_c3_live({})["supported"] is False


def _model(eligible=True, lost=0, c1=True, c3=True):
    return {"eligible": eligible, "planned_cells": 32, "lost_cells": lost,
            "c1": {"supported": c1}, "c3": {"supported": c3}}


def test_gate_outcomes():
    assert verdict_v1_gate({"claude": _model(), "codex": _model()})["decision"] == "GO"
    assert verdict_v1_gate({"claude": _model(), "codex": _model(c3=False)})["decision"] == "NO-GO"
    assert verdict_v1_gate({"claude": _model(), "codex": _model(eligible=False)})["decision"] == "INCONCLUSIVE"
    assert verdict_v1_gate({"claude": _model(lost=4), "codex": _model()})["decision"] == "INCONCLUSIVE"  # 12.5% > 10%
    assert verdict_v1_gate({"claude": _model(lost=3), "codex": _model()})["decision"] == "GO"  # 9.4%
    assert verdict_v1_gate({"claude": _model()})["decision"] == "INCONCLUSIVE"  # both models required
