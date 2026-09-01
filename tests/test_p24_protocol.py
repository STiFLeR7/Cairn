import hashlib
import json
from pathlib import Path


def test_p24_protocol_pins_all_frozen_and_new_inputs():
    path = Path("results/phase-2/p24-holdout-protocol.json")
    protocol = json.loads(path.read_text(encoding="utf-8"))

    assert protocol["status"] == "sealed-unconsumed"
    assert protocol["matrix"]["expected_attempts"] == 60
    for item in protocol["pinned_inputs"].values():
        content = Path(item["path"]).read_bytes()
        assert hashlib.sha256(content).hexdigest() == item["sha256"]
