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

import os

from benchmarks.scenarios import (
    build_live_transport,
    live_effectful_scenario,
    live_multi_file_scenario,
)
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


def run_live_study(
    model: str,
    *,
    provider: str = "openrouter",
    api_key_env: str = "OPENROUTER_API",
    n: int = 4,
    steps=(2,),
    max_calls: int = 80,
) -> None:
    """The GATED real run (AP-0040): the recovery study against an actual model.

    Enabled by ``CAIRN_LIVE_MODEL`` (see ``main``). Wraps the real transport with a
    transcript recorder (so the run replays offline) and a budget ceiling, then runs the
    B0-vs-B3 recovery contrast live. Non-deterministic and metered — honest scope applies.
    """
    os.makedirs("benchmarks/transcripts", exist_ok=True)
    transcript = f"benchmarks/transcripts/{model.replace('/', '_')}-recovery-study.jsonl"
    transport = build_live_transport(
        model, provider=provider, api_key_env=api_key_env,
        transcript_path=transcript, max_calls=max_calls,
    )
    print(f"=== LIVE recovery study — model={model} (provider={provider}) — n={n}, "
          f"k={list(steps)}, B0 (cold restart) vs B3 (RGR) ===")
    print(f"(non-deterministic + metered; transcripts -> {transcript})")
    scenario = live_multi_file_scenario(n, transport)
    skipped: list = []
    reports = run_matrix(
        scenario, steps=list(steps), baselines=[ColdRestart(), RGR()],
        on_skip=lambda k, name: skipped.append((k, name)),
    )
    if skipped:
        print(f"\n[!] {len(skipped)} cell(s) SKIPPED — the injected crash never fired because the")
        print(f"    model finished before the crash step: {skipped}")
        print("    Recovery was NOT exercised in those cells, so they are not scored.")
    if not reports:
        print("\nNo scorable cells: the model completed the task before any injected crash, so")
        print("recovery was never exercised. C1 cannot be evaluated on this task/model — the task")
        print("is batchable. A non-batchable sequential task is required (claims registry / M2).")
        print("\nHonest scope (ADR-0009): the live PIPELINE works (transcripts captured); the live")
        print("EVIDENCE for C1–C5 is not obtainable on this benchmark task. Recorded, not buried.")
        return
    summary = aggregate(reports)
    print(format_table(summary))
    b0, b3 = summary.get("B0"), summary.get("B3")
    if b0 and b3:
        # A verdict must require B3 to actually SUCCEED — lower tax on a failed task is not support.
        c1 = (
            b3["task_success"] >= 1.0
            and b3["task_success"] >= b0["task_success"]
            and b3["recovery_tax"] < b0["recovery_tax"]
            and b3["no_regression"] >= b0["no_regression"]
        )
        print(f"\nC1 (LIVE, {model}): {'SUPPORTED' if c1 else 'NOT SHOWN'} "
              f"— B3 success={b3['task_success']:.2f} tax={b3['recovery_tax']:.2f} vs "
              f"B0 success={b0['task_success']:.2f} tax={b0['recovery_tax']:.2f}")
        if not c1:
            print("  (no clean verdict — see the honest-scope note and the claims registry)")
    print("\nHonest scope (ADR-0009): a single free model, small n, few seeds — a demonstration")
    print("that the live pipeline produces real evidence, not a powered statistical study.")


def main() -> None:
    model = os.environ.get("CAIRN_LIVE_MODEL")
    if model:  # GATED live run — opt-in via env (needs a key)
        run_live_study(
            model,
            provider=os.environ.get("CAIRN_LIVE_PROVIDER", "openrouter"),
            api_key_env=os.environ.get("CAIRN_LIVE_KEY_ENV", "OPENROUTER_API"),
        )
        return
    run_offline_study()
    print("\nNOTE: the transport here is a DETERMINISTIC FAKE — no network, no API key, no spend.")
    print("Set CAIRN_LIVE_MODEL=openrouter/owl-alpha (+ an OpenRouter key in OPENROUTER_API) to run")
    print("the GATED live study. Live transcripts then replay offline (see REPRODUCE.md).")


if __name__ == "__main__":
    main()
