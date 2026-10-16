# Artifact Publication and Reservation Protocol

- Design status: BP-02 publication/retention protocol implemented and exercised against actual installed peers; target-host durability remains separate.
- Reviewed: `2026-10-15 22:24:23` (America/Chicago).
- Parent: [State and Consistency](State_and_Consistency.md).
- Owner: Data/Artifacts publication and retention module; runtime remains sole completion authority.
- Companion: [Runtime Command Protocol](Runtime_Command_Protocol.md).

## Public Boundary

The focused [Artifact Storage and Access Design](Artifact_Storage_Design.md) owns filesystem handling, upload-attempt fencing, access policy and the failure-to-test matrix. Its design status is separate from runtime implementation evidence.

Proposed operations: BeginUpload, UploadContent, FinalizeArtifact, ReserveArtifact, ConfirmRetention, ReconcileReservation and scoped GetArtifact/ReadContent. Calls bind authenticated service/worker, scope, command identity and immutable content metadata. Private artifact tables/filesystem paths are never runtime interfaces. A hash provides identity, not authentication; receipts must come from the configured authenticated artifact service and be durably bound to the runtime intent.

Resource authoring may inspect complete catalog ancestry through a scoped read-only
footprint: root plus conversion/derivation ancestor count, content-byte sum and
membership identity. This uses metadata read authority only and does not reserve,
renew, grant processing rights or accept execution. Observations can change when
later conversion lineage is registered; consumers re-assess changes and retain Data's
mandatory completion/protection checks. The approved boundary is
[POP-01.08](../../Build%20Plans/POP-01/POP-01.08%20Artifact%20ancestry%20footprint%20decision.md).

Worker recovery also needs original publication-command observation: authenticated actor/scope, original canonical request digest and pending/rejected/uploaded/finalized result. Inspection must not renew authority, change quota or expose another actor's command. BP-03.03 supplies this additive interface without reopening completed publication phases. An upload-command receipt proves allocation; only stream success proves provisional byte selection, and only finalization yields a usable artifact reference.

Tool-specific JSON payload validation uses trusted deployment-installed public schema files pinned by exact bytes. Artifact storage imports generic validation infrastructure, never tool kernels. The initial schema profile is bounded, self-contained Draft 2020-12 with local references and explicit format support; remote resolution is prohibited. Schema installation and scientific acceptance are separate responsibilities. Existing built-in content profiles retain their identities and behavior.

Provisional upload records own bounded scratch bytes. Finalized catalog references bind scope, content digest, size, media/schema identity and verified immutable bytes. Per-scope catalog identity and grants stay distinct even when underlying bytes could be deduplicated. Initial implementation need not deduplicate across scopes. No public arbitrary file paths; generated storage keys and resolved-path containment checks prevent traversal/symlink escape. Local credentials and upload/download grants restrict actions and scope; digest knowledge alone cannot fetch data.

Finalization verifies byte count and digest plus configured declared content/schema checks, publishes immutable bytes durably, then commits catalog state/receipt. Metadata never says usable before bytes are present. A filesystem move is not a database transaction: leftover verified bytes before catalog commit are recoverable orphans, not usable references. Existing immutable bytes cannot be overwritten; conflicting metadata rejects. Process-crash and power-loss/remote-volume behavior have separate evidence gates.

## Reservation Identity and State

A reservation is bound to `(scope, runtime_owner, completion_intent_id, output_binding, artifact_id, content_digest)`. The runtime intent also binds invocation, attempt/fence and semantic completion payload digest. Repeating the same request returns the same receipt; changing the binding rejects. Output and checkpoint artifacts are covered independently. Artifact content/catalog identity cannot mutate after receipt issuance.

| State | Meaning | Allowed next transition / authority |
|---|---|---|
| PROVISIONAL upload | Bytes not published, not eligible for completion | FINALIZED only after verification; abandoned provisional cleanup is bounded |
| FINALIZED artifact | Verified immutable catalog reference | Eligible for scoped reservation; no automatic deletion of finalized payloads in BP-02 |
| RESERVED binding | Durable protection for a PREPARED completion intent | CONFIRMED only with committed runtime reference; RELEASED only with authoritative aborted-intent proof |
| CONFIRMED binding | Accepted runtime output/checkpoint retains artifact | No BP-02 automatic deletion or release; explicit future retention policy required |
| RELEASED binding | Intent irrevocably aborted, this reservation no longer needed | Terminal; cannot be revived/reused for another intent |

Receipt does not expire solely because a wall-clock TTL passed. Diagnostic age can trigger reconciliation, never unsafe deletion. Unknown or unreachable runtime outcome conservatively retains bytes/protection. An expired worker lease does not itself prove its prepared intent was aborted. Failure to reach the other service is uncertainty, not negative proof.

## Commit and Release Handshake

1. Runtime registers immutable command and PREPARED intent under its run/attempt authority.
2. Runtime calls ReserveArtifact outside its transaction. Artifact service validates scope/reference and binds a durable RESERVED receipt to that intent; optional public intent lookup validates PREPARED state, but atomic release rules below carry the race safety.
3. Runtime checks the receipt against the exact output/intent and attempts its conditional completion commit. It cannot commit an ABORTED intent. The artifact service cannot release a reservation without runtime's irrevocable abort decision.
4. Accepted commit marks intent COMMITTED and persists retention-confirmation outbox intent in the same runtime transaction. Artifact service idempotently confirms against the immutable runtime outcome via its public authenticated interface.
5. Rejection/cancellation/expiry reconciliation marks a still-PREPARED intent ABORTED under the same run/attempt locks used by acceptance. This is an irrevocable tombstone; no later acceptance under that ID is possible. Artifact service may release only after authenticating that exact aborted outcome. Caller-supplied 'not found', an old cache or absence of a receipt is insufficient.
6. Reconciliation is idempotent: COMMITTED confirms; ABORTED releases; PREPARED/unknown retains and retries under a bounded operational policy. Disagreement/mismatched IDs quarantines the binding and retains bytes for diagnosis.

A late reserve request arriving after abort may be rejected using the public intent tombstone or may create protection that is subsequently safely released. It cannot authorize a runtime commit because the intent is terminal. Thus a released reservation cannot race a successful commit of the same intent. If storage retention is later expanded, the same handshake must protect shared references and old readers before deletion; this plan does not implement finalized-payload garbage collection.

## Crash and Race Decisions

| Interruption / race | Safe result and next action |
|---|---|
| Partial upload | Provisional only; never an accepted output; resume/restart or grace cleanup |
| Durable bytes, no catalog commit | Orphan bytes; retry finalization by digest/command; no usable reference until catalog commit |
| Finalize commits, reply lost | Same immutable finalization receipt on retry |
| Reservation issued, runtime crashes | RESERVED protects bytes; resume PREPARED intent or atomically abort before release |
| Cancellation versus prepared completion | Runtime lock order produces COMMITTED or ABORTED; artifact follows that durable outcome |
| Runtime commits, confirmation lost | RESERVED still protects; outbox/reconciliation eventually CONFIRMS |
| Abort proof obtained, stale completion arrives | ABORTED intent rejects; safe release remains terminal |
| Artifact/runtime unavailable | No assumed success or release; return pending/retryable disposition, retain evidence |
| Two intents share an artifact | Independent bindings; aborting one cannot release another's protection |
| Wrong scope, digest, binding or issuer | Reject; no accepted runtime reference |

## Limits, Tests and Future Owners

P3 tests belong in `services/data_artifacts/tests/publication/` and `tests/retention/`; cross-service proof belongs in the separate BP-02 integration harness. Tests use distinct credentials/processes and real PostgreSQL roles. Every crash point has exact command/intent/artifact IDs and observed state. Runtime tests must demonstrate no network call inside the acceptance transaction and that atomic abort/commit prevents release races.

Artifact finalization means verified storage, not scientific evidence acceptance. Research/Knowledge keep independent receipts. Rights deletion/legal holds and production backup objectives need later explicit policies; do not claim immutable storage overrides access restrictions. Local provisional cleanup may be implemented with safe grace bounds; final artifact retention remains conservative and capacity is bounded by configured uploads/quotas in the developer profile. BP-09 owns target-host restore and durability evidence.

Implementation evidence: [artifact module](../../../services/data_artifacts/README.md), [recovery runbook](../../../services/campaign_runtime/RECOVERY.md) and [BP-02 closeout](../../Audits/BP-02_Foundation_Closeout.md). REC-01..09 separates actual process recovery/replacement from host backup/power-loss acceptance. This design document itself grants no scientific or operational authority.
