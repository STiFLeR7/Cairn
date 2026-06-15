from cairn.app import build_harness
from cairn.model import CODE, Action
from cairn.model_mock import ScriptableMockModel
from cairn.tasks import CreateFileTask


def _script_for(filename, content):
    code = f"open({filename!r}, 'w').write({content!r})"
    return ScriptableMockModel([Action(kind=CODE, code=code)])


def test_baseline_task_completes_and_checkpoints(tmp_path):
    task = CreateFileTask("out.txt", "hello cairn")
    harness, runtime = build_harness(
        model=_script_for("out.txt", "hello cairn"), base_dir=str(tmp_path)
    )

    result = harness.run(task)

    assert result.success is True
    assert result.steps == 1
    assert result.checkpoints >= 1

    # the checkpoint mechanism actually persisted a loadable cairn
    loaded = runtime.load_latest()
    assert loaded is not None
    state, snap, offset = loaded
    assert state.durable_core.intent.root_goal == task.goal
    assert snap  # a workspace snapshot id was recorded


def test_no_hardcoded_swap_task_and_model(tmp_path):
    # Swapping the task and the scripted model requires zero harness changes.
    task = CreateFileTask("data.txt", "42")
    harness, _ = build_harness(model=_script_for("data.txt", "42"), base_dir=str(tmp_path))
    assert harness.run(task).success is True


def test_unsatisfied_task_reports_failure(tmp_path):
    # Model writes the wrong content -> oracle reports failure (no false success).
    task = CreateFileTask("out.txt", "expected")
    harness, _ = build_harness(model=_script_for("out.txt", "WRONG"), base_dir=str(tmp_path))
    assert harness.run(task).success is False
