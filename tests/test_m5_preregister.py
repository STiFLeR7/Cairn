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
