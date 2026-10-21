"""Public API contract — the lock on the top-level `cairn` surface (M4 AP-5).

If you add/remove/rename a public name, this test fails on purpose: update `EXPECTED`
deliberately (a public-surface change is a decision, not an accident) and document it in
CHANGELOG.md + docs/guide/public-api-reference.md in the same change.
"""

import cairn

# The exact, intended public surface as of Milestone M4 (BYOM recovery library).
EXPECTED = {
    "__version__",
    # types
    "Action", "StepRecord", "Checkpoint", "Regrounded", "Resolution", "ResumePlan", "AgentRun",
    # contracts (Protocols)
    "World", "CheckpointStore", "EffectLedger",
    # effect safety
    "EffectfulTool", "EscalationRequired",
    # reference implementations
    "Workspace", "FileCheckpointStore", "FileEffectLedger",
    # primitives
    "checkpoint", "recover", "regrounded_history",
    # opt-in loop
    "Agent",
}


def test_all_matches_the_intended_surface_exactly():
    actual = set(cairn.__all__)
    missing = EXPECTED - actual
    extra = actual - EXPECTED
    assert not missing, f"public names declared but missing from __all__: {sorted(missing)}"
    assert not extra, f"public names in __all__ not in the intended contract: {sorted(extra)}"


def test_all_has_no_duplicates():
    assert len(cairn.__all__) == len(set(cairn.__all__))


def test_every_public_name_is_importable():
    for name in cairn.__all__:
        assert hasattr(cairn, name), f"cairn.{name} is in __all__ but not importable"


def test_version_is_1_0_0():
    # v1.0.0 was approved by the owner on 2026-10-21 (AP-0036) after the M5 GO gate.
    assert cairn.__version__ == "1.0.0"
