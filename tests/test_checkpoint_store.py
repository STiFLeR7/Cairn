from cairn.runtime.checkpoint_store import CheckpointStore
from cairn.state import ContinuationState, Intent


def test_load_latest_and_roundtrip(tmp_path):
    cs = CheckpointStore(str(tmp_path / "ck"))
    assert cs.load_latest() is None

    s = ContinuationState()
    s.durable_core.intent = Intent("g", "first")
    cs.checkpoint(s, "snap_0", 0)

    s.durable_core.intent.active_subgoal = "second"
    cs.checkpoint(s, "snap_1", 5)

    loaded = cs.load_latest()
    assert loaded is not None
    state, snap, offset = loaded
    assert snap == "snap_1"
    assert offset == 5
    assert state.durable_core.intent.active_subgoal == "second"


def test_partial_tmp_is_ignored(tmp_path):
    d = tmp_path / "ck"
    d.mkdir()
    # a leftover partial write must never be loaded (atomicity, I2)
    (d / "ckpt_9.json.tmp").write_text("{ not valid json")
    cs = CheckpointStore(str(d))
    assert cs.load_latest() is None
