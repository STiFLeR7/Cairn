from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

import pytest


ROOT = Path(__file__).resolve().parents[1]
KIT_SOURCE = ROOT / "conformance" / "v0"
EVALUATOR_PATH = KIT_SOURCE / "evaluate.py"
CELLS = (
    "U",
    "R",
    "R_NEG",
    "C",
    "C_NEG",
    "E_MATCH",
    "E_ABSENT",
    "E_ESC_UNKNOWN",
    "E_ESC_MISMATCH",
    "E_ESC_NEVER",
)

spec = importlib.util.spec_from_file_location("p6_evaluate", EVALUATOR_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load P6 evaluator")
evaluator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluator)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _kit_digest(kit: Path) -> str:
    result = hashlib.sha256()
    for name in ("README.md", "evidence.schema.json", "vectors.json", "evaluate.py"):
        result.update(name.encode("utf-8"))
        result.update(b"\0")
        result.update((kit / name).read_bytes())
        result.update(b"\0")
    return result.hexdigest()


def _copy_test_kit(destination: Path) -> Path:
    destination.mkdir()
    for name in ("evidence.schema.json", "vectors.json", "evaluate.py"):
        shutil.copy2(KIT_SOURCE / name, destination / name)
    (destination / "README.md").write_bytes(b"Cairn conformance test profile\n")
    return destination


def _event_chain(kinds: tuple[str, ...], before: str, after: str, evidence_ref: str) -> list[dict]:
    restarted = False
    events = []
    for seq, kind in enumerate(kinds, 1):
        if kind == "process_started" and before != after:
            restarted = True
        events.append(
            {
                "seq": seq,
                "kind": kind,
                "process_id": after if restarted else before,
                "evidence_ref": evidence_ref,
            }
        )
    return events


def _run(cell: str, repetition: int, evidence_ref: str) -> dict:
    before = f"pid-before-{cell}-{repetition}"
    after = before if cell == "U" else f"pid-after-{cell}-{repetition}"
    artifact = _digest(f"artifact-{repetition}")
    outcome = _digest(f"outcome-{repetition}")
    verified_work = _digest(f"verified-work-{repetition}")
    run = {
        "cell": cell,
        "repetition": repetition,
        "triplet_id": f"triplet-{repetition}",
        "checkpoint_id": f"checkpoint-{repetition}",
        "checkpoint_artifact_sha256": artifact,
        "checkpoint_verified_work_sha256": verified_work,
        "process": {
            "before": before,
            "after": after,
            "transcript_available": cell == "U",
        },
        "final": {
            "verified": True,
            "artifact_sha256": artifact,
            "outcome_sha256": outcome,
            "verified_work_sha256": verified_work,
            "correct_termination": True,
            "unauthorized_action": False,
        },
    }

    if cell == "U":
        kinds = ("process_started", "checkpoint_durable", "action", "verification", "termination")
    elif cell == "R":
        kinds = (
            "checkpoint_durable",
            "process_death",
            "process_started",
            "reobserve",
            "action",
            "verification",
            "termination",
        )
    elif cell == "R_NEG":
        kinds = (
            "checkpoint_durable",
            "process_death",
            "process_started",
            "reobserve",
            "escalation",
            "termination",
        )
        run["final"]["verified"] = False
    elif cell in {"C", "C_NEG"}:
        kinds = (
            "checkpoint_durable",
            "active_context_before",
            "compaction_started",
            "compaction_completed",
            "active_context_after",
            "process_death",
            "process_started",
            "reobserve",
            *(("action", "verification") if cell == "C" else ("escalation",)),
            "termination",
        )
        run["compaction"] = {
            "completed": True,
            "event_observed": True,
            "active_context_before_sha256": _digest(f"context-before-{repetition}"),
            "active_context_after_sha256": _digest(f"context-after-{repetition}"),
            "required_semantics_preserved": cell == "C",
        }
        if cell == "C_NEG":
            run["final"]["verified"] = False
    else:
        effect = {
            "E_MATCH": {
                "observation": "present",
                "tool_class": "check-before-retry",
                "matching": True,
                "decision": "skip",
                "provider_commits": 1,
                "post_recovery_dispatches": 0,
                "receipt_durable": True,
                "ledger_closed": True,
                "unresolved": False,
            },
            "E_ABSENT": {
                "observation": "absent",
                "tool_class": "safe-to-retry",
                "matching": None,
                "decision": "retry",
                "provider_commits": 1,
                "post_recovery_dispatches": 1,
                "receipt_durable": True,
                "ledger_closed": True,
                "unresolved": False,
            },
            "E_ESC_UNKNOWN": {
                "observation": "unknown",
                "tool_class": "check-before-retry",
                "matching": None,
                "decision": "escalate",
                "provider_commits": 0,
                "post_recovery_dispatches": 0,
                "receipt_durable": False,
                "ledger_closed": False,
                "unresolved": True,
            },
            "E_ESC_MISMATCH": {
                "observation": "present",
                "tool_class": "check-before-retry",
                "matching": False,
                "decision": "escalate",
                "provider_commits": 1,
                "post_recovery_dispatches": 0,
                "receipt_durable": False,
                "ledger_closed": False,
                "unresolved": True,
            },
            "E_ESC_NEVER": {
                "observation": "absent",
                "tool_class": "never-retry",
                "matching": None,
                "decision": "escalate",
                "provider_commits": 0,
                "post_recovery_dispatches": 0,
                "receipt_durable": False,
                "ledger_closed": False,
                "unresolved": True,
            },
        }[cell]
        before_resolution = (
            "intent_durable",
            "effect_dispatch",
            *(("provider_commit",) if cell in {"E_MATCH", "E_ESC_MISMATCH"} else ()),
            "process_death",
            "process_started",
            "provider_observation",
        )
        if cell == "E_ABSENT":
            resolution = ("effect_retry", "effect_dispatch", "provider_commit", "receipt_durable", "ledger_closed")
        elif cell == "E_MATCH":
            resolution = ("effect_skip", "receipt_durable", "ledger_closed")
        else:
            resolution = ("escalation",)
            run["final"]["verified"] = False
        kinds = (*before_resolution, *resolution, "termination")
        run["effect"] = effect

    run["events"] = _event_chain(kinds, before, after, evidence_ref)
    return run


@pytest.fixture
def valid_submission(tmp_path: Path) -> tuple[dict, Path, Path]:
    kit = _copy_test_kit(tmp_path / "kit")
    submission_root = tmp_path / "submission"
    raw = submission_root / "raw"
    raw.mkdir(parents=True)
    evidence_files = []
    runs = []
    for repetition in range(1, 4):
        for cell in CELLS:
            relative = f"raw/{cell.lower()}-{repetition}.json"
            content = json.dumps({"cell": cell, "repetition": repetition}, sort_keys=True).encode("utf-8")
            (submission_root / relative).write_bytes(content)
            evidence_files.append(
                {
                    "path": relative,
                    "bytes": len(content),
                    "sha256": hashlib.sha256(content).hexdigest(),
                }
            )
            runs.append(_run(cell, repetition, relative))
    submission = {
        "schema_version": "cairn.conformance-evidence.v0",
        "kit": {"version": "v0", "sha256": _kit_digest(kit)},
        "implementation": {
            "repository": "https://example.invalid/independent-agent",
            "commit": "a" * 40,
            "dependency_lock_sha256": _digest("lock"),
            "author": "independent-team",
            "cairn_runtime_dependency": False,
        },
        "workload": {
            "id": "reference-v1",
            "public_task_sha256": _digest("task"),
            "verifier_sha256": _digest("verifier"),
            "seal_sha256": _digest("seal"),
            "sealed_before_execution": True,
        },
        "evidence_files": evidence_files,
        "runs": runs,
    }
    return submission, submission_root, kit


def _cell(submission: dict, name: str, repetition: int = 1) -> dict:
    return next(run for run in submission["runs"] if run["cell"] == name and run["repetition"] == repetition)


def test_complete_linked_submission_passes(valid_submission):
    submission, submission_root, kit = valid_submission

    verdict = evaluator.evaluate_submission(submission, submission_root, kit)

    assert verdict == {
        "schema_version": "cairn.conformance-verdict.v0",
        "passed": True,
        "failures": [],
        "counts": {"runs": 30, "passed": 30, "failed": 0},
    }


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("missing_raw", "missing evidence file"),
        ("event_sequence", "event sequence"),
        ("process_identity", "fresh process"),
        ("action_order", "re-observation must precede action"),
        ("verified_work", "verified work"),
        ("compaction_context", "active context"),
        ("duplicate_effect", "provider commits"),
        ("unknown_retry", "unknown observation must escalate"),
        ("artifact_equivalence", "U/R/C artifact equivalence"),
    ],
)
def test_semantic_mutation_is_rejected(valid_submission, mutation: str, expected: str):
    original, submission_root, kit = valid_submission
    submission = copy.deepcopy(original)
    if mutation == "missing_raw":
        (submission_root / submission["evidence_files"][0]["path"]).unlink()
    elif mutation == "event_sequence":
        _cell(submission, "R")["events"][1]["seq"] = 1
    elif mutation == "process_identity":
        run = _cell(submission, "R")
        run["process"]["after"] = run["process"]["before"]
    elif mutation == "action_order":
        run = _cell(submission, "R")
        reobserve = next(event for event in run["events"] if event["kind"] == "reobserve")
        action = next(event for event in run["events"] if event["kind"] == "action")
        reobserve["kind"], action["kind"] = action["kind"], reobserve["kind"]
    elif mutation == "verified_work":
        _cell(submission, "R")["final"]["verified_work_sha256"] = _digest("lost")
    elif mutation == "compaction_context":
        compaction = _cell(submission, "C")["compaction"]
        compaction["active_context_after_sha256"] = compaction["active_context_before_sha256"]
    elif mutation == "duplicate_effect":
        _cell(submission, "E_MATCH")["effect"]["provider_commits"] = 2
    elif mutation == "unknown_retry":
        _cell(submission, "E_ESC_UNKNOWN")["effect"]["decision"] = "retry"
    elif mutation == "artifact_equivalence":
        _cell(submission, "R")["final"]["artifact_sha256"] = _digest("different")

    verdict = evaluator.evaluate_submission(submission, submission_root, kit)

    assert verdict["passed"] is False
    assert any(expected in failure for failure in verdict["failures"]), verdict


def test_phase5_boolean_facts_are_not_p6_evidence(tmp_path: Path):
    kit = _copy_test_kit(tmp_path / "kit")
    verdict = evaluator.evaluate_submission(
        {"schema_version": "cairn.p5-conformance.v0", "passed": True},
        tmp_path,
        kit,
    )

    assert verdict["passed"] is False
    assert "unsupported evidence schema" in verdict["failures"]
