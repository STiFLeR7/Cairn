"""Repository-backed World for the Phase 1 terminal recovery control."""

from __future__ import annotations

from typing import Optional

from .workspace import Workspace


class TerminalWorld(Workspace):
    """A Workspace that executes terminal commands in its repository root."""

    def execute(self, command: str, cwd: Optional[str] = None):
        return self.sandbox.run(command, cwd=cwd or self.workspace_dir, timeout=30.0)
