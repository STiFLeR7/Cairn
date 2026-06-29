from cairn.harness.distill import distill, CHECKPOINT
from cairn.harness.observe import observe


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
