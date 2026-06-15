"""Recovery benchmark — the (step × baseline) matrix + the effect-safety contrast (AP-0033).

Run from the repo root:

    python benchmarks/recovery_matrix.py

Deterministic reference harness (ADR-0009): results are reproducible demonstrations, not a
live-LLM study. Prints per-baseline summaries and the C1 / C3 verdicts.
"""

import _bootstrap  # noqa: F401  (sys.path setup)

from benchmarks.scenarios import effectful_scenario, multi_file_scenario
from cairn.eval.baselines import ColdRestart, RGR
from cairn.eval.runner import aggregate, format_table, run_matrix


def main() -> None:
    print("=== Recovery matrix — multi-file task (n=5), failures at k=1..4, baselines B0–B3 ===")
    scenario = multi_file_scenario(n=5)
    reports = run_matrix(scenario, steps=[1, 2, 3, 4])
    summary = aggregate(reports)
    print(format_table(summary))

    b0, b3 = summary["B0"], summary["B3"]
    c1 = b3["recovery_tax"] < b0["recovery_tax"] and b3["no_regression"] > b0["no_regression"]
    print(f"\nC1 (RGR beats cold restart): {'SUPPORTED' if c1 else 'NOT SUPPORTED'} "
          f"— B3 tax={b3['recovery_tax']:.2f} vs B0 tax={b0['recovery_tax']:.2f}; "
          f"B3 no-regression={b3['no_regression']:.2f} vs B0={b0['no_regression']:.2f}")

    print("\n=== Effect-safety — effectful task, torn effect at k=2; B0 (no WAL) vs B3 (WAL) ===")
    eff = effectful_scenario(n=4, effect_step=2)
    ereports = run_matrix(eff, steps=[2], baselines=[ColdRestart(), RGR()])
    by = {r.baseline: r for r in ereports}
    print(format_table(aggregate(ereports)))
    c3 = by["B3"].effect_duplicates == 0 and by["B0"].effect_duplicates >= 1
    print(f"\nC3 (WAL eliminates duplicate effects): {'SUPPORTED' if c3 else 'NOT SUPPORTED'} "
          f"— B3 duplicates={by['B3'].effect_duplicates} (gate {'PASS' if by['B3'].passes_gate else 'FAIL'}); "
          f"B0 duplicates={by['B0'].effect_duplicates} (gate {'PASS' if by['B0'].passes_gate else 'FAIL'})")

    print("\nScope: deterministic reference harness with a scripted mock model (ADR-0009).")


if __name__ == "__main__":
    main()
