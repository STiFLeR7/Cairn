"""Recovery baselines B0–B3 behind one interface (AP-0029).

Each strategy recovers a *failed* scenario (durable state already on disk under `base_dir`)
and returns a `RunOutcome`. Definitions follow ADR-0009 §2:

  B0 ColdRestart  — wipe the workspace, run the task from scratch (external world persists).
  B1 LogReplay    — replay the recorded action log into a fresh workspace, then continue
                    (no semantic re-grounding, no effect-safety).
  B2 SnapshotOnly — restore the latest workspace snapshot, then continue with a fresh model
                    context (no reconcile, no effect-safety).
  B3 RGR          — `CodeHarness.resume`: re-ground from the cairn + effect ledger.
"""

from __future__ import annotations

from typing import Protocol

from ..model import CODE, Action, StepRecord
from ..runtime.digest import world_digest
from .scenario import RunOutcome, harness_for, outbox_count, wipe_workspace


class RecoveryStrategy(Protocol):
    name: str

    def recover(self, scenario, base_dir: str) -> RunOutcome:
        ...


def _outcome(scenario, rt, base_dir, *, success, executed, result=None) -> RunOutcome:
    return RunOutcome(
        success=success,
        executed=executed,
        final_digest=world_digest(rt.workspace_dir),
        outbox_count=outbox_count(base_dir),
        result=result,
    )


class ColdRestart:
    name = "B0"

    def recover(self, scenario, base_dir: str) -> RunOutcome:
        h, rt = harness_for(scenario, base_dir)
        wipe_workspace(rt)  # start over; the external world (outbox) persists
        from .scenario import _completed_effect_hook

        hook = _completed_effect_hook(scenario, rt, base_dir) if scenario.effect else None
        res = h.run(scenario.task_factory(), step_hook=hook)
        return _outcome(scenario, rt, base_dir, success=res.success, executed=res.steps, result=res)


class LogReplay:
    name = "B1"

    def recover(self, scenario, base_dir: str) -> RunOutcome:
        h, rt = harness_for(scenario, base_dir)
        loaded = rt.load_latest()
        wipe_workspace(rt)
        history: list[StepRecord] = []
        if loaded:
            state, _snap, _off = loaded
            for i, p in enumerate(state.durable_core.plan):  # replay the recorded log
                r = rt.execute(p.description, cwd=rt.workspace_dir)
                history.append(
                    StepRecord(step=i, action=Action(kind=CODE, code=p.description),
                               returncode=r.returncode, stdout=r.stdout, stderr=r.stderr)
                )
        res = h.continue_from(scenario.task_factory(), history)  # continue, no re-grounding
        executed = len(history) + (res.recovery_tax or 0)
        return _outcome(scenario, rt, base_dir, success=res.success, executed=executed, result=res)


class SnapshotOnly:
    name = "B2"

    def recover(self, scenario, base_dir: str) -> RunOutcome:
        h, rt = harness_for(scenario, base_dir)
        loaded = rt.load_latest()
        if loaded:
            _state, snap, _off = loaded
            rt.restore_workspace(snap)  # restore bytes, but no semantic re-grounding
        res = h.run(scenario.task_factory())  # fresh model context → restarts from step 0
        return _outcome(scenario, rt, base_dir, success=res.success, executed=res.steps, result=res)


class RGR:
    name = "B3"

    def recover(self, scenario, base_dir: str) -> RunOutcome:
        h, rt = harness_for(scenario, base_dir)
        res = h.resume(scenario.task_factory())  # load → re-observe → reconcile → continue
        executed = res.recovery_tax if res.recovery_tax is not None else res.steps
        return _outcome(scenario, rt, base_dir, success=res.success, executed=executed, result=res)


ALL_BASELINES = [ColdRestart(), LogReplay(), SnapshotOnly(), RGR()]
