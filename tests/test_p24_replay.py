import json

from benchmarks.p24_matrix import run_p24_cell
from benchmarks.p24_replay import replay_p24_branch


def test_p24_replay_requires_source_digest_equivalence(tmp_path):
    cell = {"provider": "fake", "model": "fake", "fixture": "p24_queue_policy", "split_step": 1, "repetition": 1}
    record_path = tmp_path / "record.json"
    record_path.write_text(json.dumps(run_p24_cell(cell, {}, tmp_path / "runs")), encoding="utf-8")

    replay = replay_p24_branch(record_path, "U", "C", tmp_path / "replay")

    assert replay["verified"] is True
    assert replay["final_digest"] == replay["source_final_digest"]


def test_p24_replay_reconstructs_recovery_target(tmp_path):
    cell = {"provider": "fake", "model": "fake", "fixture": "p24_queue_policy", "split_step": 1, "repetition": 1}
    record_path = tmp_path / "record.json"
    record_path.write_text(json.dumps(run_p24_cell(cell, {}, tmp_path / "runs")), encoding="utf-8")

    replay = replay_p24_branch(record_path, "U", "R", tmp_path / "replay")

    assert replay["verified"] is True
    assert replay["final_digest"] == replay["source_final_digest"]
