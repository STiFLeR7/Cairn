"""LocalRuntime — composes the Runtime-side pieces behind the boundary contract.

All storage lives under an injected `base_dir`; the sandbox and interpreter are
injected (defaults provided). No hardcoded paths (ADR-0007).
"""

from __future__ import annotations

import os
import sys
from typing import Optional, Sequence, Tuple

from ..sandbox import ExecResult, Sandbox
from ..state import ContinuationState
from .checkpoint_store import CheckpointStore
from .effect_ledger import EffectLedger
from .sandbox_local import LocalSubprocessSandbox
from .workspace import WorkspaceManager


class LocalRuntime:
    def __init__(
        self,
        base_dir: str,
        sandbox: Optional[Sandbox] = None,
        interpreter: Optional[str] = None,
        ledger_id: str = "run",
    ) -> None:
        self.base_dir = base_dir
        self.workspace_dir = os.path.join(base_dir, "workspace")
        os.makedirs(self.workspace_dir, exist_ok=True)
        self._wm = WorkspaceManager(self.workspace_dir, os.path.join(base_dir, "snapshots"))
        self._ledger = EffectLedger(os.path.join(base_dir, "effects.jsonl"), ledger_id)
        self._ckpt = CheckpointStore(os.path.join(base_dir, "checkpoints"))
        self.sandbox: Sandbox = sandbox or LocalSubprocessSandbox()
        self.interpreter = interpreter or sys.executable

    # --- execution substrate (code-as-action) -------------------------------
    def execute(self, code: str, cwd: Optional[str] = None) -> ExecResult:
        argv: Sequence[str] = [self.interpreter, "-c", code]
        return self.sandbox.run(argv, cwd=cwd or self.workspace_dir)

    # --- workspace -----------------------------------------------------------
    def snapshot_workspace(self) -> str:
        return self._wm.snapshot()

    def restore_workspace(self, snap_id: str) -> None:
        self._wm.restore(snap_id)

    # --- checkpoint store ----------------------------------------------------
    def checkpoint(self, state: ContinuationState, snap_id: str, effect_offset: int) -> str:
        return self._ckpt.checkpoint(state, snap_id, effect_offset)

    def load_latest(self) -> Optional[Tuple[ContinuationState, str, int]]:
        return self._ckpt.load_latest()

    # --- effect ledger -------------------------------------------------------
    def append_effect(
        self, intent: str, idempotency_key: str, tool_class: str = "never-retry", step: int = 0
    ) -> int:
        return self._ledger.append_effect(intent, idempotency_key, tool_class, step)

    def complete_effect(self, idempotency_key: str) -> None:
        self._ledger.complete_effect(idempotency_key)

    def list_effects_since(self, offset: int) -> list[dict]:
        return self._ledger.list_effects_since(offset)

    def current_effect_offset(self) -> int:
        return self._ledger.current_offset()
