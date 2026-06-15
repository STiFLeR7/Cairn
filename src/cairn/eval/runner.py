"""Matrix runner + aggregation (AP-0033).

Sweeps a scenario across failure steps × baselines, scoring each recovery against the
uninterrupted reference run, and aggregates per-baseline summaries.
"""

from __future__ import annotations

import tempfile
from typing import Callable

from .baselines import ALL_BASELINES
from .metrics import RecoveryReport, score
from .scenario import run_reference, run_until_failure


def run_matrix(
    scenario,
    steps,
    baselines=ALL_BASELINES,
    *,
    base_factory: Callable[[], str] = tempfile.mkdtemp,
) -> list[RecoveryReport]:
    reference = run_reference(scenario, base_factory())
    reports: list[RecoveryReport] = []
    for k in steps:
        for b in baselines:
            base = base_factory()
            run_until_failure(scenario, base, k)
            outcome = b.recover(scenario, base)
            reports.append(score(scenario, k, b.name, outcome, reference))
    return reports


def aggregate(reports: list[RecoveryReport]) -> dict:
    by: dict[str, list[RecoveryReport]] = {}
    for r in reports:
        by.setdefault(r.baseline, []).append(r)
    summary = {}
    for name, rs in by.items():
        n = len(rs)
        summary[name] = {
            "task_success": sum(x.task_success for x in rs) / n,
            "solution_quality": sum(x.solution_quality for x in rs) / n,
            "no_regression": sum(x.no_regression for x in rs) / n,
            "recovery_tax": sum(x.recovery_tax for x in rs) / n,
            "effect_duplicates": sum(x.effect_duplicates for x in rs),
            "gate_pass_rate": sum(1 for x in rs if x.passes_gate) / n,
        }
    return summary


def format_table(summary: dict) -> str:
    cols = ["task_success", "solution_quality", "no_regression", "recovery_tax",
            "effect_duplicates", "gate_pass_rate"]
    head = "baseline | " + " | ".join(cols)
    lines = [head, "-" * len(head)]
    for name in sorted(summary):
        row = summary[name]
        cells = []
        for c in cols:
            v = row[c]
            cells.append(f"{v:.2f}" if isinstance(v, float) else str(v))
        lines.append(f"{name:>8} | " + " | ".join(cells))
    return "\n".join(lines)
