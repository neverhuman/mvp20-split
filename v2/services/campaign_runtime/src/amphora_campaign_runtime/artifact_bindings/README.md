# Typed Artifact binding execution

- Status: BP-04.04A / B2 verified; B3 actual process proof active; canonical child owns completion.
- Owner: Campaign Runtime. Architecture: [Typed Graph and Artifact Bindings](../../../../../docs/Architecture/System/Graph_Artifact_Bindings.md).
- Scope: explicit wire-v4 `artifact_project` and `artifact_materialize`; no scientific transformations, discovery or worker attempts.

## Responsibilities

| Module | Owned behavior |
|---|---|
| `model.py` | Stable address, semantic input cut and cumulative conversion budget |
| `encoding.py` | Finite JSON with exact decimal encoding and bounded nesting |
| `conversion.py` | Declared path/field conversion, exact pinned schema validation, ordered and missing slots |
| `publication.py` | Authenticated public HTTP upload/finalize and receipt-first recovery |
| `storage.py` | Opening and terminal records within the existing run transaction |
| `coordinator.py` | Short owner transactions around external I/O, reservation preparation, lease fencing and final acceptance |

Runtime accepts configured exact schemas through the reviewed plan catalog. JSON content cannot introduce a new schema, external reference, executable expression or scientific authority. Explicit `references` verifies each referenced Artifact through its owner; `items` publishes inline records against the declared member schema. Inline materialization verifies Artifact content before embedding it. Missing collection members retain their reason/member object and require an output schema that accepts it. No conversion silently filters, sorts or ranks a collection.

## State and public boundaries

`runtime_0012` owns `binding_intents`, `binding_reservations` and immutable `binding_closures`; `runtime_0013` widens the graph node-kind column for the explicit materialization tag. Service grants permit preparation/lease/status updates but cannot rewrite the opening node, inputs, deadline or identity; closure insertion references the same owner audit revision. Startup never migrates.

An issued graph node has one `binding:<UUIDv5>` identity derived from scope/run/activation/plan. Its input fingerprint includes the normalized node, named committed inputs, ordered members and missing reasons. Opening revision and database deadline are retained separately. Unrelated run revisions never create a new conversion. Private closure receipts are durable logical conversion outcomes, not worker attempts or synthetic user commands; the public Artifact outcome protocol uses their stable receipt IDs.

The coordinator claims a renewable 30-second private I/O lease bounded by the original deadline. Every I/O boundary rechecks the run, node, token and source cut under the run lock, then releases SQL before network calls. A later process can resume after lease expiry. Finally blocks release only their own token. Lease renewal cannot extend the authored conversion deadline.

Before reading content, Runtime records the exact source protection request and reserves it through Artifact's public API. Published member/result references are recorded and protected similarly. Accepted outputs must match their declared type and scope, have exact saved reservation evidence, and pass a final database-clock check. Output, logical receipt, retention proof, node state and audit commit atomically. Binding work does not create activations/attempts or change spent/reserved scientific invocation budget.

Publication identities derive from the conversion, public command family and positional slot. Begin-upload replay returns the original upload; finalization history is checked before another stream. A lost finalization response recovers the original owner receipt. Network timeouts leave the conversion prepared within its original deadline. A terminal owner rejection blocks the binding explicitly. This is replayable logical publication, not a promise of exactly one HTTP request or provisional file.

Cancellation and graph closure abort prepared conversions in the owner transaction. Late reservations are saved against the original prepared binding and queued for reconciliation; they cannot revive a closed output. The polling path also settles conversions left by other terminal transitions. Notifications and in-memory objects have no execution authority.

Configured hosting requires an explicit `bindings` Artifact endpoint/token plus the existing reservation peer. Default admission keeps wire-v4 disabled. `/v3/graph-runs` exposes the new node kinds; older graph pages reject wire-v4 rather than omit its nodes. Worker payloads and scientific tools retain their existing contracts.

## Verification and replacement

Owned suites: `services/campaign_runtime/tests/bindings`; selector `dev/run_tests.py --module runtime --area bindings --coverage`. SQL tests use the actual Runtime owner and a labeled scripted Artifact peer. The dynamic graph runs the actual affine kernel in process through Runtime claim/completion transactions: producer, graph-controlled scatter/scoring, ordered gather, consumer and two iterations. Independent expected values are `[7, 11, 15]`, ten tool invocations and twenty conversions. This is not installed tool/Artifact process acceptance.

Replacement must preserve stable input/slot identities, schema pins, budgets, recorded deadlines, exact reservation binding, immutable closure evidence and original outcomes. Required B3/V1 gates add actual process contention/death and independently installed peer/replacement proof. Target-host power-loss durability, high-volume throughput and scientific validity remain outside this module's evidence.

B3 checkpoint (`2026-09-29 16:08:36`): 59 owned tests pass, including five actual process cases, claim-time source-cut rejection, post-publication source-cut rejection and reverse member completion. Parent-interpreter binding coverage is 415/442 statements and 71/82 branches; child-process lines are not included. Actual installed Artifact/tool replacement remains V1. The [installed acceptance harness](../../../tests/bindings/acceptance/README.md) documents that independent tier.

B2 focused checkpoint (`2026-09-29 15:45:24`): 39 owned tests pass; artifact_bindings coverage 408/442 statements and 70/82 branches. Remaining gaps include claim-time expiry/source-cut failure, malformed peer responses and actual process interruption; B3/V1 own their independent proof. A fresh CLI process test catches import-order startup regressions that an already-initialized test interpreter can hide.

V1 checkpoint (`2026-09-29 16:25:58`): actual installed scope `2d3aa4d553874342a550f4de8381cc9b` passed finalization-response interruption, original receipt/no-restream recovery, committed proof replacement and two-generation [7,11,15] execution. All 30 reservations confirmed through bounded passes. B3/V1 required gates are complete; scientific/target-host exclusions above remain.

Supervised materialization uses effective.resolve_effective for both BindingExecution intent opening and BindingCoordinator.context revalidation. It checks the actual scoped checkpoint winner, rejects pending/blocked decisions, and overlays only exact permitted scalar values through ScalarSelection while retaining original node/plan. Both paths compute the same semantic input digest. Unsupervised materialization and Artifact projection preserve ordinary resolution. Accepted parameter selection remains separate from publication, reservations and committed outputs.
