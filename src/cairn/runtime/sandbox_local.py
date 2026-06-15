"""Default Sandbox: run commands in a local subprocess.

A str command runs via the shell; a sequence runs as argv (no shell, no quoting
surprises — used for code-as-action). This is the only built-in sandbox; others are
injected (ADR-0007).
"""

from __future__ import annotations

import subprocess
from typing import Optional

from ..sandbox import Command, ExecResult


class LocalSubprocessSandbox:
    def run(
        self,
        command: Command,
        cwd: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> ExecResult:
        shell = isinstance(command, str)
        proc = subprocess.run(
            command if shell else list(command),
            shell=shell,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return ExecResult(proc.returncode, proc.stdout or "", proc.stderr or "")
