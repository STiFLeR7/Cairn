from pathlib import Path

import pytest

from benchmarks.p4_claude_protocol import TASK_PROMPT, prepare, run


def test_prepare_seals_public_contexts_before_host_execution(tmp_path: Path):
    contexts = prepare(tmp_path)

    assert (tmp_path / "protocol.json").is_file()
    assert (tmp_path / "prepared-contexts.json").is_file()
    assert (Path(contexts["holdout"]) / "TASK.md").is_file()
    assert TASK_PROMPT == "Read TASK.md and execute it exactly."


def test_run_refuses_to_start_without_a_matching_pre_run_freeze(tmp_path: Path):
    prepare(tmp_path)

    with pytest.raises(RuntimeError, match="pre-run controls"):
        run("not-invoked", tmp_path)
