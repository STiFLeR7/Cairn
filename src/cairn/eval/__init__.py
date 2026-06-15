"""Cairn evaluation framework (Phase 5).

Reusable benchmark machinery — failure injection, baselines, metrics, ablation, and the
matrix runner. Concrete experiment wiring (tasks, models, result tables) lives in
`benchmarks/`, not here (ADR-0009). Nothing concrete is hardcoded: scenarios inject the
task, model, failure type, and effect (ADR-0007).
"""
