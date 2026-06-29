"""Public Re-grounding Recovery primitives — bring your own model AND your own loop.

`checkpoint(...)` distills + snapshots + persists a durable cairn each step. `recover(...)`
performs the full RGR (load -> restore -> re-observe -> reconcile -> resolve effects ->
re-ground) and hands back a `history` the caller continues their own loop from. Both operate
over the `World` / `CheckpointStore` / `EffectLedger` seams (cairn.contract), so nothing about
the model, the world, or the persistence is hardcoded (ADR-0007).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .harness.distill import CHECKPOINT, distill
from .harness.effects import EffectfulTool, EscalationRequired, Resolution, resolve_danger_window
from .harness.observe import observe
from .harness.reconcile import ResumePlan, reconcile
from .model import CODE, Action, StepRecord
from .state import ContinuationState, PlanStep

#: A durable checkpoint (the "cairn"). Transparent alias of the internal state type, so
#: ``isinstance(c, cairn.Checkpoint)`` is exactly ``isinstance(c, ContinuationState)``.
Checkpoint = ContinuationState


@dataclass
class Regrounded:
    """The result of `recover`: the re-grounded history + what recovery did."""

    history: list[StepRecord] = field(default_factory=list)
    resolutions: list[Resolution] = field(default_factory=list)
    plan: Optional[ResumePlan] = None


def checkpoint(
    goal: str,
    history: list,
    world,
    store,
    ledger,
    *,
    step: int,
    model_version: str = "",
    harness_version: str = "",
) -> Checkpoint:
    """Distill `history` into a cairn, snapshot the world, and persist atomically."""
    snap = world.snapshot()
    offset = ledger.current_offset()
    state = distill(
        goal, history, mode=CHECKPOINT, step=step,
        model_version=model_version, harness_version=harness_version,
        effect_offset=offset, snap_id=snap, digest=world.digest(),
    )
    store.checkpoint(state, snap, offset)
    return state


def recover(world, store, ledger, *, effect_tools=None, escalate: bool = True) -> Regrounded:
    """The RGR protocol as a primitive. Returns a `Regrounded` to continue your loop from.

    No durable checkpoint -> empty history (start fresh). Otherwise: restore the world, re-observe
    via the World's digest, reconcile the torn step, resolve any effect danger window (exactly-once,
    ADR-0006), and re-ground a minimal history from the cairn's done steps. The goal is not a
    parameter — it is carried in the loaded cairn (`state.durable_core.intent`).
    """
    loaded = store.load_latest()
    if loaded is None:
        return Regrounded(history=[], resolutions=[], plan=None)
    state, snap_id, offset = loaded
    world.restore(snap_id)
    observed = observe(world, ledger, offset)
    plan = reconcile(state, observed)
    resolutions = resolve_danger_window(plan.danger_window, effect_tools or {}, ledger, escalate=escalate)
    return Regrounded(history=regrounded_history(plan.plan), resolutions=resolutions, plan=plan)


# NOTE: harness/agent_loop.py imports this directly (the single source of re-grounding logic).
def regrounded_history(plan_steps: list[PlanStep]) -> list[StepRecord]:
    """Re-ground a minimal history from the cairn's *done* steps (re-grounding, not replay)."""
    out: list[StepRecord] = []
    i = 0
    for p in plan_steps:
        if p.status == "done":
            out.append(StepRecord(step=i, action=Action(kind=CODE, code=p.description), returncode=0))
            i += 1
    return out
