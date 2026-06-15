"""ModelProvider interface and the action/observation types.

In a Code Harness the model proposes *code* as its action. The provider is always
injected; the default deterministic implementation is cairn.model_mock.ScriptableMockModel.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

CODE = "code"
FINISH = "finish"


@dataclass
class Action:
    """A proposed action. kind == CODE carries code to execute; FINISH ends the run."""

    kind: str
    code: str = ""
    result: str = ""


@dataclass
class StepRecord:
    """One executed step: the action plus the observation it produced."""

    step: int
    action: Action
    returncode: int = 0
    stdout: str = ""
    stderr: str = ""


@runtime_checkable
class ModelProvider(Protocol):
    def propose(self, goal: str, history: list[StepRecord]) -> Action:
        ...
