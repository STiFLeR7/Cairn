"""AP-0032 / C4 — checkpoint under model version A, resume under version B.

Exercises the cross-version resume *mechanism*: RGR re-grounds from the cairn + observed
world rather than reproducing the original model's tokens, so resume completes even though a
different model version takes over, and `provenance` records both versions. (Honest scope,
ADR-0009: scripted mock 'versions', not live multi-model LLMs.)
"""

from benchmarks.scenarios import multi_file_scenario
from cairn.eval.baselines import RGR
from cairn.eval.scenario import harness_for, run_until_failure


def test_c4_cross_version_resume(tmp_path):
    base = str(tmp_path / "xver")
    a = multi_file_scenario(n=4, version="model-A")
    run_until_failure(a, base, k=1)

    _h, rt = harness_for(a, base)
    state_a, _snap, _off = rt.load_latest()
    assert state_a.durable_core.provenance.model_version == "model-A"

    # A different version resumes and reaches the same goal.
    b = multi_file_scenario(n=4, version="model-B")
    outcome = RGR().recover(b, base)
    assert outcome.success  # RGR re-grounds across versions

    _h2, rt2 = harness_for(b, base)
    state_b, _s, _o = rt2.load_latest()
    assert state_b.durable_core.provenance.model_version == "model-B"  # resume recorded under B
