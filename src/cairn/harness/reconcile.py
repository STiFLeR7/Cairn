"""Reconcile — step 3 of RGR: compare the cairn against the re-observed world.

Resolves the *torn step* (the window between the last checkpoint and the failure) along
three axes from the resume protocol (ADR-0004):

  * **torn writes**  — a `world.digest` entry that no longer matches the restored workspace.
  * **plan drift**   — `plan.status` reconciled against what the world shows actually happened.
  * **effect danger window** — `INTENT`-without-`COMPLETE` keys, surfaced here and *resolved*
    by the effect-safety protocol (`harness.effects.resolve_danger_window`, AP-0026).

`reconcile` is a pure function of `(state, observed)`; it produces a `ResumePlan` the harness
acts on. Re-planning itself is the model's job (a different valid path is fine — the bar is
outcome equivalence, not replay).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..state import ContinuationState, PlanStep
from .effects import danger_window
from .observe import ObservedWorld


@dataclass
class ResumePlan:
    torn_files: list[str] = field(default_factory=list)  # digest mismatch vs the cairn
    lost_files: list[str] = field(default_factory=list)  # in cairn, absent from world
    plan: list[PlanStep] = field(default_factory=list)  # reconciled plan
    danger_window: list[dict] = field(default_factory=list)  # INTENT-without-COMPLETE
    note: str = ""

    @property
    def clean(self) -> bool:
        """True when nothing diverged — a straightforward continue."""
        return not (self.torn_files or self.lost_files or self.danger_window)


def reconcile(state: ContinuationState, observed: ObservedWorld) -> ResumePlan:
    cairn_digest = dict(state.durable_core.world.digest or {})
    obs = observed.digest

    torn: list[str] = []
    lost: list[str] = []
    for path, h in cairn_digest.items():
        if path not in obs:
            lost.append(path)
        elif obs[path] != h:
            torn.append(path)

    diverged = set(torn) | set(lost)
    plan = _reconcile_plan(state.durable_core.plan, diverged)
    dw = danger_window(observed.effects_since)

    note = (
        f"reconciled: {len(torn)} torn, {len(lost)} lost, "
        f"{len(dw)} effect(s) in danger window"
    )
    return ResumePlan(
        torn_files=sorted(torn),
        lost_files=sorted(lost),
        plan=plan,
        danger_window=dw,
        note=note,
    )


def _reconcile_plan(plan: list[PlanStep], diverged: set[str]) -> list[PlanStep]:
    """Carry the cairn's plan forward; mark a 'done' step pending if its evidence diverged.

    v1 is conservative: when the world no longer matches what a step produced, we cannot
    trust that step's `done` status, so it is re-opened for the re-planner to redo.
    """
    out: list[PlanStep] = []
    for p in plan:
        status = p.status
        if status == "done" and any(p.id in d or d in p.description for d in diverged):
            status = "pending"
        out.append(PlanStep(id=p.id, description=p.description, status=status, depends_on=list(p.depends_on)))
    return out
