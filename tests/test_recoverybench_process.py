import subprocess
import sys
from pathlib import Path

import pytest

from cairn.eval.recoverybench import (
    BENCHMARK_SCRIPT,
    INJECTED_FAILURE_EXIT,
    LiveRunConfig,
    load_fixture,
    run_paired_control,
    run_paired_live,
)
import cairn.eval.recoverybench as recoverybench


def test_recovery_uses_new_process_and_persisted_artifacts_only(tmp_path):
    result = run_paired_control(tmp_path, "bugfix", fault_step=1)

    assert result.failure.fired
    assert result.failure.worker_pid != result.recovery.worker_pid
    assert result.failure.exit_code == INJECTED_FAILURE_EXIT
    assert result.recovery.used_in_memory_history is False
    assert result.recovery.resume_plan_clean
    assert result.verification.passed


@pytest.mark.parametrize("fixture_name", ["bugfix", "config", "tests", "followup"])
def test_every_nonterminal_checkpoint_boundary_recovers(tmp_path, fixture_name):
    fixture = load_fixture(fixture_name)

    for fault_step in range(fixture.work_units - 1):
        result = run_paired_control(tmp_path, fixture_name, fault_step)
        assert result.failure.fired
        assert result.recovery.worker_pid != result.failure.worker_pid
        assert result.verification.passed


def test_resume_without_a_durable_failure_receipt_is_invalid(tmp_path):
    run_root = tmp_path / "missing-receipt"
    run_root.mkdir()

    result = subprocess.run(
        [sys.executable, str(BENCHMARK_SCRIPT), "--worker", "resume", "--run-root", str(run_root)],
        cwd=BENCHMARK_SCRIPT.parent.parent,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert not (run_root / "recovery.json").exists()


def test_recoverybench_cli_exposes_the_budgeted_live_matrix():
    result = subprocess.run(
        [sys.executable, str(BENCHMARK_SCRIPT), "--help"],
        cwd=BENCHMARK_SCRIPT.parent.parent,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "--live PROVIDER:MODEL" in result.stdout
    assert "--max-calls" in result.stdout
    assert "--max-tokens" in result.stdout


def test_live_worker_failure_is_durable_evidence(tmp_path, monkeypatch):
    failure = subprocess.CompletedProcess(["worker"], 3, "worker stdout", "worker stderr")
    monkeypatch.setattr(recoverybench, "_run_worker", lambda *_args, **_kwargs: failure)

    with pytest.raises(RuntimeError, match="baseline_worker_exit_3"):
        run_paired_live(
            tmp_path, "bugfix", 1, LiveRunConfig(provider="fake", model="fake/repository-agent"),
        )

    run_root = next(Path(tmp_path).iterdir())
    assert (run_root / "baseline" / "worker_failure.json").read_text(encoding="utf-8")


def test_live_terminal_agent_recovers_in_a_fresh_process_with_a_fake_transport(tmp_path):
    result = run_paired_live(
        tmp_path, "bugfix", 1, LiveRunConfig(provider="fake", model="fake/repository-agent"),
    )

    assert result.failure.fired
    assert result.failure.worker_pid != result.recovery.worker_pid
    assert result.recovery.used_in_memory_history is False
    assert result.recovery.resume_plan_clean
    assert result.verification.passed
    assert result.failure.checkpoint.provenance["model_version"] == "fake/repository-agent"
