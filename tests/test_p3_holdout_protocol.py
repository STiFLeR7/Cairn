import hashlib
import json
from pathlib import Path

from benchmarks.p3_holdout import holdout_cells


ROOT = Path(__file__).resolve().parents[1]


def test_holdout_protocol_is_sealed_and_pins_author_and_runner_inputs():
    protocol = json.loads((ROOT / "results" / "phase-3" / "p3-holdout-protocol.json").read_text(encoding="utf-8"))
    author = json.loads((ROOT / protocol["author_output"]).read_text(encoding="utf-8"))

    assert protocol["status"] == "sealed-unconsumed"
    assert len(holdout_cells(author, protocol["repetitions"])) == 15
    for pin in protocol["pinned_inputs"].values():
        assert hashlib.sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"]
