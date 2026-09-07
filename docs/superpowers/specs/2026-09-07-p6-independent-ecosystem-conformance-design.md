# P6 Independent Ecosystem Conformance Design

## Status

Approved in chat on 2026-09-07. This document governs P6 of the newer recovery proof program. It
does not replace or renumber the legacy project phase named "Phase 6 - Paper & Release."

## Objective

Determine whether a non-Cairn implementation can consume the admitted Recovery, Continuation v0,
and Receipt/Reconciliation v0 obligations from a standalone conformance kit, without importing
Cairn code, using a Cairn-maintained host adapter, or adopting Cairn's runtime architecture.

The preferred third validation target is a Pydantic AI v2 coding-agent application running in a
DBOS durable workflow. This target is capability-gated. LangGraph/Deep Agents is the fallback only
if the preferred released stack cannot directly expose the required recovery, compaction, and
effect-ordering boundaries.

## Why this phase exists

P4 and P5 proved deterministic portability across Claude Code and OpenHands, but Cairn maintainers
implemented both host boundaries and normalized their evidence. That does not establish that an
outside implementer can derive the behavior from Cairn's contracts alone.

P6 separates three claims:

1. **Kit executability:** the published requirements and evaluator are internally coherent.
2. **Technical code independence:** a separate implementation with no Cairn runtime dependency can
   pass the evaluator.
3. **Independent ecosystem conformance:** a non-Cairn contributor authored that implementation and
   an independent party authored and sealed its holdout.

Only the third claim admits P6. A Cairn-authored clean-room rehearsal may prove the first two claims
but cannot substitute for independent authorship.

## Ecosystem decision

### Preferred: Pydantic AI v2 plus DBOS

This combination has the strongest adversarial proof value:

- its state is a workflow/operation journal rather than a CLI transcript or OpenHands conversation;
- recovery is runtime replay from persisted steps;
- unfinished I/O steps may execute again, directly challenging blind-retry and effect-ambiguity
  handling;
- Pydantic AI's public durable-backend surface includes model requests, tools, event handlers, and
  message compaction;
- the application remains responsible for its model, messages, tools, dependencies, and workflow.

The implementation must pin released versions after P6.2 capability acquisition. No target version
is normative before that evidence exists.

### Fallback: LangGraph/Deep Agents

LangGraph provides durable checkpoints, resumable threads, ordered events, persistent context
summarization, and explicit task replay semantics. Deep Agents adds a real terminal coding-agent
harness. Its compaction implementation was changing during reconnaissance, so it is a fallback,
not a simultaneous second target.

### Rejected for the first P6 attempt

- Google ADK: event-tracked session state is observable, but no adequate released, directly
  observable compaction boundary was established during reconnaissance.
- AutoGen: save/load is public, but bounded model context does not presently give the required
  durable compaction proof.
- Letta: strong persisted-memory and compaction concepts, but a less direct external-effect and
  fresh-process boundary for the smallest proof.
- a third Cairn-maintained adapter: repeats P5 and cannot answer the independent-implementation
  question.

## Frozen boundary

P6 must not edit or reinterpret:

- the Phase 1 recovery contract or evidence;
- `docs/design/continuation-contract-v0.md`;
- `docs/design/receipt-reconciliation-contract-v0.md`;
- Phase 1-5 benchmark drivers, fixtures, results, seals, or verdicts;
- Cairn runtime, Agent, World, checkpoint, recovery, or effect-ledger behavior.

P6 may extract existing obligations into a distributable conformance profile. Every normative P6
requirement must cite an existing admitted clause. An obligation with no such source is non-normative
research and cannot fail a submission.

## Ownership boundary

```text
external implementation
  owns runtime, loop, model/session, memory, tools, persistence, scheduling, effects
       |
       | emits observations in the evidence envelope
       v
standalone Cairn conformance kit
  owns requirements, failure semantics, vectors, evidence validation, verdict
```

The evidence envelope standardizes observations, not host state. Cairn does not define a common
checkpoint, continuation-state, receipt, workflow, memory, transcript, or session wire format.

## State machine

```text
P6.0 FROZEN_OBLIGATIONS
  -> P6.1 KIT_READY
  -> P6.2 TARGET_CAPABLE
  -> P6.3 INDEPENDENT_IMPLEMENTATION_ACCEPTED
  -> P6.4 REFERENCE_CONFORMANT
  -> P6.5 HOLDOUT_CONFORMANT
  -> P6.6 INDEPENDENT_CONFORMANCE_ADMITTED
```

No state may be skipped. A stopped target does not authorize simulation or weaker evidence.

## P6.0 - freeze and obligation extraction

### Hypothesis

The admitted contracts contain enough behavioral information to derive tests without exposing
Cairn implementation details.

### Work and artifact

Create a freeze manifest for the admitted contract documents, their admission verdicts, the P5
host-neutral evaluator, repository commit, Python version, and test baseline. Publish a requirement
table containing:

- requirement identifier;
- normative source clause;
- protected invariant;
- accepted observation;
- counterexample;
- applicable matrix cells.

### Exit gate

Every failing requirement maps to an admitted contract clause, and the freeze recheck is byte
identical. If extraction reveals ambiguity, record it as a contract-specification defect and stop;
do not silently clarify the contract through evaluator code.

## P6.1 - standalone conformance kit

### Minimal deliverable

Use the fewest files that preserve separation:

```text
conformance/v0/
  README.md                 normative profile and submission protocol
  evidence.schema.json      evidence observations only
  vectors.json              positive and negative semantic vectors
  evaluate.py               standard-library evaluator and seal checker
```

Tests live with the existing test suite. The evaluator must import only the Python standard library
and operate after `conformance/v0` is copied outside the Cairn repository.

### Evidence model

Each submission records:

- kit version and hash;
- implementation repository, commit, dependency lock hash, and authorship assertion;
- host/runtime/model identities;
- workload, public task, verifier, and seal hashes;
- cell, repetition, process identities, checkpoint identity, and artifact digests;
- ordered semantic observations with links and hashes for host-native raw evidence;
- compaction trigger, completion, and before/after active-context evidence;
- effect intent, observation, provider resource/fingerprint, receipt, resolution, and call counts;
- verification, termination, artifact equivalence, and outcome equivalence.

The evaluator checks internal consistency, hashes, ordering, required observations, and contract
decisions. It cannot authenticate an arbitrary host's semantic mapping by itself; P6.6 therefore
requires a mapping audit against sampled raw host evidence.

### Exit gate

- zero imports from `cairn` or a host SDK;
- a clean copied-kit self-check passes;
- each deliberately mutated invariant is rejected;
- unknown fields are tolerated but cannot satisfy missing normative evidence;
- P5's trusted Boolean facts alone are rejected as insufficient P6 evidence.

## P6.2 - target capability acquisition

Run the smallest host-only probes before implementing Cairn semantics. The pinned Pydantic AI/DBOS
stack must directly expose:

1. durable workflow and session identity;
2. real process-death injection and recovery in a fresh PID;
3. durable workspace and workflow journal observation;
4. host-owned message compaction with observed completion;
5. changed active model context after compaction;
6. ordered tool/effect observations sufficient to distinguish observe-before-action;
7. a crash window after provider commit but before local durable receipt.

No transcript scraping, prompt-simulated compaction, polling used as semantic evidence, or Cairn
runtime code is allowed. If any capability is absent, preserve negative evidence and stop this target.
Only then may the already-approved LangGraph/Deep Agents fallback undergo the same probe.

## P6.3 - independent implementation acceptance

The candidate submission must:

- live outside Cairn core and use its own repository history;
- be authored by a non-Cairn contributor after the kit version is frozen;
- depend on no Cairn package, source tree, adapter, fixture, or runtime service;
- consume only the published profile, vectors, evidence schema, and evaluator;
- own all host execution and persistence decisions;
- provide a clause-to-host mapping and exact reproduction command.

A Cairn-maintained clean-room rehearsal is allowed before this state only to improve kit usability.
Its evidence is permanently labeled `rehearsal` and is ineligible for admission.

## P6.4 - reference conformance

The public reference matrix contains these cell families:

| Cell | Required behavior |
|---|---|
| `U` | uninterrupted baseline reaches the public verifier |
| `R` | clean checkpoint, real death, fresh process, re-ground before action, equivalent outcome |
| `R_NEG` | stale or insufficient continuation evidence causes a safe stop |
| `C` | host compaction preserves intent, decisions, verified work, verification state, stop conditions, and correct next action |
| `C_NEG` | compaction missing a required obligation causes a safe stop |
| `E_MATCH` | provider commit without durable receipt is re-observed, matched, and skipped |
| `E_ABSENT` | observed absence is retried only for a safe/proven-idempotent class and converges |
| `E_ESC_UNKNOWN` | unknown observation escalates without dispatch |
| `E_ESC_MISMATCH` | mismatching resource escalates without dispatch |
| `E_ESC_NEVER` | never-retry intent escalates without dispatch |

Run three fresh-process repetitions per physical cell. U, R, and C share the same starting
checkpoint within a triplet. Real-model canaries are descriptive and cannot replace deterministic
conformance.

### Reference exit gate

- no missing or incomplete cells;
- every seal and evidence link validates;
- all recovery identities are fresh where required;
- first recovered operation is re-observation;
- verified work is preserved;
- U/R/C reach verifier-equivalent outcomes and artifact-equivalent required files;
- all effect decisions match the admitted receipt/reconciliation table;
- no duplicate or silently lost effect;
- every negative cell terminates without unauthorized action;
- three of three repetitions pass every cell.

## P6.5 - independently sealed holdout

The holdout author/sealer must not be the implementation author. Its public task must state every
acceptance criterion. The private verifier, workload package, configuration, matrix, and thresholds
are hashed before the implementation receives the workload.

Run the unchanged matrix and evaluator. No post-seal changes to prompts, tasks, verifier, schema,
thresholds, driver, or contract mapping are permitted. A fixture defect invalidates the holdout;
it does not authorize tuning or reuse.

### Holdout exit gate

All reference gates pass on the independently authored holdout, the seal remains byte-identical,
and an uninvolved reproducer obtains the same verdict from the published implementation commit.

## P6.6 - audit and admission

Admission additionally requires:

- dependency and source scan proving no Cairn runtime import or copied adapter;
- repository and authorship provenance review;
- manual audit of sampled evidence-envelope observations against host-native raw records;
- reproduction from a clean environment using only published inputs;
- full Cairn regression suite and all kit tests green;
- precise documentation of target versions, limitations, and stopped attempts;
- raw evidence, manifests, seals, and verdict committed without modifying P1-P5 evidence.

The strongest allowed claim is:

> One independently authored implementation satisfied Cairn Conformance Kit v0 without importing
> Cairn runtime code.

One passing implementation does not make Cairn an ecosystem standard. Standard-candidate work
requires multiple independently owned implementations, public change control, versioning rules,
and evidence of implementer feedback changing the profile.

## Failure classification

Classify a failed gate before changing anything:

1. host capability limitation;
2. implementation defect;
3. workload/verifier defect;
4. evidence-envelope or evaluator defect;
5. admitted-contract ambiguity or deficiency;
6. infrastructure/model failure.

Only category 4 permits a pre-seal kit correction. Category 5 stops P6 for an explicit contract
review; it does not permit a casual contract expansion. Any post-seal correction invalidates the
affected workload identity.

## Explicit non-goals

- no adapter marketplace or host plugin registry;
- no universal continuation-state or receipt JSON format;
- no Cairn workflow engine, scheduler, memory layer, agent loop, or persistence service;
- no framework-specific abstraction in `src/cairn`;
- no benchmark-score optimization or real-model pass threshold;
- no exactly-once claim;
- no standard claim from one additional implementation;
- no weakening or broadening of P1-P5 contracts.

## Publication outcomes

P6 can end in one of three honest states:

- `KIT_READY`: the profile is executable, but no eligible external submission exists;
- `TECHNICALLY_CONFORMANT_REHEARSAL`: a code-independent Cairn-authored rehearsal passed, but
  independent authorship is unproven;
- `INDEPENDENT_CONFORMANCE_ADMITTED`: every P6.0-P6.6 gate passed.

If external authorship is unavailable, publish the kit and stopped state. Do not relabel an internal
rehearsal as independent evidence.

## Research sources

- Pydantic AI durable backend: <https://pydantic.dev/docs/ai/capabilities/durable_execution/backends/>
- Pydantic AI DBOS integration: <https://pydantic.dev/docs/ai/capabilities/durable_execution/dbos/>
- Pydantic AI version policy: <https://github.com/pydantic/pydantic-ai/blob/main/docs/version-policy.md>
- LangGraph functional durability and replay: <https://docs.langchain.com/oss/python/langgraph/functional-api>
- LangGraph ordered event stream: <https://docs.langchain.com/oss/python/langgraph/event-streaming>
- LangChain persistent summarization: <https://docs.langchain.com/oss/python/langchain/context-engineering>
- Deep Agents coding harness: <https://github.com/langchain-ai/deepagents>
- Google ADK session state: <https://github.com/google/adk-docs/blob/main/docs/sessions/state.md>
- AutoGen state: <https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/state.html>
- Letta agent state: <https://docs.letta.com/api/resources/agents>
