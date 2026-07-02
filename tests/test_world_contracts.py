from cairn.contract import CheckpointStore as CheckpointStoreProto
from cairn.contract import EffectLedger as EffectLedgerProto
from cairn.contract import World as WorldProto
from cairn.harness.distill import CHECKPOINT, distill
from cairn.harness.observe import observe
from cairn.runtime.checkpoint_store import CheckpointStore as ConcreteCkpt
from cairn.runtime.effect_ledger import EffectLedger as ConcreteLedger
from cairn.worlds import Workspace


class _DigestWorld:
    def __init__(self, digest): self._d = digest
    def snapshot(self): return "s0"
    def restore(self, snap_id): pass
    def digest(self): return self._d


class _Ledger:
    def list_effects_since(self, offset): return [{"seq": offset, "type": "INTENT"}]


def test_distill_uses_supplied_digest_over_workspace():
    # When a digest is supplied (the World seam), distill records it verbatim and does NOT
    # touch the filesystem — so a non-workspace World works.
    state = distill(
        "goal", [], mode=CHECKPOINT, step=0,
        digest={"k": "v"}, workspace_dir="/does/not/exist",
    )
    assert state.durable_core.world.digest == {"k": "v"}


def test_distill_without_digest_falls_back_to_workspace(tmp_path):
    (tmp_path / "a.txt").write_text("hi", encoding="utf-8")
    state = distill("goal", [], mode=CHECKPOINT, step=0, workspace_dir=str(tmp_path))
    assert "a.txt" in state.durable_core.world.digest  # legacy path unchanged


def test_observe_reads_world_digest_and_ledger():
    obs = observe(_DigestWorld({"f": "h"}), _Ledger(), since_offset=3)
    assert obs.digest == {"f": "h"}
    assert obs.effects_since == [{"seq": 3, "type": "INTENT"}]


def test_concrete_impls_satisfy_protocols(tmp_path):
    ckpt = ConcreteCkpt(str(tmp_path / "ck"))
    ledger = ConcreteLedger(str(tmp_path / "e.jsonl"), "run")
    assert isinstance(ckpt, CheckpointStoreProto)
    assert isinstance(ledger, EffectLedgerProto)
    assert isinstance(_DigestWorld({}), WorldProto)  # a duck-typed World qualifies


def test_workspace_world_snapshot_restore_digest(tmp_path):
    ws_dir = tmp_path / "ws"
    ws_dir.mkdir()
    snaps = tmp_path / "snaps"
    w = Workspace(str(ws_dir), str(snaps))
    (ws_dir / "a.txt").write_text("one", encoding="utf-8")
    snap = w.snapshot()
    d1 = w.digest()
    assert "a.txt" in d1
    (ws_dir / "a.txt").write_text("two", encoding="utf-8")   # diverge
    assert w.digest() != d1
    w.restore(snap)                                          # restore the snapshot
    assert w.digest() == d1
    assert isinstance(w, WorldProto)


from cairn.runtime.local_runtime import LocalRuntime


def test_local_runtime_satisfies_the_byom_protocols(tmp_path):
    rt = LocalRuntime(str(tmp_path / "rt"))
    assert isinstance(rt, WorldProto)
    assert isinstance(rt, CheckpointStoreProto)
    assert isinstance(rt, EffectLedgerProto)


def test_local_runtime_world_aliases_round_trip(tmp_path):
    rt = LocalRuntime(str(tmp_path / "rt"))
    from pathlib import Path
    Path(rt.workspace_dir, "a.txt").write_text("one", encoding="utf-8")
    snap = rt.snapshot()                       # alias of snapshot_workspace
    d1 = rt.digest(); assert "a.txt" in d1      # alias of world_digest(workspace_dir)
    Path(rt.workspace_dir, "a.txt").write_text("two", encoding="utf-8")
    rt.restore(snap)                            # alias of restore_workspace
    assert rt.digest() == d1
    assert rt.current_offset() == rt.current_effect_offset()  # ledger alias


def test_workspace_executes_code_in_its_dir(tmp_path):
    ws_dir = tmp_path / "ws"; ws_dir.mkdir()
    w = Workspace(str(ws_dir), str(tmp_path / "snaps"))
    res = w.execute("open('made.txt', 'w').write('hi')")
    assert res.returncode == 0
    assert (ws_dir / "made.txt").read_text(encoding="utf-8") == "hi"
