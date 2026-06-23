"""Task interface — what the agent is asked to do, plus its success oracle.

Tasks are injected; the harness knows nothing about any concrete task.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class Task(ABC):
    @property
    @abstractmethod
    def goal(self) -> str:
        """Natural-language description of the task (handed to the model)."""

    @abstractmethod
    def is_complete(self, workspace: str) -> bool:
        """Success oracle: inspect the workspace and report whether the task is done."""

    def setup(self, workspace: str) -> None:
        """Prepare the task environment in `workspace` before the agent runs (default: no-op).

        Called by the harness at the start of every run/resume/continue. Use it to plant
        fixtures the agent needs (e.g. a stateful tool module) — *not* agent progress, which
        must stay recoverable. Must be idempotent and must not reset partial progress, since
        it runs again on each recovery attempt (after a cold-restart wipe, it re-establishes
        the environment the agent redoes its work against).
        """
