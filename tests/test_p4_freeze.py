from pathlib import Path

from benchmarks.p4_freeze import freeze_phase4_inputs, phase4_inputs_match


def test_phase4_freeze_reuses_hash_control_and_detects_change(tmp_path: Path):
    frozen = tmp_path / "contract.md"
    frozen.write_text("v0\n", encoding="utf-8")

    manifest = freeze_phase4_inputs([frozen], {"phase": "P4.0"})
    assert manifest["schema_version"] == "cairn.p4-freeze.v0.1"
    assert phase4_inputs_match(manifest) is True

    frozen.write_text("changed\n", encoding="utf-8")
    assert phase4_inputs_match(manifest) is False
