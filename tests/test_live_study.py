"""Tests for the live-pipeline study runner (AP-0040), fully offline.

These exercise the entire live pipeline — LiveModelProvider -> parse -> harness ->
matrix -> metrics — using the deterministic fake transport. They are the standing
proof that swapping in a real transport (build_live_transport) is the *only* change
needed to run the paid study; that gated step is not executed here.
"""

from __future__ import annotations

import json

import pytest

from benchmarks.scenarios import (
    build_live_transport,
    fake_chain_transport,
    fake_multifile_transport,
    live_effectful_scenario,
    live_multi_file_scenario,
)
from benchmarks.live_study import run_live_study
from cairn.eval.baselines import ColdRestart, RGR
from cairn.eval.runner import aggregate, run_matrix
from cairn.eval.scenario import run_reference
from cairn.model_live import LiveModelConfigError


def test_fake_transport_emits_next_file_then_completes():
    transport = fake_multifile_transport(["a.txt", "b.txt"])
    assert "a.txt" in transport("GOAL\nHISTORY: (none yet — this is the first step)")
    assert "b.txt" in transport("GOAL\n--- step 0 ---\nyou ran:\nx\nreturncode: 0")
    assert transport("GOAL\n--- step 0 ---\n--- step 1 ---").strip() == "TASK_COMPLETE"


def test_live_pipeline_reference_run_succeeds(tmp_path):
    outcome = run_reference(live_multi_file_scenario(4), str(tmp_path))
    assert outcome.success
    assert outcome.executed == 4  # one CODE action per file, then FINISH


def test_live_pipeline_matrix_supports_c1():
    summary = aggregate(run_matrix(live_multi_file_scenario(5), steps=[1, 2, 3, 4]))
    b0, b3 = summary["B0"], summary["B3"]
    assert b3["recovery_tax"] < b0["recovery_tax"]      # RGR pays less tax than cold restart
    assert b3["no_regression"] > b0["no_regression"]    # ...and preserves pre-failure work
    assert b3["task_success"] == 1.0


def test_live_pipeline_effect_safety_supports_c3():
    reports = run_matrix(live_effectful_scenario(4, effect_step=2), steps=[2],
                         baselines=[ColdRestart(), RGR()])
    by = {r.baseline: r for r in reports}
    assert by["B3"].effect_duplicates == 0 and by["B3"].passes_gate
    assert by["B0"].effect_duplicates >= 1


def test_build_live_transport_is_inert_without_key(monkeypatch):
    # The gated live path is wired but must not run without an explicit key.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(LiveModelConfigError):
        build_live_transport("claude-some-model-id")


def test_live_study_runs_on_chain_offline(tmp_path, monkeypatch):
    """AP-0046 pipeline proof: run_live_study on the NON-BATCHABLE chain with an injected fake
    transport (no key, no network). Crashes fire (nothing skipped), C1 is SUPPORTED with stats,
    and an auditable manifest is written. The only change for the real run is the transport."""
    monkeypatch.chdir(tmp_path)
    verdict = run_live_study(
        "fake/chain", transport=fake_chain_transport(6), n=6, steps=(2, 3), repeats=2
    )
    assert verdict["claim"] == "C1" and verdict["supported"] is True
    manifest = tmp_path / "benchmarks" / "transcripts" / "fake_chain-chain-study.manifest.json"
    assert manifest.exists()
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["fired"] == 8 and data["skipped"] == 0 and data["c1_supported"] is True
