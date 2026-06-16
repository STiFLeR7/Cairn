# Phase 6 — Paper & Release

- **Status:** 🟡 In Progress *(2026-06-15 — paper + repro `Done`; release/announce prepared, gated on approval)*
- **Goal:** Tell the story and ship the artifact. Synthesize Phases 0–5 into a research **paper draft**
  ("Checkpoints Are Compactions"), make the repository **reproducible** by anyone, and prepare the
  **v1.0 release** + public positioning — with the release and announcement gated on explicit approval.

## Goals

- **Paper draft** (`AP-0034`) — a self-contained write-up: problem, the two-layer model, Continuation
  State, Re-grounding Recovery, effect-safety, unified distillation, the Phase 5 evaluation (with honest
  scope), limitations, and future work. Cites the in-repo concept/design docs and the claims registry.
- **Reproducibility package** (`AP-0035`) — one-command setup + run for the tests, the recovery demo, and
  all three benchmarks; documented environment; a repro guide so the headline numbers regenerate.
- **v1.0 release** (`AP-0036`) — version bump, release notes, `CITATION.cff` finalized, tag `v1.0.0`.
  **Gated:** the tag/GitHub release is cut only on explicit approval.
- **Public positioning** (`AP-0037`) — final README/landing polish + an announcement draft. **Gated:** any
  external posting happens only on explicit approval.

**Constraints:** **Honest framing** (ADR-0009) carries into the paper and README — v1 results are from the
deterministic reference harness; the live-LLM study is future work. **Outward actions are gated:** cutting
the release tag and posting the announcement require explicit human go-ahead.

## Action Points

| ID | Title | Status |
|---|---|---|
| [AP-0034](action-points/AP-0034-paper-draft.md) | Paper draft ("Checkpoints Are Compactions") | Done |
| [AP-0035](action-points/AP-0035-reproducibility-package.md) | Reproducibility package & artifact polish | Done |
| [AP-0036](action-points/AP-0036-v1-release.md) | v1.0 OSS release (docs, examples, citation) | Accepted *(prepared; gated)* |
| [AP-0037](action-points/AP-0037-public-positioning.md) | Public positioning (README, announcement) | Accepted *(prepared; gated)* |

## Dependency order

```
AP-0034 (paper draft) ──┐
AP-0035 (repro package) ─┼─→ AP-0036 (v1.0 release — GATED) ──→ AP-0037 (positioning/announce — GATED)
```

## Checklist

- [x] Paper draft covers problem → method → evaluation → limitations, cites in-repo docs (AP-0034)
- [x] One-command repro for tests + demo + benchmarks; environment documented (AP-0035)
- [x] Release notes drafted; version bump + `CITATION.cff` finalize + tag held for approval (AP-0036)
- [x] README polished + announcement drafted; external posting held for approval (AP-0037)
- [x] Honest framing preserved (ADR-0009); docs + trackers updated; tests green

## Completion criteria

- [ ] `PAPER.md` (or `docs/paper/`) drafted and internally consistent with the repo's claims/results
- [ ] A fresh clone reproduces the test suite, the recovery demo, and the benchmark tables via the repro guide
- [ ] v1.0 release artifacts prepared (notes, citation, version); **release performed only after approval**
- [ ] Public positioning prepared; **announcement posted only after approval**
- [ ] All Phase 6 APs `Done` (release/announce APs may remain `Blocked: awaiting approval` if not yet greenlit)
