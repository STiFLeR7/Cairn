import json

from benchmarks.phase2_semantic_control import run_semantic_control


def test_semantic_control_reaches_identical_verified_outcomes(tmp_path):
    evidence = run_semantic_control(tmp_path)

    assert evidence["schema_version"] == "cairn.phase-2-semantic-control.v0.1"
    assert evidence["cells"] == 11
    assert evidence["complete_triplets"] == 11
    assert evidence["digest_mismatches"] == 0
    assert all(cell["branches"][name]["success"] for cell in evidence["records"] for name in ("U", "R", "C"))


def test_semantic_control_writer_is_replayable_json(tmp_path):
    output = tmp_path / "semantic-control.json"
    evidence = run_semantic_control(tmp_path / "runs", output=output)

    assert json.loads(output.read_text(encoding="utf-8")) == evidence
