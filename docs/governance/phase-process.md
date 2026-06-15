---
title: Phase Process
status: active
last_updated: 2026-06-15
owner: maintainers
related_aps: [AP-0003]
related_adrs: [ADR-0001]
---

# Phase Process

Cairn progresses through **phases**. Each phase has a clear goal, a checklist, and explicit completion
criteria. The canonical phase list is in [ROADMAP.md](../../ROADMAP.md).

## Principles

- **One active phase at a time.** Work belongs to the current phase.
- **Phases are entered, not pre-designed.** Only the *current* phase's APs are committed. Later-phase
  APs are provisional placeholders, refined/split when the phase is entered. This prevents speculative
  detail from rotting.
- **Phases gate on completion criteria**, not on a calendar.

## Phase anatomy

Each phase has a directory `project/phases/<phase>/` containing:

- `README.md` — goal, checklist, completion criteria, and the phase's AP list
  (see [template](../../project/templates/phase-template.md)).
- `action-points/` — the AP files for that phase.

## Phase lifecycle

```
Not started → In Progress → Complete
                        ↘ Blocked
```

**Entering a phase:** refine its provisional APs into committed ones; set status `In Progress` in
[ROADMAP.md](../../ROADMAP.md) and [phase-tracking](../../project/tracking/phase-tracking.md).

**Completing a phase:** every completion criterion is checked; all the phase's APs are `Done` or
explicitly deferred (with a recorded reason); the roadmap and trackers are updated.

## The 7-phase arc

`define → frame → design → build substrate → build recovery → evaluate → publish`

| Phase | Name |
|---|---|
| 0 | Project Definition |
| 1 | Conceptual & Research Foundation |
| 2 | Architecture & Protocol Design |
| 3 | Minimal Harness |
| 4 | Recovery v1 (three pillars) |
| 5 | Evaluation & Benchmark |
| 6 | Paper & Release |

See [ROADMAP.md](../../ROADMAP.md) for goals and completion criteria per phase.
