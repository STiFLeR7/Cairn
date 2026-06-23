"""Non-batchable sequential task — AP-0043 (Milestone M2).

These tests pin the property the M1 NO-GO showed was missing: a task a capable model
*cannot one-shot*, so an injected crash genuinely interrupts partial work and recovery is
measurable. The mechanism is the per-process chain oracle (`cairn.eval.chain.Chain`): each
agent step is a fresh subprocess, and the oracle advances at most once per process.

Acceptance criteria covered:
  1. Step N+1's input is unavailable until step N runs — a batched one-shot fails.        (test_batching_one_shot_does_not_complete, test_chain_blocks_second_advance_in_a_process)
  2. A correct sequential run completes; a crash at k leaves genuine partial progress.     (test_correct_sequential_run_completes, test_crash_leaves_partial_then_rgr_recovers)
  3. Works behind the existing seams with the scripted mock and LiveModelProvider.         (mock: chain_scenario; live-fake: live_chain_scenario)
  4. (No-hardcoding / docs handled outside the test.)
"""

from __future__ import annotations

import json
import os
import tempfile

from benchmarks.scenarios import (
    batching_chain_transport,
    chain_scenario,
    fake_chain_transport,
    live_chain_scenario,
)
from cairn.eval.baselines import ColdRestart, RGR
from cairn.eval.chain import Chain, ChainViolation, expected_tokens, seed_token
from cairn.eval.runner import run_matrix
from cairn.eval.scenario import run_reference, run_until_failure


# --- the primitive ----------------------------------------------------------
def test_chain_blocks_second_advance_in_a_process():
    """One Chain instance == one process: the 2nd advance is the batching block."""
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "chain_state.json")
        c = Chain("salt", path)
        t1 = c.advance(c.current())
        assert t1 == expected_tokens("salt", 1)[1]
        try:
            c.advance(t1)
        except ChainViolation:
            pass
        else:
            raise AssertionError("expected ChainViolation on the 2nd advance in one process")
        # Only one token committed despite the attempt.
        assert json.load(open(path))["pos"] == 1


def test_fresh_chain_per_process_continues():
    """A new Chain instance (== a new step) resumes from the committed token."""
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "chain_state.json")
        Chain("salt", path).advance(seed_token("salt"))      # step 0 (process A)
        c2 = Chain("salt", path)                              # step 1 (process B)
        c2.advance(c2.current())
        assert Chain("salt", path).is_complete(2)


def test_advance_rejects_non_current_token():
    with tempfile.TemporaryDirectory() as d:
        c = Chain("salt", os.path.join(d, "chain_state.json"))
        try:
            c.advance("not-the-seed")
        except ChainViolation:
            return
        raise AssertionError("expected ChainViolation when advancing from a stale token")


# --- the task end-to-end (criterion 2 & 3) ----------------------------------
def test_correct_sequential_run_completes_mock():
    with tempfile.TemporaryDirectory() as d:
        out = run_reference(chain_scenario(4), d)
        assert out.success is True
        chain = Chain("chain-4-secret", os.path.join(d, "workspace", "chain_state.json"))
        assert chain.pos() == 4


def test_correct_sequential_run_completes_livefake():
    # Same task driven through LiveModelProvider + a fake transport (the live seam).
    with tempfile.TemporaryDirectory() as d:
        out = run_reference(live_chain_scenario(4), d)
        assert out.success is True


# --- criterion 1: batching is impossible ------------------------------------
def test_batching_one_shot_does_not_complete():
    """A model that tries to advance the whole chain in one action fails to complete it,
    while a correct step-by-step run on the identical task succeeds."""
    with tempfile.TemporaryDirectory() as d:
        batched = run_reference(live_chain_scenario(4, batching_chain_transport(4)), d)
        assert batched.success is False
        # Exactly one token committed before the per-process guard tripped.
        assert Chain("chain-4-secret", os.path.join(d, "workspace", "chain_state.json")).pos() == 1

    with tempfile.TemporaryDirectory() as d2:
        stepwise = run_reference(live_chain_scenario(4, fake_chain_transport(4)), d2)
        assert stepwise.success is True


# --- criterion 2: crash leaves genuine partial progress, RGR recovers -------
def test_crash_leaves_partial_then_rgr_recovers():
    scenario = chain_scenario(6)
    base = tempfile.mkdtemp()
    inj = run_until_failure(scenario, base, k=3)
    assert inj.fired is True                       # the crash actually fired (not vacuous)
    assert not inj.completed                        # genuine partial: task not yet done
    pos = Chain("chain-6-secret", os.path.join(base, "workspace", "chain_state.json")).pos()
    assert 0 < pos < 6                              # real, incomplete progress on disk


def test_rgr_recovers_cheaper_than_cold_restart():
    """C1 in miniature on the non-batchable task: B3 (RGR) completes with less recovery tax
    and no regression vs B0 (cold restart), which redoes the whole chain."""
    reports = run_matrix(chain_scenario(6), steps=[3], baselines=[ColdRestart(), RGR()])
    by = {r.baseline: r for r in reports}
    assert set(by) == {"B0", "B3"}                 # both cells fired and were scored
    assert by["B3"].task_success and by["B0"].task_success
    assert by["B3"].recovery_tax < by["B0"].recovery_tax
    assert by["B3"].no_regression > by["B0"].no_regression
