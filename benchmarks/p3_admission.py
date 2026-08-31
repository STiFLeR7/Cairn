"""Narrow, evidence-only gate for Receipt/Reconciliation Contract v0."""

from __future__ import annotations


def _failures(label: str, analysis: dict, expected_attempts: int) -> list[str]:
    analysis = analysis.get("analysis", analysis)
    failures = []
    if analysis.get("attempts") != expected_attempts:
        failures.append(f"{label}: attempts {analysis.get('attempts')}/{expected_attempts}")
    for field, expected in (("structural_failures", 0), ("silent_losses", 0), ("semantic_failures", 0)):
        if analysis.get(field) != expected:
            failures.append(f"{label}: {field} {analysis.get(field)}")
    for field in ("correct_decisions", "duplicate_free"):
        if analysis.get(field) != expected_attempts:
            failures.append(f"{label}: {field.replace('_', '-')} evidence {analysis.get(field)}/{expected_attempts}")
    return failures


def evaluate_admission(reference: dict, holdout: dict, *, freeze_matches: bool) -> dict:
    failures = _failures("reference", reference, 36) + _failures("holdout", holdout, 15)
    if not freeze_matches:
        failures.append("Phase 1/2 freeze mismatch")
    return {"admitted": not failures, "failures": failures}
