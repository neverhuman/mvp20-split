# Derived closure retention

POP-01.06 / Data0.32 owns immutable catalog-ancestry protection under a Runtime
completion proof. Architecture: [Artifact publication](../../../../../docs/Architecture/System/Artifact_Publication_Protocol.md).
The additive public artifact_retention contract owns DTOs and route schemas.

ClosureReservations authenticates the same scoped retention grant and runtime_owner
identity as ordinary reservations. POST `/v1/retention-closures/reserve` captures
the exact root plus complete current immutable derivation/conversion ancestry.
Existing ancestry traversal enforces4096 distinct artifacts,128 direct parents and
cycle rejection. Missing, foreign or conflicting catalog identities reject. The
canonical sorted full-reference set defines the membership digest. No payload or
scientific-schema inspection, processing-rights grant, worker retention authority,
network I/O or peer SQL occurs here.

Migration artifact_0013 adds INSERT/SELECT-only closure metadata and membership.
Root reservation and all members commit with command receipt/audit in one Data
transaction, under the existing capacity lock. A savepoint removes all new state
before recording a semantic rejection. Ordinary existing roots cannot be upgraded
silently. New-command duplicates reuse exact immutable membership; same-command
replay returns its original receipt. Scoped GET `/v1/retention-closures/{id}` reads
the current root status and original count/digest without changing state.

Membership has no independent mutable status. Existing root confirm/reconcile
applies Runtime's exact committed/aborted proof; every member inherits that one
state atomically. Pending, unknown or unavailable proof keeps protection. The
artifact_protection owner view includes both ordinary roots and closure members
while reserved/confirmed; released roots remove that group's protection only.
Other reservations for a shared artifact remain independent. No TTL release or
finalized-content deletion is introduced. Immutable history is retained on rollback.

Tests belong under the Data owner's tests/retention_closures and existing Dev
data-artifacts scope. Qualification must cover DAG sharing, bounds, exact identity,
atomic rejection/failure, replay/readback, root proof transitions and independent
installed restart. Runtime's profile binding and worker declaration completeness
are subsequent integration gates; this Data module cannot infer undeclared children.
