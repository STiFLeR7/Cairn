---
id: AP-0009
title: Related-work survey & positioning matrix
phase: phase-1-conceptual-foundation
status: Done
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: [AP-0007]
related_docs: [docs/research/related-work.md]
related_adrs: [ADR-0001]
---

## Objective

Survey prior art honestly and build a positioning matrix that makes Cairn's white space explicit:
crash-recovery **+** non-determinism **+** effect-safety **+** context-loss, unified under
"Checkpoints Are Compactions" with a fidelity metric.

## Scope

**In:** durable-execution engines (e.g. Temporal); agent-framework persistence (LangGraph checkpointers,
OpenHands state); virtual context management (MemGPT/Letta); classical recovery (ARIES, event sourcing,
CRIU/DMTCP/HPC checkpoint-restart). A capability × system matrix and an honest novelty statement.
**Out:** an exhaustive literature review; benchmarking competitors (Phase 5).

## Deliverables

- `docs/research/related-work.md` with: per-system summary + citation; a positioning matrix (rows =
  systems, columns = crash-recovery, non-determinism handling, effect-safety, context-loss recovery,
  fidelity metric); a paragraph stating exactly what is and is not novel.

## Acceptance Criteria

- [x] At least six prior systems/approaches surveyed, each with a citation/reference
- [x] Positioning matrix present and filled, showing the gap Cairn occupies
- [x] Novelty statement is honest about what prior work already solves
- [x] Cross-links to `docs/vision/positioning.md` (which references this survey)
- [x] Documentation updated (single source of truth, front-matter current)
- [x] Trackers updated (`ap-index.md`, `phase-tracking.md`, `CHANGELOG.md`)

## Dependencies

- AP-0007 (need the problem framing to position against)

## Status / Log

- 2026-06-15 — Proposed → Accepted (refined on Phase 1 entry).
- 2026-06-15 — Accepted → Done. Delivered `docs/research/related-work.md` (7 prior systems, filled
  positioning matrix, honest novelty statement).
