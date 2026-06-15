"""Continuation-State ablation (AP-0031) — locate the minimal sufficient `S` (C5, C2).

Strip a named component from the cairn, re-checkpoint it as the latest, resume, and measure
fidelity. The component whose removal degrades recovery was necessary; the rest was slack.
Deterministic reference harness only (ADR-0009): this identifies the sufficient statistic
*for this harness*, not a universal claim.
"""

from __future__ import annotations

import tempfile
from typing import Callable, Optional

from ..state import ContinuationState
from .baselines import RGR
from .metrics import RecoveryReport, score
from .scenario import harness_for, run_reference, run_until_failure

DROPPABLE = ["plan", "decisions", "ruled_out", "world_digest", "verification"]


def ablate(state: ContinuationState, drop: Optional[str]) -> ContinuationState:
    s = ContinuationState.from_dict(state.to_dict())  # deep copy via round-trip
    if drop is None:
        return s
    c = s.durable_core
    if drop == "plan":
        c.plan = []
    elif drop == "decisions":
        c.decisions = []
    elif drop == "ruled_out":
        c.decisions = [d for d in c.decisions if not d.ruled_out]
    elif drop == "world_digest":
        c.world.digest = {}
    elif drop == "verification":
        c.verification = []
    else:
        raise ValueError(f"unknown ablation component: {drop!r}")
    return s


def run_ablation(
    scenario, k: int, drop: Optional[str], *, base_factory: Callable[[], str] = tempfile.mkdtemp
) -> RecoveryReport:
    reference = run_reference(scenario, base_factory())
    base = base_factory()
    run_until_failure(scenario, base, k)

    # Replace the latest checkpoint with the ablated cairn, then resume from it.
    _h, rt = harness_for(scenario, base)
    loaded = rt.load_latest()
    if loaded:
        state, snap, off = loaded
        rt.checkpoint(ablate(state, drop), snap, off)

    outcome = RGR().recover(scenario, base)
    label = "full-cairn" if drop is None else f"drop:{drop}"
    return score(scenario, k, f"RGR/{label}", outcome, reference)


def run_ablation_suite(scenario, k: int, *, base_factory=tempfile.mkdtemp) -> list[RecoveryReport]:
    return [run_ablation(scenario, k, drop, base_factory=base_factory) for drop in [None, *DROPPABLE]]
