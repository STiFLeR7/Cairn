---
title: Concepts
status: active
last_updated: 2026-06-15
owner: maintainers
related_aps: [AP-0007, AP-0008, AP-0010, AP-0012]
related_adrs: [ADR-0001]
---

# Concepts

The conceptual framework, authored across Phase 1.

| Document | Covers | AP | Status |
|---|---|---|---|
| [problem-formalization.md](problem-formalization.md) | The agent-recovery problem; continuation sufficiency | AP-0007 | ✅ done |
| [code-harness-and-runtime.md](code-harness-and-runtime.md) | Two-layer model + the *one concern, two altitudes* rule | AP-0010 | ✅ done |
| [recovery-in-the-two-layer-model.md](recovery-in-the-two-layer-model.md) | Recovery = Runtime mechanism + Code Harness semantics | AP-0010 | ✅ done |
| [recovery-fidelity.md](recovery-fidelity.md) | Recovery-fidelity metric (outcome equivalence) | AP-0008 | ✅ done |
| [state-taxonomy.md](state-taxonomy.md) | Five-layer agent-state taxonomy | AP-0012 | ✅ done |
| [tool-effect-taxonomy.md](tool-effect-taxonomy.md) | Tool reversibility classes + recovery policy | AP-0012 | ✅ done |

Research-side companions live in [`../research/`](../research/): the
[related-work survey](../research/related-work.md) and the
[claims registry](../research/claims-registry.md).

See also the [glossary](../governance/glossary.md) and the [vision](../vision/vision.md).
