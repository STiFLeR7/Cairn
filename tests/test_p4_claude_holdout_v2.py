from pathlib import Path

from benchmarks.p4_claude_holdout_v2 import prepare_holdout_workspace


def test_second_holdout_is_distinct_from_the_invalidated_first_holdout(tmp_path: Path):
    workspace = prepare_holdout_workspace(tmp_path / "workspace", tmp_path / "remote")

    assert "join_segments" in (workspace / "TASK.md").read_text(encoding="utf-8")
    assert "p4-claude-holdout-v2-key" in (workspace / "effect_tool.py").read_text(encoding="utf-8")
