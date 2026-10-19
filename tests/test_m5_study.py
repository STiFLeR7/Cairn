from __future__ import annotations

import json

import pytest

from benchmarks.m5_preregister import preregistration_digest
from benchmarks.m5_study import StudyPaused, compute_gate, run_m5_model
from benchmarks.scenarios import fake_chain_transport, live_chain_effect_scenario, live_chain_scenario
from cairn.eval.baselines import ColdRestart, RGR
from cairn.eval.calibration import run_calibration
from cairn.eval.runner import run_repeated

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
        assert rec["call_stats"] == {}
        assert rec["preregistration_sha256"] == preregistration_digest()
        assert rec["error_count"] == 0 and rec["resumed_errors"] == {"count": 0, "errors": []}
        assert "is_error" in rec["notes"]
        assert not (tmp_path / f"{label}.partial.jsonl").exists()
        assert len(list(tmp_path.glob(f"{label}.partial.done-*.jsonl"))) == 1
        assert rec["c3"]["supported"] is True
        assert "supported" in rec["c1_strict"]
        assert json.loads((tmp_path / f"{label}.json").read_text())["label"] == label
    gate = compute_gate(str(tmp_path))
    assert gate["decision"] == "GO"
    assert (tmp_path / "gate-verdict.json").exists()
    assert set(gate["models"]) == {"claude", "codex"}
    assert gate["models"]["claude"]["accounting"]["balanced"] is True
    assert set(gate["models"]["codex"]) == {"accounting", "skipped_cells", "call_stats", "observed_models"}
    assert gate["superseded_files"] == []


def test_gate_is_inconclusive_when_a_record_is_not_bound_to_the_preregistration(tmp_path):
    for label in ("claude", "codex"):
        run_m5_model(label, PROTOCOL, transport=fake_chain_transport(6), out_dir=str(tmp_path))
    gate = compute_gate(str(tmp_path), prereg_digest="f" * 64)
    assert gate["decision"] == "INCONCLUSIVE"
    assert "claude.json" in gate["reason"] and "codex.json" in gate["reason"]


def test_ineligible_model_skips_study(tmp_path):
    def gives_up(_prompt):
        return "TASK_COMPLETE"  # completes every run without doing the task

    rec = run_m5_model("codex", PROTOCOL, transport=gives_up, out_dir=str(tmp_path))
    assert rec["calibration"]["completed"] == 10 and rec["calibration"]["successes"] == 0
    assert rec["calibration"]["eligible"] is False
    assert rec["study_run"] is False and rec["lost_cells"] == rec["planned_cells"]
    assert rec["accounting"]["balanced"] is True


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


class UsageCap(RuntimeError):
    pass


def _counting(calls, fail_at=()):
    def transport(prompt):
        calls[0] += 1
        if calls[0] in fail_at or (fail_at == "all"):
            raise UsageCap("usage limit reached")
        return fake_chain_transport(6)(prompt)

    return transport


def _unit_calls(kind, k=None):
    calls = [0]
    t = _counting(calls)
    if kind == "cal":
        run_calibration(live_chain_scenario(6, t), runs=1)
    else:
        run_repeated(live_chain_effect_scenario(6, k, t), steps=[k], baselines=[ColdRestart(), RGR()], repeats=1)
    return calls[0]


def test_consecutive_errors_pause_and_keep_the_checkpoint(tmp_path):
    with pytest.raises(StudyPaused):
        run_m5_model("codex", PROTOCOL, transport=_counting([0], "all"), out_dir=str(tmp_path))
    assert not (tmp_path / "codex.json").exists()
    lines = [json.loads(x) for x in (tmp_path / "codex.partial.jsonl").read_text().splitlines()]
    assert set(lines[0]) == {"preregistration_sha256", "label"}
    assert [u["status"] for u in lines[1:]] == ["error", "error"]
    with pytest.raises(FileExistsError):  # an interrupted run is never silently restarted
        run_m5_model("codex", PROTOCOL, transport=fake_chain_transport(6), out_dir=str(tmp_path))


def test_resume_after_usage_cap_reuses_finished_units_and_keeps_errors(tmp_path):
    cal, s2, s3 = _unit_calls("cal"), _unit_calls("study", 2), _unit_calls("study", 3)
    first = [0]
    cap_from = 10 * cal + s2 + 2  # the cap hits inside the 2nd study unit (k=2, repeat 1)
    capped = _counting(first, fail_at=set(range(cap_from, 10_000)))
    with pytest.raises(StudyPaused):
        run_m5_model("claude", PROTOCOL, transport=capped, out_dir=str(tmp_path))
    lines = [json.loads(x) for x in (tmp_path / "claude.partial.jsonl").read_text().splitlines()][1:]
    assert sum(u["status"] == "ok" for u in lines) == 11  # 10 calibration + (k=2, repeat 0)
    assert [(u["k"], u["i"]) for u in lines if u["status"] == "error"] == [(2, 1), (3, 0)]

    resumed = [0]
    # Fresh transport after the cap resets; its first call errors once, so (k=2, repeat 1) stays lost.
    rec = run_m5_model("claude", PROTOCOL, transport=_counting(resumed, fail_at={1}), out_dir=str(tmp_path),
                       resume=True)
    assert resumed[0] == 1 + 2 * s3  # finished units were reused, not re-run
    assert rec["resumed_errors"]["count"] == 2 and all("UsageCap" in e for e in rec["resumed_errors"]["errors"])
    assert rec["lost_cells"] == 2 and rec["error_count"] == 1
    assert rec["fired_cells"] == 6 and rec["accounting"]["balanced"] is True
    assert rec["calibration"]["completed"] == 10 and rec["calibration"]["eligible"] is True
    assert not (tmp_path / "claude.partial.jsonl").exists()
    assert len(list(tmp_path.glob("claude.partial.done-*.jsonl"))) == 1


def test_resume_refuses_a_checkpoint_from_another_preregistration(tmp_path):
    (tmp_path / "claude.partial.jsonl").write_text(
        json.dumps({"preregistration_sha256": "0" * 64, "label": "claude"}) + "\n")
    with pytest.raises(ValueError, match="preregistration"):
        run_m5_model("claude", PROTOCOL, transport=fake_chain_transport(6), out_dir=str(tmp_path), resume=True)
