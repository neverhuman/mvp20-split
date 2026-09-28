# State and Consistency

- Design status: proposed authoritative-state and transaction design
- Parent: [System Architecture](System_Architecture.md)
- Scope: persistent records, atomicity, publication and crash recovery

## Proposed Persistence Model

Use PostgreSQL as the initial transactional metadata store, immutable files/objects behind an artifact interface for large scientific payloads, and separately versioned projections for traversal/retrieval/UI. The initial artifact implementation can use a durable server volume; remote workers access it through scoped upload/download grants. A future object-store implementation must preserve artifact identities and verification semantics.

This is not universal event sourcing. Transactional current state answers operational questions, immutable revisions preserve scientific history, and audit/outbox records retain transitions and support projections. Accepted knowledge operations additionally form the authoritative replay log required for graph rebuilds. Do not implement three unrelated copies of the same execution state.

## Proposed Record Families and Ownership

[Service Isolation](Service_Isolation.md) refines physical ownership: one PostgreSQL installation may host distinct service-owned schemas/roles, not unrestricted shared table access. Atomic runtime completion commits the runtime result/checkpoint/attempt/budget and outbox. Research/Knowledge acceptance is a separate idempotent transaction with a receipt; dependent nodes wait for it. Artifact finalization needs a reservation/retention protocol across publication and runtime commit. No cross-service database transaction or remote call inside the runtime commit is implied by the logical record families below.

| Record family | Authoritative writer | Key relationship / invariant |
|---|---|---|
| Project, objective/envelope and approval revisions | Research/application policy commands | Signed objective references exact immutable inputs and authority |
| Campaign revisions and execution plans | Campaign compiler/activation commands | Plan hash binds graph and resolved dependencies; active plan content cannot change |
| Runs, activations, attempts and state revisions | Runtime application commands | Unique activation path; current attempt fence; conditional state revision advancement |
| Dispatch intents, receipts and external jobs | Runtime/external-action commands | One logical operation identity; distinguish sent, acknowledged, uncertain and terminal |
| Capability/model/source/profile versions | Their owning registry commands | Immutable version identity; mutable lifecycle/access posture separately checked |
| Entity/assertion revisions and graph change log | Knowledge commit commands | Base-head precondition, ordered accepted operations, preserved source/evidence and identity mapping |
| Artifact catalog and evidence bindings | Artifact finalization and domain evidence commands | Verified content exists before usable reference publication; separate rights/provenance bindings |
| Results, eligibility and selection decisions | Research/search commands | Exact input/result/policy revisions; corrections supersede rather than overwrite |
| Audit events and outbox commitments | Same transaction as consequential commands | No successful state mutation without required durable event commitment |
| Projection/index generation manifests | Projection publisher | Built/verified generation precedes atomic active-pointer change |

All object relationships include tenant/scope identity and must reject cross-scope references at the write boundary. JSON payloads can encode versioned graph/port values, but relational identity, references, uniqueness and revision preconditions remain explicit. Typed domain objects validate behavior before serialization.

## Atomic Completion

One accepted node completion uses a short transaction:

1. Lock or conditionally advance the affected run/activation ownership record.
2. Confirm command identity, current attempt fence, plan binding, expected state revision, grants and budget disposition.
3. Confirm finalized output artifacts and validate the typed result.
4. Insert the accepted result and any state revision; mark the attempt/activation disposition.
5. Append audit/outbox events and any newly eligible dispatch records.
6. Commit, then notify workers/UI asynchronously.

Start by serializing committed transitions within a run. Computation still runs in parallel; only short state commits serialize. This simplifies correct joins, cancellation ordering and budget updates. If measured high-fanout throughput requires finer-grained commit ownership, change that protocol with concurrency tests rather than prematurely assuming lock-free state updates.

Database isolation alone is not the entire protocol. The default PostgreSQL isolation permits different statements to observe different committed snapshots; multi-record invariants need explicit locking/revision checks or stronger isolation with whole-transaction retries. See [PostgreSQL transaction isolation](https://www.postgresql.org/docs/current/transaction-iso.html). Lock ordering and retry limits must be part of implementation, and external side effects must never be repeated as an incidental database transaction retry.

## Command Idempotency and Ordering

Graph Runner engagements persist request/outbox before remote model calls. A supervision decision and resulting runtime transitions commit atomically against decision identity, scope, relevant input versions, grants and budget. Duplicate, late, conflicting or stale proposals cannot each advance the run. Aggregation receipts pin accepted member/results and required scientific-domain receipts; projections are reconstructible, not new sources of truth. See [Graph Runner](Graph_Runner.md) for engagement lifecycle and race handling.

Persist `(scope, command_id, request_digest, disposition)` so duplicate submission returns the same receipt, while reuse of the identity with a different payload is rejected. Enforce at most one accepted result for an activation/output identity. A stale worker may retain a diagnostic result but cannot become the accepted writer.

Ordering uses a per-run or per-aggregate committed revision/sequence. Wall-clock time and a globally allocated database ID are not a proof of causal order or gap-free commitment. Cross-aggregate operations explicitly reference prior decisions and snapshots. A UI consistent-cut query identifies the revisions it combines; it must not fabricate global atomicity from timestamps.

## Payload Finalization and Projections

Workers upload provisional content, then request finalization with digest, type and scope. Artifact validation establishes content identity and retention/rights metadata before a completion can bind it. A crash can leave unreferenced uploads; a grace-period garbage collector removes them only after proving they are uncommitted/unreferenced. Metadata rollback must not delete another invocation's shared artifact.

Graph snapshots are manifests of immutable entity/assertion revisions plus rule/schema identity. New revisions may reuse unchanged records. A full rebuild materializes a candidate from accepted history, catches up and publishes a new manifest pointer with compare-and-set. Vector and UI projections use the same build-verify-publish pattern but never become scientific authority. Readers receive generation/watermark/freshness metadata.

## External Effects and Recovery

Persist the external-operation intent before submission. Use provider idempotency/correlation where available. If the provider accepts a job but the receipt is lost, the durable intent becomes uncertain; reconcile by provider key/status or human investigation. Do not infer failure and submit a second experiment. A cancelled run prevents new dispatch but cannot undo chemistry already underway.

Startup recovers incomplete dispatch, expired attempts, uncertain external jobs and unfinished publication. Recover projections from durable state/logs and artifacts. Backups must preserve a recoverable metadata snapshot plus referenced immutable payload generations; verify restore by traversing references and re-running deterministic fixtures.

Access revocation, retention and legal hold remain live policies, including for historical snapshots. If content must be removed, retain only permitted tombstones and expose lost replay capability. Hashes, immutable logs and backups do not override deletion/access obligations.

## Deferred Choices and Evidence Gates

This design selects a transactional relational baseline, not a final physical schema or capacity promise. Before implementation acceptance, test concurrent completions, cancellation races, two budget spenders, crash points around artifact/metadata publication, duplicate commands and external acknowledgement loss. Select backup objectives, supported database version and performance targets through the first deployment plan.

## Initial Protocol Decisions

[Initial Persistence Record Design](Persistence_Record_Design.md) owns service roles, relational constraints and transaction write sets for BP-02.02. Migration and concurrency evidence remain separate gates.

BP-02 decomposes this design into the [Runtime Command Protocol](Runtime_Command_Protocol.md) and [Artifact Publication Protocol](Artifact_Publication_Protocol.md). These own the first slice's command digest, transition, budget, fencing and reservation decisions. Their design status is distinct from contract/database verification, which remains in the BP-02 task gates.
