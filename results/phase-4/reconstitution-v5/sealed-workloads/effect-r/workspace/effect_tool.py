import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path[:0] = ['D:\\project-unknown-phase4', 'D:\\project-unknown-phase4\\src']
from benchmarks.p3_effect_service import CreateOnceProvider, Intent, Receipt
from cairn.runtime.effect_ledger import EffectLedger

WORKSPACE = Path(__file__).resolve().parent
REMOTE = Path('D:\\project-unknown-phase4\\results\\phase-4\\reconstitution-v5\\sealed-workloads\\effect-r\\remote')
INTENT_PATH = WORKSPACE / ".cairn-effect-intent.json"
RESPONSE_PATH = WORKSPACE / ".cairn-provider-response.json"
OBSERVATION_PATH = WORKSPACE / ".cairn-effect-observation.json"
RECEIPT_PATH = WORKSPACE / ".cairn-effect-receipt.json"
RESOLUTION_PATH = WORKSPACE / ".cairn-effect-resolution.json"
LEDGER = WORKSPACE / ".cairn-effects.jsonl"

def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def intent():
    return Intent("p4-claude-create-once", "p4-claude-key", "p4-claude-request", "create-once")

def load_intent():
    return Intent(**json.loads(INTENT_PATH.read_text(encoding="utf-8")))

def main(command):
    provider = CreateOnceProvider(REMOTE)
    if command == "init":
        value = intent()
        write(INTENT_PATH, asdict(value))
        EffectLedger(str(LEDGER), "p4-claude").append_effect("create-once", value.idempotency_key, value.tool_class)
        print("intent-durable")
    elif command == "create":
        value = load_intent()
        provider.dispatch(value)
        write(RESPONSE_PATH, asdict(provider.commit(value)))
        print("provider-committed-without-durable-receipt")
    elif command == "observe":
        value = load_intent()
        observation = provider.observe(value)
        write(OBSERVATION_PATH, asdict(observation))
        print(observation.state)
    elif command in {"receipt", "close-skip"}:
        value = load_intent()
        observation = provider.observe(value)
        if observation.state != "present" or observation.request_fingerprint != value.request_fingerprint:
            raise SystemExit("cannot close without matching observed resource")
        receipt = Receipt(value.effect_id, value.idempotency_key, value.request_fingerprint, observation.resource_id, "commit" if command == "receipt" else "reobserve")
        write(RECEIPT_PATH, asdict(receipt))
        EffectLedger(str(LEDGER), "p4-claude").complete_effect(value.idempotency_key)
        write(RESOLUTION_PATH, {"decision": "complete" if command == "receipt" else "skip", "observation": asdict(observation)})
        print("closed")
    else:
        raise SystemExit("usage: effect_tool.py init|create|observe|receipt|close-skip")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) == 2 else "")
