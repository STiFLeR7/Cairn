# Phase 2 interim evidence

## P2.0 — passed

`control-freeze.json` pins the four final Phase 1 Claude artifacts (110 rows) by SHA-256.
Its complete failure attribution is:

| class | rows |
| --- | ---: |
| baseline completion failure | 54 |
| checkpoint acquisition failure | 1 |
| recovery-path failure | 0 |
| recovered success | 55 |

The observed absolute completion rate is therefore not evidence of an RGR failure.

## P2.1 — passed

The U/R/C reference control now creates C from an actual checkpoint, serializes and reloads it,
derives the goal from durable state, and does not retain the original observations/transcript.
The deterministic U/R/C behavioral control reaches the same next verified work unit.

## P2.2 — live continuity evidence (partial; not an exit)

Structural ablations show that the pre-existing fresh continuation path re-grounded only plan
history: decisions, verification, and world facts were durable but never supplied to the coding
model. `continuation_prompt()` is the smallest reference-harness correction: it deterministically
renders existing durable facts and adds no schema fields or fixture-specific instruction.

The following frozen `tests@2`, Opus, split-0 controls completed with U/R/C all verified at four
work units:

| C condition | artifact | result |
| --- | --- | --- |
| full durable state | `urc-claude-opus-tests-s0-background.json` | pass |
| decisions removed | `urc-claude-opus-tests-s0-no-decisions.json` | pass |
| plan/history removed | `urc-claude-opus-tests-s0-no-plan-rerun.json` | pass |

Those two ablations are non-discriminating for this fixture/model cell; they do **not** establish
that decisions or plan are optional in a contract. The eligible intent ablation
(`urc-claude-opus-tests-s0-no-intent.json`) had U and R pass but C fail with
`unverified_progress`. It is one causal signal that task intent matters, not a sufficient basis
for a stable requirement. Its replication is retained but ineligible:
`urc-claude-opus-tests-s0-no-intent-replication.json` has an uninterrupted U failure
(`unverified_mutation`) before C.

That signal does not generalize to the independent `bugfix@2` control:
`urc-claude-opus-bugfix-s0-no-intent.json` passed U/R/C with intent removed. Therefore intent
loss is currently fixture-dependent, not a justified universal Continuation Contract requirement.
No state or RGR correction is admitted from these ablations.

Checkpoint coverage is also incomplete: the completed split checkpoint has goal, plan, decision,
and workspace digest populated, but an empty `verification` list. This is an observed capture
gap, not yet evidence that a schema or RGR change would improve continuity.

## Matrix control correction

The initial matrix (`matrix-v02`) is retained as raw diagnostic evidence but excluded from every
Phase 2 gate. Its U, R, and C branches independently generated their model-driven prefix, so a
branch could fail before it had reached a common checkpoint. For example, an apparent C-only
failure could be a multi-unit mutation during C's own prefix. `matrix-protocol.json` v0.3 pins the
corrected control: one live prefix produces one clean checkpoint; U, R, and C materialize from
that identical repository state before their distinct continuation paths begin.

## Hard-gate status

Not earned. Live U/R/C records now exist, but there are not 100 qualified paired continuations,
there is no blinded holdout, and the causal ablation evidence is insufficient to publish
Continuation Contract v0. No claim of improved recovery or compaction continuity is made.

## v0.4 terminal matrix finding — gate blocked

`matrix-protocol.json` v0.3 exposed a runner defect: a prefix-stage exception returned from
`capture_live_urc()` but did not write its `evidence_path`, silently removing attempts. The
minimal v0.4 correction writes the returned invalid record, with a regression test. v0.4 pins
that source hash in `matrix-protocol-v04.json`; it changes no fixture, prompt, state schema, RGR
behavior, or model configuration.

The clean v0.4 run stopped only when its fixed gate became mathematically impossible:

| measure | count |
| --- | ---: |
| scheduled attempts | 176 |
| retained attempts | 151 |
| remaining scheduled cells | 25 |
| qualified U/R/C triplets | 74 |
| recovery successes among qualified | 74 / 74 |
| compaction successes among qualified | 74 / 74 |
| maximum possible qualified total | 99 |
| required qualified total | 100 |

The final atomic record was allowed to settle before stopping the worker. Thus the `99` upper
bound is not a transient partial-file calculation.

| model | qualified | baseline-only failure | pre-checkpoint failure |
| --- | ---: | ---: | ---: |
| Opus | 41 | 11 | 11 |
| Sonnet | 33 | 12 | 43 |

All pre-checkpoint failures are model/task-progress failures: `model_no_verified_progress`,
`unverified_mutation`, or `unverified_progress`. Baseline-only failures are
`unverified_mutation`. None is an RGR or compaction failure. The causal conclusion is therefore
limited: for 74 independently verified common-checkpoint continuations, full durable state and
compacted durable state had equal success; the Phase 2 sample-size gate failed because the frozen
models did not reliably acquire/maintain a valid prefix, not because Cairn recovery lost state.

Consequences: do not publish Continuation Contract v0, do not consume the blinded holdout, and do
not introduce a state/RGR correction. A new Phase 2 attempt requires an explicitly approved,
newly pinned execution protocol that addresses prefix acquisition without prompt-tuning to these
fixtures.

## v0.6 checkpoint-ready control — terminal gate result

The approved checkpoint-ready control used the fixture's existing verified control commands to
reach the shared split checkpoint, then ran the unchanged U/R/C continuations under the same two
Claude Code configurations. This isolates continuation behavior from the v0.4 model prefix
acquisition ceiling; it does not replace the v0.4 end-to-end result. v0.5 is retained separately
as a harness-environment failure: all 176 control commands used a host Python path that was not
available inside the Docker world.

The v0.6 protocol is pinned by
`matrix-protocol-v06-control-prefix-portable.json`. Its 176/176 raw cell files are present and
the final deterministic summary is:

| measure | count |
| --- | ---: |
| scheduled/attempted cells | 176 / 176 |
| complete records | 176 |
| Opus records / Sonnet records | 88 / 88 |
| control-prefix records | 176 |
| U-eligible records | 106 |
| U-ineligible records | 70 |
| recovery successes among U-eligible | 100 / 106 |
| compaction successes among U-eligible | 104 / 106 |
| complete U/R/C triplets | 99 |
| required complete triplets | 100 |

The hard gate therefore fails by one qualified triplet. All seven U-eligible divergences are on
the `tests` fixture under Sonnet and all carry `ValueError: unverified_progress`; one record has
both R and C fail, five have R-only failure, and one has C-only failure. This is a named fixture /
model concentration, not evidence of a universal missing ContinuationState field or an RGR-only
defect. The raw identities and branch outcomes remain in `matrix-v06-control-prefix/*.json`.

Because the fixed gate failed, the blinded holdout was not consumed, Continuation Contract v0 was
not published, and no state, prompt, fixture, schema, or RGR correction was admitted. The scoped
finding is: the harness can produce 99/106 checkpoint-ready U/R/C triplets across two models, but
the required 100-pair evidence threshold is not earned; the end-to-end v0.4 prefix limitation also
remains unresolved.

### Transcript audit of the seven divergences

The preserved transcripts show an existing composition detail: `continuation_prompt()` already
renders `GOAL:`, and the generic live provider renderer wraps that text again, so R/C model inputs
contain `GOAL:\nGOAL:` while U contains one wrapper. This behavior was present in the pinned run and
was identical in intent across R and C; it was not changed post hoc. The divergent Sonnet replies
also include read-only loops and broad full-file rewrites rather than one verified unit. These
observations support a future prompt-composition counterfactual, but do not establish that it is a
Cairn state defect. Under the protocol's correction rule, no prompt change, frozen rerun, or
holdout is admitted after the 99/100 gate failure.

## v0.7 single-GOAL counterfactual — invalidated

The approved v0.7 counterfactual changed only R/C prompt composition: the durable continuation
body was passed to the renderer without its already-rendered outer `GOAL:` line, producing exactly
one renderer-owned wrapper. The control prefix, ContinuationState, RGR, fixtures, models, and
verification remained pinned to v0.6. The protocol is
`matrix-protocol-v07-single-goal.json`; v0.6 remains the immutable paired baseline.

The complete raw audit passed: all 176 registered filenames are present, all records parse, all
records carry `prefix.mode=control` and `prompt_composition=single_goal`, both model configurations
have 88 records, and every pinned source hash matches. The final summary is:

| measure | v0.7 count |
| --- | ---: |
| scheduled/attempted cells | 176 / 176 |
| complete records | 176 |
| Opus records / Sonnet records | 88 / 88 |
| U-eligible records | 106 |
| U-ineligible records | 70 |
| recovery successes among U-eligible | 104 / 106 |
| compaction successes among U-eligible | 104 / 106 |
| complete U/R/C triplets | 98 |
| required complete triplets | 100 |

The v0.7 hard gate fails by two triplets and is one triplet below the v0.6 paired baseline (99).
The 176 filename-matched cell comparison shows no improvement outside the concentrated
`sonnet/tests` stratum: Opus `bugfix`, `config`, `tests`, and all `followup` strata retain the
same triplet outcomes; the only triplet gains and losses occur within Sonnet `tests`, with a net
loss. The named duplicated-wrapper hypothesis therefore does not replicate and is invalidated as
a general Cairn correction. The observed changes are model/task stochasticity, not evidence that
ContinuationState or RGR needs a schema or semantic change.

Per the pinned correction rule, the blinded `phase2_holdout` was not consumed and
Continuation Contract v0 was not published. No further prompt, fixture, schema, RGR, framework, or
effect change is admitted from this experiment. The current blocker is empirical: the frozen
checkpoint-ready reference has not earned the 100-pair evidence gate, and the only authorized
prompt-composition counterfactual failed to improve it.

## v0.8 verification-state pilot — neutral; no correction admitted

The completed v0.7 checkpoints provide a second, independent observation: the existing
`durable_core.verification` field is empty even after verified control-prefix steps. The v0.8 pilot
tested whether preserving pass `VerificationItem`s for those already-verified prefix steps changes
fresh R/C continuation behavior. It changed no production distillation or RGR code; the hook is
benchmark-scoped and the empty arm is the control. The paired protocols are
`matrix-protocol-v08-verification-empty.json` and `matrix-protocol-v08-verification-progress.json`.

Both arms completed their 20/20 registered records with matching model, fixture, split, and
single-GOAL controls. Raw records parsed and carried the expected arm metadata. Results:

| measure | empty arm | progress arm |
| --- | ---: | ---: |
| records | 20 | 20 |
| U-eligible | 18 | 18 |
| recovery successes | 19 | 18 |
| compaction successes | 18 | 18 |
| complete U/R/C triplets | 16 | 16 |

The 20 filename-matched pairs had 16 unchanged complete triplets. The only changes were one
R-success loss and one C-success loss in the progress arm; no improvement occurred in any
model/fixture/split stratum. The verification-state hypothesis is therefore neutral in this pilot,
with a weak negative signal rather than evidence of a causal continuity defect. No full frozen
rerun, holdout, schema change, distillation change, or RGR correction is authorized from this
result. Continuation Contract v0 remains unpublished.

## v0.9 model/task attribution probe — followup ceiling persists outside Claude Code

The v0.9 probe was pre-registered in `matrix-protocol-v09-model-attribution.json` before live
execution. It changed no Cairn code or semantics: the portable deterministic control prefix,
legacy prompt composition, empty verification capture, ContinuationState, RGR, and all fixtures
were retained. It used one independent `nvidia_nim` transport/model on the unchanged `bugfix` and
`followup` fixtures only; `phase2_holdout` was not read or executed. The v0.6 Claude Code matrix
is the frozen comparator.

All 12 registered cells have durable raw evidence. The first runner left one final `C` branch
partial when its provider worker was terminated after the 12th filename was written. That partial
JSON is retained unchanged; the exact same `followup/split=3/repetition=2` cell was completed to
`followup-s3-r02-complete.json` and is the counted replacement. No partial record is counted.

| fixture | records | U success | R success | C success | complete U/R/C triplets |
| --- | ---: | ---: | ---: | ---: | ---: |
| `bugfix` | 4 | 2 / 4 | 1 / 4 | 2 / 4 | 0 / 4 |
| `followup` | 8 | 0 / 8 | 0 / 8 | 0 / 8 | 0 / 8 |
| total | 12 | 2 / 12 | 1 / 12 | 2 / 12 | 0 / 12 |

Every `followup` U failure is a model/task execution failure (`model_finished_before_verification`
5/8, `model_no_verified_progress` 1/8, `unverified_mutation` 2/8); its R/C failures carry the
same classes, with no successful U baseline from which a recovery-only loss could be inferred.
The transcripts show prose, inspection loops, and non-single-unit rewrites rather than verified
one-unit edits. The simpler `bugfix` sanity cells also vary independently of Cairn (U 2/4, R 1/4,
C 2/4); one R failure is an HTTP 503 transport error. These are model/provider outcomes, not
evidence of a missing state field or RGR defect.

The independent model therefore reproduces the frozen Claude result that `followup` is not a
qualified continuation task under this action contract: v0.6 had U eligibility 0/32 for each
Claude configuration, and v0.9 has 0/8 for NIM. This supports the scoped attribution that the
current ~50% ceiling is dominated by model/task execution and provider reliability. It does not
prove the task is intrinsically impossible, and it does not establish a positive correction to
ContinuationState, distillation, RGR, prompt composition, or verification capture.

The v0.9 probe is diagnostic only: it is excluded from every Phase 2 gate, no holdout was consumed,
and Continuation Contract v0 remains unpublished. The next admissible experiment is a newly pinned
full frozen replication of the v0.6 matrix (all models, fixtures, splits, and repetitions) if a
second independent gate sample is needed; targeted followup-only reruns or prompt/fixture changes
would be benchmark tuning and are forbidden.

## v0.10 full frozen replication — 97/100 gate; no correction admitted

Protocol `matrix-protocol-v10-frozen-replication.json` was pinned before execution. It retains the
v0.6 control prefix, legacy prompt composition, empty verification capture, unchanged
ContinuationState/RGR, the four existing fixtures, both Claude Code models, four splits, and eight
repetitions per cell. The registered holdout was not read or executed.

The first pass produced 72 `command_failed` records because the Docker Linux engine was stopped;
those raw records are retained unchanged. After Docker was restored, the exact 72 cells were rerun
serially into `.retry.json` files, without overwriting originals. One interrupted non-invalid C
branch was completed into `-complete.json`; its partial original is also retained. The audit
selected exactly one complete record for each of the 176 registered cells (missing: 0).

| model | fixture | records | U success | R success | C success | complete U/R/C |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Opus | bugfix | 16 | 16 | 16 | 16 | 16 |
| Opus | config | 16 | 15 | 16 | 16 | 15 |
| Opus | tests | 24 | 24 | 24 | 24 | 24 |
| Opus | followup | 32 | 0 | 0 | 0 | 0 |
| Sonnet | bugfix | 16 | 16 | 16 | 16 | 16 |
| Sonnet | config | 16 | 16 | 16 | 16 | 16 |
| Sonnet | tests | 24 | 15 | 19 | 16 | 10 |
| Sonnet | followup | 32 | 0 | 0 | 0 | 0 |
| **total** |  | **176** |  |  |  | **97** |

The hard gate requires 100 complete triplets, so this replication misses by three. The 64
`followup` records fail U before a verified unit is established under both models; their R/C
failures therefore cannot identify a recovery-only loss. Outside that ineligible fixture, Opus has
one config U failure and Sonnet has stochastic tests failures; the failure classes are
`unverified_progress`, `unverified_mutation`, and one provider/CLI failure. There is no concentrated
RGR-only or ContinuationState-only loss. This is consistent with the earlier model-attribution
probe and does not establish a causal Cairn defect.

The conditional divergence audit is also negative for a compaction-specific defect. Among records
with U success, only two have R failure and four have C failure; the four C-only losses are all
`sonnet/tests/split=1` (`r01`–`r04`). For those four preserved runs, the first R and C continuation
inputs have identical `prompt_key`s and identical prompt/history lengths. C therefore received the
same model-visible durable state, re-grounded history, workspace, and continuation prompt as R;
the differing outcome is a fresh model response, not a serialized-state omission. The one U-success
R-failure/C-success case is in the same stochastic stratum. This evidence rules out admitting a
compaction-state or RGR correction from v0.10.

Per the pre-registered correction rule, no state schema, distillation, RGR, prompt, fixture, or
verification change is admitted. No holdout was consumed and Continuation Contract v0 remains
unpublished. The current finding is a reproducible empirical ceiling in model/task execution and
provider reliability, with a near-miss on the aggregate gate—not evidence that Cairn's recovery
semantics should be changed.

## Deterministic semantic control — serialization and compaction pass

To separate Cairn semantics from live-model variance, `benchmarks/phase2_semantic_control.py` runs
the existing reference U/R/C loop with the deterministic fake coding agent, the control prefix, and
the unchanged hidden fixture verifiers. It covers all four fixtures and all 11 non-terminal split
positions. The durable artifact is `semantic-control-v01.json`.

All 11 cells produced verified U, R, and C outcomes (`11/11` complete triplets). Final repository
digests matched across all three branches (`0` mismatches), and C was created from a serialized,
reloaded checkpoint with no original transcript. This establishes that the current checkpoint,
serialization, re-grounding, compaction, and hidden-verifier path is semantically sound under a
deterministic continuation; it does not raise the live-model gate or justify a state correction.

## Acquisition/continuity stratification — v0.10 conditional audit

`benchmarks/phase2_acquisition_continuity.py` selects one record per v0.10 cell, preferring the
registered retry or completion replacement and never overwriting raw files. Its durable output is
`v10-acquisition-continuity.json`.

The 176 attempts contain 102 U-eligible checkpoints and 74 acquisition failures. Conditional on
those 102 checkpoints, R succeeds 100 times, C succeeds 98 times, and 97 records complete all three
branches. The conditional divergence is one R-only failure, three C-only failures, and one record
where both fail. This is the correct denominator for continuity analysis; the 74 U-ineligible
records are model/task acquisition outcomes and cannot be interpreted as recovery loss.

The repository already contains independent live evidence for this capability confound. The
non-batchable chain study records B3/RGR success of `11/15` for `openai/gpt-oss-120b` (Groq) and
`1/2` for `nvidia/nemotron-3-super-120b-a12b:free` (OpenRouter); the other two provider/model
studies produced no fired cells and transport errors. Those manifests are not U/R/C continuity
evidence, but they justify treating model/provider acquisition as a separately calibrated axis
before another live contract attempt.

The next-study boundary is pinned in `matrix-protocol-v11-neutral-tranche.json` as design-only. It
requires disjoint calibration and holdout tasks, a minimum of 100 eligible checkpoints, and
conditional R/C gates before the holdout can be consumed. No v0.10 result is reclassified by this
design, and no current fixture is edited to satisfy it.

## C-only replay control — causal continuity check passes

The three valid v0.10 C-only divergences (U and R both succeeded) were replayed offline with
`benchmarks/phase2_replay_control.py`. Each replay started from the original prefix checkpoint,
serialized/reloaded it through the existing compaction path, and fed the recorded successful R
replies to a fresh C branch. All three reached the hidden verifier (`3/3`), with identical final
artifact digests. This is direct causal evidence that the compaction/checkpoint path can preserve
the work when the same actions are supplied; the original C losses are model-response variance.
The replay artifact is `v10-c-replay-u-r-success.json`.

## Independent chain calibration control — deterministic U/R/C pass

The pre-registered v11 calibration task is the independently authored, non-batchable
`chain-6` hash-chain task. `benchmarks/phase2_chain_urc.py` runs the same reference
TerminalWorld loop at each of its five non-terminal checkpoints, then exercises U,
fresh-process R, and serialized/reloaded C branches without changing Cairn semantics.
The durable artifact is `chain-urc-v01.json`.

All five cells produced verified U/R/C outcomes (`5/5` complete triplets), and every
branch produced the same final workspace digest (`0` mismatches). R reports a fresh
resume and C reports the compacted continuation path. This is a deterministic
calibration control for the v11 denominator and serialization semantics; it is not a
live-model contract result and does not consume the holdout.

The existing live chain manifests remain capability diagnostics only: `gpt-oss-120b`
on Groq reached `11/15` B3 successes, while the NIM Nemotron study reached `1/2` and
also recorded rate-limit errors. Those results motivate a capability-matched live
tranche, but they do not identify a ContinuationState or RGR defect.

## v0.11 live tranche — NIM half complete; frozen gate is unreachable

`matrix-protocol-v11-neutral-tranche.json` pins 110 cells across two independent
provider/model configurations, all four frozen repository fixtures, every non-terminal
split, and five repetitions. The first external half uses
`nvidia/nemotron-3-ultra-550b-a55b` through NVIDIA NIM. All 55 registered NIM cells are now
terminal. The interrupted primary `tests/s2/r04` record remains preserved and its completed
retry is selected. The 55 Groq cells have not run. The holdout has not been read or executed.

Two benchmark-runner defects were corrected without changing Cairn semantics, prompts,
fixtures, or scoring. External model IDs are now serialized to filesystem-safe cell stems,
and a primary record containing only some branches is preserved while the exact cell resumes
to the selector's existing `.retry.json` path. The raw malformed-path and interrupted records
remain on disk. Tests cover both corrections.

`v11-nim-half-acquisition-continuity.json` is the deterministic audit of the completed NIM
half:

- 55 attempts selected, with no incomplete records and 23 top-level terminal-invalid attempts;
- 25 U-eligible checkpoints and 30 acquisition-ineligible attempts;
- conditional R success `24/25`, C success `20/25`, and `20/25` complete triplets;
- four C-only divergences and one terminal record where both R and C fail.

The 23 top-level terminal failures are 18 `model_no_verified_progress` and five
`model_finished_before_verification`. The other seven acquisition-ineligible attempts fail in
U: four unverified mutations, one premature finish, one unverified-progress outcome, and one
provider 503. These are reported as acquisition/provider failures rather than continuity loss.

The five eligible continuity divergences do not establish a state defect. Replaying the
successful R actions for the four C-only cells through a fresh compacted branch reaches the
hidden verifier `4/4` (`v11-c-replay-nim-partial.json`). Replaying U's successful actions for
the one terminal R-and-C-fail cell also reaches it `1/1`
(`v11-c-replay-nim-u-source.json`). Thus all observed terminal NIM divergences complete under
counterfactual action parity (`5/5`), attributing the live losses to fresh model-response
variance rather than an omitted ContinuationState field. No state, RGR, prompt, or verifier
correction is admitted.

The frozen v0.11 gate is now mathematically unreachable. The protocol requires at least 100
eligible checkpoints and 100 complete triplets. NIM contributes 25 eligible checkpoints; even
if every one of the 55 unrun Groq cells succeeded, the maximum would be 80 eligible checkpoints
and 75 complete triplets. Running Groq therefore cannot change the gate verdict and would not be
a valid reason to consume the holdout.

This is a blocking finding, not a Cairn correction trigger. The deterministic controls pass,
Phase 1 parity remains intact, and every observed eligible NIM divergence completes under
counterfactual action parity. The failed denominator instead shows that this provider/model and
fixture distribution cannot acquire enough verified checkpoints for the pre-registered contract
test. No state, RGR, prompt, fixture, verifier, or threshold change is admitted. The Groq half and
blinded holdout remain unconsumed; Continuation Contract v0 is not published.

## v0.12.1 powered live gate — passed

The corrected, pre-registered v0.12.1 live matrix completed all 242 cells with no selected-record
incompletes, missing cells, or terminal-invalid records. The qualifying results are 141 eligible
U checkpoints, 135 conditional R successes, 135 conditional C successes, and 133 complete U/R/C
triplets. This exceeds every frozen live threshold of 100.

Eight eligible divergences were observed: four R-and-C failures, two C-only failures, and two
R-only failures, all in Sonnet `tests/s1`. Every required target-aware counterfactual verified:
U→R `4/4`, U→C `4/4`, R→C `2/2`, and C→R `2/2`. The `12/12` action-parity result provides no
causal evidence of a ContinuationState, RGR, verifier, or compaction defect, so no correction is
admitted.

Phase 1 parity is byte-identical at SHA-256
`7f969a9c861ad8e85a8103e3b421c78d3a1f2ddb8a37b3d2316e0e8c80bbcc56`.
The full repository suite passes (`232 passed`), scoped Ruff passes, and `git diff --check` reports
no whitespace error. The live protocol SHA-256 is
`0d5a1a7da9c2adad1647365a22e0c2793c67b71435e7cbf831ab3e2b1def746d`.

The holdout-admission machine check read only `v12-acquisition-continuity.json` and the four replay
summaries, enforced the frozen counts plus `verified == replayed`, and exited zero with:

```json
{"verdict":"PASS","attempts":242,"eligible":141,"R":135,"C":135,"triplets":133,"replayed":12.0,"verified":12.0,"phase1_sha":"7f969a9c861ad8e85a8103e3b421c78d3a1f2ddb8a37b3d2316e0e8c80bbcc56","tests":"232 passed"}
```

`v12-holdout-admission.json` records that verdict and the hashes of its inputs. The sealed v0.12
holdout is admitted without modifying its pre-run `sealed-unconsumed` protocol.

## v0.12 holdout — terminal blocking finding

The admitted holdout completed all 60 registered cells (30 Opus and 30 Sonnet) with no missing,
incomplete, terminal-invalid, or retry records. Its conditional gate nevertheless has zero
eligible U checkpoints, zero R successes, zero C successes, and zero complete triplets. No
eligible divergence exists to replay.

This is a task-specification failure, not evidence of continuity loss. Across all 180 final branch
workspaces (60 each for U, R, and C), the normalize, clamp, and exact-token contracts pass. Every
workspace implements `render_tags(["a", "b"])` as `"[a][b]"` and `render_tags([])` as `""`.
The hidden verifier instead requires `"[a|b]"` and `"[]"`. The task supplied to the models says
only “render tags in brackets”; it does not specify a pipe separator, a single enclosing bracket
pair, or the empty-list representation. The identical U/R/C behavior therefore cannot establish
a ContinuationState or RGR defect.

The holdout hard gate fails and Continuation Contract v0 is not published. Per the pre-registered
failure rule, this holdout cannot be edited and reused after its hidden expectations are exposed.
No state, RGR, prompt, runtime, or verifier correction is admitted from this result. A future
attempt requires a new independently authored and sealed holdout whose public task text fully
specifies every behavior scored by its hidden verifier; it must be pre-registered before any model
call and cannot be combined with this failed holdout.

`v12-holdout-verdict.json` preserves the terminal attribution. The holdout protocol SHA-256 is
`0e68107dfef775fa764a924ee0163a1b053640a01a5f51376bca859b0edb4fcc`; the analysis SHA-256 is
`952d24d3efdd834cf428609e6124baac6bad075076356a08b422332957a89501`.

## Reproduction

```powershell
$env:PYTHONPATH='D:\project-unknown-phase1\src;D:\project-unknown-phase1'
python benchmarks\phase2.py --freeze results\phase-1\live-claude-sonnet-coverage-1.jsonl results\phase-1\live-claude-sonnet-accumulation-4x.jsonl results\phase-1\live-claude-opus-coverage-1.jsonl results\phase-1\live-claude-opus-accumulation-4x.jsonl --output results\phase-2\control-freeze-recheck.json
python benchmarks\phase2_semantic_control.py --output results\phase-2\semantic-control-v01.json --base-dir results\phase-2\semantic-control-v01-runs
python benchmarks\phase2_acquisition_continuity.py --matrix-dir results\phase-2\matrix-v10-frozen-replication --protocol results\phase-2\matrix-protocol-v10-frozen-replication.json --output results\phase-2\v10-acquisition-continuity.json
python benchmarks\phase2_replay_control.py --matrix-dir results\phase-2\matrix-v10-frozen-replication --records results\phase-2\matrix-v10-frozen-replication\sonnet-tests-s1-r01.json results\phase-2\matrix-v10-frozen-replication\sonnet-tests-s1-r02.json results\phase-2\matrix-v10-frozen-replication\sonnet-tests-s1-r04.json --source-branch R --output results\phase-2\v10-c-replay-u-r-success.json
python benchmarks\phase2_chain_urc.py --n 6 --base-dir results\phase-2\chain-urc-v01-runs --output results\phase-2\chain-urc-v01.json
python benchmarks\phase2_acquisition_continuity.py --matrix-dir results\phase-2\matrix-v11-live-tranche --protocol results\phase-2\matrix-protocol-v11-neutral-tranche.json --output results\phase-2\v11-nim-half-acquisition-continuity.json
python benchmarks\phase2_replay_control.py --matrix-dir results\phase-2\matrix-v11-live-tranche --records results\phase-2\matrix-v11-live-tranche\nvidia_nemotron-3-ultra-550b-a55b-bugfix-s0-r04.json results\phase-2\matrix-v11-live-tranche\nvidia_nemotron-3-ultra-550b-a55b-config-s0-r03.json results\phase-2\matrix-v11-live-tranche\nvidia_nemotron-3-ultra-550b-a55b-config-s0-r04.json results\phase-2\matrix-v11-live-tranche\nvidia_nemotron-3-ultra-550b-a55b-tests-s1-r02.json --source-branch R --output results\phase-2\v11-c-replay-nim-partial.json
python benchmarks\phase2_replay_control.py --matrix-dir results\phase-2\matrix-v11-live-tranche --records results\phase-2\matrix-v11-live-tranche\nvidia_nemotron-3-ultra-550b-a55b-tests-s0-r01.json --source-branch U --output results\phase-2\v11-c-replay-nim-u-source.json
python benchmarks\phase2_matrix.py --protocol results\phase-2\matrix-protocol-v12-powered-control-prefix.json --model opus --output-dir results\phase-2\matrix-v12-powered-control-prefix
python benchmarks\phase2_matrix.py --protocol results\phase-2\matrix-protocol-v12-powered-control-prefix.json --model sonnet --output-dir results\phase-2\matrix-v12-powered-control-prefix
python benchmarks\phase2_acquisition_continuity.py --matrix-dir results\phase-2\matrix-v12-powered-control-prefix --protocol results\phase-2\matrix-protocol-v12-powered-control-prefix.json --output results\phase-2\v12-acquisition-continuity.json
python benchmarks\phase2.py --freeze results\phase-1\live-claude-sonnet-coverage-1.jsonl results\phase-1\live-claude-sonnet-accumulation-4x.jsonl results\phase-1\live-claude-opus-coverage-1.jsonl results\phase-1\live-claude-opus-accumulation-4x.jsonl --output results\phase-2\control-freeze-recheck-v12.json
python benchmarks\phase2_matrix.py --protocol results\phase-2\holdout-protocol-v12.json --model opus --output-dir results\phase-2\matrix-v12-holdout
python benchmarks\phase2_matrix.py --protocol results\phase-2\holdout-protocol-v12.json --model sonnet --output-dir results\phase-2\matrix-v12-holdout
python benchmarks\phase2_acquisition_continuity.py --matrix-dir results\phase-2\matrix-v12-holdout --protocol results\phase-2\holdout-protocol-v12.json --output results\phase-2\v12-holdout-acquisition-continuity.json
```

## P2.4 independent holdout reconstitution — passed

The independently authored and sealed `p24_queue_policy` holdout completed all 60 registered
primary cells: Claude Code Opus and Sonnet, three nonterminal checkpoints, and ten repetitions
per model/checkpoint. Every pinned P2.4 input still matches its protocol SHA-256. The Phase 1
control-freeze recheck is byte-identical at SHA-256
`7f969a9c861ad8e85a8103e3b421c78d3a1f2ddb8a37b3d2316e0e8c80bbcc56`.

Forty cells acquired an eligible U checkpoint. All forty then completed U/R/C: 40 recovery
successes, 40 transcript-unavailable serialized compaction successes, 40 complete triplets, and
zero structural failures. Fresh R and C workers never used parent in-memory history; C never had
the original transcript; every accepted continuation action advanced the ordered public contract;
and every branch terminated under the public verifier. There were no eligible divergences, so the
pre-registered identical-action replay obligation was vacuously satisfied.

Twenty Sonnet cells (all split 0 and split 1 repetitions) are preserved as `ValueError:
unverified_progress`. Their U continuation attempted multiple remaining public units in a single
mutation, which the frozen one-unit verifier rejected before R/C existed. This is a model
checkpoint-acquisition/action-granularity finding, not a ContinuationState, RGR, or compaction
defect; it is excluded from conditional continuation outcomes rather than hidden or retried.

The final full suite passes: `248 passed in 292.53s`. `p24-analysis.json` and
`p24-verdict.json` contain the selected-record counts, gate decision, and limitation. The
independent holdout therefore admits the narrow behavioral `docs/design/continuation-contract-v0.md`.

Reproduction uses the sealed protocol and raw evidence:

```powershell
python benchmarks\p24_matrix.py --protocol results\phase-2\p24-holdout-protocol.json --model opus --output-dir results\phase-2\p24-matrix
python benchmarks\p24_matrix.py --protocol results\phase-2\p24-holdout-protocol.json --model sonnet --output-dir results\phase-2\p24-matrix
python -m pytest -q
```
