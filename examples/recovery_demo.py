"""Recovery demo: crash an agent mid-task, then resume it via Re-grounding Recovery.

Run from the repo root:

    python examples/recovery_demo.py

Shows the three pillars together: a checkpoint written each step (unified distillation), a
crash in an effect's danger window, and a fresh runtime that resumes — re-grounding from the
cairn, resolving the effect safely (no duplicate), and finishing the task. Everything concrete
(task, model, effect) is wired here, not in the library (ADR-0007).
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))  # run without PYTHONPATH

from cairn.app import build_harness
from cairn.harness.effects import CHECK_BEFORE_RETRY, EffectfulTool
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


def main() -> None:
    base = tempfile.mkdtemp(prefix="cairn_recovery_")
    names = ["step0.txt", "step1.txt", "step2.txt"]
    task = MultiFileTask(names)
    script = [Action(kind=CODE, code=f"open({n!r},'w').write({n!r})") for n in names]
    outbox = os.path.join(base, "outbox.txt")  # the external world (not the workspace)

    # --- run until a crash between a checkpoint and an effect's COMPLETE -------
    h1, rt1 = build_harness(model=ScriptableMockModel(script), base_dir=base)

    def inject(step):
        rt1.append_effect("send_report", "send-1", CHECK_BEFORE_RETRY, step)  # INTENT durable
        with open(outbox, "a", encoding="utf-8") as f:
            f.write("sent\n")  # effect happens; crash before COMPLETE

    try:
        h1.run(task, step_hook=crash_after(1, do=inject))
    except InjectedFailure as e:
        print(f"[crash] {e}")

    print(f"[state] files={sorted(os.listdir(rt1.workspace_dir))} outbox_lines={_lines(outbox)}")

    # --- resume in a fresh runtime over the same base_dir ---------------------
    tool = EffectfulTool(
        "send_report",
        CHECK_BEFORE_RETRY,
        run=lambda: open(outbox, "a", encoding="utf-8").write("sent\n"),
        verify=lambda: os.path.exists(outbox) and os.path.getsize(outbox) > 0,
    )
    h2, rt2 = build_harness(
        model=ScriptableMockModel(script), base_dir=base, effect_tools={"send-1": tool}
    )
    result = h2.resume(task)

    print(f"[resume] success={result.success} recovery_tax={result.recovery_tax} "
          f"(cold restart would be {len(script)})")
    print(f"[resume] effect resolutions={[(r.key, r.action) for r in result.resolutions]}")
    print(f"[done] files={sorted(os.listdir(rt2.workspace_dir))} outbox_lines={_lines(outbox)} "
          f"(effect happened exactly once)")


def _lines(path):
    if not os.path.exists(path):
        return 0
    with open(path, encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


if __name__ == "__main__":
    main()
