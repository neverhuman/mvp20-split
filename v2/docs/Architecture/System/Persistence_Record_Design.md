# Initial Persistence Record and Transaction Design

- Design status: BP-02 physical-design baseline; owner migrations, role/transaction tests and installed recovery now implemented.
- Parent: [State and Consistency](State_and_Consistency.md).
- Protocols: [Runtime commands](Runtime_Command_Protocol.md), [artifact publication](Artifact_Publication_Protocol.md).
- Reviewed: `2026-09-25 13:40:55` (America/Chicago).

## Installation and Roles

Use PostgreSQL 17 for the local test profile and pin the resolved image digest. Major 17 is supported according to the [official versioning policy](https://www.postgresql.org/support/versioning/). Record the actual server version in evidence. Read Committed requires explicit locks/constraints for multi-record invariants; ordinary reads alone are insufficient ([transaction isolation](https://www.postgresql.org/docs/17/transaction-iso.html)).

One installation hosts separate `runtime` and `artifacts` schemas. `runtime_migrator` and `artifact_migrator` own their respective schema only. `runtime_service` and `artifact_service` have explicit owned-table DML permissions, are not members of migration roles, and cannot access the other schema. Revoke public CREATE and application TEMP/CREATE privileges. Independent Alembic histories live in each owned schema. Bootstrap administration belongs only to the disposable local harness.

Owned domain identities/relationships include tenant and project; run-local relationships additionally include run ID. Runtime outbox scope is inherited from its uniquely referenced owned audit event rather than duplicated columns. Composite foreign keys prevent a valid ID in another scope/run from satisfying the relationship. No cross-private-schema FK. Versioned payloads may use JSONB, but uniqueness, state, revision and accepted identity remain relational. Schema checks supplement typed/domain validation.

## Runtime Records

| Table | Identity and constraints | Mutation owner |
|---|---|---|
| admission_guard | Singleton installation slot; lock before new campaign admission | Run admission; ensures single active campaign across scopes |
| runs | Scoped run PK; immutable plan/input/fixture; nonnegative revision/counters; reserved+spent <= finite limit | Run aggregate |
| commands | Scoped actor/family/command PK; immutable digest/profile/canonical bytes; scoped unique operation ID | Pending/terminal receipt owner |
| activations | Scoped run/activation PK; unique invocation; FK run; positive bounded attempt counter | Activation lifecycle |
| attempts | Scoped attempt PK; FK activation; unique activation/fence | Lease, worker, status and settlement; never reuse history identity |
| completion_intents | Scoped intent PK; FK exact attempt and command; immutable semantic digest/output bindings | PREPARED to COMMITTED or ABORTED only |
| accepted_completions | Scoped completion PK; unique accepted result per activation; FK exact intent/attempt | Immutable acceptance owner |
| state_revisions | Scoped activation/revision PK; FK accepted completion | Immutable checkpoint lineage |
| worker_policy | Scoped worker PK; revision/revocation epoch | Local policy owner under run serialization |
| audit_events | Unique event identity and run/revision/ordinal | Append-only transition owner |
| outbox | Stable operation/event ID and immutable target/payload | Delivery claims, lease, attempt count and acknowledgement |

Service roles receive column-level UPDATE grants where needed and cannot rewrite identity or accepted-result fields. Append-only tables receive INSERT/SELECT only. State membership checks are not transition proofs: domain transitions use conditional writes under the declared locks. Migration credentials never enter ordinary API handlers.

## Artifact Records

| Table | Identity and constraints | Mutation owner |
|---|---|---|
| commands | Scoped actor/family/command identity and immutable digest/profile | Artifact command receipts |
| uploads | Scoped upload PK; immutable expected descriptor/generated storage key | Provisional upload lifecycle |
| catalog | Scoped artifact PK; immutable digest, size, media/schema and generated key | Finalization; no finalized garbage collection in this slice |
| reservations | Scoped reservation PK; unique owner/intent/output/artifact/digest binding; FK owned catalog | RESERVED to CONFIRMED or RELEASED with authenticated outcome |
| audit_events / outbox | Owner-local stable event/operation identities | Atomic artifact transition and replayable delivery |

Runtime references are external immutable identities, never private foreign keys. Query authenticated runtime outcome outside artifact transactions. Immutable terminal runtime outcomes make binding-matched proof reusable. Unknown/pending retains protection. Shared content never merges authorization or reservations across scopes.

## Transaction Write Sets

Lock order: admission guard when needed, then run, worker-policy rows, activation, attempt, intent and command; sort sibling IDs. Pending command registration is a separate short unique-key transaction, not a lock held across remote I/O. Artifact operations lock scope capacity when allocating storage, then own upload/catalog, reservation and command. Streaming and remote outcome lookup occur outside those transactions; generation checks fence stale upload writers.

| Operation | Atomic owned write set | Outside transaction |
|---|---|---|
| Register command | Pending identity/digest/profile; conflicting reuse rejected | None |
| Admit run | Admission slot, run, activations, terminal receipt, audit/outbox | Fixture validation before authoritative recheck |
| Claim/renew/expire | Lease/fence/status, budget reservation/settlement, receipt/events | Worker computation |
| Prepare completion | Immutable PREPARED intent or stable rejection | Artifact reservation after commit |
| Accept completion | Result, checkpoint, attempt/activation, budget, COMMITTED intent, command receipt, audit/outbox | No artifact network call under lock |
| Cancel/abort | Cancellation/revocation, settlement, ABORTED intents, receipt/events | Artifact reconciliation after commit |
| Finalize artifact | Catalog and finalization receipt/events | Hash/verify and durable byte publication first |
| Reserve/confirm/release | Binding/status, verified proof, receipt/events | Public runtime outcome query; no private reads |

Recheck live lease/fence/authority and checkpoint preconditions under the runtime lock. Independent valid completions serialize without treating every unrelated run revision as staleness. An explicitly supplied run revision remains a genuine precondition. Serialization/deadlock retries reload all state, at most three attempts, with no external action in the retry closure. Unique-key conflicts reselect authoritative records and compare digests. Pending registration surviving a crash is not successful acceptance.

## Verification Matrix

S3/S4 migration tests cover fresh/repeated upgrade, independent histories, wrong-role SELECT/DML/DDL, scoped FK mismatch, duplicate invocation/fence/accepted output, invalid counters/status and identity overwrite. Restart must preserve inserted fixtures. S5 uses distinct actual PostgreSQL connections and explicit barriers for same-command contention, changed-payload conflict, rollback after event insertion and transaction serialization retry. BP-02.04/.05 now provide run-authority/transition race proof and .06 adds installed process recovery; persistence tests alone do not establish those guarantees. SQLite/mocks/static SQL inspection cannot satisfy these gates.

Later lifecycle/completion children implement full command transactions. Persistence S5 exposes only owner-specific receipt/transaction primitives. Test resets are limited to named disposable harness resources; startup never resets state. Production evidence migration and rollback need explicit policies, not a destructive automatic downgrade. Each service owns migrations, adapters, module README and tests.
