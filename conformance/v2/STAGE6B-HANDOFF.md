# Phase 6B external sealing and reproduction

**State: `STAGE 6A PASS; PHASE 6 BLOCKED / UNADMITTED`.** This procedure
starts from the frozen candidate-7 implementation. It does not authorize a
Cairn maintainer, the implementation author, or this workspace to act as the
SEALER or REPRODUCER.

## Frozen inputs

| Input | Required identity |
| --- | --- |
| Cairn ancestry floor | `17089a8532bce9ddcdfd30c8eda77f5d4e241a6f` |
| Candidate bundle | `results/phase-6/stage-6a-haiku-candidate-7/candidate.bundle` |
| Bundle SHA-256 | `e964ea84a7145477183942912b76493a37af753abe3a7fd5bf9a75a98e21b33d` |
| Candidate commit | `ca29b601454f83d0ab75433522c40930089bc5d3` |
| Candidate tree | `35c9c96e3f0d4cf869cba39a20629fe30b2ca61e` |
| Host command | `python host.py <execute|prepare|recover> <request-json>` |
| Reference witness SHA-256 | `f175254920909f6d882b15ae3d6532a503087b48346ad79f4ee0dc505742ded5` |
| Semantic-rules SHA-256 | `e6d3037d736a3961ef6e4e1a09de592a12a79ebfd07d29a9f4e169e4e925107a` |

The candidate's bundled `public-kit/witness.py` records its original public
input. It is evidence, not the Phase 6B verifier. The external SEALER authors a
new post-freeze witness from the public v2 protocol, and the REPRODUCER uses
that sealed witness unchanged. Kit v2 has no separate `evaluate.py`: the
verifier-owned witness produces and evaluates the evidence.

## Actor boundary

- **SEALER:** a person/session distinct from the candidate implementer. Authors
  the holdout after the candidate freeze, seals it before execution, and never
  changes candidate source.
- **REPRODUCER:** an uninvolved person/session in a fresh environment. Receives
  only the frozen candidate bundle, sealed holdout, this public procedure, and
  an append-only custody record. It cannot patch any input.
- **Cairn maintainer:** may audit submitted artifacts but cannot supply either
  missing provenance role.

Any actor overlap, candidate mutation, post-seal holdout mutation, or rerun
under the same failed seal is a hard `FAIL`.

## SEALER commands

Run in a new directory. Do not use the original candidate workspace.

```powershell
$RunRoot = 'D:/phase6b-sealer-<unique-id>'
$Cairn = "$RunRoot/Cairn"
$Candidate = "$RunRoot/candidate"

git clone https://github.com/STiFLeR7/Cairn.git $Cairn
git -C $Cairn merge-base --is-ancestor 17089a8532bce9ddcdfd30c8eda77f5d4e241a6f HEAD
if ($LASTEXITCODE -ne 0) { throw 'Cairn checkout predates the v2 verifier fix' }

$WitnessHash = (Get-FileHash "$Cairn/conformance/v2/witness.py" -Algorithm SHA256).Hash.ToLowerInvariant()
$VectorsHash = (Get-FileHash "$Cairn/conformance/v2/vectors.json" -Algorithm SHA256).Hash.ToLowerInvariant()
if ($WitnessHash -ne 'f175254920909f6d882b15ae3d6532a503087b48346ad79f4ee0dc505742ded5') {
  throw 'reference witness digest mismatch'
}
if ($VectorsHash -ne 'e6d3037d736a3961ef6e4e1a09de592a12a79ebfd07d29a9f4e169e4e925107a') {
  throw 'semantic-rules digest mismatch'
}

$Bundle = "$Cairn/results/phase-6/stage-6a-haiku-candidate-7/candidate.bundle"
if ((Get-FileHash $Bundle -Algorithm SHA256).Hash.ToLowerInvariant() -ne
    'e964ea84a7145477183942912b76493a37af753abe3a7fd5bf9a75a98e21b33d') {
  throw 'candidate bundle digest mismatch'
}

git clone $Bundle $Candidate
if ((git -C $Candidate rev-parse HEAD) -ne
    'ca29b601454f83d0ab75433522c40930089bc5d3') {
  throw 'candidate commit mismatch'
}
if ((git -C $Candidate rev-parse 'HEAD^{tree}') -ne
    '35c9c96e3f0d4cf869cba39a20629fe30b2ca61e') {
  throw 'candidate tree mismatch'
}
if (@(git -C $Candidate status --porcelain).Count -ne 0) {
  throw 'candidate worktree is dirty'
}
$TestOutput = python -B -m unittest discover -s $Candidate -p 'test_host.py' -v 2>&1
$TestExit = $LASTEXITCODE
$TestOutput
if ($TestExit -ne 0 -or ($TestOutput -join "`n") -notmatch 'Ran 23 tests') {
  throw 'candidate 23-test gate failed'
}
if (@(git -C $Candidate status --porcelain).Count -ne 0) {
  throw 'candidate tests changed the frozen worktree'
}
```

Copy
[`stage6b-chain-of-custody.template.json`](stage6b-chain-of-custody.template.json)
outside both repositories and fill the SEALER fields before authoring.

## Holdout obligations

The SEALER creates a new repository containing a fully specified task,
verifier-owned witness, effect provider, and manifest. It must:

1. exercise the same ten semantic classes and three repetitions (30 cells);
2. use new task values, continuation values, volatile context, effect
   fingerprints, provider state, nonces, and workspace identities;
3. never disclose a case label, negative flag, expected status, expected
   decision, matching conclusion, or answer table to the host;
4. spawn and kill the prepare process itself, confirm OS-reported forced
   termination, and start recovery in a distinct process and directory;
5. recompute filesystem/checkpoint/artifact hashes and provider observations
   independently of the host;
6. require re-observation before any recovery action;
7. test real compact-state reduction and loss of volatile context while
   preserving the eight continuation obligations;
8. test matching, absent, unknown, mismatch, and never-retry effect outcomes
   against a verifier-owned create-once provider whose durable state is
   externally observed, never inferred from a cell name;
9. derive verdicts exclusively from verifier-owned observations; and
10. preserve every cell's request, raw process record, workspace inventory,
    provider ledger, evidence, stdout, and stderr.

The public task states all acceptance criteria. The witness implementation and
expected outcomes may remain private until sealing, but their hashes and the
complete file inventory must be committed before the candidate is executed.
The SEALER must also record an authorship declaration stating that the holdout
was authored after candidate freeze without candidate modification or coaching.

Seal the entire holdout repository, not selected files:

```powershell
$Holdout = "$RunRoot/holdout"
git -C $Holdout status --porcelain
git -C $Holdout rev-parse HEAD | Set-Content "$RunRoot/holdout-commit.txt" -NoNewline
git -C $Holdout ls-files -s | Set-Content "$RunRoot/holdout-index.txt" -NoNewline
git bundle create "$RunRoot/holdout.bundle" --all
Get-FileHash "$RunRoot/holdout.bundle" -Algorithm SHA256 |
  Select-Object Path,Hash | ConvertTo-Json |
  Set-Content "$RunRoot/holdout-bundle-digest.json"
```

After sealing, execute the holdout's documented command with the frozen host.
The command shape must remain:

```powershell
python "$Holdout/witness.py" --output "$RunRoot/sealer-output" --host python "$Candidate/host.py"
```

If the sealed witness reports anything other than 30/30, preserve the run and
stop. Do not patch or rerun it under the same holdout identity.

## REPRODUCER commands

The REPRODUCER receives immutable copies of `candidate.bundle`,
`holdout.bundle`, their recorded digests, and the partially completed custody
record. In a new environment:

```powershell
$RunRoot = 'D:/phase6b-reproducer-<unique-id>'
$Candidate = "$RunRoot/candidate"
$Holdout = "$RunRoot/holdout"

Get-FileHash "$RunRoot/candidate.bundle","$RunRoot/holdout.bundle" -Algorithm SHA256
git clone "$RunRoot/candidate.bundle" $Candidate
git clone "$RunRoot/holdout.bundle" $Holdout

if ((git -C $Candidate rev-parse HEAD) -ne
    'ca29b601454f83d0ab75433522c40930089bc5d3') {
  throw 'candidate commit mismatch'
}
if (@(git -C $Candidate status --porcelain).Count -ne 0 -or
    @(git -C $Holdout status --porcelain).Count -ne 0) {
  throw 'reproduction input is dirty'
}

$TestOutput = python -B -m unittest discover -s $Candidate -p 'test_host.py' -v 2>&1
$TestExit = $LASTEXITCODE
$TestOutput
if ($TestExit -ne 0 -or ($TestOutput -join "`n") -notmatch 'Ran 23 tests') {
  throw 'candidate 23-test gate failed'
}
if (@(git -C $Candidate status --porcelain).Count -ne 0) {
  throw 'candidate tests changed the frozen worktree'
}
python "$Holdout/witness.py" --output "$RunRoot/reproducer-output" --host python "$Candidate/host.py"
```

The REPRODUCER independently inventories the output, records environment and
command digests, and compares the semantic verdict with the SEALER result.
Fresh random challenges mean raw evidence files need not be byte-identical;
the sealed witness, candidate identity, 30/30 outcome, and protected
invariants must match.

## Admission decision

**PASS** requires all of the following:

- verified distinct SEALER and REPRODUCER provenance;
- byte-identical frozen candidate and sealed holdout inputs;
- 30/30 verifier-owned results from both actors;
- no unsupported or self-attested critical runtime fact;
- no duplicate, silent loss, blind retry, action-before-observation, transcript
  replay, or merely semantic reconstruction where exact bytes are required;
- complete raw evidence and custody hashes; and
- no mutation of the original `D:/imgshape` repository. A snapshot may be used;
  the original target is not required for Stage 6B.

**FAIL** is any semantic failure, provenance overlap, candidate or post-seal
mutation, fabricated fact, unsupported critical claim, or target corruption.
Preserve evidence and do not tune.

**INCONCLUSIVE** is limited to missing evidence or infrastructure interruption
before a semantic result. A replacement attempt requires a new holdout identity
and seal.

Only after Cairn maintainers independently audit the complete submission may
Phase 6 be admitted. One passing external chain is evidence of independent
implementability, not an ecosystem standard or universal compatibility.
