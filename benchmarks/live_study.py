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

try:
    import _bootstrap  # noqa: F401  (sys.path + UTF-8 stdout when run as a script)
except ModuleNotFoundError:
    pass  # imported as a module (e.g. by tests) — paths already set by conftest/pythonpath

import json
import os

from benchmarks.scenarios import (
    build_live_transport,
    live_chain_scenario,
    live_effectful_scenario,
    live_multi_file_scenario,
)
from cairn.eval.baselines import ColdRestart, RGR
from cairn.eval.runner import (
    AxisStat,
    aggregate,
    aggregate_repeated,
    format_repeated_table,
    format_table,
    run_matrix,
    run_repeated,
    verdict_c1,
)


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

    run_offline_repeated_study()


def run_offline_repeated_study(repeats: int = 5) -> None:
    """AP-0045 demonstration: the **non-batchable chain** task (AP-0043) run with repetitions and
    statistics. Offline the model is deterministic, so the spread is 0 and the verdict is clean —
    this is the exact machinery AP-0046 uses live (only the transport changes), where repeats
    capture the real model's non-determinism."""
    print(f"\n=== Repeated recovery study on the NON-BATCHABLE chain (OFFLINE) — "
          f"n=6, k=2,3, repeats={repeats} ===")
    skipped: list = []
    run = run_repeated(
        live_chain_scenario(6), steps=[2, 3], baselines=[ColdRestart(), RGR()],
        repeats=repeats, on_skip=lambda k, name: skipped.append((k, name)),
    )
    print(f"fired cells={run.fired}, skipped (vacuous)={run.skipped}")
    stats = aggregate_repeated(run)
    print(format_repeated_table(stats))
    v = verdict_c1(stats)
    print(f"\nC1 (repeated, chain): {'SUPPORTED' if v['supported'] else 'NOT SHOWN'} — {v['reason']}")


def _axisstat_to_dict(stat) -> dict:
    return {"mean": stat.mean, "stdev": stat.stdev, "min": stat.min, "max": stat.max, "n": stat.n}


def _stats_to_jsonable(stats: dict) -> dict:
    out: dict = {}
    for name, row in stats.items():
        out[name] = {
            k: (_axisstat_to_dict(v) if isinstance(v, AxisStat) else v) for k, v in row.items()
        }
    return out


def run_live_study(
    model: str,
    *,
    provider: str = "openrouter",
    api_key_env: str = "OPENROUTER_API",
    n: int = 6,
    steps=(2, 3),
    repeats: int = 3,
    max_calls: int = 400,
    transport=None,
) -> dict:
    """The GATED real run (AP-0046): the **non-batchable chain** recovery study, live + repeated.

    This is the run M1 could not produce — the chain task forces sequential steps, so an injected
    crash genuinely fires and recovery is exercised. The real transport (built when `transport` is
    None) is wrapped with a transcript recorder (replays offline) and a budget ceiling; for offline
    validation a fake chain transport is injected directly. Runs the B0-vs-B3 contrast `repeats`
    times with the AP-0045 harness, writes a manifest, and returns the verdict dict. Non-deterministic
    and metered against a real model — honest scope (ADR-0009) applies; a negative is recorded.
    """
    os.makedirs("benchmarks/transcripts", exist_ok=True)
    # Sanitize the model id for a filename: '/' and ':' (e.g. "...:free") are illegal on Windows
    # (':' silently opens an NTFS alternate data stream), so map every non-safe char to '_'.
    slug = "".join(c if (c.isalnum() or c in "-.") else "_" for c in model)
    transcript = f"benchmarks/transcripts/{slug}-chain-study.jsonl"
    manifest_path = f"benchmarks/transcripts/{slug}-chain-study.manifest.json"
    # Record to a `.partial` and finalize on success: `record_to` truncates on wrap, so a
    # crashing re-run (e.g. a rate-limit 429 mid-study) must NOT clobber a prior good transcript.
    transcript_partial = transcript + ".partial"
    recording = transport is None  # we only wire a transcript when we build the real transport
    if recording:
        transport = build_live_transport(
            model, provider=provider, api_key_env=api_key_env,
            transcript_path=transcript_partial, max_calls=max_calls,
        )
    print(f"=== LIVE chain recovery study — model={model} (provider={provider}) — n={n}, "
          f"k={list(steps)}, repeats={repeats}, B0 (cold restart) vs B3 (RGR) ===")
    print(f"(non-batchable task; non-deterministic + metered; transcripts -> {transcript})")

    scenario = live_chain_scenario(n, transport)
    skipped: list = []
    errors: list = []
    run = run_repeated(
        scenario, steps=list(steps), baselines=[ColdRestart(), RGR()],
        repeats=repeats, on_skip=lambda k, name: skipped.append((k, name)),
        on_error=lambda i, exc: errors.append((i, f"{type(exc).__name__}: {exc}")),
    )
    print(f"\nfired cells={run.fired}, skipped (vacuous)={run.skipped}, errored repeats={run.errored}")
    if run.skipped:
        print(f"[!] {run.skipped} cell(s) skipped — the model finished before the crash step "
              f"(unexpected on a non-batchable task; the model may be misusing the oracle).")
    if run.errored:
        print(f"[!] {run.errored} repeat(s) aborted by a transport error (isolated, not fatal) — e.g.:")
        for i, msg in errors[:3]:
            print(f"    repeat {i}: {msg[:120]}")

    stats = aggregate_repeated(run)
    if stats:
        print(format_repeated_table(stats))
    verdict = verdict_c1(stats)
    if run.fired == 0:
        verdict = {"claim": "C1", "supported": False,
                   "reason": "no cells fired live — the model did not drive the sequential task far "
                             "enough for an injected crash to interrupt genuine progress"}
    print(f"\nC1 (LIVE chain, {model}): {'SUPPORTED' if verdict['supported'] else 'NOT SHOWN'} "
          f"— {verdict['reason']}")

    manifest = {
        "study": "M2-chain-live",
        "model": model,
        "provider": provider,
        "task": f"non-batchable chain (n={n})",
        "steps": list(steps),
        "repeats": repeats,
        "fired": run.fired,
        "skipped": run.skipped,
        "errored": run.errored,
        "errors": [msg for _, msg in errors[:5]],
        "stats": _stats_to_jsonable(stats),
        "c1_supported": verdict["supported"],
        "c1_reason": verdict["reason"],
        "scope": "live-LLM study (M2); single model, small n, few repeats — honest scope (ADR-0009)",
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    if recording and os.path.exists(transcript_partial):
        os.replace(transcript_partial, transcript)  # finalize: only a completed run clobbers
    print(f"\nmanifest -> {manifest_path}")
    print("Honest scope (ADR-0009): a single model, small n, few repeats — a demonstration that the")
    print("live pipeline produces real, statistically-summarized evidence on a recovery-faithful task,")
    print("not a powered study. C2/C4/C5 remain reference-harness; this run targets C1 (and C3 if wired).")
    return verdict


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
