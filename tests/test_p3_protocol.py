import hashlib
import json
from pathlib import Path

from benchmarks.p3_matrix import reference_cells


ROOT = Path(__file__).resolve().parents[1]


def test_reference_protocol_is_sealed_and_pins_its_inputs():
    protocol = json.loads((ROOT / "results" / "phase-3" / "p3-reference-protocol.json").read_text(encoding="utf-8"))

    assert protocol["status"] == "sealed-unconsumed"
    assert len(reference_cells(protocol)) == 36
    for pin in protocol["pinned_inputs"].values():
        path = ROOT / pin["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == pin["sha256"]
