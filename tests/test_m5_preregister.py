from __future__ import annotations

from benchmarks import m5_preregister as pre

FILES = ["src/cairn/a.py", "src/cairn/eval/x.py", "benchmarks/s.py", "results/m5/protocol.json"]


def _tree(tmp_path):
    for rel in FILES:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"content of " + rel.encode() + b"\n")


def _frozen(tmp_path):
    _tree(tmp_path)
    pre.write_preregistration(str(tmp_path))
    return str(tmp_path)


def test_verify_passes_then_names_changed_file(tmp_path):
    root = _frozen(tmp_path)
    assert pre.verify(root) == []
    target = tmp_path / "src/cairn/eval/x.py"
    target.write_bytes(target.read_bytes().replace(b"\n", b"\r\n"))  # line-ending churn counts
    problems = pre.verify(root)
    assert len(problems) == 1 and "src/cairn/eval/x.py" in problems[0]


def test_verify_without_preregistration_fails(tmp_path):
    _tree(tmp_path)
    assert pre.verify(str(tmp_path)) and "preregistration" in pre.verify(str(tmp_path))[0]


def test_missing_frozen_file_reported(tmp_path):
    root = _frozen(tmp_path)
    (tmp_path / "benchmarks/s.py").unlink()
    problems = pre.verify(root)
    assert len(problems) == 1 and "benchmarks/s.py" in problems[0] and "missing" in problems[0]


def test_new_source_file_reported(tmp_path):
    root = _frozen(tmp_path)
    (tmp_path / "src/cairn/new.py").write_text("x = 1\n")
    problems = pre.verify(root)
    assert len(problems) == 1 and "src/cairn/new.py" in problems[0] and "not in preregistration" in problems[0]


def test_pycache_ignored(tmp_path):
    root = _frozen(tmp_path)
    c = tmp_path / "src/cairn/__pycache__"
    c.mkdir()
    (c / "junk.py").write_text("x\n")
    assert pre.verify(root) == []


def test_digest_is_none_without_preregistration_then_sha256_of_its_bytes(tmp_path):
    import hashlib

    _tree(tmp_path)
    assert pre.preregistration_digest(str(tmp_path)) is None
    pre.write_preregistration(str(tmp_path))
    data = (tmp_path / pre.PREREG).read_bytes()
    assert pre.preregistration_digest(str(tmp_path)) == hashlib.sha256(data).hexdigest()


def test_write_refuses_overwrite_without_force(tmp_path):
    import pytest

    root = _frozen(tmp_path)
    with pytest.raises(FileExistsError):
        pre.write_preregistration(root)
    pre.write_preregistration(root, force=True)
    assert len(list((tmp_path / "results/m5").glob("preregistration.json.superseded-*"))) == 1
    assert pre.verify(root) == []


def _git(root, *args):
    import subprocess

    subprocess.run(["git", "-C", str(root), "-c", "core.autocrlf=false", "-c", "user.name=t",
                    "-c", "user.email=t@example.invalid", *args], check=True, capture_output=True)


def test_write_refuses_frozen_bytes_that_differ_from_head(tmp_path):
    import pytest

    _tree(tmp_path)
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "init")
    target = tmp_path / "src/cairn/eval/x.py"
    target.write_bytes(target.read_bytes().replace(b"\n", b"\r\n"))
    with pytest.raises(RuntimeError, match="src/cairn/eval/x.py"):
        pre.write_preregistration(str(tmp_path))
    assert not (tmp_path / pre.PREREG).exists()
    _git(tmp_path, "checkout", "--", "src/cairn/eval/x.py")
    (tmp_path / "benchmarks/untracked.py").write_text("x = 1\n")
    with pytest.raises(RuntimeError, match="benchmarks/untracked.py"):
        pre.write_preregistration(str(tmp_path))
    (tmp_path / "benchmarks/untracked.py").unlink()
    assert pre.write_preregistration(str(tmp_path))["git_commit"]
