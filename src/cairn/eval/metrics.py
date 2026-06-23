"""The five recovery-fidelity axes, measured vs the uninterrupted reference (AP-0030).

Axes (see docs/concepts/recovery-fidelity.md):
  - task_success      — did the recovered run complete the task? (oracle)
  - solution_quality  — artifact-digest match ratio vs the reference run (v1 proxy; ADR-0009)
  - no_regression     — did recovery avoid redoing/discarding pre-failure completed work?
  - effect_duplicates — duplicate/spurious external effects (a HARD GATE; lower better, 0 ideal)
  - recovery_tax      — work units (re)done to recover (lower better)

**Action-granularity robustness (AP-0044).** `no_regression` and `recovery_tax` are defined in
**work units** (a task-defined increment of progress, `Task.progress`), not model *actions*.
M1 showed action-count metrics are meaningless when a real model chunks work differently than
the scripted mock — coarser or finer actions changed the score without changing the recovery.
Measuring in work units removes that dependence: the non-batchable chain task (AP-0043) pins one
work unit per action, so the deterministic numbers are unchanged while the definition no longer
*assumes* that cadence. When a task exposes no work-unit notion (`progress()` → None), scoring
falls back to the original action-count form (`executed`, nominal step `k`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


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


def no_regression(recovery_units: int, work_at_crash: int, total_units: int) -> float:
    """1.0 when no pre-failure work was redone; 0.0 when all of it was — in **work units**.

    `recovery_units`  — work units the recovery (re)performed.
    `work_at_crash`   — work units already completed when the failure hit (measured progress).
    `total_units`     — work units in the full task (the uninterrupted reference, `W`).

    Of the recovery's work, only `total_units - work_at_crash` was *genuinely remaining*; any
    excess is pre-failure work redone. Cold restart redoes everything (→ 0.0); RGR continues
    from the crash point and redoes nothing (→ 1.0). Independent of how many *actions* the
    recovery used — that is the granularity robustness (AP-0044).
    """
    if work_at_crash <= 0:
        return 1.0
    genuinely_remaining = max(0, total_units - work_at_crash)
    redone = max(0, recovery_units - genuinely_remaining)
    return max(0.0, 1.0 - redone / work_at_crash)


def effect_duplicates(outcome, scenario) -> int:
    expected = 1 if scenario.effect else 0
    return max(0, outcome.outbox_count - expected)


def score(
    scenario, k: int, baseline_name: str, outcome, reference, *, work_at_crash: Optional[int] = None
) -> RecoveryReport:
    """Score one recovery against the reference, in work units when the task exposes them.

    `recovery_units` is the recovery's effort. In this harness one code-as-action performs one
    work unit (the scripted mock is 1:1; the non-batchable chain pins 1 link per action), so
    `outcome.executed` *is* the work-unit count — the metrics are unit-measured, not
    action-measured. When the task has no work-unit notion, fall back to the nominal step `k`
    and `scenario.n_steps` (the original action-count behavior).
    """
    total_units = reference.work_units if reference.work_units is not None else scenario.n_steps
    crash_units = work_at_crash if work_at_crash is not None else k
    recovery_units = outcome.executed
    return RecoveryReport(
        baseline=baseline_name,
        failure_step=k,
        task_success=outcome.success,
        solution_quality=solution_quality(outcome, reference),
        no_regression=no_regression(recovery_units, crash_units, total_units),
        effect_duplicates=effect_duplicates(outcome, scenario),
        recovery_tax=recovery_units,
    )
