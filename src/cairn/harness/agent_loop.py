"""The agent loop — observe -> decide -> act (code) -> observe — now with recovery.

`run` drives a task forward, checkpointing at each step boundary. `resume` implements the
Re-grounding Recovery protocol (ADR-0004): load the latest cairn, restore the workspace,
re-observe the world, reconcile the torn step (incl. resolving the effect danger window via
the effect-safety protocol), then continue from where the cairn left off — a different but
valid path is acceptable (outcome equivalence, not replay).

Everything is injected (model, tools, effect tools, runtime); nothing concrete is hardcoded
(ADR-0007). The optional `step_hook` is a generic lifecycle seam used (among other things) to
inject failures in tests without baking a crash flag into the harness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Mapping, Optional

from ..contract import Runtime
from ..model import CODE, FINISH, Action, ModelProvider, StepRecord
from ..state import ContinuationState, PlanStep
from ..task import Task
from ..tools import ToolRegistry
from .distill import CHECKPOINT, distill
from .effects import EffectfulTool, Resolution, resolve_danger_window
from .observe import observe_world
from .reconcile import ResumePlan, reconcile

StepHook = Callable[[int], None]


@dataclass
class RunResult:
    success: bool
    steps: int
    checkpoints: int
    final_state: Optional[ContinuationState]
    resumed: bool = False
    recovery_tax: Optional[int] = None  # steps executed after resume (vs a cold restart)
    resolutions: list[Resolution] = field(default_factory=list)
    resume_plan: Optional[ResumePlan] = None


class CodeHarness:
    def __init__(
        self,
        runtime: Runtime,
        model: ModelProvider,
        tools: Optional[ToolRegistry] = None,
        *,
        max_steps: int = 20,
        model_version: str = "mock",
        harness_version: Optional[str] = None,
        checkpoint_each_step: bool = True,
        effect_tools: Optional[Mapping[str, EffectfulTool]] = None,
        escalate_never_retry: bool = True,
    ) -> None:
        self.runtime = runtime
        self.model = model
        self.tools = tools or ToolRegistry()
        self.max_steps = max_steps
        self.model_version = model_version
        if harness_version is None:
            from .. import __version__

            harness_version = f"cairn-{__version__}"
        self.harness_version = harness_version
        self.checkpoint_each_step = checkpoint_each_step
        self.effect_tools: Mapping[str, EffectfulTool] = effect_tools or {}
        self.escalate_never_retry = escalate_never_retry

    def distill(self, goal: str, history: list, *, step: int) -> ContinuationState:
        return distill(
            goal,
            history,
            mode=CHECKPOINT,
            step=step,
            model_version=self.model_version,
            harness_version=self.harness_version,
            effect_offset=self.runtime.current_effect_offset(),
            workspace_dir=getattr(self.runtime, "workspace_dir", ""),
        )

    # --- normal operation ----------------------------------------------------
    def run(
        self, task: Task, workspace: Optional[str] = None, *, step_hook: Optional[StepHook] = None
    ) -> RunResult:
        cwd = workspace or getattr(self.runtime, "workspace_dir", None)
        steps, checkpoints, final_state = self._loop(task, [], cwd, start=0, step_hook=step_hook)
        return RunResult(
            success=bool(task.is_complete(cwd)) if cwd else False,
            steps=steps,
            checkpoints=checkpoints,
            final_state=final_state,
        )

    # --- recovery: Re-grounding Resume (RGR) ---------------------------------
    def resume(
        self, task: Task, workspace: Optional[str] = None, *, step_hook: Optional[StepHook] = None
    ) -> RunResult:
        cwd = workspace or getattr(self.runtime, "workspace_dir", None)

        # 1. LOAD (Runtime) — most recent fully-durable checkpoint (I5).
        loaded = self.runtime.load_latest()
        if loaded is None:
            return self.run(task, workspace, step_hook=step_hook)  # nothing to resume from
        state, snap_id, offset = loaded
        self.runtime.restore_workspace(snap_id)

        # 2. RE-OBSERVE (Code Harness) — look before acting.
        observed = observe_world(self.runtime, offset, cwd or "")

        # 3. RECONCILE (Code Harness) — torn writes, plan drift, effect danger window.
        plan = reconcile(state, observed)
        resolutions = resolve_danger_window(
            plan.danger_window,
            self.effect_tools,
            self.runtime,
            escalate=self.escalate_never_retry,
        )

        # 4 & 5. RE-PLAN + CONTINUE — re-ground history from the cairn so the model
        # continues from where it left off rather than restarting from scratch.
        history = _history_from_plan(plan.plan)
        executed, checkpoints, final_state = self._loop(
            task, history, cwd, start=len(history), step_hook=step_hook
        )
        return RunResult(
            success=bool(task.is_complete(cwd)) if cwd else False,
            steps=len(history),
            checkpoints=checkpoints,
            final_state=final_state,
            resumed=True,
            recovery_tax=executed,
            resolutions=resolutions,
            resume_plan=plan,
        )

    # --- shared decide-act-checkpoint loop -----------------------------------
    def _loop(self, task, history, cwd, *, start, step_hook):
        checkpoints = 0
        executed = 0
        final_state: Optional[ContinuationState] = None

        for step in range(start, self.max_steps):
            action = self.model.propose(task.goal, history)
            if action.kind == FINISH:
                break
            res = self.runtime.execute(action.code, cwd=cwd)
            history.append(
                StepRecord(
                    step=step,
                    action=action,
                    returncode=res.returncode,
                    stdout=res.stdout,
                    stderr=res.stderr,
                )
            )
            executed += 1
            if self.checkpoint_each_step:
                snap = self.runtime.snapshot_workspace()
                state = distill(
                    task.goal,
                    history,
                    mode=CHECKPOINT,
                    step=step,
                    model_version=self.model_version,
                    harness_version=self.harness_version,
                    effect_offset=self.runtime.current_effect_offset(),
                    snap_id=snap,
                    workspace_dir=cwd or "",
                )
                self.runtime.checkpoint(state, snap, self.runtime.current_effect_offset())
                final_state = state
                checkpoints += 1
            if step_hook is not None:
                step_hook(step)  # lifecycle seam (e.g. injected failure) — after checkpoint

        return executed, checkpoints, final_state


def _history_from_plan(plan: list[PlanStep]) -> list[StepRecord]:
    """Re-ground a minimal history from the cairn's *done* steps.

    Length is what an injected (mock) model uses to continue at the next un-done step; a
    reopened (torn) step is excluded so it gets redone. This is re-grounding from the cairn,
    not a token-level replay of the original trajectory.
    """
    out: list[StepRecord] = []
    i = 0
    for p in plan:
        if p.status == "done":
            out.append(StepRecord(step=i, action=Action(kind=CODE, code=p.description), returncode=0))
            i += 1
    return out
