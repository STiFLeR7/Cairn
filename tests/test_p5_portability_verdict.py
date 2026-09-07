from pathlib import Path

from benchmarks.p5_portability_verdict import build_verdict


ROOT = Path(__file__).resolve().parents[1]


def test_p5_two_host_verdict_requires_the_admitted_claude_and_openhands_evidence():
    verdict = build_verdict(
        ROOT / "results/phase-4/reconstitution-v5",
        ROOT / "results/phase-4/reconstitution-v6",
        ROOT / "results/phase-5/openhands-reference-v1/reference-run-11",
        ROOT / "results/phase-5/openhands-holdout-v1/holdout-run-1",
    )

    assert verdict["passed"] is True
    assert verdict["hosts"] == ["Claude Code", "OpenHands SDK LocalConversation"]
