"""M5 calibration: a model's own success rate on the task with no injected failure."""

from __future__ import annotations

import tempfile
from typing import Callable

from .scenario import run_reference

ELIGIBLE_RATE = 0.80
MIN_COMPLETED = 9


def run_calibration(scenario, runs: int = 10, *, base_factory: Callable[[], str] = tempfile.mkdtemp) -> dict:
    """Run the uncrashed task `runs` times; a run that raises counts as not completed."""
    outcomes: list[bool] = []
    errors: list[str] = []
    for _ in range(runs):
        try:
            outcome = run_reference(scenario, base_factory())
        except Exception as exc:  # noqa: BLE001 — a transport error is recorded, not fatal
            errors.append(f"{type(exc).__name__}: {exc}"[:300])
            continue
        outcomes.append(bool(outcome.success))
    return calibration_summary(runs, outcomes, errors)


def calibration_summary(runs: int, outcomes: list[bool], errors: list[str]) -> dict:
    """The calibration record and eligibility rule over completed runs' successes (`outcomes`)."""
    completed, successes = len(outcomes), sum(outcomes)
    rate = successes / completed if completed else 0.0
    return {
        "runs": runs,
        "completed": completed,
        "successes": successes,
        "errors": errors,
        "calibration_rate": rate,
        "eligible": completed >= MIN_COMPLETED and rate >= ELIGIBLE_RATE,
    }
