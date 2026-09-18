from __future__ import annotations

import hashlib
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "conformance" / "v2" / "STAGE6B-HANDOFF.md"


def _handoff_hash(label: str) -> str:
    match = re.search(rf"\| {re.escape(label)} \| `([0-9a-f]{{64}})` \|", HANDOFF.read_text(encoding="utf-8"))
    assert match, f"missing {label} hash in Stage 6B handoff"
    return match.group(1)


def _git_blob_bytes(path: str) -> bytes:
    completed = subprocess.run(
        ["git", "show", f"HEAD:{path}"], cwd=ROOT, check=True, capture_output=True,
    )
    return completed.stdout


def test_stage6b_handoff_hashes_are_canonical_git_bytes_and_checkout_stable():
    artifacts = {
        "Reference witness SHA-256": "conformance/v2/witness.py",
        "Semantic-rules SHA-256": "conformance/v2/vectors.json",
        "Real-provider SHA-256": "conformance/v2/stage6b_provider.py",
    }
    for label, relative in artifacts.items():
        expected = _handoff_hash(label)
        blob = _git_blob_bytes(relative)
        checkout = (ROOT / relative).read_bytes()
        assert hashlib.sha256(blob).hexdigest() == expected
        assert hashlib.sha256(checkout).hexdigest() == expected
        assert checkout == blob
        attribute = subprocess.run(
            ["git", "check-attr", "eol", "--", relative], cwd=ROOT,
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        assert attribute.endswith("eol: lf")


def test_stage6b_handoff_pinned_candidate_and_ancestry_inputs_resolve():
    text = HANDOFF.read_text(encoding="utf-8")
    candidate_digest = re.search(r"\| Bundle SHA-256 \| `([0-9a-f]{64})` \|", text)
    candidate_commit = re.search(r"\| Candidate commit \| `([0-9a-f]{40})` \|", text)
    candidate_tree = re.search(r"\| Candidate tree \| `([0-9a-f]{40})` \|", text)
    floor = re.search(r"\| Cairn ancestry floor \| `([0-9a-f]{40})` \|", text)
    assert candidate_digest and candidate_commit and candidate_tree and floor
    bundle = ROOT / "results" / "phase-6" / "stage-6a-haiku-candidate-7" / "candidate.bundle"
    assert hashlib.sha256(bundle.read_bytes()).hexdigest() == candidate_digest.group(1)
    assert subprocess.run(
        ["git", "merge-base", "--is-ancestor", floor.group(1), "HEAD"], cwd=ROOT,
    ).returncode == 0
