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
