import json

import pytest

from benchmarks.p6_pydantic_dbos_probe import CAPABILITIES, capability_verdict, main


def test_capability_verdict_requires_every_directly_observed_boundary():
    observations = {capability: True for capability in CAPABILITIES}

    assert capability_verdict(observations)["passed"] is True

    for missing in CAPABILITIES:
        candidate = dict(observations)
        candidate[missing] = False
        verdict = capability_verdict(candidate)

        assert verdict["passed"] is False
        assert verdict["state"] == "TARGET_STOPPED"
        assert verdict["missing"] == [missing]


def test_capability_verdict_rejects_unknown_or_missing_evidence():
    observations = {capability: True for capability in CAPABILITIES}
    observations["not-a-capability"] = True

    with pytest.raises(ValueError, match="unknown"):
        capability_verdict(observations)

    with pytest.raises(ValueError, match="missing"):
        capability_verdict({})


def test_verdict_cli_writes_the_capability_gate(tmp_path):
    observations = {capability: True for capability in CAPABILITIES}
    source = tmp_path / "observations.json"
    output = tmp_path / "verdict.json"
    source.write_text(json.dumps(observations), encoding="utf-8")

    assert main(["--mode", "verdict", "--observations", str(source), "--output", str(output)]) == 0
    assert json.loads(output.read_text(encoding="utf-8"))["state"] == "TARGET_CAPABLE"
