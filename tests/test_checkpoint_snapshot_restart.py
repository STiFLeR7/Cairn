"""AP-0024 — snapshot numbering continues across restart; checkpoint+snapshot survive it."""

import os

from cairn.runtime.local_runtime import LocalRuntime
from cairn.runtime.workspace import WorkspaceManager
from cairn.state import ContinuationState


def test_snapshot_numbering_continues_after_reconstruction(tmp_path):
    ws = str(tmp_path / "ws")
    snaps = str(tmp_path / "snaps")
    wm = WorkspaceManager(ws, snaps)
    with open(os.path.join(ws, "a.txt"), "w", encoding="utf-8") as f:
        f.write("1")
    assert wm.snapshot() == "snap_0"
    assert wm.snapshot() == "snap_1"

    # Reconstruct (the resume case): must NOT reset to snap_0 and overwrite snap_0/snap_1.
    wm2 = WorkspaceManager(ws, snaps)
    assert wm2.snapshot() == "snap_2"
    assert os.path.isdir(os.path.join(snaps, "snap_0"))
    assert os.path.isdir(os.path.join(snaps, "snap_1"))


def test_checkpoint_and_snapshot_survive_process_restart(tmp_path):
    base = str(tmp_path / "base")
    rt = LocalRuntime(base_dir=base)
    target = os.path.join(rt.workspace_dir, "a.txt")
    with open(target, "w", encoding="utf-8") as f:
        f.write("v1")
    snap = rt.snapshot_workspace()
    state = ContinuationState()
    state.durable_core.world.snapshot_id = snap
    rt.checkpoint(state, snap, rt.current_effect_offset())

    # Fresh runtime over the same base_dir (simulated restart).
    rt2 = LocalRuntime(base_dir=base)
    loaded = rt2.load_latest()
    assert loaded is not None
    _state2, snap2, _off2 = loaded
    assert snap2 == snap  # the checkpoint still references its snapshot (I4)

    # The referenced snapshot is still restorable after the restart.
    with open(target, "w", encoding="utf-8") as f:
        f.write("v2")
    rt2.restore_workspace(snap2)
    with open(target, encoding="utf-8") as f:
        assert f.read() == "v1"

    # A new snapshot after restart does not collide with the preserved one.
    assert rt2.snapshot_workspace() != snap
