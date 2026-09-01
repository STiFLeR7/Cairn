from benchmarks.phase2_chain_urc import run_chain_urc


def test_chain_urc_deterministic_control_preserves_all_split_positions(tmp_path):
    evidence = run_chain_urc(tmp_path, n=6, model_factory="fake")

    assert evidence["schema_version"] == "cairn.phase-2-chain-urc.v0.1"
    assert evidence["cells"] == 5
    assert evidence["complete_triplets"] == 5
    assert all(
        all(cell["branches"][branch]["success"] for branch in ("U", "R", "C"))
        for cell in evidence["records"]
    )
    assert all(cell["digests_equal"] for cell in evidence["records"])
