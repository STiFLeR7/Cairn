"""Read-only Phase 2 evidence helpers.

These functions classify RecoveryBench records; they do not change prompts,
fixtures, verification, continuation state, or recovery behavior.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
import shutil
import uuid

from ..model import StepRecord
from ..recovery import regrounded_history
from ..state import ContinuationState, VerificationItem


@dataclass(frozen=True)
class CompactedContinuation:
    """A fresh-agent input reconstructed from a compacted state only."""

    goal: str
    prompt: str
    state: ContinuationState
    history: list[StepRecord]


def compacted_continuation(checkpoint: ContinuationState) -> CompactedContinuation:
    """Compact an actual checkpoint, serialize it, and re-ground without its transcript."""
    payload = checkpoint.to_dict()
    tail = payload["elastic_tail"]
    tail["recent_steps"] = tail.get("recent_steps", [])[-1:]
    tail["scratch"] = f"compacted@{checkpoint.durable_core.provenance.step_index + 1}"
    fresh_state = ContinuationState.from_json(json.dumps(payload))
    return CompactedContinuation(
        fresh_state.durable_core.intent.root_goal,
        continuation_prompt(fresh_state),
        fresh_state,
        regrounded_history(fresh_state.durable_core.plan),
    )


def continuation_prompt(state: ContinuationState) -> str:
    """Render only durable operational facts for a fresh coding-agent turn."""
    core = state.durable_core
    lines = [f"GOAL:\n{core.intent.root_goal}"]
    if core.intent.active_subgoal:
        lines.append(f"ACTIVE SUBGOAL: {core.intent.active_subgoal}")
    if core.decisions:
        lines.append("DECISIONS:\n" + "\n".join(
            f"- {item.decision}: {item.rationale}".rstrip(": ") for item in core.decisions
        ))
    if core.verification:
        lines.append("VERIFICATION:\n" + "\n".join(
            f"- {item.target}: {item.result}" for item in core.verification
        ))
    if core.world.digest:
        lines.append("WORLD:\n" + "\n".join(f"- {name}: {digest}" for name, digest in core.world.digest.items()))
    return "\n\n".join(lines)


def ablated_continuation(checkpoint: ContinuationState, field: str) -> CompactedContinuation:
    """Build one compaction ablation without changing the original checkpoint."""
    payload = checkpoint.to_dict()
    core = payload["durable_core"]
    if field == "intent":
        core["intent"] = {}
    elif field in ("plan", "decisions", "verification"):
        core[field] = []
    elif field == "world":
        core["world"] = {}
    else:
        raise ValueError(f"unknown continuation-state field: {field}")
    return compacted_continuation(ContinuationState.from_dict(payload))


def run_live_urc(base_dir: Path, fixture_name: str, *, split_step: int, config, ablate: str = "",
                 evidence_path: Path | None = None, prefix_mode: str = "live",
                 prompt_composition: str = "legacy", verification_mode: str = "empty") -> dict:
    """Run independent uninterrupted, RGR, and compacted fresh-agent continuations."""
    from . import recoverybench

    fixture = recoverybench.load_fixture(fixture_name)
    if not 0 <= split_step < fixture.work_units - 1:
        raise ValueError("split_step must be a non-terminal work unit")
    if prefix_mode not in {"live", "control"}:
        raise ValueError("prefix_mode must be live or control")
    if prompt_composition not in {"legacy", "single_goal"}:
        raise ValueError("prompt_composition must be legacy or single_goal")
    if verification_mode not in {"empty", "progress"}:
        raise ValueError("verification_mode must be empty or progress")
    wire = {"live": asdict(config)}
    goal = recoverybench._live_goal(fixture)
    run_dir = Path(base_dir) / f"urc-{uuid.uuid4().hex}"

    def prepare_prefix():
        prefix_root = run_dir / "prefix"
        root = fixture.copy_to(prefix_root)
        world = recoverybench._live_world(root, prefix_root, wire)
        store = recoverybench.CheckpointStore(str(prefix_root / "checkpoints"))
        ledger = recoverybench.EffectLedger(str(prefix_root / "effects.jsonl"), "prefix")
        history: list[StepRecord] = []
        provider = (
            recoverybench._live_provider(wire, fixture, prefix_root / "prefix.transcript.jsonl")
            if prefix_mode == "live" else None
        )
        for step in range(split_step + 1):
            if prefix_mode == "control":
                recoverybench.run_control_step(
                    goal, fixture, world, store, ledger, run_id="prefix", step=step, history=history,
                )
            else:
                recoverybench.run_live_step(
                    goal, fixture, world, store, ledger, provider, run_id="prefix", step=step,
                    history=history, model_version=config.model,
                )
        return root, list(history)

    prefix_root, prefix_history = prepare_prefix()

    def continuation_input(state: ContinuationState) -> str:
        prompt = continuation_prompt(state)
        return prompt.removeprefix("GOAL:\n") if prompt_composition == "single_goal" else prompt

    def materialize(name: str):
        run_root = run_dir / name
        root = run_root / fixture.name
        shutil.copytree(prefix_root, root)
        world = recoverybench._live_world(root, run_root, wire)
        store = recoverybench.CheckpointStore(str(run_root / "checkpoints"))
        ledger = recoverybench.EffectLedger(str(run_root / "effects.jsonl"), name)
        state = recoverybench.checkpoint(
            goal, list(prefix_history), world, store, ledger, step=split_step,
            model_version=config.model, harness_version=recoverybench.HARNESS_VERSION,
        )
        if verification_mode == "progress":
            state.durable_core.verification = [
                VerificationItem(target=f"step:{record.step}", result="pass", at_step=record.step)
                for record in prefix_history if record.returncode == 0
            ]
            store.checkpoint(state, state.durable_core.world.snapshot_id, state.durable_core.effects_ref.offset)
        return run_root, root, world, store, ledger, list(prefix_history), state

    def finish(name: str, prompt: str, history: list[StepRecord], prepared) -> dict:
        run_root, root, world, store, ledger, _, state = prepared
        provider = recoverybench._live_provider(wire, fixture, run_root / "continuation.transcript.jsonl")
        for step in range(split_step + 1, fixture.work_units):
            recoverybench.run_live_step(
                prompt, fixture, world, store, ledger, provider, run_id=name, step=step,
                history=history, model_version=config.model,
            )
        return {
            "success": fixture.verify(root).passed,
            "work_units": fixture.progress(root),
            "history_length": len(history),
            "state_digest": state.durable_core.world.digest,
        }

    def run_branch(name: str) -> dict:
        try:
            prepared = materialize(name)
            if name == "U":
                return finish(name, goal, list(prepared[5]), prepared)
            if name == "R":
                regrounded = recoverybench.recover(prepared[2], prepared[3], prepared[4])
                return finish(name, continuation_input(prepared[6]), regrounded.history, prepared)
            branch = ablated_continuation(prepared[6], ablate) if ablate else compacted_continuation(prepared[6])
            result = finish(name, continuation_input(branch.state), branch.history, prepared)
            result["original_transcript_available"] = False
            result["prompt_has_durable_state"] = bool(branch.state.durable_core.world.digest)
            return result
        except Exception as exc:
            return {"success": False, "invalid": f"{type(exc).__name__}: {exc}"}

    record = {
        "schema_version": "cairn.phase-2-urc.v0.1",
        "fixture": {"name": fixture.name, "version": fixture.version},
        "run_id": run_dir.name,
        "split_step": split_step,
        "prefix": {"mode": prefix_mode, "work_units": split_step + 1},
        "prompt_composition": prompt_composition,
        "verification_mode": verification_mode,
        "ablation": ablate or None,
        "live": {"provider": config.provider, "model": config.model},
        "branches": {},
    }
    for name in ("U", "R", "C"):
        record["branches"][name] = run_branch(name)
        if evidence_path is not None:
            evidence_path.parent.mkdir(parents=True, exist_ok=True)
            evidence_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def capture_live_urc(base_dir: Path, fixture_name: str, *, split_step: int, config, ablate: str = "",
                     evidence_path: Path | None = None, prefix_mode: str = "live",
                     prompt_composition: str = "legacy", verification_mode: str = "empty") -> dict:
    """Return a raw evidence record even when a live branch cannot reach a checkpoint."""
    try:
        return run_live_urc(
            base_dir, fixture_name, split_step=split_step, config=config, ablate=ablate,
            evidence_path=evidence_path, prefix_mode=prefix_mode,
            prompt_composition=prompt_composition, verification_mode=verification_mode,
        )
    except Exception as exc:
        record = {
            "schema_version": "cairn.phase-2-urc.v0.1",
            "fixture": {"name": fixture_name, "version": "2"},
            "split_step": split_step,
            "prefix": {"mode": prefix_mode},
            "prompt_composition": prompt_composition,
            "verification_mode": verification_mode,
            "ablation": ablate or None,
            "live": {"provider": config.provider, "model": config.model},
            "invalid": {"stage": "urc", "detail": f"{type(exc).__name__}: {exc}"},
        }
        if evidence_path is not None:
            evidence_path.parent.mkdir(parents=True, exist_ok=True)
            evidence_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        return record


def freeze_phase_one_controls(paths: list[Path]) -> dict:
    """Return a hash-pinned, read-only description of Phase 1 evidence."""
    records: list[dict] = []
    artifacts = []
    for path in paths:
        content = path.read_bytes()
        rows = [json.loads(line) for line in content.decode("utf-8").splitlines() if line.strip()]
        records.extend(rows)
        artifacts.append({
            "path": path.name,
            "records": len(rows),
            "sha256": hashlib.sha256(content).hexdigest(),
        })
    return {
        "schema_version": "cairn.phase-2-control-freeze.v0.1",
        "artifacts": artifacts,
        "records": len(records),
        "diagnosis": diagnose_phase_one_records(records),
    }


def diagnose_phase_one_records(records: list[dict]) -> dict:
    """Separate pre-checkpoint failures from recovery-path failures."""
    counts = Counter()
    reasons = Counter()
    for record in records:
        counts["attempted"] += 1
        invalid = record.get("invalid")
        if invalid:
            stage = invalid.get("stage", "unknown")
            reason = _reason(invalid.get("detail", ""))
            if reason:
                reasons[reason] += 1
            if stage == "baseline":
                counts["baseline_completion_failures"] += 1
            elif stage == "crash":
                counts["checkpoint_acquisition_failures"] += 1
            elif stage == "resume":
                counts["recovery_path_failures"] += 1
            else:
                counts["unattributed_failures"] += 1
            continue
        outcome = record.get("outcome", {})
        if not outcome.get("baseline_success"):
            counts["baseline_completion_failures"] += 1
        elif not outcome.get("recovery_success"):
            counts["recovery_path_failures"] += 1
        else:
            counts["recovered_successes"] += 1
    return {
        key: counts[key]
        for key in (
            "attempted", "baseline_completion_failures", "checkpoint_acquisition_failures",
            "recovery_path_failures", "recovered_successes", "unattributed_failures",
        )
    } | {"failure_reasons": dict(sorted(reasons.items()))}


def summarize_urc_records(records: list[dict]) -> dict:
    """Count eligible U/R/C controls without treating model failures as recovery failures."""
    counts = Counter(attempted=0, complete_records=0, incomplete_records=0,
                     baseline_eligible=0, ineligible_baseline=0, recovery_successes=0,
                     compaction_successes=0, complete_triplets=0)
    for record in records:
        counts["attempted"] += 1
        branches = record.get("branches", {})
        if not all(name in branches for name in ("U", "R", "C")):
            counts["incomplete_records"] += 1
            continue
        counts["complete_records"] += 1
        if not branches.get("U", {}).get("success"):
            counts["ineligible_baseline"] += 1
            continue
        counts["baseline_eligible"] += 1
        recovered = branches.get("R", {}).get("success", False)
        compacted = branches.get("C", {}).get("success", False)
        counts["recovery_successes"] += recovered
        counts["compaction_successes"] += compacted
        counts["complete_triplets"] += recovered and compacted
    return dict(counts)


def matrix_cells(protocol: dict) -> list[dict]:
    """Enumerate the protocol's fixed unablated cells in deterministic order."""
    from .recoverybench import load_fixture

    matrix = protocol["matrix"]
    cells = []
    for model in matrix["models"]:
        for repetition in range(1, matrix["repetitions_per_model_fixture_split"] + 1):
            for fixture_name in matrix["fixtures"]:
                fixture = load_fixture(fixture_name)
                for split_step in range(fixture.work_units - 1):
                    cells.append({
                        "provider": model["provider"], "model": model["model"],
                        "fixture": fixture_name, "split_step": split_step, "repetition": repetition,
                    })
    return cells


def matrix_cell_stem(cell: dict) -> str:
    """Return a filesystem-safe, deterministic stem for one registered matrix cell."""
    model = re.sub(r"[^A-Za-z0-9_.-]", "_", cell["model"])
    return f"{model}-{cell['fixture']}-s{cell['split_step']}-r{cell['repetition']:02d}"


def _reason(detail: str) -> str:
    marker = "ValueError: "
    if marker not in detail:
        return ""
    return detail.rsplit(marker, 1)[-1].splitlines()[0].strip()
