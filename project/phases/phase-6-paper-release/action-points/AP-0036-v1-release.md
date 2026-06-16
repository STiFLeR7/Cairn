---
id: AP-0036
title: v1.0 OSS release (docs, examples, citation)
phase: phase-6-paper-release
status: Blocked
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: [AP-0034, AP-0035]
related_docs: [CITATION.cff, CHANGELOG.md]
related_adrs: [ADR-0001]
---

## Objective

Prepare and (on approval) perform the **v1.0.0** open-source release: finalize the version, release notes,
and citation metadata so the artifact is durably citable and installable.

## Scope

**In:** version bump in `pyproject.toml` to `1.0.0`; a `CHANGELOG.md` release section (move `Unreleased`
→ `v1.0.0`); finalize `CITATION.cff`; draft GitHub release notes. **The tag `v1.0.0` and the GitHub
release are cut only after explicit human approval.**
**Out:** PyPI publishing (optional later); signed releases (optional later).

## Acceptance Criteria

- [ ] `pyproject.toml` version set to `1.0.0`; `CHANGELOG.md` has a dated `v1.0.0` section *(on approval)*
- [ ] `CITATION.cff` finalized with `version`/`date-released` *(on approval; title/authors/URL already set)*
- [x] Release notes drafted (highlights, scope/limitations, repro pointer) — `docs/release/RELEASE_NOTES_v1.0.0.md`
- [ ] **Gate:** tag + GitHub release performed **only** on explicit approval (recorded in the log)
- [x] Documentation + trackers updated

## Dependencies

- AP-0034 (paper), AP-0035 (repro) — the release points at both

## Status / Log

- 2026-06-15 — Proposed → Accepted (refined on Phase 6 entry). Release execution gated on approval.
- 2026-06-15 — Prepared: release notes drafted (`docs/release/RELEASE_NOTES_v1.0.0.md`). **Remaining
  (gated on approval):** bump `pyproject` to 1.0.0, finalize `CITATION.cff` version/date, move CHANGELOG
  `Unreleased` → `v1.0.0`, tag `v1.0.0`, publish GitHub release.
- 2026-06-15 — **Decision: deferred.** Hold the v1.0 release; keep the project at 0.x until a live-LLM study validates the claims (current evidence is reference-harness only, ADR-0009). Release notes draft stays ready; execution moves to a future v1.0 milestone. Status → Blocked (deliberate hold, not an impediment).
