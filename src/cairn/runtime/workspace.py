"""Workspace snapshot / restore (taxonomy layer 1)."""

from __future__ import annotations

import os
import shutil


class WorkspaceManager:
    def __init__(self, workspace_dir: str, snapshots_dir: str) -> None:
        self.workspace_dir = workspace_dir
        self.snapshots_dir = snapshots_dir
        os.makedirs(workspace_dir, exist_ok=True)
        os.makedirs(snapshots_dir, exist_ok=True)
        self._n = 0

    def snapshot(self) -> str:
        snap_id = f"snap_{self._n}"
        self._n += 1
        dest = os.path.join(self.snapshots_dir, snap_id)
        if os.path.exists(dest):
            shutil.rmtree(dest)
        shutil.copytree(self.workspace_dir, dest)
        return snap_id

    def restore(self, snap_id: str) -> None:
        src = os.path.join(self.snapshots_dir, snap_id)
        if not os.path.isdir(src):
            raise FileNotFoundError(f"unknown snapshot: {snap_id}")
        for name in os.listdir(self.workspace_dir):
            p = os.path.join(self.workspace_dir, name)
            if os.path.isdir(p):
                shutil.rmtree(p)
            else:
                os.remove(p)
        for name in os.listdir(src):
            s = os.path.join(src, name)
            d = os.path.join(self.workspace_dir, name)
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
