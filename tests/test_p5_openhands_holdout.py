import base64
import importlib
import re


def test_p5_holdout_control_implements_the_sealed_ledger_task():
    protocol = importlib.import_module("benchmarks.p5_openhands_holdout")
    command = protocol.coding_commands()[1]
    encoded = re.search(r"b64decode\('([^']+)'\)", command).group(1)
    namespace: dict[str, object] = {}
    exec(base64.b64decode(encoded), namespace)

    assert namespace["ledger_digest"]([{"account": "ops", "delta": 4}, {"account": "tax", "delta": -2}, {"account": "ops", "delta": 5}]) == "ops=9\ntax=-2"
