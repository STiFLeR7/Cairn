"""Workspace — the reference filesystem World (snapshot/restore + content digest).

Wraps the proven runtime pieces (`WorkspaceManager` + `world_digest`) behind the public
`World` seam, so the recovery primitives treat the filesystem like any other World.
"""

from __future__ import annotations

from ..runtime.digest import world_digest
from ..runtime.workspace import WorkspaceManager


class Workspace:
    def __init__(self, workspace_dir: str, snapshots_dir: str) -> None:
        self.workspace_dir = workspace_dir
        self._wm = WorkspaceManager(workspace_dir, snapshots_dir)

    def snapshot(self) -> str:
        return self._wm.snapshot()

    def restore(self, snap_id: str) -> None:
        self._wm.restore(snap_id)

    def digest(self) -> dict:
        return world_digest(self.workspace_dir)
