"""Exact action-parity replay for eligible P2.4 branch divergences."""

from __future__ import annotations

import base64
import json
from pathlib import Path
import shutil
import uuid

try:
    import _bootstrap  # noqa: F401
except ModuleNotFoundError:
    from benchmarks import _bootstrap  # noqa: F401

from cairn.eval.phase2 import compacted_continuation
from cairn.eval.recoverybench import CheckpointStore, EffectLedger, _live_world, load_fixture
from cairn.recovery import recover
from cairn.state import ContinuationState

from benchmarks.p24_fixture import register_fixture


def _wire(cell: dict) -> dict:
    return {"live": {"provider": cell["provider"], "model": cell["model"]}}


def replay_p24_branch(record_path: Path, source: str, target: str, output_dir: Path) -> dict:
    """Reconstruct target from its durable prefix and apply source's accepted actions exactly."""
    record = json.loads(Path(record_path).read_text(encoding="utf-8"))
    if source not in record["branches"] or target not in {"R", "C"}:
        raise ValueError("source must exist and target must be R or C")
    register_fixture()
    fixture = load_fixture(record["cell"]["fixture"])
    replay_dir = Path(output_dir) / f"replay-{uuid.uuid4().hex}"
    shutil.copytree(Path(record["run_dir"]) / "prefix", replay_dir)
    root = replay_dir / fixture.name
    world = _live_world(root, replay_dir, _wire(record["cell"]))
    store = CheckpointStore(str(replay_dir / "checkpoints"))
    ledger = EffectLedger(str(replay_dir / "effects.jsonl"), f"replay-{target}")
    loaded = store.load_latest()
    if loaded is None:
        raise RuntimeError("durable checkpoint missing")
    state = loaded[0]
    if target == "R":
        recover(world, store, ledger)
    else:
        compacted_continuation(ContinuationState.from_json(state.to_json()))
    for action in record["branches"][source]["accepted_actions"]:
        payload = base64.b64encode(action["code"].encode("utf-8")).decode("ascii")
        result = world.execute(f'"{world.interpreter}" -c "import base64; exec(base64.b64decode(\'{payload}\'))"')
        if not result.ok:
            raise RuntimeError("recorded source action failed during replay")
    final_digest = world.digest()
    return {
        "source": source,
        "target": target,
        "verified": fixture.verify(root).passed,
        "source_final_digest": record["branches"][source]["final_digest"],
        "final_digest": final_digest,
    }
