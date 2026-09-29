# External wait boundary

Owner: Campaign Runtime, package 0.5.0. Active delivery: [BP-04.03](../../../../../docs/Build%20Plans/BP-04/BP-04.03%20Aggregation%20and%20failure%20policy.md). Design: [Graph execution](../../../../../docs/Architecture/System/Graph_Execution_Model.md). This module implements B1 identity, compatibility and storage preparation. The v3 execution profile is rejected by admission until B2 supplies transition/retention integration.

## Responsibilities and authority

`WaitRecord.pin` binds one run/activation/plan occurrence to an exact issuer, purpose, subject artifact, expected external revision, output schema/representation/unit, timeout disposition and deadline. The deadline is the earlier of the node timeout and admitted run deadline. UTC microseconds use exact integer arithmetic, preserving the portable command encoding. Versioned content identity includes all pins. Recreating a record with a later deadline cannot replay the original opening.

`ReceiptEvidence` preserves the issuer's immutable receipt identity and typed accepted/rejected/abstained/superseded outcome. `WaitRecord.validate_receipt` checks all bindings and exact accepted output type. Superseded, foreign-purpose/revision/subject receipts cannot satisfy the wait. This check grants neither scientific authority nor execution acceptance. The configured principal and command boundary own authentication; Research/Knowledge scientific acceptance remains a separate owner. The initial acceptance peer is explicitly synthetic.

Raw DTO fields are revalidated before serialization. This matters because a programmatically constructed invalid integer DTO can serialize a boolean as an integer. `wire.raw_fields` is a private conversion helper, with no policy, state or cross-service imports.

## Durable boundaries

Migration `runtime_0009` adds the await node tag, immutable `graph_waits`, `graph_wait_receipts`, `graph_wait_closures`, separate `wait_retention_intents`, and immutable `wait_intent_reservations`. Opening and closure records bind the scoped ordinal-zero run audit through deferred foreign keys. One activation has one pinned opening and at most one closure. A closure must match the opening's revision and expectation hash. Receipt IDs are unique per scope/issuer; byte changes under the same identity are rejected. Service grants exclude rewriting/deleting pins, receipts, closures and reservation evidence. Only retention status/outcome are updateable by this owner.

`WaitRecords.open(connection, record, opened_revision)` takes the run lock, checks live run/node/plan/deadline and the next run revision, and inserts the pin. The caller must append the matching audit and commit the associated run transition atomically. Exact opening replay returns its original identity, including after subsequent run revisions. `retain_receipt` inserts or verifies immutable issuer bytes; it does not unblock anything.

`WaitRetentionIntent` binds the exact expectation/receipt to one registered command operation and configured runtime owner. Intent IDs use a distinct `wait:` namespace. Its public Artifact reservation uses one internal `result` binding; this is independent of the authored node output-port name. `WaitPreparation.prepare` runs under the same run lock, checks a live unclosed deadline and the exact pending `graph.submit_receipt` payload, then records PREPARED protection before any external call. Replaying PREPARED rechecks authority/deadline; replaying a terminal proof preserves history. No worker attempt/fence is fabricated and no attempt budget is reserved or spent.

## Public compatibility and remaining implementation

Public [graph contracts](../../../../../contracts/graph_runtime/README.md) define issuer receipts, pinned expectations, submit commands, closure/observation DTOs and a separately versioned graph page. The compiler accepts campaign wire-v3, including nested waits, while old wire-v1/v2 schemas and plan identity remain unchanged. Admission still rejects wire-v3 with `graph_execution_profile_unavailable`. There is no receipt HTTP handler, waiting-loop dispatcher, timeout/acceptance policy or new Artifact outcome proof wired into hosting yet.

B2 must connect Artifact reservation outside SQL, exact post-I/O rechecks, atomic closure/receipt/audit/output acceptance, separate intent outcome lookup, terminal confirmation/reconciliation and cancellation/timeout cleanup. B3 must prove competing processes choose one closure and cannot reopen cancelled scopes. B1 storage fixtures build v3 parent rows directly and explicitly do not substitute for those gates. V1 must use the installed owner plus an actual synthetic issuer and available peers, preserving history across replacement.

Owned tests: `tests/waits`; selector `dev/run_tests.py --module runtime --area waits --coverage`. Actual PostgreSQL cases require `AMPHORA_TEST_POSTGRES=1`. Replacement preserves wire versions, both identity profiles, exact issuer/subject/type pins, scoped foreign keys, stable prepared intents and immutable audit-linked history. It may not infer scientific eligibility or missing values from transport success.
