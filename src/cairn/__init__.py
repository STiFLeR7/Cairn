"""Cairn — recoverable long-horizon agents (reference harness + benchmark).

A fully pluggable Code Harness + Runtime honouring the boundary contract, with
Re-grounding Recovery (unified distillation + re-observe/reconcile + effect-safety
WAL) and a recovery-faithful, non-batchable live benchmark (Milestone M2).

Nothing in this package hardcodes a model, toolset, task, or path — all are
injected (see ADR-0007). The project remains 0.x: v1.0 is held until a *powered*
live-LLM study confirms the claims (current live evidence is suggestive, not
confirmed — see docs/research/claims-registry.md).
"""

__version__ = "0.2.0"

from .contract import CheckpointStore, EffectLedger, World
from .harness.effects import EffectfulTool, EscalationRequired
from .model import Action, StepRecord
from .recovery import Checkpoint, Regrounded, checkpoint, recover, regrounded_history
from .worlds import Workspace

__all__ = [
    "__version__",
    # contracts
    "World", "CheckpointStore", "EffectLedger",
    # types
    "Action", "StepRecord", "Checkpoint", "Regrounded",
    # primitives
    "checkpoint", "recover", "regrounded_history",
    # effect-safety
    "EffectfulTool", "EscalationRequired",
    # reference world
    "Workspace",
]
