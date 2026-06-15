# Phase 1 — Conceptual & Research Foundation

- **Status:** 🟡 In Progress *(entered 2026-06-15)*
- **Goal:** Formalize the recovery problem and map the field — establish the vocabulary, the
  formal objects, and the research claims that the rest of the project will build on. **No code.**

## Goals

Phase 0 defined *who* the project is and *how* it operates. Phase 1 defines *what* it is about,
rigorously:

- A formal statement of the agent-recovery problem and why classical recovery does not apply.
- The **recovery-fidelity** metric (conceptual) the project will be measured against.
- An honest **related-work** survey and positioning matrix showing the white space.
- The canonical **conceptual framework** (Code Harness / Agent Runtime Harness / recovery).
- A frozen **research claims registry** — the falsifiable claims we commit to defending.
- The **state** and **tool-effect** taxonomies that feed Phase 2 design.

This phase produces *understanding*, captured as documents. It commits nothing about implementation
(that is Phase 2 design and Phase 3+ code).

## Action Points

| ID | Title | Status |
|---|---|---|
| [AP-0007](action-points/AP-0007-formalize-recovery-problem.md) | Formalize the recovery problem (continuation sufficiency) | Accepted |
| [AP-0008](action-points/AP-0008-recovery-fidelity-metric.md) | Define recovery-fidelity metric & eval dimensions (conceptual) | Accepted |
| [AP-0009](action-points/AP-0009-related-work-positioning.md) | Related-work survey & positioning matrix | Accepted |
| [AP-0010](action-points/AP-0010-conceptual-framework.md) | Conceptual framework docs (Code Harness / Runtime / recovery) | Accepted |
| [AP-0011](action-points/AP-0011-claims-registry.md) | Establish research claims registry | Accepted |
| [AP-0012](action-points/AP-0012-state-and-tool-taxonomies.md) | State taxonomy + tool effect taxonomy (conceptual) | Accepted |

## Dependency order

```
AP-0007 (problem)  ─┬─→ AP-0008 (fidelity) ─┬─→ AP-0011 (claims)
                    ├─→ AP-0009 (related work)│
AP-0010 (framework)─┴─→ AP-0012 (taxonomies) ─┘
```

Suggested execution: **AP-0007 → AP-0010** first (the two foundational docs), then
**AP-0008, AP-0009, AP-0012** in parallel, then **AP-0011** last (it references fidelity + claims-worthy
findings).

## Checklist

- [ ] Recovery problem formalized; continuation sufficiency defined (AP-0007)
- [ ] Recovery-fidelity metric and axes defined (AP-0008)
- [ ] Related-work survey + positioning matrix complete (AP-0009)
- [ ] Conceptual framework docs authored (AP-0010)
- [ ] Claims registry stood up with initial falsifiable claims (AP-0011)
- [ ] State + tool-effect taxonomies authored (AP-0012)

## Completion criteria

- [ ] Continuation-sufficiency and recovery-fidelity are *defined* (not merely asserted)
- [ ] Related work mapped; the white space is explicit and defensible
- [ ] Conceptual framework + taxonomies authored and internally consistent
- [ ] Claims registry populated and frozen
- [ ] All Phase 1 APs `Done` or explicitly deferred (with reason)
- [ ] ROADMAP and trackers updated
- [ ] No code introduced (Phase 1 is conceptual)
