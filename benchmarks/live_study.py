"""Live-LLM failure-injection study runner (AP-0040).

Runs the Phase 5 recovery matrix through the **live pipeline** (`LiveModelProvider` +
`live_controls`) instead of the scripted mock. The model is reached only through an
injected transport, so the SAME runner is both:

    python benchmarks/live_study.py     # OFFLINE: deterministic fake transport — no key, no spend

and the real, paid study — by swapping in ``benchmarks.scenarios.build_live_transport(model=…)``,
which is AP-0040's **gated** step (needs ``ANTHROPIC_API_KEY`` + the ``cairn[live]`` extra; see
REPRODUCE.md). The offline path exercises the entire pipeline end-to-end (prompt render → parse →
harness → matrix → metrics); only the transport changes for a live run, and live transcripts then
replay offline.
"""

import _bootstrap  # noqa: F401  (sys.path + UTF-8 stdout)

from benchmarks.scenarios import live_effectful_scenario, live_multi_file_scenario
from cairn.eval.baselines import ColdRestart, RGR
from cairn.eval.runner import aggregate, format_table, run_matrix


def run_offline_study() -> None:
    print("=== Live-pipeline recovery matrix (OFFLINE fake transport) — n=5, failures k=1..4 ===")
    summary = aggregate(run_matrix(live_multi_file_scenario(n=5), steps=[1, 2, 3, 4]))
    print(format_table(summary))
    b0, b3 = summary["B0"], summary["B3"]
    c1 = b3["recovery_tax"] < b0["recovery_tax"] and b3["no_regression"] > b0["no_regression"]
    print(
        f"\nC1 via live pipeline: {'SUPPORTED' if c1 else 'NOT SUPPORTED'} "
        f"— B3 tax={b3['recovery_tax']:.2f} vs B0 tax={b0['recovery_tax']:.2f}; "
        f"B3 no-regression={b3['no_regression']:.2f} vs B0={b0['no_regression']:.2f}"
    )

    print("\n=== Effect-safety (OFFLINE) — torn effect at k=2; B0 (no WAL) vs B3 (WAL) ===")
    ereports = run_matrix(live_effectful_scenario(n=4, effect_step=2), steps=[2],
                          baselines=[ColdRestart(), RGR()])
    by = {r.baseline: r for r in ereports}
    print(format_table(aggregate(ereports)))
    c3 = by["B3"].effect_duplicates == 0 and by["B0"].effect_duplicates >= 1
    print(
        f"\nC3 via live pipeline: {'SUPPORTED' if c3 else 'NOT SUPPORTED'} "
        f"— B3 duplicates={by['B3'].effect_duplicates} (gate {'PASS' if by['B3'].passes_gate else 'FAIL'}); "
        f"B0 duplicates={by['B0'].effect_duplicates} (gate {'PASS' if by['B0'].passes_gate else 'FAIL'})"
    )


def main() -> None:
    run_offline_study()
    print("\nNOTE: the transport here is a DETERMINISTIC FAKE — no network, no API key, no spend.")
    print("The paid live study (AP-0040) swaps in benchmarks.scenarios.build_live_transport(model=…)")
    print("and is GATED on explicit approval. Live transcripts then replay offline (see REPRODUCE.md).")


if __name__ == "__main__":
    main()
