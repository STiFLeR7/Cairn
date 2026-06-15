---
title: ADR-0001 — Foundational project decisions
status: frozen
last_updated: 2026-06-15
owner: maintainers
related_aps: [AP-0001, AP-0002, AP-0003, AP-0006]
related_adrs: []
---

# ADR-0001 — Foundational project decisions

- **Status:** Accepted
- **Date:** 2026-06-15

## Context

Phase 0 (Project Definition) establishes the project's identity and operating model before any technical
implementation. Several foundational decisions were made during the definition discussion and are
recorded here as the project's first immutable reference point.

## Decisions

1. **Name: `Cairn`.** A cairn is a durable trail marker left so a route can be re-found after the trail
   is lost — the metaphor *is* the mechanism (a checkpoint / Continuation State). Short, low-collision,
   gives a coherent vocabulary ("dropping a cairn" = writing a checkpoint).
2. **Method name: Re-grounding Recovery (RGR).** The durable artifact is a *Continuation State* (a cairn).
3. **Thesis: "Checkpoints Are Compactions."** Compaction and crash-recovery checkpointing are the same
   operation at different timescales, served by one distillation mechanism.
4. **License: Apache-2.0.** Chosen over MIT/BSD for its explicit patent grant, contributor clarity, and
   institutional credibility for a research artifact.
5. **Operating model:** documentation-first, Action-Point (AP) driven, phase-based, with always-visible
   trackers (`ROADMAP.md`, `CHECKLIST.md`, `project/tracking/`).
6. **Repository structure:** separate **knowledge** (`docs/`) from **live state** (`project/`); surface
   at-a-glance trackers at the repo root.
7. **Project spine: a 7-phase arc** — define → frame → design → build substrate → build recovery →
   evaluate → publish — with 37 planned APs (only Phase 0's are committed).
8. **Spine of the contribution: method/architecture.** The core deliverable is the RGR mechanism + the
   compaction≡checkpoint unification, with evaluation as support.
9. **v1 substrate: a minimal custom harness** (not OpenHands/LangGraph), including all three recovery
   pillars; effect-safety evaluated on a small tool set.

## Consequences

- The boundary contract between Code Harness and Runtime becomes a primary design artifact (Phase 2).
- Evaluation (Phase 5) supports the method rather than being the headline contribution.
- Documentation and tracking overhead is accepted as a deliberate, enforced cost (see
  [documentation policy](../governance/documentation-policy.md)).

## Supersedes / superseded by

None.
