"""Standalone evaluator for Cairn recovery conformance evidence v0."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


SCHEMA_VERSION = "cairn.conformance-evidence.v0"
VERDICT_VERSION = "cairn.conformance-verdict.v0"
KIT_FILES = ("README.md", "evidence.schema.json", "vectors.json", "evaluate.py")
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
RECOVERY_CELLS = set(CELLS) - {"U"}
CONTINUATION_CELLS = {"R", "R_NEG", "C", "C_NEG"}
NEGATIVE_CELLS = {"R_NEG", "C_NEG", "E_ESC_UNKNOWN", "E_ESC_MISMATCH", "E_ESC_NEVER"}
EFFECT_CELLS = {"E_MATCH", "E_ABSENT", "E_ESC_UNKNOWN", "E_ESC_MISMATCH", "E_ESC_NEVER"}
OPERATION_KINDS = {
    "action",
    "effect_dispatch",
    "effect_retry",
    "effect_skip",
    "escalation",
    "provider_observation",
    "reobserve",
    "verification",
}


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _kit_sha256(kit_root: Path) -> str:
    result = hashlib.sha256()
    for name in KIT_FILES:
        result.update(name.encode("utf-8"))
        result.update(b"\0")
        result.update((kit_root / name).read_bytes())
        result.update(b"\0")
    return result.hexdigest()


def _safe_path(root: Path, relative: object) -> Path | None:
    if not isinstance(relative, str) or not relative:
        return None
    try:
        candidate = (root / relative).resolve()
        candidate.relative_to(root.resolve())
    except (OSError, ValueError):
        return None
    return candidate


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _index(events: list[dict], kind: str, *, after: int = -1) -> int | None:
    return next(
        (event["seq"] for event in events if event.get("kind") == kind and event.get("seq", -1) > after),
        None,
    )


def _first_operation(events: list[dict], *, after: int) -> str | None:
    operations = [
        event for event in events
        if event.get("seq", -1) > after and event.get("kind") in OPERATION_KINDS
    ]
    return min(operations, key=lambda event: event["seq"])["kind"] if operations else None


def _required_fields(value: object, fields: tuple[str, ...], label: str, fail) -> dict:
    if not isinstance(value, dict):
        fail(f"{label}: expected object")
        return {}
    for field in fields:
        if field not in value:
            fail(f"{label}: missing {field}")
    return value


def _load_vectors(kit_root: Path, fail) -> list[dict]:
    try:
        vectors = json.loads((kit_root / "vectors.json").read_text(encoding="utf-8"))
        effects = vectors["effect_resolution"]
        if not isinstance(effects, list):
            raise TypeError
        return effects
    except (KeyError, OSError, TypeError, json.JSONDecodeError):
        fail("kit: invalid effect vectors")
        return []


def _validate_inventory(
    submission_root: Path,
    inventory: object,
    fail,
) -> set[str]:
    if not isinstance(inventory, list):
        fail("evidence_files: expected array")
        return set()
    valid = set()
    seen = set()
    for position, item in enumerate(inventory):
        label = f"evidence_files[{position}]"
        item = _required_fields(item, ("path", "bytes", "sha256"), label, fail)
        relative = item.get("path")
        if relative in seen:
            fail(f"{label}: duplicate evidence path")
            continue
        seen.add(relative)
        target = _safe_path(submission_root, relative)
        if target is None:
            fail(f"{label}: unsafe evidence path")
        elif not target.is_file():
            fail(f"{label}: missing evidence file {relative}")
        else:
            content = target.read_bytes()
            if item.get("bytes") != len(content) or item.get("sha256") != _sha256(content):
                fail(f"{label}: evidence hash mismatch {relative}")
            else:
                valid.add(relative)
    return valid


def _validate_events(run: dict, label: str, valid_evidence: set[str], fail) -> list[dict]:
    events = run.get("events")
    if not isinstance(events, list) or not events:
        fail(f"{label}: events must be a non-empty array")
        return []
    if any(not isinstance(event, dict) for event in events):
        fail(f"{label}: every event must be an object")
        return []
    sequences = [event.get("seq") for event in events]
    if sequences != list(range(1, len(events) + 1)):
        fail(f"{label}: event sequence must be contiguous and ordered")
    for event in events:
        if not event.get("kind") or not event.get("process_id"):
            fail(f"{label}: event identity is incomplete")
        if event.get("evidence_ref") not in valid_evidence:
            fail(f"{label}: event references unverified raw evidence")
    return events


def _require_kinds(events: list[dict], kinds: set[str], label: str, fail) -> None:
    observed = {event.get("kind") for event in events}
    for kind in sorted(kinds - observed):
        fail(f"{label}: missing {kind} event")


def _validate_fresh_boundary(run: dict, events: list[dict], label: str, expected_first: str, fail) -> None:
    process = _required_fields(
        run.get("process"),
        ("before", "after", "transcript_available"),
        f"{label}.process",
        fail,
    )
    if process.get("before") == process.get("after"):
        fail(f"{label}: recovery requires a fresh process")
    if process.get("transcript_available") is not False:
        fail(f"{label}: original transcript must be unavailable")
    started = _index(events, "process_started")
    if started is None:
        fail(f"{label}: missing process_started event")
        return
    first = _first_operation(events, after=started)
    if first != expected_first:
        if expected_first == "reobserve":
            fail(f"{label}: re-observation must precede action")
        else:
            fail(f"{label}: provider observation must be first after recovery")


def _validate_continuation(run: dict, events: list[dict], label: str, fail) -> None:
    required = {"checkpoint_durable", "process_death", "process_started", "reobserve", "termination"}
    required.add("escalation" if run["cell"] in NEGATIVE_CELLS else "action")
    if run["cell"] not in NEGATIVE_CELLS:
        required.add("verification")
    _require_kinds(events, required, label, fail)
    _validate_fresh_boundary(run, events, label, "reobserve", fail)
    reobserve = _index(events, "reobserve")
    action = _index(events, "action")
    if action is not None and (reobserve is None or reobserve >= action):
        fail(f"{label}: re-observation must precede action")


def _validate_compaction(run: dict, events: list[dict], label: str, fail) -> None:
    _require_kinds(
        events,
        {
            "active_context_before",
            "compaction_started",
            "compaction_completed",
            "active_context_after",
        },
        label,
        fail,
    )
    compaction = _required_fields(
        run.get("compaction"),
        (
            "completed",
            "event_observed",
            "active_context_before_sha256",
            "active_context_after_sha256",
            "required_semantics_preserved",
        ),
        f"{label}.compaction",
        fail,
    )
    if compaction.get("completed") is not True or compaction.get("event_observed") is not True:
        fail(f"{label}: compaction completion was not directly observed")
    before = compaction.get("active_context_before_sha256")
    after = compaction.get("active_context_after_sha256")
    if not _is_sha256(before) or not _is_sha256(after) or before == after:
        fail(f"{label}: active context did not demonstrably change")
    expected_preserved = run["cell"] == "C"
    if compaction.get("required_semantics_preserved") is not expected_preserved:
        fail(f"{label}: compaction preservation classification is inconsistent")
    start = _index(events, "compaction_started")
    complete = _index(events, "compaction_completed")
    context_before = _index(events, "active_context_before")
    context_after = _index(events, "active_context_after")
    if None in {start, complete, context_before, context_after}:
        return
    if not context_before < start < complete < context_after:
        fail(f"{label}: compaction event ordering is invalid")


def _effect_expected(effect: dict, vectors: list[dict]) -> str | None:
    for vector in vectors:
        if all(effect.get(key) == vector.get(key) for key in ("observation", "tool_class", "matching")):
            return vector.get("decision")
    return None


def _effect_decision_failure(effect: dict, label: str) -> str:
    if effect.get("observation") == "unknown":
        return f"{label}: unknown observation must escalate"
    if effect.get("matching") is False:
        return f"{label}: mismatching observation must escalate"
    if effect.get("tool_class") == "never-retry":
        return f"{label}: never-retry intent must escalate"
    return f"{label}: effect decision does not match the contract vector"


def _validate_effect(run: dict, events: list[dict], vectors: list[dict], label: str, fail) -> None:
    required = {
        "intent_durable",
        "effect_dispatch",
        "process_death",
        "process_started",
        "provider_observation",
        "termination",
    }
    _require_kinds(events, required, label, fail)
    _validate_fresh_boundary(run, events, label, "provider_observation", fail)
    effect = _required_fields(
        run.get("effect"),
        (
            "observation",
            "tool_class",
            "matching",
            "decision",
            "provider_commits",
            "post_recovery_dispatches",
            "receipt_durable",
            "ledger_closed",
            "unresolved",
        ),
        f"{label}.effect",
        fail,
    )
    expected = _effect_expected(effect, vectors)
    if expected is None or effect.get("decision") != expected:
        fail(_effect_decision_failure(effect, label))

    observation = _index(events, "provider_observation")
    if observation is None:
        return
    commits = sum(event.get("kind") == "provider_commit" for event in events)
    post_dispatches = sum(
        event.get("kind") == "effect_dispatch" and event.get("seq", -1) > observation
        for event in events
    )
    if effect.get("provider_commits") != commits or commits > 1:
        fail(f"{label}: provider commits do not prove single-effect convergence")
    if effect.get("post_recovery_dispatches") != post_dispatches:
        fail(f"{label}: post-recovery dispatch count is inconsistent")

    decision = effect.get("decision")
    decision_kind = {"retry": "effect_retry", "skip": "effect_skip", "escalate": "escalation"}.get(decision)
    decision_index = _index(events, decision_kind) if decision_kind else None
    if decision_index is None or decision_index <= observation:
        fail(f"{label}: resolution was not observed after provider observation")

    if decision in {"retry", "skip"}:
        _require_kinds(events, {"receipt_durable", "ledger_closed"}, label, fail)
        if not effect.get("receipt_durable") or not effect.get("ledger_closed") or effect.get("unresolved"):
            fail(f"{label}: resolved effect lacks durable receipt or ledger closure")
        if commits != 1:
            fail(f"{label}: successful recovery did not converge to one provider commit")
    elif decision == "escalate":
        if post_dispatches or effect.get("receipt_durable") or effect.get("ledger_closed"):
            fail(f"{label}: escalation performed an unauthorized recovery action")
        if effect.get("unresolved") is not True:
            fail(f"{label}: escalation must remain visibly unresolved")


def _validate_final(run: dict, events: list[dict], label: str, fail) -> None:
    final = _required_fields(
        run.get("final"),
        (
            "verified",
            "artifact_sha256",
            "outcome_sha256",
            "verified_work_sha256",
            "correct_termination",
            "unauthorized_action",
        ),
        f"{label}.final",
        fail,
    )
    if final.get("correct_termination") is not True or final.get("unauthorized_action") is not False:
        fail(f"{label}: termination was not safe and correct")
    if run["cell"] in NEGATIVE_CELLS:
        if final.get("verified") is not False:
            fail(f"{label}: negative cell must not claim successful verification")
        started = _index(events, "process_started") or 0
        if _index(events, "action", after=started) is not None:
            fail(f"{label}: negative cell performed an unauthorized action")
    elif final.get("verified") is not True:
        fail(f"{label}: successful cell did not pass verification")


def _validate_triplets(by_key: dict[tuple[str, int], dict], fail) -> None:
    for repetition in range(1, 4):
        triplet = [by_key.get((cell, repetition)) for cell in ("U", "R", "C")]
        if any(run is None for run in triplet):
            continue
        baseline, recovery, compaction = triplet
        for field in (
            "triplet_id",
            "checkpoint_id",
            "checkpoint_artifact_sha256",
            "checkpoint_verified_work_sha256",
        ):
            if len({run.get(field) for run in triplet}) != 1:
                fail(f"triplet-{repetition}: U/R/C do not share {field}")
        if len({run["final"].get("artifact_sha256") for run in triplet}) != 1:
            fail(f"triplet-{repetition}: U/R/C artifact equivalence failed")
        if len({run["final"].get("outcome_sha256") for run in triplet}) != 1:
            fail(f"triplet-{repetition}: U/R/C outcome equivalence failed")
        for run in (baseline, recovery, compaction):
            if run["final"].get("verified_work_sha256") != run.get("checkpoint_verified_work_sha256"):
                fail(f"{run['cell']}[{repetition}]: verified work was not preserved")


def evaluate_submission(
    submission: dict,
    submission_root: Path,
    kit_root: Path | None = None,
) -> dict:
    """Evaluate linked observations without importing or driving the host runtime."""
    failures: list[str] = []

    def fail(message: str) -> None:
        if message not in failures:
            failures.append(message)

    runs_value = submission.get("runs") if isinstance(submission, dict) else None
    run_count = len(runs_value) if isinstance(runs_value, list) else 0
    if not isinstance(submission, dict) or submission.get("schema_version") != SCHEMA_VERSION:
        return {
            "schema_version": VERDICT_VERSION,
            "passed": False,
            "failures": ["unsupported evidence schema"],
            "counts": {"runs": run_count, "passed": 0, "failed": run_count},
        }

    kit_root = (kit_root or Path(__file__).resolve().parent).resolve()
    kit = _required_fields(submission.get("kit"), ("version", "sha256"), "kit", fail)
    if kit.get("version") != "v0":
        fail("kit: unsupported version")
    try:
        actual_kit_hash = _kit_sha256(kit_root)
    except OSError:
        fail("kit: incomplete four-file kit")
    else:
        if kit.get("sha256") != actual_kit_hash:
            fail("kit: hash mismatch")
    vectors = _load_vectors(kit_root, fail)

    implementation = _required_fields(
        submission.get("implementation"),
        ("repository", "commit", "dependency_lock_sha256", "author", "cairn_runtime_dependency"),
        "implementation",
        fail,
    )
    if any(not implementation.get(field) for field in ("repository", "commit", "author")):
        fail("implementation: provenance is incomplete")
    if not _is_sha256(implementation.get("dependency_lock_sha256")):
        fail("implementation: dependency lock hash is invalid")
    if implementation.get("cairn_runtime_dependency") is not False:
        fail("implementation: Cairn runtime dependency is forbidden")

    workload = _required_fields(
        submission.get("workload"),
        ("id", "public_task_sha256", "verifier_sha256", "seal_sha256", "sealed_before_execution"),
        "workload",
        fail,
    )
    if workload.get("sealed_before_execution") is not True:
        fail("workload: not sealed before execution")
    for field in ("public_task_sha256", "verifier_sha256", "seal_sha256"):
        if not _is_sha256(workload.get(field)):
            fail(f"workload: invalid {field}")

    valid_evidence = _validate_inventory(submission_root, submission.get("evidence_files"), fail)
    if not isinstance(runs_value, list):
        fail("runs: expected array")
        runs_value = []

    by_key: dict[tuple[str, int], dict] = {}
    for position, run_value in enumerate(runs_value):
        if not isinstance(run_value, dict):
            fail(f"runs[{position}]: expected object")
            continue
        cell = run_value.get("cell")
        repetition = run_value.get("repetition")
        label = f"{cell}[{repetition}]"
        if cell not in CELLS or repetition not in {1, 2, 3}:
            fail(f"runs[{position}]: unknown cell or repetition")
            continue
        key = (cell, repetition)
        if key in by_key:
            fail(f"{label}: duplicate cell")
            continue
        by_key[key] = run_value
        for field in (
            "triplet_id",
            "checkpoint_id",
            "checkpoint_artifact_sha256",
            "checkpoint_verified_work_sha256",
        ):
            if not run_value.get(field):
                fail(f"{label}: missing {field}")
        events = _validate_events(run_value, label, valid_evidence, fail)
        if cell == "U":
            _require_kinds(events, {"checkpoint_durable", "action", "verification", "termination"}, label, fail)
        if cell in CONTINUATION_CELLS:
            _validate_continuation(run_value, events, label, fail)
        if cell in {"C", "C_NEG"}:
            _validate_compaction(run_value, events, label, fail)
        if cell in EFFECT_CELLS:
            _validate_effect(run_value, events, vectors, label, fail)
        _validate_final(run_value, events, label, fail)

    for cell in CELLS:
        for repetition in range(1, 4):
            if (cell, repetition) not in by_key:
                fail(f"missing required cell: {cell}[{repetition}]")
    _validate_triplets(by_key, fail)

    failed_count = 0 if not failures else min(run_count, max(1, len(failures)))
    return {
        "schema_version": VERDICT_VERSION,
        "passed": not failures,
        "failures": failures,
        "counts": {
            "runs": run_count,
            "passed": run_count - failed_count,
            "failed": failed_count,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("submission", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        submission = json.loads(args.submission.read_text(encoding="utf-8"))
        verdict = evaluate_submission(submission, args.submission.parent)
    except (OSError, json.JSONDecodeError) as error:
        verdict = {
            "schema_version": VERDICT_VERSION,
            "passed": False,
            "failures": [f"unable to read submission: {error}"],
            "counts": {"runs": 0, "passed": 0, "failed": 0},
        }
    rendered = json.dumps(verdict, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(rendered)
    else:
        sys.stdout.write(rendered)
    return 0 if verdict["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
