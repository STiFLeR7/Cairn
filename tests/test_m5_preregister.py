from __future__ import annotations

import json
import os

from benchmarks import m5_preregister as pre


def _tree(tmp_path):
    for rel in pre.FROZEN_FILES:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"content of " + rel.encode() + b"\n")


def test_verify_passes_then_names_changed_file(tmp_path):
    _tree(tmp_path)
    pre.write_preregistration(str(tmp_path))
    assert pre.verify(str(tmp_path)) == []
    target = tmp_path / pre.FROZEN_FILES[0]
    target.write_bytes(target.read_bytes().replace(b"\n", b"\r\n"))  # line-ending churn counts
    problems = pre.verify(str(tmp_path))
    assert len(problems) == 1 and pre.FROZEN_FILES[0] in problems[0]


def test_verify_without_preregistration_fails(tmp_path):
    _tree(tmp_path)
    assert pre.verify(str(tmp_path)) and "preregistration" in pre.verify(str(tmp_path))[0]
