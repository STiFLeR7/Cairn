import sys

from cairn.runtime.sandbox_local import LocalSubprocessSandbox


def test_argv_execution():
    sb = LocalSubprocessSandbox()
    res = sb.run([sys.executable, "-c", "print('hi cairn')"])
    assert res.ok
    assert "hi cairn" in res.stdout


def test_nonzero_returncode():
    sb = LocalSubprocessSandbox()
    res = sb.run([sys.executable, "-c", "import sys; sys.exit(3)"])
    assert res.returncode == 3
    assert not res.ok
