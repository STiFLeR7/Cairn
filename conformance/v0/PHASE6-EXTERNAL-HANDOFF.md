# Phase 6 external-authority handoff

**State: `STAGE 6A PASS; PHASE 6 BLOCKED / UNADMITTED`.** The frozen Stage 6A
candidate and reference evidence are published at
[`results/phase-6/stage-6a-haiku-candidate-7/`](../../results/phase-6/stage-6a-haiku-candidate-7/).
The remaining procedure requires a genuinely separate SEALER and uninvolved
REPRODUCER; it does not claim Phase 6 conformance or alter Cairn contracts.

For candidate 7, the IMPLEMENTER build/freeze and v2 reference-execution
sections are complete and immutable. Do not repeat or adapt them. The next
authorized transition starts at **Holdout and reproduction** with the published
`candidate.bundle`. Commands below that mention the historical v0 evaluator are
format guidance only; the corrected v2 witness and candidate-7 publication
manifest are the authoritative Stage 6A inputs.

## Objective and boundary

Prove or falsify that an independently implemented coding-agent host meets
the existing recovery, continuation, compaction, and receipt/reconciliation
semantics on `D:/imgshape`. The unchanged v0 evaluator must accept a 30-cell
reference matrix, a separately sealed 30-cell holdout, and an uninvolved
reproduction.

The host owns its runtime, loop, state, persistence, model/session handling,
tools, and scheduling. Cairn supplies only the copied kit and this procedure.

## Independent actors

| Actor | Required | Can do | Cannot do |
| --- | --- | --- | --- |
| IMPLEMENTER | Separate repository/workspace; Claude Code team using **Haiku only**. | Independently build and freeze a host. | Read/import Cairn runtime, adapters, `Agent`, internal state schemas, past candidate code, or unreleased holdout data. |
| SEALER | Different human/session from IMPLEMENTER. | Capture baseline; author/seal reference and post-freeze holdout. | Modify, coach, or rebuild frozen implementation. |
| REPRODUCER | Uninvolved human/session. | Run frozen implementation and copied evaluator in a fresh environment. | Tune/prompt/patch implementation, kit, workload, verifier, or evidence. |

Cairn maintainers may inspect/evaluate evidence, but may not author or repair
the submitted host. A failed candidate stops; it is never tuned against a
reference or holdout.

## Information available to IMPLEMENTER

Only these inputs are allowed:

1. A byte-identical copy of `README.md`, `evidence.schema.json`,
   `vectors.json`, and `evaluate.py`. `vectors.json` is the frozen reference
   semantic vector set and is unchanged for both reference and holdout.
2. A released, sealed reference package.
3. A read-only `imgshape` snapshot supplied by SEALER.
4. This public procedure.

`D:/imgshape` is an external workload, never a Cairn implementation. Forbidden
inputs include every other Cairn source file, runtime dependency, adapter,
internal state format, previous candidate repository/evidence, private
verifier/holdout, and prior agent/session transcript.

## Preserve D:/imgshape exactly

SEALER runs this before anyone executes a workload. It writes only outside
the target and must never be followed by `reset`, `clean`, checkout, rebase,
restore, or any mutation command inside `D:/imgshape`.

```powershell
$Target = 'D:/imgshape'
$RunRoot = 'D:/phase6-external-run'
New-Item -ItemType Directory -Force -Path $RunRoot | Out-Null
git -C $Target rev-parse HEAD | Set-Content "$RunRoot/imgshape-head.txt" -NoNewline
git -C $Target status --porcelain=v1 | Set-Content "$RunRoot/imgshape-status-before.txt" -NoNewline
git -C $Target diff --binary | Set-Content "$RunRoot/imgshape-tracked.patch" -NoNewline
robocopy $Target "$RunRoot/imgshape-snapshot" /E /COPY:DAT /DCOPY:DAT /R:0 /W:0 /XD .git
if ($LASTEXITCODE -gt 7) { throw "snapshot failed: robocopy exit $LASTEXITCODE" }
Get-ChildItem "$RunRoot/imgshape-snapshot" -Recurse -Force -File | Sort-Object FullName |
  ForEach-Object {
    $p = $_.FullName.Substring("$RunRoot/imgshape-snapshot".Length).TrimStart([char[]]@('\','/'))
    [pscustomobject]@{path=$p;bytes=$_.Length;sha256=(Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
  } | ConvertTo-Json -Depth 4 | Set-Content "$RunRoot/imgshape-snapshot-manifest.json"
Get-FileHash "$RunRoot/imgshape-snapshot-manifest.json" -Algorithm SHA256 |
  Select-Object Path,Hash | ConvertTo-Json | Set-Content "$RunRoot/imgshape-baseline-digest.json"
```

Every reference, holdout, and reproduction run operates on a new copy beneath
`$RunRoot`. Re-run the baseline commands afterward. Any difference in target
head, status, patch, or snapshot manifest is `INCONCLUSIVE` until the owner
resolves it.

## IMPLEMENTER: build and freeze

1. Record separate repository URL/path, immutable commit, dependency-lock
   digest, actor/session ID, and exact Claude Code invocation proving Haiku is
   the only model.
2. Independently implement the semantics. Raw evidence must show abrupt
   process death, a distinct fresh process, durable state loaded and
   re-observed before action, persisted compaction consumed after restart, and
   provider-derived intent/observation/receipt/ledger decisions.
3. Declare the **implementation-owned** reference command in the custody
   manifest. Cairn defines no entrypoint or host interface; the command must
   accept the released workload/snapshot/output paths and fail closed when any
   are absent.
4. Freeze source, command, and dependencies before holdout creation:

```powershell
$ImplementationRoot = 'D:/external-implementation'
git -C $ImplementationRoot status --porcelain=v1
git -C $ImplementationRoot rev-parse HEAD | Set-Content "$RunRoot/implementation-commit.txt" -NoNewline
Compress-Archive -Path "$ImplementationRoot/*" -DestinationPath "$RunRoot/implementation.zip" -Force
Get-FileHash "$RunRoot/implementation.zip" -Algorithm SHA256 |
  Select-Object Path,Hash | ConvertTo-Json | Set-Content "$RunRoot/implementation-archive-digest.json"
```

Dirty source, an unpinned lock, or an implementation/command change after
freeze is a `FAIL`.

## SEALER: reference vector

SEALER authors a fully specified public package from the immutable snapshot:

```text
reference/
  task.md                 # public repository-edit task and acceptance criteria
  verifier/               # deterministic public verifier
  effect-provider/        # deterministic local create-once provider
  imgshape-snapshot/      # copied baseline; never D:/imgshape itself
  manifest.json           # cell matrix, crash boundaries, commands, hashes
  seal.json               # package digests
```

The public task must state all acceptance criteria and bind the unchanged
copied `vectors.json` digest. `manifest.json` fixes all ten cells—`U`, `R`, `R_NEG`, `C`, `C_NEG`, `E_MATCH`, `E_ABSENT`,
`E_ESC_UNKNOWN`, `E_ESC_MISMATCH`, `E_ESC_NEVER`—and all three repetitions,
verifier, effect provider, crash boundaries, and output roots.

```powershell
$Package = "$RunRoot/reference"
Get-ChildItem $Package -Recurse -File | Sort-Object FullName | Get-FileHash -Algorithm SHA256 |
  Select-Object Path,Hash | ConvertTo-Json -Depth 4 | Set-Content "$RunRoot/reference-file-digests.json"
Get-FileHash "$Package/manifest.json","$RunRoot/reference-file-digests.json" -Algorithm SHA256 |
  Select-Object Path,Hash | ConvertTo-Json -Depth 4 | Set-Content "$Package/seal.json"
```

Release only this sealed reference package to IMPLEMENTER. Any later change to
the task, verifier, schema, threshold, model, command, or implementation stops
the run.

## Reference execution and evaluator

IMPLEMENTER runs its frozen command against a fresh reference copy and retains
all attempts. Then evaluate using the unchanged copied kit:

```powershell
$Kit = 'D:/phase6-external-run/copied-kit'
$Evidence = 'D:/phase6-external-run/reference-output/evidence.json'
python "$Kit/evaluate.py" $Evidence --output 'D:/phase6-external-run/reference-output/verdict.json'
```

For all 30 cells retain host/model configuration; task/verifier/seal hashes;
checkpoint and process identities; actual crash return status; first
post-restart operation; checkpoint/context artifacts; workspace manifests and
verifier outputs; provider/resource/receipt/ledger records; evidence inventory;
stdout/stderr; and evaluator verdict.

## Holdout and reproduction

After reference execution and implementation freeze, SEALER independently
authors a new, fully specified holdout with different `imgshape` task/verifier
and effect data but unchanged copied `vectors.json`, matrix, and contract thresholds. SEALER seals it
with the same commands and records the frozen implementation archive digest
before releasing it. No failure permits tuning.

REPRODUCER starts fresh with only the implementation archive, copied kit,
sealed holdout, and custody manifest:

```powershell
$RunRoot = 'D:/phase6-reproduction'
Get-FileHash "$RunRoot/implementation.zip","$RunRoot/holdout/seal.json","$RunRoot/copied-kit/evaluate.py" -Algorithm SHA256
Expand-Archive "$RunRoot/implementation.zip" "$RunRoot/implementation"
# Execute the immutable implementation command recorded in chain-of-custody.
python "$RunRoot/copied-kit/evaluate.py" "$RunRoot/holdout-output/evidence.json" --output "$RunRoot/holdout-output/verdict.json"
```

REPRODUCER preserves actual command, environment, evidence, raw output, and
verdict comparison. It may only write its own output root.

## Verdict

**PASS:** distinct actor provenance; copied evaluator passes all reference and
holdout cells; raw records support every claim; REPRODUCER gets the same
holdout verdict; and `D:/imgshape` is exactly preserved.

**FAIL:** semantic/evaluator failure, post-seal mutation, provenance overlap,
unsupported raw claim, duplicate/lost/blind effect, or experiment-caused target
change. Preserve evidence and stop; do not change Cairn contracts.

**INCONCLUSIVE:** missing raw artifact, infrastructure interruption before a
cell result, unexplained preservation mismatch, or incomplete reproduction.
Classify and restart only under a new sealed identity.

## Chain of custody

Complete [phase6-chain-of-custody.template.json](phase6-chain-of-custody.template.json)
in append-only order. Replace every required `null` before sealing its state.
It is provenance metadata—not a Cairn checkpoint, state schema, evaluator
input, or host interface.
