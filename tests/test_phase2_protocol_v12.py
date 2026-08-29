import hashlib
import json
from pathlib import Path

from cairn.eval.phase2 import matrix_cells


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "phase-2"


def _sha(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def test_v12_live_protocol_is_hash_pinned_and_has_242_cells():
    protocol = json.loads(
        (RESULTS / "matrix-protocol-v12-powered-control-prefix.json").read_text(encoding="utf-8")
    )

    assert protocol["status"] == "live-tranche-pinned"
    assert protocol["matrix"]["prefix_mode"] == "control"
    assert len(matrix_cells(protocol)) == protocol["matrix"]["expected_attempts"] == 242
    for item in protocol["pinned_inputs"].values():
        assert _sha(item["path"]) == item["sha256"]


def test_v12_holdout_protocol_is_sealed_and_reuses_v11_source_hashes():
    holdout = json.loads((RESULTS / "holdout-protocol-v12.json").read_text(encoding="utf-8"))
    v11 = json.loads(
        (RESULTS / "matrix-protocol-v11-neutral-tranche.json").read_text(encoding="utf-8")
    )

    assert holdout["status"] == "sealed-unconsumed"
    assert holdout["holdout"]["consume"] is False
    assert (
        holdout["holdout"]["task_sources"]
        == v11["task_selection"]["holdout"]["task_sources"]
    )
    assert holdout["gate"]["minimum_complete_triplets"] == 10
