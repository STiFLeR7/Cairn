# Announcement (DRAFT — do not post without approval)

> **Gated (AP-0037).** This is a draft for review. No external posting happens without explicit human
> approval. Edit freely before publishing.

---

## Short form (≤280 chars)

> Cairn v1.0: a reference implementation + benchmark for **recoverable long-horizon agents**. The thesis —
> *Checkpoints Are Compactions* — unifies context compaction and crash recovery. Re-grounding (not replay)
> resume + effect-safety so agents don't re-send that email. Apache-2.0.
> github.com/STiFLeR7/Cairn

## Medium form (blog/README intro)

When an AI agent fails at step 47, today it usually starts over — wasting work and risking **duplicate
irreversible actions** (re-sending an email, re-charging a card). Cairn makes recovery a first-class,
*measurable* property.

The core idea: **Checkpoints Are Compactions.** Long-horizon agents already recover from information loss
every time they compact an overflowing context window. A crash-recovery checkpoint is just a compaction
you can roll back to. Cairn builds *one* distillation mechanism for both.

Three pillars:
- **Continuation State** — a typed, durable "cairn": the sufficient statistic to keep going, plus a
  prunable tail.
- **Re-grounding Recovery** — resume by re-observing the world and reconciling against the cairn, not by
  replaying a non-deterministic trajectory. Survives where replay breaks; even resumes across model versions.
- **Effect-safety** — a write-ahead ledger that stops a resumed agent re-firing irreversible effects.

And it's *measured*: a failure-injection benchmark scores recovery fidelity against four baselines. In the
reference harness, re-grounding beats cold restart on cost and preserved work, and the write-ahead ledger
eliminates duplicate effects for queryable tools.

**Bring your own model.** Cairn ships the recovery mechanism as a library — public `checkpoint`/`recover`
primitives and an opt-in `Agent` loop over a pluggable `World` — so you can add crash-recovery to *your*
agent with *your* model and keys, and reproduce the recovery-vs-restart result yourself.

**Honest scope:** the in-harness results establish mechanism correctness and reproducibility. Live runs
against real models (Milestones M1–M3) look promising — re-grounding roughly halves recovery tax — but the
headline live claim is **suggestive, not yet confirmed** (a powered study on a paid/reliable API is the
remaining gate), so the project deliberately stays 0.x. Cairn *complements* agent frameworks rather than
replacing them.

Library + spec + reference implementation + benchmark, Apache-2.0: **github.com/STiFLeR7/Cairn**

## Notes for the poster

- Lead with the concrete pain (duplicate effects / wasted work), then the thesis.
- Always include the honest-scope line — do not imply a live-LLM benchmark.
- Link `PAPER.md` for the full write-up and `REPRODUCE.md` for one-command reproduction.
