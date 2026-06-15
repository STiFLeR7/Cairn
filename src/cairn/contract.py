"""The Code Harness <-> Runtime boundary contract, as Python Protocols.

Mirrors docs/design/boundary-contract.md (AP-0014). Implementations live in
cairn.runtime (Runtime side) and cairn.harness (Code Harness side). The invariants
I1-I5 are documented here and upheld by implementations.
"""

from __future__ import annotations

from typing import Optional, Protocol, Tuple, runtime_checkable

from .state import ContinuationState


@runtime_checkable
class Runtime(Protocol):
    """Runtime-owned mechanism (faithful, durable). Upholds invariants I1-I5."""

    # --- execution substrate -------------------------------------------------
    def execute(self, code: str, cwd: Optional[str] = None) -> "object":
        """Run code in the sandbox; returns an ExecResult-like object."""

    # --- workspace (taxonomy layer 1) ---------------------------------------
    def snapshot_workspace(self) -> str:
        ...

    def restore_workspace(self, snap_id: str) -> None:
        ...

    # --- checkpoint store (atomic, I2) --------------------------------------
    def checkpoint(self, state: ContinuationState, snap_id: str, effect_offset: int) -> str:
        ...

    def load_latest(self) -> Optional[Tuple[ContinuationState, str, int]]:
        ...

    # --- effect ledger (append-only, write-ahead I1, monotonic I3) ----------
    def append_effect(
        self, intent: str, idempotency_key: str, tool_class: str = "never-retry", step: int = 0
    ) -> int:
        ...

    def complete_effect(self, idempotency_key: str) -> None:
        ...

    def list_effects_since(self, offset: int) -> list[dict]:
        ...

    def current_effect_offset(self) -> int:
        ...


@runtime_checkable
class CodeHarness(Protocol):
    """Code-Harness-owned semantics (intelligent, lossy)."""

    def distill(self, goal: str, history: list, *, step: int) -> ContinuationState:
        ...

    def reconcile(self, state: ContinuationState, observed: "object") -> "object":
        """On resume, compare the cairn against the re-observed world and produce a
        ResumePlan (the next action / repaired plan). Implemented in Phase 4 (AP-0025)."""
