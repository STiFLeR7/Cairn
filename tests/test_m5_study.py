from __future__ import annotations

import json

from benchmarks.m5_study import compute_gate, run_m5_model
from benchmarks.scenarios import fake_chain_transport

PROTOCOL = {"models": {"claude": {"provider": "claude_code", "model": "sonnet"},
                       "codex": {"provider": "codex_cli", "model": "default"}},
            "n": 6, "steps": [2, 3], "repeats": 2, "calibration_runs": 10, "max_calls": 2000}


def test_offline_pipeline_produces_records_and_gate(tmp_path):
    for label in ("claude", "codex"):
        rec = run_m5_model(label, PROTOCOL, transport=fake_chain_transport(6), out_dir=str(tmp_path))
        assert rec["calibration"]["eligible"] is True
        assert rec["planned_cells"] == 2 * 2 * 2
        assert rec["lost_cells"] == 0
        assert rec["fired_cells"] == 8 and rec["skipped_cells"] == 0
        assert rec["accounting"]["balanced"] is True
        assert rec["fired_by_baseline"] == {"B0": 4, "B3": 4}
        assert rec["observed_models"] == []
        assert rec["c3"]["supported"] is True
        assert "supported" in rec["c1_strict"]
        assert json.loads((tmp_path / f"{label}.json").read_text())["label"] == label
    gate = compute_gate(str(tmp_path))
    assert gate["decision"] == "GO"
    assert (tmp_path / "gate-verdict.json").exists()


def test_ineligible_model_skips_study(tmp_path):
    def broken(_prompt):
        raise RuntimeError("usage cap")

    rec = run_m5_model("codex", PROTOCOL, transport=broken, out_dir=str(tmp_path))
    assert rec["calibration"]["eligible"] is False
    assert rec["study_run"] is False and rec["lost_cells"] == rec["planned_cells"]


def test_errored_repeat_is_lost_and_balanced(tmp_path):
    from cairn.eval.calibration import run_calibration
    from benchmarks.scenarios import live_chain_scenario

    calls = [0]

    def counting(prompt):
        calls[0] += 1
        return fake_chain_transport(6)(prompt)

    run_calibration(live_chain_scenario(6, counting), runs=10)
    calib_calls = calls[0]
    calls[0] = 0

    def flaky(prompt):
        calls[0] += 1
        if calls[0] == calib_calls + 5:
            raise RuntimeError("boom")
        return fake_chain_transport(6)(prompt)

    rec = run_m5_model("claude", PROTOCOL, transport=flaky, out_dir=str(tmp_path))
    assert rec["lost_cells"] == 2
    assert rec["errors"]
    assert rec["accounting"]["balanced"] is True


def test_rerun_protection(tmp_path):
    import pytest

    run_m5_model("claude", PROTOCOL, transport=fake_chain_transport(6), out_dir=str(tmp_path))
    with pytest.raises(FileExistsError):
        run_m5_model("claude", PROTOCOL, transport=fake_chain_transport(6), out_dir=str(tmp_path))
    run_m5_model("claude", PROTOCOL, transport=fake_chain_transport(6), out_dir=str(tmp_path), force=True)
    assert list(tmp_path.glob("claude.json.superseded-*"))
