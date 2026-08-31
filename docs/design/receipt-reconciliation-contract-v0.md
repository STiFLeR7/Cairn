# Receipt/Reconciliation Contract v0

**Status:** admitted by Phase 3 evidence only for the deterministic create-once reference effect.

## Claim and boundary

After a process death in the ambiguity window between dispatch and durable receipt, recovery starts in a fresh process and re-observes the provider before deciding. Cairn does not claim exactly-once delivery or a generic durable-effects subsystem.

## Stable semantic contract

1. Persist an effect intent before external dispatch. It identifies the intended effect, idempotency key, request fingerprint, and tool class.
2. Treat a receipt as durable evidence binding that intent to a provider resource identity and the observation that established it. The reference fields are `effect_id`, `idempotency_key`, `request_fingerprint`, `resource_id`, and `observed_from`; this is not yet a cross-provider wire schema.
3. In a fresh process, re-observe before any retry. The first recovery operation is the provider observation.
4. Reconcile only from observation plus intent:
   - `absent` → retry;
   - `present` with matching fingerprint → skip;
   - `unknown` → escalate;
   - fingerprint/key mismatch → escalate;
   - `never-retry` tool class → escalate.
5. Close the durable ledger only after receipt/resolution is durable. An escalation remains visibly unresolved; it is not a successful recovery.

## Evidence required to rely on it

The contract is admitted only where raw evidence proves injected death, a distinct fresh recovery process, first-operation re-observation, the correct decision, no duplicate provider commits, no silent loss, and durable ledger closure for resolved cells. Phase 3 met those gates on the sealed 36-cell reference matrix and a separately authored, sealed 15-cell holdout. See `results/phase-3/p3-verdict.json`.

## Not standardized

Provider APIs, receipt serialization, retry scheduling, escrow or compensation, multi-effect transactions, authentication, network partitions, and framework adapters remain outside v0. A future interoperability contract needs independent provider implementations and additional effect classes before any broader claim.
