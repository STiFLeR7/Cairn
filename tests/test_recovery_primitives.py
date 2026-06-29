# tests/test_recovery_primitives.py
from cairn.model import Action, CODE, StepRecord
from cairn.recovery import checkpoint, recover, Regrounded
from cairn.runtime.checkpoint_store import CheckpointStore
from cairn.runtime.effect_ledger import EffectLedger
from cairn.worlds import Workspace


def _fixture(tmp_path):
    ws_dir = tmp_path / "ws"; ws_dir.mkdir()
    world = Workspace(str(ws_dir), str(tmp_path / "snaps"))
    store = CheckpointStore(str(tmp_path / "ck"))
    ledger = EffectLedger(str(tmp_path / "e.jsonl"), "run")
    return ws_dir, world, store, ledger


def test_checkpoint_persists_a_loadable_state(tmp_path):
    ws_dir, world, store, ledger = _fixture(tmp_path)
    (ws_dir / "a.txt").write_text("done", encoding="utf-8")
    history = [StepRecord(step=0, action=Action(kind=CODE, code="write a.txt"), returncode=0)]
    state = checkpoint("the goal", history, world, store, ledger, step=0)
    assert state.durable_core.intent.root_goal == "the goal"
    loaded = store.load_latest()
    assert loaded is not None and loaded[0].durable_core.plan[0].status == "done"


def test_recover_with_no_checkpoint_starts_fresh(tmp_path):
    _, world, store, ledger = _fixture(tmp_path)
    out = recover("goal", world, store, ledger)
    assert isinstance(out, Regrounded) and out.history == [] and out.plan is None


def test_recover_regrounds_history_from_checkpoint(tmp_path):
    ws_dir, world, store, ledger = _fixture(tmp_path)
    (ws_dir / "a.txt").write_text("done", encoding="utf-8")
    history = [StepRecord(step=0, action=Action(kind=CODE, code="write a.txt"), returncode=0)]
    checkpoint("goal", history, world, store, ledger, step=0)
    out = recover("goal", world, store, ledger)
    assert len(out.history) == 1                      # the one done step is re-grounded
    assert out.history[0].action.code == "write a.txt"
    assert out.plan is not None and out.plan.clean    # nothing diverged (restore matched)
