from pathlib import Path

from benchmarks.p3_freeze import freeze_manifest, frozen_paths_match


def test_freeze_manifest_detects_changed_contract_file(tmp_path: Path):
    contract = tmp_path / "continuation-contract-v0.md"
    contract.write_text("contract-v0\n", encoding="utf-8")

    manifest = freeze_manifest([contract], {"phase": "P3.0"})
    assert frozen_paths_match(manifest) is True

    contract.write_text("contract-v1\n", encoding="utf-8")
    assert frozen_paths_match(manifest) is False
