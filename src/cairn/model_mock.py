"""ScriptableMockModel — the default, deterministic ModelProvider.

Returns a fixed script of actions in order; once exhausted it returns FINISH. Makes
end-to-end runs and (Phase 4+) recovery tests reproducible without a live LLM.
Real LLM adapters are injected plugins; nothing here is hardcoded into the harness.
"""

from __future__ import annotations

from typing import Sequence

from .model import Action, FINISH, StepRecord


class ScriptableMockModel:
    def __init__(self, script: Sequence[Action]) -> None:
        self._script = list(script)

    def propose(self, goal: str, history: list[StepRecord]) -> Action:
        idx = len(history)
        if idx < len(self._script):
            return self._script[idx]
        return Action(kind=FINISH, result="script exhausted")
