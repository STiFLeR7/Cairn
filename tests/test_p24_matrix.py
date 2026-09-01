from pathlib import Path

from benchmarks.p24_matrix import p24_cells, run_p24_cell


def _fake_cell(split_step: int = 1) -> dict:
    return {
        "provider": "fake",
        "model": "fake",
        "fixture": "p24_queue_policy",
        "split_step": split_step,
        "repetition": 1,
    }


def test_p24_fake_cell_runs_r_and_c_in_distinct_processes(tmp_path):
    record = run_p24_cell(_fake_cell(), {}, tmp_path)

    assert (Path(record["run_dir"]) / "prefix" / "p24_queue_policy" / "project.py").is_file()
    assert record["branches"]["R"]["worker_pid"] != record["parent_pid"]
    assert record["branches"]["C"]["worker_pid"] != record["parent_pid"]
    assert record["branches"]["R"]["used_in_memory_history"] is False
    assert record["branches"]["C"]["original_transcript_available"] is False


def test_p24_fake_cell_preserves_prefix_and_next_ordered_action(tmp_path):
    record = run_p24_cell(_fake_cell(), {}, tmp_path)

    for branch in record["branches"].values():
        assert branch["start_progress"] == 2
        assert branch["accepted_progress"] == [3, 4]
        assert branch["final_progress"] == 4
        assert branch["verified"] is True
        assert branch["success"] is True
        assert len(branch["accepted_actions"]) == 2
        assert all(action["code"] for action in branch["accepted_actions"])


def test_p24_cells_enumerates_the_sealed_matrix_shape():
    protocol = {"matrix": {"models": [{"provider": "claude_code", "model": "opus"}, {"provider": "claude_code", "model": "sonnet"}], "repetitions_per_model_fixture_split": 10}}

    cells = p24_cells(protocol)

    assert len(cells) == 60
    assert {cell["split_step"] for cell in cells} == {0, 1, 2}
