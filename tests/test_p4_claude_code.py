from pathlib import Path

from benchmarks.p4_claude_code import prepare_claude_workspace, prepare_effect_workspace, stream_has_tool


def test_claude_workspace_is_public_and_stream_tool_evidence_is_host_native(tmp_path: Path):
    workspace = prepare_claude_workspace(tmp_path / "workspace")

    assert workspace == (tmp_path / "workspace")
    assert "greet" in (workspace / "TASK.md").read_text(encoding="utf-8")
    assert "verify.py" in (workspace / "TASK.md").read_text(encoding="utf-8")
    assert stream_has_tool(
        [{"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash"}]}}], "Bash"
    )


def test_effect_workspace_reuses_the_admitted_create_once_provider(tmp_path: Path):
    workspace = prepare_effect_workspace(tmp_path / "effect-workspace", tmp_path / "remote")

    task = (workspace / "EFFECT_TASK.md").read_text(encoding="utf-8")
    tool = (workspace / "effect_tool.py").read_text(encoding="utf-8")
    assert "re-observe" in task
    assert "CreateOnceProvider" in tool
    assert "EffectLedger" in tool
