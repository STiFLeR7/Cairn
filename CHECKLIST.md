# Cairn — Master Checklist

> Single always-visible status surface. Rolls up phases and Action Points. Detailed status:
> [`project/tracking/phase-tracking.md`](project/tracking/phase-tracking.md) ·
> [`project/tracking/ap-index.md`](project/tracking/ap-index.md).

## Phases

- [x] **Phase 0 — Project Definition** 🟢 *(complete — reviewed & approved 2026-06-15)*
- [x] **Phase 1 — Conceptual & Research Foundation** 🟢 *(complete & merged — PR #1)*
- [x] **Phase 2 — Architecture & Protocol Design** 🟢 *(complete & merged — PR #2)*
- [x] **Phase 3 — Minimal Harness** 🟢 *(complete & merged — PR #3; 13 tests passing)*
- [x] **Phase 4 — Recovery v1 (three pillars)** 🟢 *(complete & merged — PR #4; 33 tests passing)*
- [x] **Phase 5 — Evaluation & Benchmark** 🟢 *(complete & merged — PR #5; 42 tests passing)*
- [x] **Phase 6 — Paper & Release** 🟢 *(core done & merged — PR #6: paper + repro; v1.0 release & announcement **deferred** to Milestone M1's go/no-go)*

## Milestones (post-7-phase)

- [x] **Milestone M1 — Live-LLM Validation** 🟢 *(complete & merged PR #7, 2026-06-16; 5 / 5 APs; **outcome NO-GO** — live run didn't validate the claims, project stays 0.x)*
- [x] **Milestone M2 — Recovery-faithful live benchmark** 🟢 *(complete 2026-06-23; 5 / 5 APs; shipped as **v0.2.0**; **v1.0 go/no-go take 2 → NO-GO** — live C1 suggestive not confirmed, project stays 0.x)*
- [x] **Milestone M3 — Powered live study (v1.0 gate)** 🟢 *(complete 2026-06-29; 4 / 4 APs; **v1.0 go/no-go take 3 → NO-GO** — strongest live signal yet (`gpt-oss-120b`, RGR ≈ halves recovery tax) but strict verdict confounded; project stays 0.x)*
- [x] **Milestone M4 — BYOM Recovery Library** 🟢 *(complete & merged 2026-07-02, PRs #10/#11/#12; 5 / 5 slices AP-1…AP-5; recovery mechanism shipped as a bring-your-own-model library; in-repo, 0.x — ships nothing outward)*

## Phase 0 — Action Points

- [x] `AP-0001` Establish repository structure & skeleton
- [x] `AP-0002` Ratify documentation governance model
- [x] `AP-0003` Define AP & phase workflow process docs
- [x] `AP-0004` Author vision, positioning & scope docs
- [x] `AP-0005` Stand up master trackers (ROADMAP, CHECKLIST, ap-index, phase-tracking)
- [x] `AP-0006` License + contribution + citation scaffolding

## Phase 0 completion criteria

- [x] Repository structure scaffolded (`docs/` + `project/` + root trackers)
- [x] Documentation governance model ratified (ADR-0001)
- [x] AP & phase workflow documented with templates
- [x] Vision, positioning, and scope authored and approved
- [x] Master trackers live and cross-linked
- [x] Apache-2.0 license + contribution + citation files present

## Phase 1 — Action Points

- [x] `AP-0007` Formalize the recovery problem (continuation sufficiency)
- [x] `AP-0008` Define recovery-fidelity metric & eval dimensions (conceptual)
- [x] `AP-0009` Related-work survey & positioning matrix
- [x] `AP-0010` Conceptual framework docs (Code Harness / Runtime / recovery)
- [x] `AP-0011` Establish research claims registry
- [x] `AP-0012` State taxonomy + tool effect taxonomy (conceptual)

## Phase 1 completion criteria

- [x] Continuation-sufficiency and recovery-fidelity *defined* (not asserted)
- [x] Related work mapped; white space explicit and defensible
- [x] Conceptual framework + taxonomies authored and internally consistent
- [x] Claims registry populated and frozen
- [x] No code introduced (Phase 1 is conceptual)

## Phase 2 — Action Points

- [x] `AP-0013` Continuation State (cairn) schema spec
- [x] `AP-0014` Code Harness ↔ Runtime boundary contract spec
- [x] `AP-0015` Re-grounding resume protocol spec
- [x] `AP-0016` Unified compaction/checkpoint distillation design (core/tail)
- [x] `AP-0017` Effect-safety write-ahead protocol spec
- [x] `AP-0018` Tool effect taxonomy → recovery-policy mapping

## Phase 2 completion criteria

- [x] All six specs authored in `docs/design/` and internally consistent
- [x] Every design decision traces to a Phase 1 concept
- [x] ADRs accepted for the keystone decisions (schema, boundary contract, unified distillation)
- [x] Design is implementable — Phase 3 can build against these contracts
- [x] No runnable code (Phase 2 is design)

## Phase 3 — Action Points

- [x] `AP-0021` Boundary-contract interfaces + core data models
- [x] `AP-0019` Minimal Runtime (sandbox, workspace, effect ledger, checkpoint store)
- [x] `AP-0020` Minimal Code Harness (agent loop, code-as-action, model provider)
- [x] `AP-0022` Baseline task suite (no recovery) + smoke tests

## Phase 3 completion criteria

- [x] Assembled harness completes a baseline task end-to-end
- [x] `pytest` smoke suite passes (contract behaviors + baseline task)
- [x] No hardcoded harness — model/tools/tasks/sandbox injected (ADR-0007)
- [x] Recovery not implemented (Phase 4); seams exist

## Phase 4 — Action Points

- [x] `AP-0023` Unified distillation engine (cairn writer)
- [x] `AP-0024` Checkpoint persistence + workspace snapshot integration
- [x] `AP-0025` Re-grounding resume protocol implementation
- [x] `AP-0026` Effect-safety WAL + idempotency enforcement
- [x] `AP-0027` End-to-end recovery from injected failure

## Phase 4 completion criteria

- [x] Agent recovers from an injected failure end-to-end and completes the task (claim C1)
- [x] Unified `distill` yields an identical durable core for compaction and checkpoint paths (claim C2)
- [x] No duplicate effect for safe-to-retry / check-before-retry; never-retry escalates (claim C3)
- [x] `pytest` green across the new recovery suite and the existing Phase 3 tests
- [x] No hardcoded harness (ADR-0007); docs + ADR-0008 + trackers updated

## Phase 5 — Action Points

- [x] `AP-0028` Failure-injection harness (step × failure-type matrix)
- [x] `AP-0029` Baselines (cold restart, log-replay, snapshot-only, RGR)
- [x] `AP-0030` Metrics implementation (five fidelity axes)
- [x] `AP-0031` Continuation-State ablation study
- [x] `AP-0032` Cross-version resume experiment
- [x] `AP-0033` Results aggregation & claims update

## Phase 5 completion criteria

- [x] Benchmark runs end-to-end; results table over (step × type × baseline)
- [x] C1 supported: B3 (RGR) beats B0 (cold restart) on recovery tax + no-regression
- [x] C3 supported: with-WAL resume yields 0 duplicate effects vs without-WAL
- [x] C2/C5 evidenced by ablation; C4 mechanism shown by cross-version experiment
- [x] Claims registry updated with dated, honestly-scoped evidence (ADR-0009)
- [x] `pytest` green across the new eval suite and all prior tests
- [x] No hardcoded harness (ADR-0007); docs + ADR-0009 + trackers updated

## Phase 6 — Action Points

- [x] `AP-0034` Paper draft ("Checkpoints Are Compactions")
- [x] `AP-0035` Reproducibility package & artifact polish
- [~] `AP-0036` v1.0 OSS release — *deferred to the v1.0 milestone (release notes ready)*
- [~] `AP-0037` Public positioning — *deferred to the v1.0 milestone (announcement drafted)*

## Phase 6 completion criteria

- [ ] `PAPER.md` drafted; consistent with the repo's claims/results and honest scope
- [ ] Fresh clone reproduces tests + demo + benchmarks via `REPRODUCE.md`
- [x] v1.0 release artifacts prepared (release notes draft); **tag deferred to Milestone M1's go/no-go (decision)**
- [x] Public positioning prepared (announcement draft); **posting deferred to Milestone M1's go/no-go (decision)**
- [x] Docs + trackers updated; tests green

## Milestone M1 — Action Points

- [x] `AP-0038` Live LLM `ModelProvider` adapters (injected, no hardcoding)
- [x] `AP-0039` Determinism, cost & reproducibility controls for live runs
- [x] `AP-0040` Live failure-injection study (Phase 5 matrix, real model) — *ran `owl-alpha`; honest negative*
- [x] `AP-0041` Live results analysis & claims update (C1–C5)
- [x] `AP-0042` v1.0 go/no-go gate — **NO-GO** (project stays 0.x)

## Milestone M1 completion criteria

- [x] ≥1 real LLM provider integrated behind the model seam, injected via config (no hardcoding, ADR-0007/0010)
- [x] Live failure-injection study ran against a real model, reproducibly (transcript captured + offline-replayable)
- [x] Claims registry carries dated **live-LLM** evidence — a recorded **negative** (C1 not validated live; C1–C5 stay reference-harness-only)
- [x] Recorded v1.0 go/no-go — **NO-GO**; AP-0036/0037 stay `Blocked` (the "go" condition was not met)

## Milestone M2 — Action Points

- [x] `AP-0043` Non-batchable sequential benchmark task
- [x] `AP-0044` Action-granularity-robust recovery metrics
- [x] `AP-0045` Repetition + statistics harness (injection-fired enforced)
- [x] `AP-0046` Live re-run + claims update (C1–C5, with statistics)
- [x] `AP-0047` v1.0 go/no-go, take 2 — **NO-GO** (stays 0.x; M2 shipped as v0.2.0)

## Milestone M2 completion criteria

- [x] A task a capable model cannot one-shot; a crash at step k leaves genuine partial progress (verified by test)
- [x] Recovery metrics measured in progress/work-units, robust to action granularity
- [x] Each cell run N times with seeds; mean ± spread reported; vacuous cells skipped (M1 fix carried forward)
- [x] Live re-run produces dated C1–C5 evidence with statistics, honestly scoped *(crash fired; C1 suggestive not confirmed at n=2)*
- [x] Recorded v1.0 go/no-go take 2; version status reflects the evidence *(NO-GO; shipped as v0.2.0, stays 0.x)*

## Milestone M3 — Action Points

- [x] `AP-0048` Success-conditioned recovery tax (a failed run can't register a cheap tax)
- [x] `AP-0049` Multi-provider OpenAI-compatible transports (Groq, ZenMux) — config, not per-vendor code
- [x] `AP-0050` Powered live study + claims update — *`gpt-oss-120b`, 28 fired cells; RGR ≈ halves tax; strict verdict NOT SHOWN*
- [x] `AP-0051` v1.0 go/no-go, take 3 — **NO-GO** (stays 0.x; AP-0036/0037 stay `Blocked`)

## Milestone M3 completion criteria

- [x] Recovery tax is success-conditioned (fairness fix); a non-recovery cannot look cheap
- [x] ≥2 OpenAI-compatible providers usable by config so the run isn't hostage to one rate-limited free tier
- [x] Powered live run executed and analyzed; dated C1–C5 evidence, honestly scoped *(RGR ≈ halves tax, higher success; strict verdict confounded)*
- [x] Recorded v1.0 go/no-go take 3 — **NO-GO**; next gate = paid/reliable model + capability-matched C1 + C3 live

## Milestone M4 — Action Points *(superpowers spec→plan→execute slices)*

- [x] `AP-1` Split contracts (`World`/`CheckpointStore`/`EffectLedger` Protocols; `LocalRuntime` satisfies) — PR #10
- [x] `AP-2` Recovery primitives (`checkpoint`/`recover`) + fake-World abstraction proof — PR #10
- [x] `AP-3` Opt-in `Agent` loop on the primitives + `regrounded_history` de-dup — PR #10
- [x] `AP-4` BYOM example + guide + public API reference + CI smoke test — PR #11
- [x] `AP-5` Public-API contract lock + design-spec reconciliation (§12) + trackers/CHANGELOG — PR #12

## Milestone M4 completion criteria

- [x] A clean public API an outside dev can use to add recovery to their own agent (primitives + `Agent`)
- [x] `World` abstraction so recovery isn't married to the filesystem (proven by in-memory fake Worlds)
- [x] The existing benchmark/eval runs unchanged on the new public API (regression guard green)
- [x] A runnable, offline, deterministic example + guide + public API reference; example smoke-tested in CI
- [x] Public surface locked by a contract test; `__version__` guarded at 0.x; ships nothing outward (v1.0 hold intact)
