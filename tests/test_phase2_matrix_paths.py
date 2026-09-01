from pathlib import Path
import json

from benchmarks.phase2_matrix import next_evidence_path
from cairn.eval.phase2 import matrix_cell_stem


def test_matrix_cell_stem_keeps_model_ids_in_one_evidence_directory():
    cell = {
        "model": "nvidia/nemotron-3-ultra-550b-a55b",
        "fixture": "bugfix",
        "split_step": 0,
        "repetition": 1,
    }

    stem = matrix_cell_stem(cell)

    assert stem == "nvidia_nemotron-3-ultra-550b-a55b-bugfix-s0-r01"
    assert Path(stem).parent == Path(".")


def test_incomplete_evidence_is_preserved_and_resumed_as_retry(tmp_path):
    output = tmp_path / "cell.json"
    output.write_text(json.dumps({"branches": {"U": {"success": True}}}), encoding="utf-8")

    assert next_evidence_path(output) == tmp_path / "cell.retry.json"
    assert output.is_file()
