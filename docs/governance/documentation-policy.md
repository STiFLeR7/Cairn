---
title: Documentation Policy
status: active
last_updated: 2026-06-15
owner: maintainers
related_aps: [AP-0002]
related_adrs: [ADR-0001]
---

# Documentation Policy

Documentation in Cairn is a **first-class artifact**, not an afterthought. This policy makes that
concrete and enforceable.

## Principles

1. **Docs ship with the change.** No unit of work is complete until its documentation is updated.
   Documentation updates land in the *same* pull request as the change they describe. This is part of
   the [Definition of Done](../../CONTRIBUTING.md#definition-of-done).
2. **Single source of truth.** Each concept is owned by exactly one document. Everything else links to
   it. No duplicated explanations that can drift apart.
3. **Traceability.** Every doc declares the APs and ADRs it relates to (front-matter). Every meaningful
   claim is traceable to an AP or ADR.
4. **Living vs. frozen.** Vision and concept docs *evolve*. ADRs and registered research claims are
   *immutable once accepted* — to change them you write a new record that supersedes the old.

## Document taxonomy

| Type | Lives in | Mutability | Owns |
|---|---|---|---|
| Vision / positioning / scope | `docs/vision/` | Living | Why the project exists, where it sits, its boundaries |
| Concepts | `docs/concepts/` | Living | The conceptual framework and terminology |
| Design / specs | `docs/design/` | Living (versioned) | Schemas, contracts, protocols |
| ADR | `docs/adr/` | **Frozen** when accepted | A single decision + its rationale |
| Research | `docs/research/` | Mixed (claims frozen) | Related work, claims registry, drafts |
| Governance | `docs/governance/` | Living | How we work |
| Glossary | `docs/governance/glossary.md` | Living | Canonical definitions |

## Front-matter (required on every doc)

```yaml
---
title: ...
status: draft | active | frozen | superseded
last_updated: YYYY-MM-DD
owner: ...
related_aps: [...]
related_adrs: [...]
---
```

## Change protocol

For every meaningful change:

1. Update the **owning** document (only one).
2. If the change embodies a **decision**, write/append an **ADR**.
3. Update **`CHANGELOG.md`**.
4. Update the relevant **trackers** (`project/tracking/`) and the **AP**.
5. Bump `last_updated` (and `status` if it changed) in touched docs.

## Review

Documentation is reviewed like code — in the same PR, against this policy. A PR that changes behavior
or decisions without a corresponding doc update does not meet the Definition of Done.
