from pathlib import Path

import pytest

from benchmarks.phase2_replay_control import replay_continuation_branch
from cairn.eval.phase2 import run_live_urc
from cairn.eval.recoverybench import LiveRunConfig, load_fixture
from cairn.runtime.digest import world_digest


@pytest.mark.parametrize("target_branch", ["R", "C"])
def test_replaying_verified_actions_completes_target_branch(tmp_path, target_branch):
    record = run_live_urc(
        tmp_path / "source",
        "bugfix",
        split_step=0,
        config=LiveRunConfig(provider="fake", model="control"),
        prefix_mode="control",
    )
    source_root = tmp_path / "source" / record["run_id"]
    fixture = load_fixture("bugfix")
    replies = [
        f"```python\nfrom pathlib import Path\nPath('project.py').write_text({fixture.steps[step]!r})\n```"
        for step in (1, 2)
    ]

    replay = replay_continuation_branch(
        source_root,
        "bugfix",
        split_step=0,
        replies=replies,
        output_dir=tmp_path / "replay",
        target_branch=target_branch,
    )

    assert replay["target_branch"] == target_branch
    assert replay["success"] is True, replay
    assert replay["verified"] is True
    assert replay["final_digest"] == world_digest(str(source_root / "U" / "bugfix"))
    assert Path(replay["workspace"]).is_dir()
