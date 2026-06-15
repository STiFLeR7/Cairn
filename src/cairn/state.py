"""The Continuation State (the "cairn") — durable core + elastic tail.

Mirrors docs/design/continuation-state-schema.md (AP-0013). Pure data; round-trips
to/from plain dicts/JSON so the Runtime can persist it without knowing its internals.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class Intent:
    root_goal: str = ""
    active_subgoal: str = ""


@dataclass
class PlanStep:
    id: str
    description: str
    status: str = "pending"  # done | pending | blocked
    depends_on: list[str] = field(default_factory=list)


@dataclass
class Decision:
    id: str
    decision: str
    rationale: str = ""
    ruled_out: bool = False


@dataclass
class EffectsRef:
    ledger_id: str = ""
    offset: int = 0


@dataclass
class WorldRef:
    snapshot_id: str = ""
    digest: dict[str, str] = field(default_factory=dict)


@dataclass
class VerificationItem:
    target: str
    result: str = "unknown"  # pass | fail | unknown
    at_step: int = 0


@dataclass
class Provenance:
    model_version: str = ""
    harness_version: str = ""
    step_index: int = 0
    created_at: str = ""
    schema_version: str = "1.0"


@dataclass
class DurableCore:
    """The sufficient statistic for continuation — never pruned."""

    intent: Intent = field(default_factory=Intent)
    plan: list[PlanStep] = field(default_factory=list)
    decisions: list[Decision] = field(default_factory=list)
    effects_ref: EffectsRef = field(default_factory=EffectsRef)
    world: WorldRef = field(default_factory=WorldRef)
    verification: list[VerificationItem] = field(default_factory=list)
    provenance: Provenance = field(default_factory=Provenance)


@dataclass
class ElasticTail:
    """Recent detail — pruned during compaction, frozen at checkpoint."""

    recent_steps: list[dict[str, Any]] = field(default_factory=list)
    scratch: Optional[str] = None


@dataclass
class ContinuationState:
    schema_version: str = "1.0"
    durable_core: DurableCore = field(default_factory=DurableCore)
    elastic_tail: ElasticTail = field(default_factory=ElasticTail)

    # --- serialization -------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=False)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ContinuationState":
        core = d.get("durable_core", {}) or {}
        tail = d.get("elastic_tail", {}) or {}
        durable = DurableCore(
            intent=Intent(**(core.get("intent") or {})),
            plan=[PlanStep(**s) for s in core.get("plan", [])],
            decisions=[Decision(**x) for x in core.get("decisions", [])],
            effects_ref=EffectsRef(**(core.get("effects_ref") or {})),
            world=WorldRef(**(core.get("world") or {})),
            verification=[VerificationItem(**v) for v in core.get("verification", [])],
            provenance=Provenance(**(core.get("provenance") or {})),
        )
        elastic = ElasticTail(
            recent_steps=list(tail.get("recent_steps", [])),
            scratch=tail.get("scratch"),
        )
        return cls(
            schema_version=d.get("schema_version", "1.0"),
            durable_core=durable,
            elastic_tail=elastic,
        )

    @classmethod
    def from_json(cls, s: str) -> "ContinuationState":
        return cls.from_dict(json.loads(s))
