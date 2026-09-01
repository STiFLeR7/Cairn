from cairn.contract import World
from cairn.sandbox import ExecResult
from cairn.worlds.terminal import TerminalWorld


def test_terminal_world_restores_repository_snapshot(tmp_path):
    workspace = tmp_path / "workspace"
    snapshots = tmp_path / "snapshots"
    workspace.mkdir()
    (workspace / "note.txt").write_text("before\n", encoding="utf-8")

    world = TerminalWorld(str(workspace), str(snapshots))
    before = world.digest()
    snapshot = world.snapshot()

    assert world.execute("echo after>note.txt").returncode == 0
    assert world.digest() != before

    world.restore(snapshot)

    assert (workspace / "note.txt").read_text(encoding="utf-8") == "before\n"
    assert isinstance(world, World)


def test_terminal_world_preserves_failed_command_result(tmp_path):
    workspace = tmp_path / "workspace"
    world = TerminalWorld(str(workspace), str(tmp_path / "snapshots"))

    result = world.execute("exit 7")

    assert result.returncode == 7
    assert not result.ok


def test_terminal_world_bounds_terminal_actions(tmp_path):
    observed = {}

    class Sandbox:
        def run(self, command, cwd=None, timeout=None):
            observed["timeout"] = timeout
            return ExecResult(0, "", "")

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    world = TerminalWorld(
        str(workspace), str(tmp_path / "snapshots"), sandbox=Sandbox()
    )

    world.execute("echo ok")

    assert observed["timeout"] == 30.0
