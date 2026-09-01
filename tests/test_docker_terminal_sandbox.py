import subprocess

from cairn.runtime.sandbox_docker import DockerTerminalSandbox


def test_docker_terminal_sandbox_isolates_the_workspace_and_disables_network(tmp_path):
    observed = {}

    def runner(argv, **kwargs):
        observed["argv"] = argv
        observed["kwargs"] = kwargs
        return subprocess.CompletedProcess(argv, 0, "ok", "")

    result = DockerTerminalSandbox(runner=runner).run("python -c \"print('ok')\"", cwd=str(tmp_path))

    assert result.ok
    argv = observed["argv"]
    assert "--network" in argv and argv[argv.index("--network") + 1] == "none"
    assert "--cap-drop=ALL" in argv
    assert "--security-opt=no-new-privileges" in argv
    assert f"{tmp_path.resolve()}:/workspace:rw" in argv
    assert argv[-3:] == ["sh", "-lc", "python -c \"print('ok')\""]
    assert "env" not in observed["kwargs"]


def test_docker_availability_is_false_when_the_client_is_not_on_path(monkeypatch):
    monkeypatch.setattr("cairn.runtime.sandbox_docker.shutil.which", lambda _name: None)

    assert not DockerTerminalSandbox.available()


def test_docker_terminal_sandbox_returns_timeout_result(tmp_path):
    calls = []

    def runner(argv, **kwargs):
        calls.append((argv, kwargs))
        if argv[:2] == ["docker", "run"]:
            raise subprocess.TimeoutExpired(argv, kwargs["timeout"])
        return subprocess.CompletedProcess(argv, 0, "", "")

    result = DockerTerminalSandbox(runner=runner).run(
        "python -c \"print('slow')\"", cwd=str(tmp_path), timeout=30.0
    )

    assert result.returncode == 124
    assert result.stderr == "command timed out after 30 seconds"
    run_argv, run_kwargs = calls[0]
    name = run_argv[run_argv.index("--name") + 1]
    assert run_argv[-3:] == ["sh", "-lc", "python -c \"print('slow')\""]
    assert run_kwargs["timeout"] == 30.0
    assert calls[1][0] == ["docker", "rm", "-f", name]
