from benchmarks.p4_native_compaction_v5 import FRESH_RECOVERY_PROMPT, prepare


def test_v5_seals_generic_authority_before_host_execution(tmp_path):
    root = tmp_path / "sealed"
    prepare(root)

    assert (root / "pre-run-freeze.json").is_file()
    assert (root / "sealed-workloads" / "source" / "TASK.md").is_file()
    assert "stage2.py" not in FRESH_RECOVERY_PROMPT
    assert "Do not read TASK.md or\nuse it as authority" in FRESH_RECOVERY_PROMPT
    assert ".cairn-continuation.json" in FRESH_RECOVERY_PROMPT
    assert ".cairn-action-map.json" in FRESH_RECOVERY_PROMPT
