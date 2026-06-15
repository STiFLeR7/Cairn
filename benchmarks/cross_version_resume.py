"""Cross-version resume demonstration (AP-0032 / C4).

Run from the repo root:

    python benchmarks/cross_version_resume.py

Checkpoints under model version A, resumes under version B, and shows RGR completes while
recording both versions in provenance. Honest scope (ADR-0009): scripted mock 'versions',
not live multi-model LLMs — this exercises the *mechanism*; the non-determinism robustness
that distinguishes RGR from log-replay is argued, and is future work to measure with real LLMs.
"""

import tempfile

import _bootstrap  # noqa: F401

from benchmarks.scenarios import multi_file_scenario
from cairn.eval.baselines import RGR
from cairn.eval.scenario import harness_for, run_until_failure


def main() -> None:
    base = tempfile.mkdtemp(prefix="cairn_xver_")
    a = multi_file_scenario(n=5, version="model-A")
    run_until_failure(a, base, k=2)

    _h, rt = harness_for(a, base)
    state_a, _snap, _off = rt.load_latest()
    print(f"checkpointed under: {state_a.durable_core.provenance.model_version!r}")

    b = multi_file_scenario(n=5, version="model-B")
    outcome = RGR().recover(b, base)

    _h2, rt2 = harness_for(b, base)
    state_b, _s, _o = rt2.load_latest()
    print(f"resumed under:      {state_b.durable_core.provenance.model_version!r}")
    print(f"resume success:     {outcome.success}  (recovery tax={outcome.executed})")
    print("C4: RGR re-grounds across model versions; provenance records A→B.")
    print("Scope: scripted mock versions; live multi-model study is future work (ADR-0009).")


if __name__ == "__main__":
    main()
