# Public API reference

Everything below is re-exported from the top-level `cairn` package (`from cairn import ...`).
Cairn is **0.x**; this surface is stabilizing but not frozen until v1.0 (held — see the
[claims registry](../research/claims-registry.md)).

## Types

| Name | What it is |
|---|---|
| `Action` | One proposed step: `Action(kind, code="", result="")`. `kind` is `"code"` or `"finish"`. |
| `StepRecord` | An executed step: `StepRecord(step, action, returncode=0, stdout="", stderr="")`. The unit of `history`. |
| `Checkpoint` | A durable checkpoint (the "cairn"). Transparent alias of the internal `ContinuationState`. |
| `Regrounded` | Result of `recover()`: `.history`, `.resolutions`, `.plan` (`plan is None` ⇒ no checkpoint). |
| `Resolution` | What recovery did to one effect: `.key`, `.tool_class`, `.action` (`"redo"`/`"skip"`/`"escalate"`), `.detail`. |
| `ResumePlan` | The reconciled resume plan (torn-step + danger window) produced during `recover()`. |
| `AgentRun` | Outcome of `Agent.run`/`.resume`: `.finished`, `.steps`, `.checkpoints`, `.history`, `.final_state`, `.resumed`, `.recovery_tax`, `.resolutions`. |

## Contracts (Protocols you implement or accept)

| Name | Method surface |
|---|---|
| `World` | `snapshot() -> str`, `restore(snap_id) -> None`, `digest() -> dict`. (The `Agent` loop also needs `execute(code, cwd=None) -> ExecResult`.) |
| `CheckpointStore` | `checkpoint(state, snap_id, effect_offset) -> str`, `load_latest() -> tuple | None`. |
| `EffectLedger` | `append_effect(intent, key, tool_class, step)`, `complete_effect(key)`, `current_offset() -> int`, `list_effects_since(offset)`. |

## Effect safety

| Name | What it is |
|---|---|
| `EffectfulTool` | An injected irreversible effect: `EffectfulTool(name, tool_class, run=None, verify=None)`. |
| `EscalationRequired` | Raised when a `never-retry` effect is found in the danger window (unless `escalate=False`). |

## Reference implementations (bundled)

| Name | What it is |
|---|---|
| `Workspace` | A local-filesystem `World` (also executable). `Workspace(workspace_dir, snapshots_dir, sandbox=None, interpreter=None)`. |
| `FileCheckpointStore` | File-backed `CheckpointStore`. `FileCheckpointStore(ckpt_dir)`. |
| `FileEffectLedger` | Append-only file-backed `EffectLedger`. `FileEffectLedger(path, ledger_id="default")`. |

## Primitives (bring your own loop)

**`checkpoint(goal, history, world, store, ledger, *, step, model_version="", harness_version="") -> Checkpoint`**
Distill `history` into a cairn, snapshot the world, and persist atomically. Returns the durable
`Checkpoint`.

**`recover(world, store, ledger, *, effect_tools=None, escalate=True) -> Regrounded`**
The full RGR protocol: load latest checkpoint → `world.restore` → re-observe → reconcile the torn
step → resolve the effect danger window (exactly-once) → re-ground a minimal history. No durable
checkpoint ⇒ empty history (start fresh). The goal is carried in the checkpoint, not passed here.

**`regrounded_history(plan_steps) -> list[StepRecord]`**
Low-level helper: reconstruct a minimal history from a checkpoint's *done* steps (faithful
summaries, ~80 chars each — re-grounding, not byte-exact replay). Used internally by `recover()`.

## Opt-in loop (batteries-included)

**`Agent(model, world, *, store, ledger, effect_tools=None, max_steps=20, escalate=True, model_version="byom", harness_version="")`**
- `run(goal) -> AgentRun` — drive from scratch, checkpointing each executed step.
- `resume(goal) -> AgentRun` — re-ground via `recover()` and continue; falls back to `run` when
  there is no checkpoint.

## Version

`cairn.__version__` — the package version (currently `0.x`).
