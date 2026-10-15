# Artifact retention contract

Version0.1.0 owns the additive POP-01.06 derived-closure reservation boundary.
Architecture: [Artifact publication](../../docs/Architecture/System/Artifact_Publication_Protocol.md).

`ReserveDerivedClosure` requires profile `derived-closure-retention-v1`, a scoped
root ArtifactRef and the existing CompletionIntentBinding. Its closed command family
is `artifacts.reserve_derived_closure`, using the ordinary canonical command encoding.
The parser rejects cross-scope roots. Data separately authenticates the retention
grant and requires the actor to equal runtime_owner.

`DerivedClosureReservationReceipt` wraps the ordinary root reservation receipt,
explicit profile, count1..4096 and membership digest. All three existing reservation
statuses remain available. Same-command replay preserves original bytes; current
readback can show a later monotonic status with the same membership identity.

Data owns atomic membership and root transitions. It walks only immutable declared
derivation/conversion edges, with4096 distinct artifacts and128 direct parents as
ceilings. Protection grants no payload-processing rights or scientific validity.
Workers must declare every referenced child; this contract does not inspect an
arbitrary scientific JSON payload or discover undeclared references.

Membership identity hashes `amphora.artifact-retention/derived-closure-v1`, one zero
byte, then UTF-8 compact sorted-key JSON of full ArtifactRefs sorted by artifact_id,
with no trailing newline and nonfinite values prohibited. The root is a member.
Data's immutable catalog and ancestry establish the set; this package supplies no
storage, traversal, networking, scheduling or execution authority.

Public routes are POST `/v1/retention-closures/reserve` and scoped GET
`/v1/retention-closures/{reservation_id}`. Existing confirm/reconcile use Runtime's
unchanged exact root completion proof. Private membership state follows the root's
status atomically. Legacy direct-root contracts remain unchanged.

Tests live under `tests/`, owned by Dev's artifact-retention scope. Replacement must
preserve command/schema bytes, strict profiles/fields, integer bounds and scope
rejection. Dev separately pins all744 predecessor schemas. Contract tests do not
establish actual owner membership, protection or restart behavior.
