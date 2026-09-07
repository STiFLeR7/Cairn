import json
from pathlib import Path
import subprocess
import sys

from benchmarks.p6_freeze import freeze_manifest, frozen_paths_match


ROOT = Path(__file__).resolve().parents[1]


def test_p6_freeze_is_portable_and_detects_mutation(tmp_path: Path):
    contract = tmp_path / "contract.md"
    contract.write_bytes(b"v0\n")

    manifest = freeze_manifest(tmp_path, [contract], {"head": "abc"})

    assert manifest["files"] == [
        {
            "path": "contract.md",
            "bytes": 3,
            "sha256": "84325551c170b6987edbe70faaec1cafb6a76ee10c13a77eb60705679dd7271a",
        }
    ]
    assert frozen_paths_match(tmp_path, manifest)

    contract.write_bytes(b"changed\n")

    assert not frozen_paths_match(tmp_path, manifest)


def test_cli_generates_and_checks_repository_freeze(tmp_path: Path):
    output = tmp_path / "freeze.json"

    generated = subprocess.run(
        [sys.executable, "benchmarks/p6_freeze.py", "--output", str(output)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert generated.returncode == 0, generated.stderr
    manifest = json.loads(output.read_text(encoding="utf-8"))
    assert manifest["metadata"]["state"] == "FROZEN_OBLIGATIONS"
    assert {item["path"] for item in manifest["files"]} == {
        "benchmarks/p5_conformance.py",
        "docs/design/continuation-contract-v0.md",
        "docs/design/receipt-reconciliation-contract-v0.md",
        "docs/superpowers/specs/2026-09-07-p6-independent-ecosystem-conformance-design.md",
        "results/phase-1/REPORT.md",
        "results/phase-2/p24-verdict.json",
        "results/phase-3/p3-verdict.json",
        "results/phase-4/reconstitution-v6/verdict.json",
        "results/phase-5/two-host-portability-verdict.json",
    }

    checked = subprocess.run(
        [sys.executable, "benchmarks/p6_freeze.py", "--check", str(output)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert checked.returncode == 0, checked.stderr
