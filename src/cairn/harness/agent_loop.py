"""The agent loop — observe -> decide -> act (code) -> observe.

Fully injected: an injected ModelProvider proposes code, the injected Runtime executes
it in the sandbox, and a checkpoint is written at each step boundary (the mechanism;
recovery/resume is Phase 4). Nothing concrete is hardcoded (ADR-0007).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..contract import Runtime
from ..model import FINISH, ModelProvider, StepRecord
from ..state import ContinuationState
from ..task import Task
from ..tools import ToolRegistry
from .distill import minimal_distill


@dataclass
class RunResult:
    success: bool
    steps: int
    checkpoints: int
    final_state: Optional[ContinuationState]


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

    def distill(self, goal: str, history: list, *, step: int) -> ContinuationState:
        return minimal_distill(
            goal,
            history,
            step=step,
            model_version=self.model_version,
            harness_version=self.harness_version,
            effect_offset=self.runtime.current_effect_offset(),
        )

    def run(self, task: Task, workspace: Optional[str] = None) -> RunResult:
        cwd = workspace or getattr(self.runtime, "workspace_dir", None)
        history: list[StepRecord] = []
        checkpoints = 0
        final_state: Optional[ContinuationState] = None

        for step in range(self.max_steps):
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
            if self.checkpoint_each_step:
                snap = self.runtime.snapshot_workspace()
                state = minimal_distill(
                    task.goal,
                    history,
                    step=step,
                    model_version=self.model_version,
                    harness_version=self.harness_version,
                    effect_offset=self.runtime.current_effect_offset(),
                    snap_id=snap,
                )
                self.runtime.checkpoint(state, snap, self.runtime.current_effect_offset())
                final_state = state
                checkpoints += 1

        success = bool(task.is_complete(cwd)) if cwd else False
        return RunResult(
            success=success,
            steps=len(history),
            checkpoints=checkpoints,
            final_state=final_state,
        )
