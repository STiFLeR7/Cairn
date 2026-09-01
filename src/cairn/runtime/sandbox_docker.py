"""A minimal Docker executor for untrusted terminal-agent actions."""

from __future__ import annotations

import subprocess
import shutil
from pathlib import Path
from typing import Callable, Optional
from uuid import uuid4

from ..sandbox import Command, ExecResult


class DockerTerminalSandbox:
    """Run actions with only the repository mounted and no network or host environment."""

    def __init__(
        self,
        *,
        image: str = "python:3.12-alpine",
        runner: Optional[Callable[..., subprocess.CompletedProcess[str]]] = None,
    ) -> None:
        self.image = image
        self._runner = runner or subprocess.run

    @staticmethod
    def available() -> bool:
        """True only when the local Docker daemon accepts commands."""
        if shutil.which("docker") is None:
            return False
        try:
            result = subprocess.run(
                ["docker", "version", "--format", "{{.Server.Version}}"],
                capture_output=True, text=True, timeout=10, check=False,
            )
        except OSError:
            return False
        return result.returncode == 0

    def run(
        self,
        command: Command,
        cwd: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> ExecResult:
        if not cwd:
            raise ValueError("DockerTerminalSandbox requires a workspace cwd")
        workspace = Path(cwd).resolve()
        if not workspace.is_dir():
            raise ValueError(f"workspace does not exist: {workspace}")
        container_name = f"cairn-{uuid4().hex}"
        argv = [
            "docker", "run", "--rm", "--name", container_name,
            "--network", "none", "--read-only",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m", "--pids-limit", "64",
            "--memory", "512m", "--cpus", "1", "--cap-drop=ALL",
            "--security-opt=no-new-privileges", "-e", "PYTHONDONTWRITEBYTECODE=1",
            "-v", f"{workspace}:/workspace:rw", "-w", "/workspace", self.image,
        ]
        if isinstance(command, str):
            argv.extend(("sh", "-lc", command))
        else:
            argv.extend(command)
        try:
            proc = self._runner(
                argv, capture_output=True, text=True, timeout=timeout, check=False
            )
        except FileNotFoundError:
            return ExecResult(127, "", "docker executable not found")
        except subprocess.TimeoutExpired:
            try:
                self._runner(
                    ["docker", "rm", "-f", container_name], capture_output=True,
                    text=True, timeout=10.0, check=False,
                )
            except (OSError, subprocess.TimeoutExpired):
                pass
            return ExecResult(124, "", f"command timed out after {timeout:g} seconds")
        return ExecResult(proc.returncode, proc.stdout or "", proc.stderr or "")
