"""Matrix runner + aggregation (AP-0033).

Sweeps a scenario across failure steps × baselines, scoring each recovery against the
uninterrupted reference run, and aggregates per-baseline summaries.
"""

from __future__ import annotations

import statistics
import tempfile
from dataclasses import dataclass
from typing import Callable, Optional

from .baselines import ALL_BASELINES
from .metrics import RecoveryReport, score
from .scenario import run_reference, run_until_failure


def run_matrix(
    scenario,
    steps,
    baselines=ALL_BASELINES,
    *,
    base_factory: Callable[[], str] = tempfile.mkdtemp,
    on_skip: Optional[Callable[[int, str], None]] = None,
) -> list[RecoveryReport]:
    """Score each (step k × baseline) cell against the reference run.

    A cell whose **injection did not fire** (the model finished before step k, so no failure
    occurred) is **skipped, not scored** — scoring a non-failure would fabricate a recovery
    result. `on_skip(k, baseline_name)` is called for each skipped cell so callers can report
    it honestly. With a well-behaved model that always reaches step k, nothing is skipped.
    """
    reference = run_reference(scenario, base_factory())
    reports: list[RecoveryReport] = []
    for k in steps:
        for b in baselines:
            base = base_factory()
            injection = run_until_failure(scenario, base, k)
            if not injection.fired:
                if on_skip is not None:
                    on_skip(k, b.name)
                continue
            outcome = b.recover(scenario, base)
            reports.append(
                score(scenario, k, b.name, outcome, reference, work_at_crash=injection.work_at_crash)
            )
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


# --- repetition + statistics (AP-0045) --------------------------------------
# A non-deterministic real model yields a *distribution* per cell, not one number. Repeat each
# cell N times and report mean +/- spread, carrying forward the M1 integrity fix: vacuous cells
# (the injected crash never fired) are skipped and counted, never averaged into the signal.


@dataclass
class AxisStat:
    """Summary of one fidelity axis across repetitions."""

    mean: float
    stdev: float       # population stdev (0.0 for a deterministic model / single sample)
    min: float
    max: float
    n: int

    def __str__(self) -> str:
        return f"{self.mean:.2f}+/-{self.stdev:.2f}"


def _axis_stat(values: list[float]) -> AxisStat:
    n = len(values)
    if n == 0:
        return AxisStat(0.0, 0.0, 0.0, 0.0, 0)
    return AxisStat(
        mean=sum(values) / n,
        stdev=statistics.pstdev(values) if n > 1 else 0.0,
        min=min(values),
        max=max(values),
        n=n,
    )


@dataclass
class RepeatedRun:
    """The raw result of repeating the matrix: every *fired* report, plus fired/skipped/errored counts."""

    reports: list[RecoveryReport]
    fired: int
    skipped: int
    repeats: int
    steps: list[int]
    baselines: list[str]
    errored: int = 0  # repeats aborted by a transport error (e.g. exhausted rate-limit retries)


def run_repeated(
    scenario,
    steps,
    baselines=ALL_BASELINES,
    *,
    repeats: int = 5,
    base_factory: Callable[[], str] = tempfile.mkdtemp,
    on_skip: Optional[Callable[[int, str], None]] = None,
    before_repeat: Optional[Callable[[int], None]] = None,
    on_error: Optional[Callable[[int, Exception], None]] = None,
    resilient: bool = True,
) -> RepeatedRun:
    """Run the (step x baseline) matrix `repeats` times and collect all fired reports.

    Each repeat is a full `run_matrix` pass (so the reference is re-run per repeat — correct for
    a non-deterministic model — and the injection-fired skip is enforced). `before_repeat(i)` is
    an optional seam for a live runner to vary a seed / temperature between repeats; deterministic
    scenarios ignore it and simply reproduce identical results (spread 0). Skipped (vacuous) cells
    are counted and reported via `on_skip`, never scored.

    **Per-repeat resilience (AP-0050).** When `resilient` (default), a repeat that raises — e.g. a
    live provider exhausts its rate-limit retries — is *isolated*: it is counted in `errored`,
    reported via `on_error`, and the surviving repeats still yield a verdict, instead of one
    transient failure discarding the entire study (the M2/free-tier fragility). A deterministic
    scenario never raises, so this is invisible there. Set `resilient=False` to fail fast.
    """
    all_reports: list[RecoveryReport] = []
    skipped = 0
    errored = 0

    def _count_skip(k: int, name: str) -> None:
        nonlocal skipped
        skipped += 1
        if on_skip is not None:
            on_skip(k, name)

    for i in range(repeats):
        if before_repeat is not None:
            before_repeat(i)
        try:
            all_reports.extend(
                run_matrix(scenario, steps, baselines, base_factory=base_factory, on_skip=_count_skip)
            )
        except Exception as exc:  # noqa: BLE001 — isolate a flaky repeat, record it honestly
            if not resilient:
                raise
            errored += 1
            if on_error is not None:
                on_error(i, exc)

    return RepeatedRun(
        reports=all_reports,
        fired=len(all_reports),
        skipped=skipped,
        repeats=repeats,
        steps=list(steps),
        baselines=[b.name for b in baselines],
        errored=errored,
    )


def aggregate_repeated(run: RepeatedRun) -> dict:
    """Per-baseline mean +/- spread over all fired repetitions (vacuous cells already excluded).

    **Success-conditioned tax (AP-0048).** `recovery_tax` is the cost of a *successful recovery*,
    so it is measured over **successful reports only**: a run that failed to complete the task
    never recovered, and its (often small) work must not register as a cheap recovery and pull the
    tax down — otherwise a baseline could "win" on tax by failing cheaply. `n_success` exposes how
    many of the `n` fired runs completed; `recovery_tax_all` keeps the full distribution for
    transparency. When a baseline has zero successes its `recovery_tax` AxisStat has `n == 0`
    (mean 0.0 by convention) — read alongside `n_success`, never as a real low tax.
    """
    by: dict[str, list[RecoveryReport]] = {}
    for r in run.reports:
        by.setdefault(r.baseline, []).append(r)
    summary: dict[str, dict] = {}
    for name, rs in by.items():
        succ = [x for x in rs if x.task_success]
        summary[name] = {
            "n": len(rs),
            "n_success": len(succ),
            "task_success": _axis_stat([float(x.task_success) for x in rs]),
            "solution_quality": _axis_stat([x.solution_quality for x in rs]),
            "no_regression": _axis_stat([x.no_regression for x in rs]),
            "recovery_tax": _axis_stat([float(x.recovery_tax) for x in succ]),
            "recovery_tax_all": _axis_stat([float(x.recovery_tax) for x in rs]),
            "effect_duplicates_total": sum(x.effect_duplicates for x in rs),
            "gate_pass_rate": sum(1 for x in rs if x.passes_gate) / len(rs),
        }
    return summary


def verdict_c1(summary: dict) -> dict:
    """C1 (RGR beats cold restart) — `supported` only with *consistent* evidence across repeats.

    Requires: both B0 and B3 have fired cells; B3 completes the task in **every** repetition
    (`task_success.min == 1.0`); B0 completes the recovery **at least once** (so there is a real
    cost-of-recovery to compare — a baseline that only fails has no tax it actually paid, AP-0048);
    B3's recovery tax is strictly lower than B0's with **no overlap** across repetitions
    (`B3.tax.max < B0.tax.min`), where both taxes are **success-conditioned**; and B3 preserves at
    least as much pre-failure work on average (`B3.no_regression.mean >= B0.no_regression.mean`).
    A lower tax on a *failed* task is never support. Returns a structured verdict.
    """
    b0, b3 = summary.get("B0"), summary.get("B3")
    if not b0 or not b3 or b3["n"] == 0 or b0["n"] == 0:
        return {"claim": "C1", "supported": False,
                "reason": "no fired B0/B3 cells to compare (task may be batchable for this model)"}
    if b3["task_success"].min < 1.0:
        return {"claim": "C1", "supported": False,
                "reason": f"B3 did not complete the task in every repetition "
                          f"(success min={b3['task_success'].min:.2f})"}
    if b0.get("n_success", b0["n"]) == 0:
        return {"claim": "C1", "supported": False,
                "reason": "B0 never completed the recovery, so it has no cost-of-recovery to "
                          "compare; a failed run's near-zero work is not a cheap recovery (AP-0048)"}
    tax_consistent = b3["recovery_tax"].max < b0["recovery_tax"].min
    reg_ok = b3["no_regression"].mean >= b0["no_regression"].mean
    supported = bool(tax_consistent and reg_ok)
    reason = (
        f"B3 tax {b3['recovery_tax']} (max {b3['recovery_tax'].max:.2f}) "
        f"{'<' if tax_consistent else '!<'} B0 tax {b0['recovery_tax']} (min {b0['recovery_tax'].min:.2f}); "
        f"B3 no-regression {b3['no_regression']} {'>=' if reg_ok else '<'} B0 {b0['no_regression']}; "
        f"B3 success {b3['task_success']}"
    )
    return {"claim": "C1", "supported": supported, "reason": reason,
            "b3_tax": b3["recovery_tax"], "b0_tax": b0["recovery_tax"]}


def format_repeated_table(summary: dict) -> str:
    """Render the per-baseline mean+/-spread summary (the repeated counterpart of `format_table`)."""
    cols = ["n", "n_success", "task_success", "solution_quality", "no_regression", "recovery_tax",
            "effect_duplicates_total", "gate_pass_rate"]
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
