"""The five recovery-fidelity axes, measured vs the uninterrupted reference (AP-0030).

Axes (see docs/concepts/recovery-fidelity.md):
  - task_success      — did the recovered run complete the task? (oracle)
  - solution_quality  — artifact-digest match ratio vs the reference run (v1 proxy; ADR-0009)
  - no_regression     — did recovery avoid redoing/discarding pre-failure completed work?
  - effect_duplicates — duplicate/spurious external effects (a HARD GATE; lower better, 0 ideal)
  - recovery_tax      — steps executed to recover (lower better)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RecoveryReport:
    baseline: str
    failure_step: int
    task_success: bool
    solution_quality: float
    no_regression: float
    effect_duplicates: int
    recovery_tax: int

    @property
    def passes_gate(self) -> bool:
        """Effect-safety is a gate: any duplicated irreversible effect fails it outright."""
        return self.effect_duplicates == 0


def solution_quality(outcome, reference) -> float:
    ref = reference.final_digest
    if not ref:
        return 1.0
    matches = sum(1 for path, h in ref.items() if outcome.final_digest.get(path) == h)
    return matches / len(ref)


def no_regression(executed: int, n_steps: int, k: int) -> float:
    """1.0 when no pre-failure work was redone; 0.0 when all of it was.

    `redone` = work beyond the genuinely-remaining steps (n_steps - k). Cold restart redoes
    all k pre-failure steps → 0.0; RGR redoes none → 1.0.
    """
    if k <= 0:
        return 1.0
    remaining = max(0, n_steps - k)
    redone = max(0, executed - remaining)
    return max(0.0, 1.0 - redone / k)


def effect_duplicates(outcome, scenario) -> int:
    expected = 1 if scenario.effect else 0
    return max(0, outcome.outbox_count - expected)


def score(scenario, k: int, baseline_name: str, outcome, reference) -> RecoveryReport:
    return RecoveryReport(
        baseline=baseline_name,
        failure_step=k,
        task_success=outcome.success,
        solution_quality=solution_quality(outcome, reference),
        no_regression=no_regression(outcome.executed, scenario.n_steps, k),
        effect_duplicates=effect_duplicates(outcome, scenario),
        recovery_tax=outcome.executed,
    )
