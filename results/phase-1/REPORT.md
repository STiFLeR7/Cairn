# Phase 1 deterministic RecoveryBench evidence

Status: **Phase 1 exit gate passed** for harness `recoverybench.v0.2`. Deterministic control and
the required external two-model live sample are complete.

The live adapter has an additional prerequisite: an available Docker terminal sandbox. It mounts
only the fixture repository, disables networking, receives no host environment, and drops Linux
capabilities; the local subprocess executor is intentionally refused for real providers. Docker
Desktop is available in this execution environment and supplied the published live pilot.

## External live pilot

One bounded pilot now provides a valid fired pair for `openrouter:stealth/Ox-alpha` on the
`bugfix` fixture, with failure injected after clean checkpoint 2. Its baseline completed 3/3 work
units; a distinct fresh process recovered the remaining unit and passed the verifier. The artifact
digest matched the baseline, recovery tax was one work unit, and the Phase 1 scope has no external
effects.

- JSONL: `live-pilot-stealth-ox-alpha-bugfix-fault-1.jsonl`
- SHA-256: `14DC3D205FFD46D437B22D20AE39E3940708044B32AECA66C2FEFCAE0C2E427F`
- Raw worker receipts and approved fixture-only transcripts:
  `live-pilot-stealth-ox-alpha-bugfix-fault-1/`

This is evidence for one model/configuration and one fault cell only. It does **not** meet the
40-valid-pair, two-independent-model Phase 1 exit gate.

## NVIDIA NIM validation

`nvidia/nemotron-3-super-120b-a12b` passed two targeted fired pairs (`bugfix` fault 1 and
`config` fault 0), each with a fresh-process recovery, artifact equivalence, no regression, and
zero duplicate effects. The raw records are `live-pilot-nvidia-nemotron-*.jsonl`.

It did **not** pass coverage: the first 11-cell run produced 1 valid pair and the corrected
11-cell rerun produced 0. Recorded failures include multi-unit or otherwise unverified mutations,
and no verified progress; these are retained in `live-nvidia-nemotron-coverage-{1,2}.jsonl`.
They are model outcomes, not exclusions from the evidence.

After applying NVIDIA's documented non-empty coding payload, Super 120B was retested on the
previously difficult `tests` fault-0 cell. It made eight baseline turns but still ended with
`model_no_verified_progress`; no crash was injected. The retained result is
`live-pilot-nvidia-super-tests-fault-0-payload.jsonl` (SHA-256
`A456728A3CF57EE88E8061516D01F9C2125B92746B572344F07050EA70ADD8E4`).

`nvidia/nemotron-3-ultra-550b-a55b` now adds one valid fired pair on `bugfix` fault 1. The
baseline, injected-crash worker, and fresh resume worker completed 3/3 work units; the hidden
verifier passed, recovery used no in-memory history, and no effects were duplicated. The source
formatting differed by one blank line, so artifact equivalence is false; this does not weaken the
live gate, which is based on hidden-verifier recovery success versus baseline. The raw record is
`live-pilot-nvidia-nemotron-ultra-bugfix-fault-1.jsonl` (SHA-256
`A01E9E1BA3445E4FE2260727745618F0C7F841D868ECBD4A51869A73DE38DE5B`).

Its 11-cell coverage matrix is negative evidence, not a gate pass: 4 valid fired pairs; five
baseline failures; and two resume failures. Baseline success was 6/11 (0.545), while fresh-process
recovery success was 4/11 (0.364), below the locked 10-percentage-point tolerance. The artifact
is `live-nvidia-ultra-coverage-1.jsonl` (SHA-256
`211674B72E5EE27EB91AA5ABC1391D430DF749B5DAD31731C238AE4BC0AFBC62`).

`nvidia/nemotron-3.5-lightning-30b-a3b` is excluded after one `bugfix` fault-1 pilot. It made
four baseline turns but never produced the next verified work unit (`model_no_verified_progress`),
so no crash was injected. The retained record is `live-pilot-nvidia-lightning-bugfix-fault-1.jsonl`
(SHA-256 `48AA53012BD0FB1B68F6B4EF3700E406BC7B6CF3BE63B597DDD15483427BD756`).

That first Lightning run included a Super/Ultra-only request field. After scoping that payload to
the documented models, Lightning completed baseline but the independently restarted crash worker
still ended with `model_no_verified_progress` before checkpoint 2. This is a direct recovery
failure, retained in `live-pilot-nvidia-lightning-bugfix-fault-1-scoped.jsonl` (SHA-256
`C361B28F43C388F76022A227F01D7D11B2D044A1BD6E80882BC7E9CE62C1A923`).

That raw crash transcript exposed a harness parser bug: the model returned executable bare Python
followed by a hallucinated `returncode: 0` line. The parser now accepts the executable prefix,
which still must pass the same one-unit verifier. The parser-corrected Lightning rerun passed
baseline, fired after clean checkpoint 2, recovered in a distinct process with no in-memory
history, and passed the hidden verifier with no regression or duplicated effects. Its final
formatting differs from baseline, so artifact equivalence is false but this is not a live-gate
criterion. The record is `live-pilot-nvidia-lightning-bugfix-fault-1-parser.jsonl` (SHA-256
`1DA73BC5B39F116C29CCE4481855C0146961A0C5F067EB32BAA0ADFEB25E73CC`).

The complete parser-corrected Lightning discovery matrix is still negative: all 11 cells are
retained failures, so it supplies zero valid fired pairs. Baseline success was 2/11 (0.182) and
fresh-process recovery success was 0/11. Nine failures occurred in baseline and two in resume;
two baseline failures were NVIDIA DNS resolution errors and are retained as provider-availability
evidence rather than attributed to agent behavior. The remaining cells include premature finish,
no verified progress, unverified mutation, and unverified multi-unit progress. Consequently,
Lightning is not gate-eligible. The artifact is `live-nvidia-lightning-coverage-2.jsonl`
(SHA-256 `73E4747CBD82B9AA8AF0697A6DA631404C990A55834DBA66B429230754BC1E69`).

The matrix also exposed that `urllib`'s socket timeout is not a total request deadline. The
OpenAI-compatible transport now enforces the configured total deadline around each request; its
offline regression test and the current complete Phase 1 harness suite passed (72 tests). This
prevents a provider response from wedging an evidence matrix indefinitely; it neither retries a
request nor changes any fixture, verifier, or recovery condition.

`openai/gpt-oss-120b`, the requested next NVIDIA NIM candidate, also completed a full 11-cell
matrix with zero valid fired pairs. Baseline success was 4/11 (0.364) and fresh-process recovery
success was 0/11. The retained failures comprise seven baseline, two crash, and two resume stages;
their immediate causes were five unverified multi-unit progress attempts, two unverified mutations,
and four failures to make verified progress. No provider-availability error occurred in this
matrix, so this is direct harness evidence that GPT-OSS 120B is not gate-eligible under the locked
single-verified-work-unit protocol. The artifact is `live-nvidia-gptoss120-coverage-1.jsonl`
(SHA-256 `76E9FE94E334520F94CCF14E76679D80690F956885C13FED878F5C3C15CB77CF`).

The available NIM `openai/gpt-oss-20b` route was also tested before the switch to OpenRouter.
All 11 cells ended in baseline with `model_finished_before_verification`, yielding zero valid
pairs; the smaller model did not improve single-action protocol compliance. The retained artifact
is `live-nvidia-gptoss20-coverage-1.jsonl` (SHA-256
`F92713CF3E618D47B6651D6EF70C0FFED2067EFBC3F52E486592C9DC995BE940`).

`deepseek-ai/deepseek-v4-flash-0731` was present in the NIM model catalog but returned HTTP 404
on every first fixture request. Its complete 11-cell artifact therefore records 11 baseline
provider-availability failures, zero baseline success, and zero valid pairs; it does **not**
support an inference about agent recovery capability. The artifact is
`live-nvidia-deepseek-v4-flash-coverage-1.jsonl` (SHA-256
`B0645C7E48058E7F76F3FBFDD564044338E31B420BBB3D07147F2F6E40799FFD`).

`moonshotai/kimi-k2.6` was likewise catalog-listed but unavailable at the NIM chat endpoint:
each of its 11 first fixture requests returned HTTP 404. This is provider-availability evidence,
not a recovery assessment. The retained artifact is `live-nvidia-kimi-k26-coverage-1.jsonl`
(SHA-256 `C6503A14DE8B4E4E912B3FD76E46BA221E9F9842DC507670B97F6BA66D92C131`).

On OpenRouter, `minimax/minimax-m3:free` passed a minimal availability probe and then completed
the same 11-cell matrix with two valid fired recoveries, zero duplicated effects, baseline success
4/11 (0.364), and recovered success 2/11 (0.182). The remaining failures were seven baseline, one
crash, and one resume stage, including premature finish and unverified changes. This confirms the
OpenRouter path can produce genuine recovery evidence but is below the locked 10-percentage-point
recovery-fidelity tolerance and cannot be promoted. The retained artifact is
`live-openrouter-minimax-m3-free-coverage-1.jsonl` (SHA-256
`E337D32939215FD6AC29628046A98CC81719D845D464028FA5F518DA9ADBD45C`).

`minimaxai/minimax-m3` passed a zero-data health probe but returned provider HTTP 429 on the
first fixture prompt, before an agent action. It is retained as availability evidence rather than
a model-quality result in `live-pilot-nvidia-minimax-m3-bugfix-fault-1.jsonl` (SHA-256
`6E7124B24FD60E11313AEBEFAC25F0B17B90EEE39B3C000C690D4960D9642C5E`).

## Claude Code validation

The installed Claude Code client is used only as a no-tools response transport: Cairn remains the
sole executor inside the Docker terminal sandbox. `sonnet` completed an 11-cell matrix with three
valid fired fresh-process recoveries. Baseline and recovery success were each 3/11 (0.273), so its
observed recovery fidelity is within the locked 10-percentage-point tolerance and no effects were
duplicated. Eight baseline cells failed the single-verified-work-unit protocol (three unverified
mutations, three unverified progress attempts, and two no-progress cases). The complete artifact
is `live-claude-sonnet-coverage-1.jsonl` (SHA-256
`F48D34B1D2062E7E2541F84FF7C4B3ED0600C3109A5E7794FDEB25F08BA0D181`). This is retained as
partial external evidence, not a gate pass: it supplies only three valid pairs.

`haiku` completed the same 11-cell matrix with four valid fired recoveries. Baseline success was
5/11 (0.455) and fresh-process recovery success was 4/11 (0.364), a 0.091 difference that is
inside the locked 10-percentage-point tolerance; no effects were duplicated. Its seven retained
failures comprise six baseline and one crash-stage protocol failures (three unverified mutations,
three no-progress cases, and one unverified-progress attempt). The artifact is
`live-claude-haiku-coverage-3.jsonl` (SHA-256
`4BE4E362BB0B10D4C444166FBB75D1EA754D87820A4449983F402BCB711E84E1`). This too is not a gate
pass: it contributes four valid pairs only.

`opus` completed its 11-cell matrix with six valid fired recoveries. Baseline success was 7/11
(0.636) and recovery success was 6/11 (0.545), also a 0.091 difference within tolerance and with
zero duplicate effects. Its five retained failures comprise four baseline and one crash-stage
unverified mutations. The artifact is `live-claude-opus-coverage-1.jsonl` (SHA-256
`FEEE45C66BE4A6E588C1219072926B1763C8A7B9C2E4668D659F96F99B145D23`). It contributes six valid
pairs, but does not by itself pass the 40-pair gate.

The four-repeat Sonnet accumulation matrix retains all 44 rows: 18 valid fired recoveries,
baseline success 18/44 (0.409), and recovery success 18/44 (0.409), with zero duplicate effects.
Its 26 baseline failures comprise 17 unverified-progress attempts, six unverified mutations, and
three no-progress cases. The artifact is `live-claude-sonnet-accumulation-4x.jsonl` (SHA-256
`B50EF07CCD135974C0F547FD9928A8EFEA7651EE9C2E2C2F2D63D54747D9E300`). This is external evidence
for the locked protocol and is incorporated into the aggregate gate adjudication below.

The paired four-repeat Opus matrix also retains all 44 rows: 28 valid fired recoveries, baseline
and recovery success both 28/44 (0.636), and zero duplicate effects. Its 16 retained baseline
failures are unverified mutations. The artifact is `live-claude-opus-accumulation-4x.jsonl`
(SHA-256 `9C8C50E3893C506B871D529C6157A55C44E389E61046342DBA89A4A320FA0BDB`).

## Corrected full-history control matrix

- Fixtures: `bugfix` (3 work units), `config` (3), `tests` (4), `followup` (5). Their verifiers
  inspect repository behavior rather than matching exact source snapshots, and each clean
  checkpoint carries the complete verified action history.
- Faults: every non-terminal clean-checkpoint boundary (11 per repeat).
- Repeats: 10 per matrix, two independent matrices.
- Valid fired recoveries: 110/110 in each matrix.
- Task success: 1.0; artifact equivalence: 1.0; no-regression: 1.0 in each matrix.
- Fresh-process recovery: each recovery record has a durable `failure_fired` receipt and a PID
  distinct from the crash worker.
- Reproducibility: `python benchmarks/recoverybench.py --compare ...a.jsonl ...b.jsonl` returned
  `True`, after removing only per-run IDs and worker PIDs.

## Raw artifacts

| Artifact | SHA-256 |
| --- | --- |
| `recoverybench-harness-v0.2-a.jsonl` | `2acbfc2cc30628645455a3d2a188a2ca677412e7d225b48ea35d8ccacf3d27d0` |
| `recoverybench-harness-v0.2-b.jsonl` | `fea9a33f30ec349b3e784fbb6f6bd79a4042b68bd39fb17406816cbad7ade267` |

## Gate status

Deterministic criteria 1–3 are supported by these v0.2 artifacts. The finalized Claude Code
aggregate combines 110 rows from the four retained Sonnet and Opus artifacts: 55 valid fired
paired recoveries across two independent model configurations; baseline success 0.509; recovery
success 0.500; and zero duplicate effects. The recovery difference (0.009) is inside the locked
10-percentage-point tolerance. `phase_1_verdict(...)` returns every criterion true. The overall
Phase 1 verdict is therefore **passed**.

The unversioned `recoverybench-deterministic-*.jsonl` files are retained only as superseded v1
evidence. The `recoverybench-v2-*` files are retained only as pre-v0.2 checkpoint-history evidence.
