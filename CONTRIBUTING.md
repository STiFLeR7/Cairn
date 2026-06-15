# Contributing to Cairn

Thanks for your interest. Cairn is documentation-first, Action-Point (AP) driven, and phase-based.
Read this before opening a PR.

## The three rules

1. **Documentation is a first-class artifact.** No change is complete until its documentation is
   updated. Doc updates ship in the *same* PR as the change. See
   [documentation policy](docs/governance/documentation-policy.md).
2. **Every change belongs to an Action Point.** Work is organized into APs, each with an Objective,
   Scope, Deliverables, Acceptance Criteria, Dependencies, and Status. See
   [AP workflow](docs/governance/ap-workflow.md).
3. **Work happens within the current phase.** See the [phase process](docs/governance/phase-process.md)
   and [ROADMAP.md](ROADMAP.md).

## Workflow

1. Find or propose the AP your change belongs to (`project/phases/<phase>/action-points/`).
2. Move the AP to `In Progress` and reference its ID in your branch and commits
   (e.g. `AP-0004: author vision doc`).
3. Make the change **and** update the docs it touches.
4. If you made a meaningful decision, write an [ADR](docs/adr/).
5. Update `CHANGELOG.md` and the trackers (`project/tracking/`).
6. Open a PR. It must satisfy the AP's Acceptance Criteria, including the documentation criterion.

## Definition of Done

A unit of work is **Done** only when:

- [ ] Acceptance Criteria met
- [ ] Documentation updated (single source of truth, front-matter current)
- [ ] ADR written if a decision was made
- [ ] `CHANGELOG.md` and trackers updated
- [ ] Tests pass *(from Phase 3 onward)*

## Commit & licensing

By contributing you agree your contributions are licensed under [Apache-2.0](LICENSE).
Commit messages reference the AP ID. Sign-off (DCO) is encouraged.
