# Typed Graph and Artifact Bindings

Design status: approved implementation boundary under [BP-04.04A](../../Build%20Plans/BP-04/BP-04.04A%20Typed%20artifact%20and%20collection%20bindings.md). Wire/compiler B1 is verified; durable execution is the active B2 delivery. Parent: [Graph Execution Model](Graph_Execution_Model.md).

## Ownership and Data Model

Graph Runtime owns finite typed conversion, source-cut identity, ordered membership and execution acceptance. Artifact owns content validation/publication/storage and protection. Scientific selection, ranking and mutation remain indexed tools. The builtin primitive catalog identifies these two Runtime operators and their schema/profile; it does not register them as scientific tool releases or grant scientific authority.

Wire-v4/profile-v3 adds `artifact_project` and `artifact_materialize`; published v1-v3 campaign roots stay byte-compatible. `artifact_project` reads one Artifact through a finite declared path. Its mode selects scalar/collection values, an explicit reference manifest, or inline members that must be published as individual Artifacts. `artifact_materialize` builds a JSON object from a finite named field list, with each field explicitly choosing inline values or reference pins. Schema, representation, unit, missing slots and resource limits are declared. Field order is nonsemantic; collection order remains semantic. JSON resembling a reference never grants authority by itself.

All referenced content is scoped and verified through Artifact's public API. Inline fields require exact content hashes and pinned schema validation. Explicit reference mode independently verifies the referenced owner object and expected schema/media type before graph exposure. Missing members preserve their member/reason object; output schema must explicitly accept it. Conversion never filters missing members, computes a fitness value or silently ranks a population.

## Stable Conversion Identity

The private address profile `amphora-binding-address-v1` binds scope, run ID, activation ID and admitted plan hash. Its UUIDv5 under the URL namespace yields `binding:<hex>` as the conversion/protection-intent identity. Identity is independent of the current polling command, worker fence, process, completion arrival order and mutable run revision.

The private input profile `amphora-binding-input-v1` hashes the normalized authored node and canonically named, committed input bindings. Collection member order and explicit missing reasons remain in that hash. Persist the opening run revision and a database deadline separately; unrelated run revisions do not change stable input identity. A resumed operation must match the retained configuration/input hash and deadline, not reconstruct them from a new wall clock.

Publication command IDs derive from conversion identity, operation family and ordered output slot. Item outputs use stable positional slots; materialization uses one result slot. Exact duplicate content may share Artifact storage but retains its declared graph member slots. Scope and logical acceptance do not collapse merely because bytes match. Artifact retention binds the conversion ID, semantic input identity and exact source/member/result slot. Returned reservations must match saved exact references; neither a fabricated worker attempt nor an execution-budget charge is needed.

## Owner Transaction and External I/O

1. Under the run lock, validate the ready node and exact committed source cut; persist the conversion identity/input/deadline and audited opening. No network or file publication occurs while this lock is held.
2. Outside SQL, retrieve and verify bounded Artifact metadata/bytes; apply the finite projection/field mapping; validate projected items and complete assembled output against pinned schemas. Enforce cumulative member, Artifact, byte and elapsed-time limits, not just per-item limits.
3. Publish outputs using stable public upload/finalize commands. Persist returned publication identities so a lost reply/restart resumes the same operation. Record exact source/result protection bindings and PREPARED intent state before calling reserve outside SQL.
4. Reacquire the run lock and recheck run authority, node status, original input fingerprint, deadline and exact reservation evidence. Commit accepted graph outputs/membership, retention outcome proof, node state, run revision, audit and original operation receipt together. No partial member list is observable as accepted.
5. If cancellation, deadline or a competing terminal transition won, preserve that transition, abort prepared protection and reconcile late reservations. Transport uncertainty remains retryable within the original deadline; malformed/hash/schema/authority failures produce explicit terminal reasons. An interrupted publication may leave unreferenced content for Artifact's bounded cleanup, never an unprotected accepted graph output.

The active coordinator processes resumable conversion work outside its ordinary locked graph pass. Passive graph advancement consumes only committed conversion outputs. Durable state and public owner receipts provide restart authority; an in-memory future or notification does not. Operators retain their own bounded resource accounting; worker attempt/spent/reserved counters retain their existing scientific-invocation meaning.

## Required Proof and Boundaries

B1 verifies public roots, old-schema pins, strict malformed fixtures, independent compiler ports/order and disabled new-profile admission. B2 supplies real private state transitions and Artifact publication/protection. B3 requires actual competing/interrupted processes with one immutable output and no unprotected accepted member. V1 runs producer -> projection -> graph scatter/gather -> materialization -> consumer through installed peers and preserves the round trip across Runtime replacement.

This boundary enables domain-general dynamic data flow. It establishes no scientific validity, arbitrary schema coercion, hidden tool scheduling, remote URI fetching, automatic nested-reference authority or target-host durability.
