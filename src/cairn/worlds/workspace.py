"""Workspace — the reference filesystem World (snapshot/restore + content digest).

Wraps the proven runtime pieces (`WorkspaceManager` + `world_digest`) behind the public
`World` seam, so the recovery primitives treat the filesystem like any other World. It is
ALSO executable (`execute`) so the opt-in `Agent` loop can run code actions against it; the
sandbox and interpreter are injected (ADR-0007), defaulting to a local subprocess.
"""

from __future__ import annotations

import sys
from typing import Optional, Sequence

from ..runtime.digest import world_digest
from ..runtime.sandbox_local import LocalSubprocessSandbox
from ..runtime.workspace import WorkspaceManager
from ..sandbox import ExecResult, Sandbox


class Workspace:
    def __init__(
        self,
        workspace_dir: str,
        snapshots_dir: str,
        sandbox: Optional[Sandbox] = None,
        interpreter: Optional[str] = None,
    ) -> None:
        self.workspace_dir = workspace_dir
        self._wm = WorkspaceManager(workspace_dir, snapshots_dir)
        self.sandbox: Sandbox = sandbox or LocalSubprocessSandbox()
        self.interpreter = interpreter or sys.executable

    # --- World seam (snapshot / restore / digest) ----------------------------
    def snapshot(self) -> str:
        return self._wm.snapshot()

    def restore(self, snap_id: str) -> None:
        self._wm.restore(snap_id)

    def digest(self) -> dict:
        return world_digest(self.workspace_dir)

    # --- executable World (used by the opt-in Agent loop) --------------------
    def execute(self, code: str, cwd: Optional[str] = None) -> ExecResult:
        argv: Sequence[str] = [self.interpreter, "-c", code]
        return self.sandbox.run(argv, cwd=cwd or self.workspace_dir)
