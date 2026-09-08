# Phase 6 External Authority Handoff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish a standalone Phase 6 handoff package that lets separate implementer, sealer, and reproducer actors run an auditable conformance experiment on an immutable `D:/imgshape` snapshot.

**Architecture:** Keep the four-file conformance kit and admitted contracts unchanged. Add only a kit-local procedural guide and a chain-of-custody JSON template; host execution remains entirely implementation-owned, while the evaluator remains the existing copied `evaluate.py`.

**Tech Stack:** Markdown, JSON, SHA-256, PowerShell, Python standard library evaluator.

**Spec:** `docs/superpowers/specs/2026-09-07-p6-independent-ecosystem-conformance-design.md`

## Global Constraints

- Phase 6 remains `BLOCKED / UNADMITTED` until distinct external actors complete the chain.
- Do not edit P1-P5 contracts, Cairn runtime, adapters, Agent, state schemas, evaluator semantics, or effect behavior.
- Do not create a Cairn integration, a host command interface, or a generic state format.
- `D:/imgshape` is an external workload only; snapshot it read-only and never mutate, clean, reset, or restore it.
- IMPLEMENTER uses Claude Code with Haiku only and receives only the copied kit plus the released workload package.
- A failure is preserved and classified; no post-seal tuning is permitted.

---

### Task 1: Create the actor-executable handoff guide

**Files:**
- Create: `conformance/v0/PHASE6-EXTERNAL-HANDOFF.md`
- Modify: `conformance/v0/README.md`

**Interfaces:**
- Consumes: the four copied kit files, `INDEPENDENT-RUNNER.md`, and `evidence.schema.json`.
- Produces: a role-separated manual with an implementation-declared `IMPLEMENTATION_COMMAND` variable.

- [ ] **Step 1: State the exact objective and non-claim**

Write that the goal is one independently implemented host satisfying the existing 30-cell evaluator matrix on a reference and independently sealed holdout. State that evaluator acceptance alone is not admission and that no contract changes are allowed.

- [ ] **Step 2: Define actor boundaries and available information**

Specify IMPLEMENTER, SEALER, and REPRODUCER permissions, including Haiku-only Claude Code for the implementer, a separate post-freeze holdout sealer, and a reproducer that cannot patch inputs. List the exact allowed inputs and explicitly prohibit Cairn runtime code, adapters, Agent, internal state schemas, prior candidate repositories, and holdout access before sealing.

- [ ] **Step 3: Define immutable imgshape preservation and vector execution**

Include read-only baseline commands, an external snapshot location, non-destructive `robocopy` capture excluding `.git`, and manifest hashing. Require all mutations to occur under a run directory outside `D:/imgshape`; use a released task/verifier package rather than presumed repository state.

- [ ] **Step 4: Define freeze, holdout, reproduction, evidence, and verdict procedures**

Give exact PowerShell/Python commands for baseline inspection, digest capture, archive freeze, evaluator invocation, manifest validation, and repro execution. Use `IMPLEMENTATION_COMMAND` only as a value recorded by the frozen implementation manifest; do not define a Cairn host API.

- [ ] **Step 5: Link the guide from the kit README**

Add one sentence distinguishing the actor-executable handoff from the four-file evaluator kit.

### Task 2: Add a chain-of-custody manifest template

**Files:**
- Create: `conformance/v0/phase6-chain-of-custody.template.json`

**Interfaces:**
- Consumes: externally supplied identities, source/workload/evaluator digests, commands, and verdicts.
- Produces: one immutable, actor-completed record; it is not evaluator input or a host-state schema.

- [ ] **Step 1: Declare only provenance and evidence fields**

Include role/session separation, implementation archive/commit/lock digests, kit digest, imgshape baseline and snapshot digests, public/holdout seals, command digests, environment data, evidence locations/hashes, evaluator verdict hashes, and final `PASS|FAIL|INCONCLUSIVE` fields. Use `null` placeholders and require actors to replace them before sealing.

- [ ] **Step 2: State freeze order inside the template metadata**

Record the required state sequence: `IMPLEMENTATION_FROZEN`, `REFERENCE_SEALED`, `REFERENCE_EXECUTED`, `HOLDOUT_SEALED`, `HOLDOUT_EXECUTED`, `REPRODUCED`, then `PASS|FAIL|INCONCLUSIVE`.

### Task 3: Verify and preserve the package

**Files:**
- Test: `tests/test_p6_conformance_kit.py` (existing regression suite; no evaluator behavior changes)

**Interfaces:**
- Consumes: unchanged copied-kit isolation test.
- Produces: focused regression result and a local documentation commit.

- [ ] **Step 1: Validate JSON and links**

Run:

```text
python -m json.tool conformance/v0/phase6-chain-of-custody.template.json
rg -n "PHASE6-EXTERNAL-HANDOFF|INDEPENDENT-RUNNER" conformance/v0
```

Expected: valid JSON and both kit-local guides linked from `README.md`.

- [ ] **Step 2: Run focused regression and review the exact diff**

Run:

```text
pytest -q tests/test_p6_conformance_kit.py tests/test_p6_freeze.py
git diff --check
git diff -- conformance/v0 docs/superpowers/plans/2026-09-08-phase6-external-authority-handoff.md
```

Expected: tests pass, no whitespace errors, and no Cairn runtime/evaluator changes.

- [ ] **Step 3: Commit locally without a conformance claim**

```text
git add conformance/v0 docs/superpowers/plans/2026-09-08-phase6-external-authority-handoff.md
git commit -m "docs: package Phase 6 external handoff"
```

Remote publication remains subject to explicit approval. Phase 6 remains blocked and unadmitted.

## Plan self-review

- Spec coverage: all fifteen required handoff items map to Task 1 or Task 2; exact verification and preservation map to Task 3.
- Scope control: only Markdown and one provenance template are added; no contract, evaluator, runtime, adapter, host command API, or imgshape mutation is introduced.
- Failure handling: every actor stops on a failed gate and preserves raw evidence; no procedure allows post-seal tuning.
