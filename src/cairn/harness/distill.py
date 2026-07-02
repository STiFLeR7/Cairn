"""Unified distillation (the `distill` seam) — implements ADR-0005 / claim C2.

One function produces the [ContinuationState] for *both* write paths:

  * ``mode="compact"``     — online compaction: keep the durable core, **prune** the tail.
  * ``mode="checkpoint"``  — durable checkpoint: keep the same core, **freeze** the tail.

The durable core (intent, plan + status, decisions incl. ruled-out dead-ends, world digest,
effect pointer, provenance) is computed *identically* regardless of mode — only tail handling
differs. That identity is the operational content of "Checkpoints Are Compactions" (C2).

The salience policy is deterministic/rule-based in v1 (no LLM): failed steps become ruled-out
decisions; the plan is derived from executed steps. Real summarization plugs in behind this seam.
"""

from __future__ import annotations

from typing import Optional

from ..model import StepRecord
from ..runtime.digest import world_digest
from ..state import (
    ContinuationState,
    Decision,
    DurableCore,
    ElasticTail,
    Intent,
    PlanStep,
    Provenance,
)

COMPACT = "compact"
CHECKPOINT = "checkpoint"

#: how many recent steps a checkpoint freezes verbatim into the tail.
TAIL_FREEZE_N = 5
#: how many a compaction keeps (pruned — the live agent can re-derive the rest).
TAIL_PRUNE_N = 1


def distill(
    goal: str,
    history: list[StepRecord],
    *,
    mode: str = CHECKPOINT,
    step: int = 0,
    model_version: str = "",
    harness_version: str = "",
    effect_offset: int = 0,
    snap_id: str = "",
    workspace_dir: str = "",
    digest: Optional[dict] = None,
) -> ContinuationState:
    """Distill the trajectory into a cairn. ``mode`` selects only the tail policy."""
    if mode not in (COMPACT, CHECKPOINT):
        raise ValueError(f"unknown distill mode: {mode!r}")

    core = _durable_core(
        goal,
        history,
        step=step,
        model_version=model_version,
        harness_version=harness_version,
        effect_offset=effect_offset,
        snap_id=snap_id,
        workspace_dir=workspace_dir,
        digest=digest,
    )
    tail = _elastic_tail(history, mode=mode)
    return ContinuationState(durable_core=core, elastic_tail=tail)


def _durable_core(
    goal: str,
    history: list[StepRecord],
    *,
    step: int,
    model_version: str,
    harness_version: str,
    effect_offset: int,
    snap_id: str,
    workspace_dir: str,
    digest: Optional[dict] = None,
) -> DurableCore:
    """The sufficient statistic S — independent of write path (mode)."""
    plan = [
        PlanStep(
            id=f"s{r.step}",
            description=_summarize_action(r),
            status="done" if r.returncode == 0 else "blocked",
        )
        for r in history
    ]
    decisions = [
        Decision(
            id=f"d{r.step}",
            decision=f"executed step {r.step}: {_summarize_action(r)}",
            rationale=(r.stdout or r.stderr or "").strip()[:200],
            ruled_out=(r.returncode != 0),  # a failed path is a recorded dead-end
        )
        for r in history
    ]
    core = DurableCore(
        intent=Intent(root_goal=goal, active_subgoal=_active_subgoal(goal, plan)),
        plan=plan,
        decisions=decisions,
        provenance=Provenance(
            model_version=model_version,
            harness_version=harness_version,
            step_index=step,
            schema_version="1.0",
        ),
    )
    core.effects_ref.offset = effect_offset
    core.world.snapshot_id = snap_id
    if digest is not None:
        core.world.digest = digest
    else:
        core.world.digest = world_digest(workspace_dir) if workspace_dir else {}
    return core


def _elastic_tail(history: list[StepRecord], *, mode: str) -> ElasticTail:
    keep = TAIL_FREEZE_N if mode == CHECKPOINT else TAIL_PRUNE_N
    recent = [
        {
            "step": r.step,
            "summary": (r.stdout or "").strip()[:120],
            "returncode": r.returncode,
        }
        for r in history[-keep:]
    ]
    scratch = None if mode == CHECKPOINT else f"compacted@{len(history)}"
    return ElasticTail(recent_steps=recent, scratch=scratch)


def _summarize_action(r: StepRecord) -> str:
    code = (r.action.code or "").strip().replace("\n", " ")
    return (code[:80] + "…") if len(code) > 80 else (code or r.action.kind)


def _active_subgoal(goal: str, plan: list[PlanStep]) -> str:
    for p in plan:
        if p.status != "done":
            return f"resolve blocked step {p.id}: {p.description}"
    return goal


# --- back-compat shim -------------------------------------------------------
# The Phase 3 agent loop imported `minimal_distill`; keep it working as a thin
# wrapper over the unified engine (checkpoint mode) so nothing breaks.
def minimal_distill(
    goal: str,
    history: list[StepRecord],
    *,
    step: int,
    model_version: str = "",
    harness_version: str = "",
    effect_offset: int = 0,
    snap_id: str = "",
    workspace_dir: str = "",
) -> ContinuationState:
    return distill(
        goal,
        history,
        mode=CHECKPOINT,
        step=step,
        model_version=model_version,
        harness_version=harness_version,
        effect_offset=effect_offset,
        snap_id=snap_id,
        workspace_dir=workspace_dir,
    )
