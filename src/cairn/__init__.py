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
