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


def test_version_is_still_0x():
    # Guards against an accidental/unapproved v1.0 bump — the v1.0 release is HELD
    # (needs explicit approval + powered live evidence; the project stays 0.x).
    assert cairn.__version__.startswith("0."), (
        f"__version__ is {cairn.__version__!r}; v1.0+ requires explicit approval + live evidence"
    )
