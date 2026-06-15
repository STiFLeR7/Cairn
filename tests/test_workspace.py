import os

from cairn.runtime.workspace import WorkspaceManager


def test_snapshot_restore_roundtrip(tmp_path):
    ws = str(tmp_path / "workspace")
    snaps = str(tmp_path / "snapshots")
    wm = WorkspaceManager(ws, snaps)

    with open(os.path.join(ws, "a.txt"), "w", encoding="utf-8") as f:
        f.write("one")

    snap = wm.snapshot()

    # mutate after the snapshot
    with open(os.path.join(ws, "a.txt"), "w", encoding="utf-8") as f:
        f.write("two")
    with open(os.path.join(ws, "b.txt"), "w", encoding="utf-8") as f:
        f.write("new")

    wm.restore(snap)

    # original content is back, and files created after the snapshot are gone
    with open(os.path.join(ws, "a.txt"), encoding="utf-8") as f:
        assert f.read() == "one"
    assert not os.path.exists(os.path.join(ws, "b.txt"))


def test_restore_unknown_snapshot_raises(tmp_path):
    wm = WorkspaceManager(str(tmp_path / "ws"), str(tmp_path / "snaps"))
    try:
        wm.restore("snap_does_not_exist")
        assert False, "expected FileNotFoundError"
    except FileNotFoundError:
        pass
