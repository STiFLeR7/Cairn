"""Continuation-State ablation study (AP-0031) — which components are sufficient?

Run from the repo root:

    python benchmarks/ablation_study.py

Strips each cairn component and measures resume fidelity, locating the cliff (necessary) vs
slack (removable). Deterministic reference harness (ADR-0009).
"""

import _bootstrap  # noqa: F401

from benchmarks.scenarios import multi_file_scenario
from cairn.eval.ablation import run_ablation_suite


def main() -> None:
    scenario = multi_file_scenario(n=5)
    reports = run_ablation_suite(scenario, k=2)

    print("=== Continuation-State ablation (multi-file n=5, failure at k=2) ===")
    head = f"{'cairn variant':<22} | success | quality | no-regression | recovery_tax"
    print(head)
    print("-" * len(head))
    for r in reports:
        print(f"{r.baseline:<22} | {str(r.task_success):>7} | {r.solution_quality:>7.2f} | "
              f"{r.no_regression:>13.2f} | {r.recovery_tax:>12}")

    full = reports[0]
    cliffs = [r for r in reports[1:] if r.recovery_tax > full.recovery_tax]
    slack = [r for r in reports[1:] if r.recovery_tax == full.recovery_tax]
    print(f"\nNecessary (fidelity cliff): {[r.baseline for r in cliffs]}")
    print(f"Slack (no degradation):     {[r.baseline for r in slack]}")
    print("C5: a minimal sufficient state is empirically identifiable in this harness.")
    print("Scope: deterministic reference harness; cliffs are harness-specific (ADR-0009).")


if __name__ == "__main__":
    main()
