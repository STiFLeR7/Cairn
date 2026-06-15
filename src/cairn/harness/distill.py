"""Minimal distillation (the `distill` seam).

Phase 3 ships a *minimal* distillation: it produces a schema-valid ContinuationState
from the run so the seam exists and checkpoints are real. The full salience policy
(durable-core/elastic-tail decisions, ruled-out dead-ends, etc.) is Phase 4 (AP-0016).
"""

from __future__ import annotations

from ..model import StepRecord
from ..state import (
    ContinuationState,
    Decision,
    DurableCore,
    ElasticTail,
    Intent,
    Provenance,
)


def minimal_distill(
    goal: str,
    history: list[StepRecord],
    *,
    step: int,
    model_version: str = "",
    harness_version: str = "",
    effect_offset: int = 0,
    snap_id: str = "",
) -> ContinuationState:
    core = DurableCore(
        intent=Intent(root_goal=goal, active_subgoal=goal),
        decisions=[
            Decision(
                id=f"d{i}",
                decision=f"executed step {r.step}",
                rationale=(r.stdout or r.stderr or "").strip()[:200],
            )
            for i, r in enumerate(history)
        ],
        provenance=Provenance(
            model_version=model_version,
            harness_version=harness_version,
            step_index=step,
            schema_version="1.0",
        ),
    )
    core.effects_ref.offset = effect_offset
    core.world.snapshot_id = snap_id
    tail = ElasticTail(
        recent_steps=[
            {"step": r.step, "summary": (r.stdout or "").strip()[:120]} for r in history[-3:]
        ]
    )
    return ContinuationState(durable_core=core, elastic_tail=tail)
