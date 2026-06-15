"""AP-0027 — end-to-end recovery from an injected failure (claims C1 + C3 together).

Run a multi-step task that performs a tracked effect, crash mid-run (an effect whose
COMPLETE never lands), then resume in a *freshly constructed* runtime over the same base_dir.
Assert: the task completes, the effect happens exactly once, and recovery does not restart
from scratch.
"""

import os

import pytest

from cairn.app import build_harness
from cairn.harness.effects import CHECK_BEFORE_RETRY, EffectfulTool, danger_window
from cairn.harness.failure import InjectedFailure, crash_after
from cairn.model import CODE, Action
from cairn.model_mock import ScriptableMockModel
from cairn.task import Task


class MultiFileTask(Task):
    def __init__(self, names):
        self.names = names

    @property
    def goal(self):
        return "create files: " + ", ".join(self.names)

    def is_complete(self, workspace):
        return all(os.path.isfile(os.path.join(workspace, n)) for n in self.names)


def _writer(name):
    # code-as-action: write the file in the sandbox cwd (the workspace)
    return Action(kind=CODE, code=f"open({name!r}, 'w').write({name!r})")


def test_end_to_end_recovery_from_injected_failure(tmp_path):
    base = str(tmp_path / "base")
    names = ["step0.txt", "step1.txt", "step2.txt"]
    task = MultiFileTask(names)
    script = [_writer(n) for n in names]

    # The effect acts on the EXTERNAL world (an outbox beside the workspace, not inside it),
    # so restore_workspace does not revert it — exactly like a real send.
    outbox = os.path.join(base, "outbox.txt")

    # --- Phase A: run until a crash in the effect's danger window --------------
    h1, rt1 = build_harness(model=ScriptableMockModel(script), base_dir=base)

    def inject_inflight_effect(step):
        # INTENT durable first (I1); the effect executes; the crash hits before COMPLETE.
        rt1.append_effect("send_report", "send-1", CHECK_BEFORE_RETRY, step)
        with open(outbox, "a", encoding="utf-8") as f:
            f.write("sent\n")

    with pytest.raises(InjectedFailure):
        h1.run(task, step_hook=crash_after(1, do=inject_inflight_effect))

    assert os.path.isfile(os.path.join(rt1.workspace_dir, "step1.txt"))
    assert not os.path.isfile(os.path.join(rt1.workspace_dir, "step2.txt"))  # crashed first
    with open(outbox, encoding="utf-8") as f:
        assert f.read() == "sent\n"  # effect happened once, COMPLETE never written

    # --- Phase B: resume in a FRESH runtime over the same base_dir -------------
    verify = lambda: os.path.exists(outbox) and os.path.getsize(outbox) > 0  # noqa: E731
    send = lambda: open(outbox, "a", encoding="utf-8").write("sent\n")  # noqa: E731
    tool = EffectfulTool("send_report", CHECK_BEFORE_RETRY, run=send, verify=verify)

    h2, rt2 = build_harness(
        model=ScriptableMockModel(script), base_dir=base, effect_tools={"send-1": tool}
    )
    result = h2.resume(task)

    # C1: recovered and completed the task.
    assert result.success
    assert result.resumed
    for n in names:
        assert os.path.isfile(os.path.join(rt2.workspace_dir, n))

    # Recovery tax: continued from the cairn, did not cold-restart all steps.
    assert result.recovery_tax == 1
    assert result.recovery_tax < len(script)

    # C3: the effect was verified-already-done → skipped, so it appears exactly once.
    assert any(r.key == "send-1" and r.action == "skip" for r in result.resolutions)
    with open(outbox, encoding="utf-8") as f:
        assert f.read() == "sent\n"  # no duplicate
    assert danger_window(rt2.list_effects_since(0)) == []  # window closed (COMPLETE written)
