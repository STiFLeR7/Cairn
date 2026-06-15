"""Sandbox interface — the Runtime's pluggable execution substrate.

The harness executes code through a Sandbox; it never assumes a particular one.
The default local-subprocess implementation lives in cairn.runtime.sandbox_local.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol, Sequence, Union, runtime_checkable


@dataclass
class ExecResult:
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


Command = Union[str, Sequence[str]]


@runtime_checkable
class Sandbox(Protocol):
    """Execute a command. A str runs via the shell; a sequence runs as argv."""

    def run(
        self,
        command: Command,
        cwd: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> ExecResult:
        ...
