"""The opt-in, batteries-included Agent loop — built on the public recovery primitives.

`Agent` is the turnkey path for a dev who wants recovery without writing their own loop:
bring a `Model` and a `World` (the bundled `Workspace`, or your own executable world) and
call `.run(goal)`; after a crash, `.resume(goal)` re-grounds via `recover()` and continues.

The loop itself is deliberately tiny — propose -> execute -> record -> checkpoint — because
all the recovery intelligence lives in the primitives (`checkpoint`/`recover`). Everything is
injected (model, world, store, ledger, effect tools); nothing is hardcoded (ADR-0007).

A `World` used by the Agent must additionally be *executable* (expose `execute(code, cwd=None)
-> ExecResult`); the bundled `Workspace` is. The Agent does not judge task success (it has no
task oracle) — it reports whether the model finished and hands back the full history + the last
checkpoint so the caller applies their own success criterion.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Optional

from .harness.effects import EffectfulTool, Resolution
from .model import FINISH, ModelProvider, StepRecord
from .recovery import Checkpoint, checkpoint, recover


@dataclass
class AgentRun:
    """The outcome of `Agent.run`/`Agent.resume`."""

    finished: bool                                  # model emitted FINISH (vs hit max_steps)
    steps: int                                      # steps executed in THIS call
    checkpoints: int                                # checkpoints written in THIS call
    history: list = field(default_factory=list)     # full StepRecord history (re-grounded + new)
    final_state: Optional[Checkpoint] = None
    resumed: bool = False
    recovery_tax: Optional[int] = None              # steps executed after resume (None for run)
    resolutions: list = field(default_factory=list)


class Agent:
    def __init__(
        self,
        model: ModelProvider,
        world,
        *,
        store,
        ledger,
        effect_tools: Optional[Mapping[str, EffectfulTool]] = None,
        max_steps: int = 20,
        escalate: bool = True,
        model_version: str = "byom",
        harness_version: str = "",
    ) -> None:
        self.model = model
        self.world = world
        self.store = store
        self.ledger = ledger
        self.effect_tools: Mapping[str, EffectfulTool] = effect_tools or {}
        self.max_steps = max_steps
        self.escalate = escalate
        self.model_version = model_version
        self.harness_version = harness_version

    def run(self, goal: str) -> AgentRun:
        """Drive the goal from scratch, checkpointing each executed step."""
        return self._loop(goal, [], start=0, resumed=False, resolutions=[])

    def resume(self, goal: str) -> AgentRun:
        """Re-ground from the latest checkpoint (RGR), then continue the loop.

        With no durable checkpoint, falls back to a fresh `run` (mirrors the primitives).
        """
        rg = recover(
            self.world, self.store, self.ledger,
            effect_tools=self.effect_tools, escalate=self.escalate,
        )
        if rg.plan is None:  # nothing to resume from
            return self.run(goal)
        return self._loop(
            goal, list(rg.history), start=len(rg.history),
            resumed=True, resolutions=rg.resolutions,
        )

    def _loop(self, goal, history, *, start, resumed, resolutions) -> AgentRun:
        executed = 0
        checkpoints = 0
        final_state: Optional[Checkpoint] = None
        finished = False
        for step in range(start, self.max_steps):
            action = self.model.propose(goal, history)
            if action.kind == FINISH:
                finished = True
                break
            res = self.world.execute(action.code)
            history.append(
                StepRecord(
                    step=step, action=action,
                    returncode=res.returncode, stdout=res.stdout, stderr=res.stderr,
                )
            )
            executed += 1
            final_state = checkpoint(
                goal, history, self.world, self.store, self.ledger, step=step,
                model_version=self.model_version, harness_version=self.harness_version,
            )
            checkpoints += 1
        return AgentRun(
            finished=finished,
            steps=executed,
            checkpoints=checkpoints,
            history=history,
            final_state=final_state,
            resumed=resumed,
            recovery_tax=executed if resumed else None,
            resolutions=list(resolutions),
        )
