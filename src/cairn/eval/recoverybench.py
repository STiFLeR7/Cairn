"""Pinned repository fixtures for the Phase 1 recovery control."""

from __future__ import annotations

import base64
import json
import os
import runpy
import shutil
import subprocess
import sys
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

from ..model import CODE, Action, ModelProvider, StepRecord
from ..model_live import LiveModelProvider
from ..recovery import checkpoint, recover
from .metrics import no_regression
from ..runtime.checkpoint_store import CheckpointStore
from ..runtime.effect_ledger import EffectLedger
from ..runtime.sandbox_docker import DockerTerminalSandbox
from ..worlds import TerminalWorld

FIXTURES_DIR = Path(__file__).resolve().parents[3] / "benchmarks" / "recoverybench_fixtures"
BENCHMARK_SCRIPT = Path(__file__).resolve().parents[3] / "benchmarks" / "recoverybench.py"
INJECTED_FAILURE_EXIT = 91
HARNESS_VERSION = "recoverybench.v0.2"


@dataclass(frozen=True)
class VerificationReceipt:
    passed: bool


@dataclass(frozen=True)
class CleanCheckpoint:
    run_id: str
    checkpoint_id: str
    step: int
    work_units: int
    digest: dict[str, str]
    provenance: dict[str, str]


@dataclass(frozen=True)
class FailureReceipt:
    fired: bool
    worker_pid: int
    exit_code: int
    checkpoint: CleanCheckpoint


@dataclass(frozen=True)
class RecoveryReceipt:
    worker_pid: int
    used_in_memory_history: bool
    resume_plan_clean: bool
    work_units: int
    recovery_units: int
    digest: dict[str, str]


@dataclass(frozen=True)
class BaselineReceipt:
    worker_pid: int
    work_units: int
    digest: dict[str, str]


@dataclass(frozen=True)
class LivePilotEvidence:
    valid_fired_pairs: int
    model_configurations: tuple[str, ...]
    recovered_success: float
    baseline_success: float
    effect_duplicates: int
    external_models: bool = False


@dataclass(frozen=True)
class LiveRunConfig:
    provider: str
    model: str
    max_calls: int = 12
    max_chars: int = 100_000
    max_tokens: int = 4096


class LiveRunFailure(RuntimeError):
    def __init__(self, stage: str, run_root: Path, detail: str) -> None:
        super().__init__(detail)
        self.stage = stage
        self.run_root = run_root


@dataclass(frozen=True)
class GateVerdict:
    deterministic_cells_pass: bool
    deterministic_fidelity: bool
    durable_failure_receipts: bool
    live_sample_size: bool
    live_fidelity: bool
    artifacts_published: bool
    adapter_adopted: bool

    @property
    def passed(self) -> bool:
        return all((
            self.deterministic_cells_pass,
            self.deterministic_fidelity,
            self.durable_failure_receipts,
            self.live_sample_size,
            self.live_fidelity,
            self.artifacts_published,
            self.adapter_adopted,
        ))


@dataclass(frozen=True)
class PairedControlResult:
    fixture: "RepositoryFixture"
    fault_step: int
    failure: FailureReceipt
    recovery: RecoveryReceipt
    baseline: BaselineReceipt
    verification: VerificationReceipt

    def to_record(self) -> dict:
        artifact_equivalence = self.recovery.digest == self.baseline.digest
        return {
            "schema_version": "recoverybench.v0.1",
            "fixture": {"name": self.fixture.name, "version": self.fixture.version},
            "fault_step": self.fault_step,
            "failure": asdict(self.failure),
            "checkpoint": asdict(self.failure.checkpoint),
            "baseline": asdict(self.baseline),
            "recovery": asdict(self.recovery),
            "verification": asdict(self.verification),
            "fidelity": {
                "task_success": self.verification.passed,
                "artifact_equivalence": artifact_equivalence,
                "solution_quality": float(artifact_equivalence),
                "no_regression": no_regression(
                    self.recovery.recovery_units,
                    self.failure.checkpoint.work_units,
                    self.baseline.work_units,
                ),
                "effect_duplicates": 0,
                "recovery_tax": self.recovery.recovery_units,
            },
        }


@dataclass(frozen=True)
class RepositoryFixture:
    name: str
    version: str
    work_units: int
    source: Path
    steps: tuple[str, ...]

    def copy_to(self, destination: Path) -> Path:
        root = destination / self.name
        shutil.copytree(self.source, root)
        return root

    def progress(self, root: Path) -> int:
        return _PROGRESS[self.name](root)

    def apply_control_action(self, root: Path, step: int) -> None:
        if step != self.progress(root):
            raise ValueError("control actions must advance sequentially")
        (root / "project.py").write_text(self.steps[step], encoding="utf-8")

    def single_unit_advance(self, previous_progress: int, root: Path) -> bool:
        return self.progress(root) == previous_progress + 1

    def control_command(self, step: int, *, interpreter: str = sys.executable) -> str:
        payload = base64.b64encode(self.steps[step].encode("utf-8")).decode("ascii")
        code = (
            "import base64; from pathlib import Path; "
            f"Path('project.py').write_bytes(base64.b64decode('{payload}'))"
        )
        return f'"{interpreter}" -c "{code}"'

    def verify(self, root: Path) -> VerificationReceipt:
        return VerificationReceipt(self.progress(root) == self.work_units)


def load_fixture(name: str) -> RepositoryFixture:
    steps = _FIXTURE_STEPS.get(name)
    if steps is None:
        raise ValueError(f"unknown recoverybench fixture: {name}")
    source = FIXTURES_DIR / name
    return RepositoryFixture(name=name, version="2", work_units=len(steps), source=source, steps=steps)


def run_control_step(
    goal, fixture, world, store, ledger, *, run_id: str, step: int,
    command: str | None = None, history: list[StepRecord] | None = None,
) -> CleanCheckpoint:
    root = Path(world.workspace_dir)
    before = fixture.progress(root)
    command = command or fixture.control_command(step, interpreter=world.interpreter)
    result = world.execute(command)
    if not result.ok:
        raise ValueError("command_failed")
    if not fixture.single_unit_advance(before, root):
        raise ValueError("unverified_progress")
    history = history if history is not None else []
    history.append(StepRecord(step=step, action=Action(kind=CODE, code=command), returncode=result.returncode))
    state = checkpoint(
        goal, history, world, store, ledger, step=step,
        model_version="control", harness_version=HARNESS_VERSION,
    )
    checkpoint_id = store.latest_id()
    if checkpoint_id is None:
        raise RuntimeError("checkpoint_not_durable")
    return CleanCheckpoint(
        run_id=run_id,
        checkpoint_id=checkpoint_id,
        step=step,
        work_units=fixture.progress(root),
        digest=world.digest(),
        provenance={
            "harness_version": state.durable_core.provenance.harness_version,
            "model_version": state.durable_core.provenance.model_version,
        },
    )


def run_live_step(
    goal, fixture, world, store, ledger, provider: ModelProvider, *, run_id: str, step: int,
    history: list[StepRecord], model_version: str, max_attempts: int = 4,
) -> CleanCheckpoint:
    """Reach one clean checkpoint, allowing read-only terminal inspection beforehand."""
    root = Path(world.workspace_dir)
    before = fixture.progress(root)
    turn_history = list(history)
    for _ in range(max_attempts):
        action = provider.propose(goal, turn_history)
        if action.kind != CODE or not action.code:
            raise ValueError("model_finished_before_verification")
        digest = world.digest()
        payload = base64.b64encode(action.code.encode("utf-8")).decode("ascii")
        command = f'"{world.interpreter}" -c "import base64; exec(base64.b64decode(\'{payload}\'))"'
        result = world.execute(command)
        record = StepRecord(
            step=step,
            action=action,
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )
        if not result.ok:
            if world.digest() != digest:
                raise ValueError("unverified_mutation")
            turn_history.append(record)
            continue
        if fixture.progress(root) == before:
            if world.digest() != digest:
                raise ValueError("unverified_mutation")
            turn_history.append(record)
            continue
        if not fixture.single_unit_advance(before, root):
            raise ValueError("unverified_progress")
        history.append(record)
        break
    else:
        raise ValueError("model_no_verified_progress")
    state = checkpoint(
        goal, history, world, store, ledger, step=step,
        model_version=model_version, harness_version=HARNESS_VERSION,
    )
    checkpoint_id = store.latest_id()
    if checkpoint_id is None:
        raise RuntimeError("checkpoint_not_durable")
    return CleanCheckpoint(
        run_id=run_id,
        checkpoint_id=checkpoint_id,
        step=step,
        work_units=fixture.progress(root),
        digest=world.digest(),
        provenance={
            "harness_version": state.durable_core.provenance.harness_version,
            "model_version": state.durable_core.provenance.model_version,
        },
    )


def run_paired_control(base_dir: Path, fixture_name: str, fault_step: int) -> PairedControlResult:
    Path(base_dir).mkdir(parents=True, exist_ok=True)
    fixture = load_fixture(fixture_name)
    if not 0 <= fault_step < fixture.work_units - 1:
        raise ValueError("fault_step must be a non-terminal work unit")

    run_root = Path(base_dir) / f"recoverybench-{uuid.uuid4().hex}"
    run_root.mkdir()
    _write_json(run_root / "run.json", {"run_id": run_root.name, "fixture": fixture_name, "fault_step": fault_step})
    baseline_root = run_root / "baseline"
    baseline_root.mkdir()
    _write_json(baseline_root / "run.json", {"run_id": f"{run_root.name}-baseline", "fixture": fixture_name})
    _run_worker("baseline", baseline_root, check=True)
    crashed = _run_worker("crash", run_root)
    if crashed.returncode != INJECTED_FAILURE_EXIT:
        raise RuntimeError(f"crash_worker_exit_{crashed.returncode}")
    _run_worker("resume", run_root, check=True)

    failure = _failure_from_dict(_read_json(run_root / "failure_fired.json"))
    recovery = _recovery_from_dict(_read_json(run_root / "recovery.json"))
    baseline = _baseline_from_dict(_read_json(baseline_root / "baseline.json"))
    verification = VerificationReceipt(**_read_json(run_root / "verification.json"))
    return PairedControlResult(
        fixture=fixture,
        fault_step=fault_step,
        failure=failure,
        recovery=recovery,
        baseline=baseline,
        verification=verification,
    )


def run_paired_live(
    base_dir: Path, fixture_name: str, fault_step: int, config: LiveRunConfig,
) -> PairedControlResult:
    Path(base_dir).mkdir(parents=True, exist_ok=True)
    if config.provider != "fake" and not DockerTerminalSandbox.available():
        raise RuntimeError("real live terminal execution requires an available Docker sandbox")
    fixture = load_fixture(fixture_name)
    if not 0 <= fault_step < fixture.work_units - 1:
        raise ValueError("fault_step must be a non-terminal work unit")

    run_root = Path(base_dir) / f"recoverybench-live-{uuid.uuid4().hex}"
    run_root.mkdir()
    live_config = asdict(config)
    _write_json(
        run_root / "run.json",
        {
            "run_id": run_root.name,
            "fixture": fixture_name,
            "fault_step": fault_step,
            "agent": "live",
            "live": live_config,
        },
    )
    baseline_root = run_root / "baseline"
    baseline_root.mkdir()
    _write_json(
        baseline_root / "run.json",
        {
            "run_id": f"{run_root.name}-baseline",
            "fixture": fixture_name,
            "agent": "live",
            "live": live_config,
        },
    )
    baseline_result = _run_worker("baseline", baseline_root)
    if baseline_result.returncode:
        _write_worker_failure("baseline", baseline_root, baseline_result)
        raise LiveRunFailure(
            "baseline", run_root,
            f"baseline_worker_exit_{baseline_result.returncode}: {baseline_result.stderr}",
        )
    crashed = _run_worker("crash", run_root)
    if crashed.returncode != INJECTED_FAILURE_EXIT:
        _write_worker_failure("crash", run_root, crashed)
        raise LiveRunFailure(
            "crash", run_root, f"crash_worker_exit_{crashed.returncode}: {crashed.stderr}",
        )
    resumed = _run_worker("resume", run_root)
    if resumed.returncode:
        _write_worker_failure("resume", run_root, resumed)
        raise LiveRunFailure(
            "resume", run_root, f"resume_worker_exit_{resumed.returncode}: {resumed.stderr}",
        )

    failure = _failure_from_dict(_read_json(run_root / "failure_fired.json"))
    recovery = _recovery_from_dict(_read_json(run_root / "recovery.json"))
    baseline = _baseline_from_dict(_read_json(baseline_root / "baseline.json"))
    verification = VerificationReceipt(**_read_json(run_root / "verification.json"))
    return PairedControlResult(
        fixture=fixture,
        fault_step=fault_step,
        failure=failure,
        recovery=recovery,
        baseline=baseline,
        verification=verification,
    )


def run_deterministic_matrix(base_dir: Path, repeats: int) -> list[PairedControlResult]:
    if repeats < 1:
        raise ValueError("repeats must be positive")
    Path(base_dir).mkdir(parents=True, exist_ok=True)
    results: list[PairedControlResult] = []
    for _ in range(repeats):
        for fixture_name in ("bugfix", "config", "tests", "followup"):
            fixture = load_fixture(fixture_name)
            for fault_step in range(fixture.work_units - 1):
                results.append(run_paired_control(base_dir, fixture_name, fault_step))
    return results


def run_live_matrix(
    base_dir: Path, configs: list[LiveRunConfig], repeats: int,
) -> list[dict]:
    if repeats < 1:
        raise ValueError("repeats must be positive")
    if not configs:
        raise ValueError("at least one live model configuration is required")
    records: list[dict] = []
    for config in configs:
        for _ in range(repeats):
            for fixture_name in ("bugfix", "config", "tests", "followup"):
                fixture = load_fixture(fixture_name)
                for fault_step in range(fixture.work_units - 1):
                    try:
                        record = run_paired_live(base_dir, fixture_name, fault_step, config).to_record()
                        record["outcome"] = {"baseline_success": True, "recovery_success": True}
                    except LiveRunFailure as failure:
                        record = {
                            "schema_version": "recoverybench.v0.1",
                            "fixture": {"name": fixture.name, "version": fixture.version},
                            "fault_step": fault_step,
                            "invalid": {
                                "stage": failure.stage,
                                "run_root": str(failure.run_root),
                                "detail": str(failure),
                            },
                            "outcome": {
                                "baseline_success": failure.stage != "baseline",
                                "recovery_success": False,
                            },
                        }
                    record["live"] = {"provider": config.provider, "model": config.model}
                    records.append(record)
    return records


def live_pilot_evidence(records: list[dict]) -> LivePilotEvidence:
    valid = [record for record in records if _record_is_valid(record)]
    live_records = [record for record in records if "live" in record]
    configurations = tuple(sorted({
        f"{record['live']['provider']}:{record['live']['model']}"
        for record in valid
        if "live" in record and "provider" in record["live"] and "model" in record["live"]
    }))
    providers = {record["live"]["provider"] for record in valid if "live" in record}
    return LivePilotEvidence(
        valid_fired_pairs=len(valid),
        model_configurations=configurations,
        recovered_success=_mean_outcome(live_records, "recovery_success"),
        baseline_success=_mean_outcome(live_records, "baseline_success"),
        effect_duplicates=sum(record["fidelity"]["effect_duplicates"] for record in valid),
        external_models=bool(configurations) and bool(providers) and all(
            provider != "fake" for provider in providers
        ),
    )


def write_records(records: list[dict], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(output.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, sort_keys=True) + "\n")
        file.flush()
        os.fsync(file.fileno())
    os.replace(tmp, output)


def deterministic_summary(records: list[dict]) -> dict:
    valid = [record for record in records if _record_is_valid(record)]
    total = len(records)
    n = len(valid)
    return {
        "total": total,
        "valid": n,
        "invalid": total - n,
        "task_success": _mean(valid, "task_success"),
        "artifact_equivalence": _mean(valid, "artifact_equivalence"),
        "no_regression": _mean(valid, "no_regression"),
    }


def phase_1_verdict(
    records: list[dict],
    *,
    live: LivePilotEvidence | None,
    artifacts_published: bool,
    adapter_adopted: bool,
) -> GateVerdict:
    valid = [record for record in records if _record_is_valid(record)]
    deterministic_cells_pass = bool(valid) and all(record["verification"]["passed"] for record in valid)
    deterministic_fidelity = bool(valid) and all(
        record["fidelity"]["artifact_equivalence"] == 1.0
        and record["fidelity"]["no_regression"] == 1.0
        for record in valid
    )
    durable_failure_receipts = bool(valid) and all(
        record["failure"]["fired"] and record["checkpoint"]["checkpoint_id"]
        for record in valid
    )
    live_sample_size = bool(
        live
        and live.external_models
        and live.valid_fired_pairs >= 40
        and len(set(live.model_configurations)) >= 2
    )
    live_fidelity = bool(
        live
        and live.recovered_success >= live.baseline_success - 0.10
        and live.effect_duplicates == 0
    )
    return GateVerdict(
        deterministic_cells_pass=deterministic_cells_pass,
        deterministic_fidelity=deterministic_fidelity,
        durable_failure_receipts=durable_failure_receipts,
        live_sample_size=live_sample_size,
        live_fidelity=live_fidelity,
        artifacts_published=artifacts_published,
        adapter_adopted=adapter_adopted,
    )


def normalize_record(record: dict) -> dict:
    normalized = json.loads(json.dumps(record))
    normalized["failure"].pop("worker_pid", None)
    normalized["baseline"].pop("worker_pid", None)
    normalized["recovery"].pop("worker_pid", None)
    normalized["checkpoint"].pop("run_id", None)
    normalized["failure"]["checkpoint"].pop("run_id", None)
    return normalized


def normalized_records_equal(first: Path, second: Path) -> bool:
    return _normalized_records(first) == _normalized_records(second)


def run_crash_worker(run_root: Path) -> int:
    config = _read_json(run_root / "run.json")
    if config.get("agent") == "live":
        return _run_live_crash_worker(run_root, config)
    fixture = load_fixture(config["fixture"])
    root = fixture.copy_to(run_root)
    world = TerminalWorld(str(root), str(run_root / "snapshots"))
    store = CheckpointStore(str(run_root / "checkpoints"))
    ledger = EffectLedger(str(run_root / "effects.jsonl"), config["run_id"])
    history: list[StepRecord] = []
    receipt = None
    for step in range(config["fault_step"] + 1):
        receipt = run_control_step(
            "complete the repository task", fixture, world, store, ledger,
            run_id=config["run_id"], step=step, history=history,
        )
    _write_json(
        run_root / "failure_fired.json",
        {"fired": True, "worker_pid": os.getpid(), "exit_code": INJECTED_FAILURE_EXIT, "checkpoint": asdict(receipt)},
    )
    return INJECTED_FAILURE_EXIT


def run_resume_worker(run_root: Path) -> int:
    if not (run_root / "failure_fired.json").is_file():
        return 2
    config = _read_json(run_root / "run.json")
    if config.get("agent") == "live":
        return _run_live_resume_worker(run_root, config)
    fixture = load_fixture(config["fixture"])
    root = run_root / fixture.name
    world = TerminalWorld(str(root), str(run_root / "snapshots"))
    store = CheckpointStore(str(run_root / "checkpoints"))
    ledger = EffectLedger(str(run_root / "effects.jsonl"), config["run_id"])
    regrounded = recover(world, store, ledger)
    history = regrounded.history
    start_units = fixture.progress(root)
    for step in range(start_units, fixture.work_units):
        run_control_step(
            "complete the repository task", fixture, world, store, ledger,
            run_id=config["run_id"], step=step, history=history,
        )
    verification = fixture.verify(root)
    _write_json(run_root / "verification.json", asdict(verification))
    _write_json(
        run_root / "recovery.json",
        {
            "worker_pid": os.getpid(),
            "used_in_memory_history": False,
            "resume_plan_clean": bool(regrounded.plan and regrounded.plan.clean),
            "work_units": fixture.progress(root),
            "recovery_units": fixture.progress(root) - start_units,
            "digest": world.digest(),
        },
    )
    return 0 if verification.passed else 3


def run_baseline_worker(run_root: Path) -> int:
    config = _read_json(run_root / "run.json")
    if config.get("agent") == "live":
        return _run_live_baseline_worker(run_root, config)
    fixture = load_fixture(config["fixture"])
    root = fixture.copy_to(run_root)
    world = TerminalWorld(str(root), str(run_root / "snapshots"))
    store = CheckpointStore(str(run_root / "checkpoints"))
    ledger = EffectLedger(str(run_root / "effects.jsonl"), config["run_id"])
    history: list[StepRecord] = []
    for step in range(fixture.work_units):
        run_control_step(
            "complete the repository task", fixture, world, store, ledger,
            run_id=config["run_id"], step=step, history=history,
        )
    verification = fixture.verify(root)
    _write_json(run_root / "verification.json", asdict(verification))
    _write_json(
        run_root / "baseline.json",
        {"worker_pid": os.getpid(), "work_units": fixture.progress(root), "digest": world.digest()},
    )
    return 0 if verification.passed else 3


def _live_goal(fixture: RepositoryFixture) -> str:
    task = (fixture.source / "README.md").read_text(encoding="utf-8")
    return (
        f"Complete this repository task:\n\n{task}\n\n"
        "Use Python terminal actions. You may inspect files read-only before an edit. Every "
        "mutation must derive from the current on-disk file content and advance exactly one "
        "independently verifiable task unit; never infer sibling source changes. Do not finish "
        "until the task is complete. Keep code short and parseable: for multi-line source text, "
        "use triple-quoted literals rather than a quoted string containing a literal newline."
    )


def _live_provider(config: dict, fixture: RepositoryFixture, transcript: Path) -> LiveModelProvider:
    live = LiveRunConfig(**config["live"])
    if live.provider == "fake":
        def transport(prompt: str) -> str:
            done = prompt.count("--- step ")
            if done >= fixture.work_units:
                return "TASK_COMPLETE"
            source = repr(fixture.steps[done])
            return f"```python\nfrom pathlib import Path\nPath('project.py').write_text({source})\n```"

        return LiveModelProvider(transport)
    from benchmarks.scenarios import build_live_transport

    return LiveModelProvider(
        build_live_transport(
            live.model,
            provider=live.provider,
            transcript_path=str(transcript),
            max_calls=live.max_calls,
            max_chars=live.max_chars,
            max_tokens=live.max_tokens,
        )
    )


def _live_world(root: Path, run_root: Path, config: dict) -> TerminalWorld:
    if config["live"]["provider"] == "fake":
        return TerminalWorld(str(root), str(run_root / "snapshots"))
    return TerminalWorld(
        str(root), str(run_root / "snapshots"), sandbox=DockerTerminalSandbox(), interpreter="python",
    )


def _run_live_crash_worker(run_root: Path, config: dict) -> int:
    fixture = load_fixture(config["fixture"])
    root = fixture.copy_to(run_root)
    world = _live_world(root, run_root, config)
    store = CheckpointStore(str(run_root / "checkpoints"))
    ledger = EffectLedger(str(run_root / "effects.jsonl"), config["run_id"])
    provider = _live_provider(config, fixture, run_root / "crash.transcript.jsonl")
    model_version = config["live"]["model"]
    history: list[StepRecord] = []
    receipt = None
    for step in range(config["fault_step"] + 1):
        receipt = run_live_step(
            _live_goal(fixture), fixture, world, store, ledger, provider, run_id=config["run_id"],
            step=step, history=history, model_version=model_version,
        )
    _write_json(
        run_root / "failure_fired.json",
        {"fired": True, "worker_pid": os.getpid(), "exit_code": INJECTED_FAILURE_EXIT, "checkpoint": asdict(receipt)},
    )
    return INJECTED_FAILURE_EXIT


def _run_live_resume_worker(run_root: Path, config: dict) -> int:
    fixture = load_fixture(config["fixture"])
    root = run_root / fixture.name
    world = _live_world(root, run_root, config)
    store = CheckpointStore(str(run_root / "checkpoints"))
    ledger = EffectLedger(str(run_root / "effects.jsonl"), config["run_id"])
    regrounded = recover(world, store, ledger)
    provider = _live_provider(config, fixture, run_root / "resume.transcript.jsonl")
    history = regrounded.history
    start_units = fixture.progress(root)
    for step in range(start_units, fixture.work_units):
        run_live_step(
            _live_goal(fixture), fixture, world, store, ledger, provider, run_id=config["run_id"],
            step=step, history=history, model_version=config["live"]["model"],
        )
    verification = fixture.verify(root)
    _write_json(run_root / "verification.json", asdict(verification))
    _write_json(
        run_root / "recovery.json",
        {
            "worker_pid": os.getpid(), "used_in_memory_history": False,
            "resume_plan_clean": bool(regrounded.plan and regrounded.plan.clean),
            "work_units": fixture.progress(root), "recovery_units": fixture.progress(root) - start_units,
            "digest": world.digest(),
        },
    )
    return 0 if verification.passed else 3


def _run_live_baseline_worker(run_root: Path, config: dict) -> int:
    fixture = load_fixture(config["fixture"])
    root = fixture.copy_to(run_root)
    world = _live_world(root, run_root, config)
    store = CheckpointStore(str(run_root / "checkpoints"))
    ledger = EffectLedger(str(run_root / "effects.jsonl"), config["run_id"])
    provider = _live_provider(config, fixture, run_root / "baseline.transcript.jsonl")
    history: list[StepRecord] = []
    for step in range(fixture.work_units):
        run_live_step(
            _live_goal(fixture), fixture, world, store, ledger, provider, run_id=config["run_id"],
            step=step, history=history, model_version=config["live"]["model"],
        )
    verification = fixture.verify(root)
    _write_json(run_root / "verification.json", asdict(verification))
    _write_json(
        run_root / "baseline.json",
        {"worker_pid": os.getpid(), "work_units": fixture.progress(root), "digest": world.digest()},
    )
    return 0 if verification.passed else 3


def _run_worker(role: str, run_root: Path, *, check: bool = False) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, str(BENCHMARK_SCRIPT), "--worker", role, "--run-root", str(run_root)],
        cwd=BENCHMARK_SCRIPT.parent.parent,
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode:
        raise RuntimeError(f"{role}_worker_exit_{result.returncode}: {result.stderr}")
    return result


def _write_worker_failure(
    stage: str, run_root: Path, result: subprocess.CompletedProcess[str],
) -> None:
    _write_json(
        run_root / "worker_failure.json",
        {
            "stage": stage,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        },
    )


def _write_json(path: Path, data: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as file:
        json.dump(data, file, sort_keys=True)
        file.flush()
        os.fsync(file.fileno())
    os.replace(tmp, path)


def _read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def _failure_from_dict(data: dict) -> FailureReceipt:
    return FailureReceipt(checkpoint=CleanCheckpoint(**data.pop("checkpoint")), **data)


def _recovery_from_dict(data: dict) -> RecoveryReceipt:
    return RecoveryReceipt(**data)


def _baseline_from_dict(data: dict) -> BaselineReceipt:
    return BaselineReceipt(**data)


def _record_is_valid(record: dict) -> bool:
    checkpoint = record.get("checkpoint", {})
    return bool(
        record.get("schema_version") == "recoverybench.v0.1"
        and record.get("failure", {}).get("fired") is True
        and checkpoint.get("checkpoint_id")
        and checkpoint.get("digest")
        and checkpoint.get("provenance")
        and record.get("baseline", {}).get("digest")
        and record.get("recovery", {}).get("digest")
        and record.get("verification", {}).get("passed") is not None
    )


def _mean(records: list[dict], field: str) -> float:
    if not records:
        return 0.0
    return sum(float(record["fidelity"][field]) for record in records) / len(records)


def _mean_outcome(records: list[dict], field: str) -> float:
    if not records:
        return 0.0
    return sum(bool(record.get("outcome", {}).get(field)) for record in records) / len(records)


def _normalized_records(path: Path) -> list[dict]:
    return [normalize_record(json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines()]


def _bugfix_progress(root: Path) -> int:
    project = _load_project(root)
    return sum((
        _call(project, "add", 2, 3) == 5 and _call(project, "add", -2, 3) == 1,
        _call(project, "multiply", 3, 4) == 12 and _call(project, "multiply", -2, 3) == -6,
        project.get("VERSION") == "1.0",
    ))


def _config_progress(root: Path) -> int:
    project = _load_project(root)
    return sum((
        project.get("DEBUG") is False,
        project.get("TIMEOUT") == 30,
        project.get("MODE") == "production",
    ))


def _tests_progress(root: Path) -> int:
    project = _load_project(root)
    return sum((
        _call(project, "is_nonempty", "x") is True and _call(project, "is_nonempty", "") is False,
        _call(project, "is_positive", 1) is True and _call(project, "is_positive", 0) is False,
        _call(project, "is_even", 4) is True and _call(project, "is_even", 3) is False,
        _call(project, "has_prefix", "cairn", "ca") is True and _call(project, "has_prefix", "cairn", "ai") is False,
    ))


def _followup_progress(root: Path) -> int:
    project = _load_project(root)
    return sum((
        _call(project, "normalize", "  cairn  ") == "cairn",
        _call(project, "is_valid", "x") is True and _call(project, "is_valid", "") is False,
        _call(project, "format_record", "x") == "record:x",
        _call(project, "count_items", ["a", "b"]) == 2,
        _call(project, "summarize", ["a", "b"]) == "a,b",
    ))


def _phase2_holdout_progress(root: Path) -> int:
    project = _load_project(root)
    return sum((
        _call(project, "normalize_key", "  Cairn Agent  ") == "cairn_agent",
        _call(project, "clamp", -1, 0, 5) == 0 and _call(project, "clamp", 6, 0, 5) == 5
        and _call(project, "clamp", 3, 0, 5) == 3,
        _call(project, "contains_token", "alpha beta", "beta") is True
        and _call(project, "contains_token", "alpha beta", "gamma") is False,
        _call(project, "render_tags", ["a", "b"]) == "[a|b]" and _call(project, "render_tags", []) == "[]",
    ))


def _load_project(root: Path) -> dict:
    try:
        return runpy.run_path(str(root / "project.py"))
    except Exception:  # verifier failure means no verified work unit
        return {}


def _call(project: dict, name: str, *args):
    try:
        return project[name](*args)
    except (KeyError, TypeError, ValueError):
        return None


_PROGRESS = {
    "bugfix": _bugfix_progress,
    "config": _config_progress,
    "tests": _tests_progress,
    "followup": _followup_progress,
    "phase2_holdout": _phase2_holdout_progress,
}


_FIXTURE_STEPS = {
    "bugfix": (
        "def add(a, b):\n    return a + b\n\ndef multiply(a, b):\n    return a - b\n",
        "def add(a, b):\n    return a + b\n\ndef multiply(a, b):\n    return a * b\n",
        "VERSION = '1.0'\n\ndef add(a, b):\n    return a + b\n\ndef multiply(a, b):\n    return a * b\n",
    ),
    "config": (
        "DEBUG = False\nTIMEOUT = 0\nMODE = 'development'\n",
        "DEBUG = False\nTIMEOUT = 30\nMODE = 'development'\n",
        "DEBUG = False\nTIMEOUT = 30\nMODE = 'production'\n",
    ),
    "tests": (
        "def is_nonempty(value):\n    return bool(value)\n\n"
        "def is_positive(value):\n    return False\n\n"
        "def is_even(value):\n    return False\n\n"
        "def has_prefix(value, prefix):\n    return False\n",
        "def is_nonempty(value):\n    return bool(value)\n\n"
        "def is_positive(value):\n    return value > 0\n\n"
        "def is_even(value):\n    return False\n\n"
        "def has_prefix(value, prefix):\n    return False\n",
        "def is_nonempty(value):\n    return bool(value)\n\n"
        "def is_positive(value):\n    return value > 0\n\n"
        "def is_even(value):\n    return value % 2 == 0\n\n"
        "def has_prefix(value, prefix):\n    return False\n",
        "def is_nonempty(value):\n    return bool(value)\n\n"
        "def is_positive(value):\n    return value > 0\n\n"
        "def is_even(value):\n    return value % 2 == 0\n\n"
        "def has_prefix(value, prefix):\n    return value.startswith(prefix)\n",
    ),
    "followup": (
        "def normalize(value):\n    return value.strip()\n\n"
        "def is_valid(value):\n    return False\n\n"
        "def format_record(value):\n    return value\n\n"
        "def count_items(values):\n    return 0\n\n"
        "def summarize(values):\n    return ''\n",
        "def normalize(value):\n    return value.strip()\n\n"
        "def is_valid(value):\n    return bool(value)\n\n"
        "def format_record(value):\n    return value\n\n"
        "def count_items(values):\n    return 0\n\n"
        "def summarize(values):\n    return ''\n",
        "def normalize(value):\n    return value.strip()\n\n"
        "def is_valid(value):\n    return bool(value)\n\n"
        "def format_record(value):\n    return f'record:{value}'\n\n"
        "def count_items(values):\n    return 0\n\n"
        "def summarize(values):\n    return ''\n",
        "def normalize(value):\n    return value.strip()\n\n"
        "def is_valid(value):\n    return bool(value)\n\n"
        "def format_record(value):\n    return f'record:{value}'\n\n"
        "def count_items(values):\n    return len(values)\n\n"
        "def summarize(values):\n    return ''\n",
        "def normalize(value):\n    return value.strip()\n\n"
        "def is_valid(value):\n    return bool(value)\n\n"
        "def format_record(value):\n    return f'record:{value}'\n\n"
        "def count_items(values):\n    return len(values)\n\n"
        "def summarize(values):\n    return ','.join(values)\n",
    ),
    "phase2_holdout": (
        "def normalize_key(value):\n    return '_'.join(value.strip().lower().split())\n\n"
        "def clamp(value, lower, upper):\n    return value\n\n"
        "def contains_token(value, token):\n    return False\n\n"
        "def render_tags(tags):\n    return ''\n",
        "def normalize_key(value):\n    return '_'.join(value.strip().lower().split())\n\n"
        "def clamp(value, lower, upper):\n    return max(lower, min(value, upper))\n\n"
        "def contains_token(value, token):\n    return False\n\n"
        "def render_tags(tags):\n    return ''\n",
        "def normalize_key(value):\n    return '_'.join(value.strip().lower().split())\n\n"
        "def clamp(value, lower, upper):\n    return max(lower, min(value, upper))\n\n"
        "def contains_token(value, token):\n    return token in value.split()\n\n"
        "def render_tags(tags):\n    return ''\n",
        "def normalize_key(value):\n    return '_'.join(value.strip().lower().split())\n\n"
        "def clamp(value, lower, upper):\n    return max(lower, min(value, upper))\n\n"
        "def contains_token(value, token):\n    return token in value.split()\n\n"
        "def render_tags(tags):\n    return '[' + '|'.join(tags) + ']'\n",
    ),
}
