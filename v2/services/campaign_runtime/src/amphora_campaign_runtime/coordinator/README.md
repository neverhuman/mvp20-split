# Durable graph coordinator

- Status: BP-04.02/B1 verified; B2 advancement active. Gates and percentages are in the [canonical child](../../../../../docs/Build%20Plans/BP-04/BP-04.02%20Frontier%20and%20scheduling.md).
- Owner: Campaign Runtime, package 0.3.0. Architecture: [Graph Execution Model](../../../../../docs/Architecture/System/Graph_Execution_Model.md), [Graph Runner](../../../../../docs/Architecture/System/Graph_Runner.md).
- Public DTOs: [graph-runtime contracts](../../../../../contracts/graph_runtime/README.md) 0.1.0; executable campaign contracts 0.2.1/wire-v2; unchanged worker contracts.

## Responsibilities and boundaries

This module turns a configured exact compiled plan into a durable, scoped graph run and initial frontier. It does not introduce another scheduling service, private peer imports, scientific adapters, a shared ORM or a second attempt/budget authority. Existing Runtime lifecycle/completion modules still own worker claims, leases/fences, conserved budget, accepted tool outcomes and artifact-retention handshakes.

| Module | Responsibility |
|---|---|
| `plans.py` | Compile configured definitions against exact public metadata; scope/hash allowlist and immutable tool descriptors |
| `values.py`, `bindings.py` | Typed committed inputs, explicit local source resolution and worker DTO projection |
| `frontier.py` | Pure scope/node identities and deterministic initial ready/waiting intents |
| `storage.py` | Transaction-local immutable plan and scoped frontier persistence |
| `materialization.py` | Idempotent conversion of ready invocation intents to existing worker activation rows |
| `admission.py` | One-running-campaign guard, atomic plan/run/frontier/receipt/audit/outbox admission |
| `reads.py` | Scoped read-only repeatable-read pages of committed graph observations |

`ReviewedPlan.compile` is an owner/configuration entry point, not proof of a human review or a live Registry decision. `PlanCatalog` explicitly authorizes only configured scope/hash entries. `GraphAdmission.admit(principal, command)` requires the existing admit action and exact command identity/scope, then validates named input types/units/schema/representation, expansion limits and the one-running-run slot. The supplied artifact references are trusted immutable pins; admission does not fetch payloads, verify their scientific validity or refresh live Registry capacity/lifecycle. Host-level public orchestration and its peer validation remain later gates; this initial library boundary is not exposed as a general executable HTTP API.

## Durable invariants and transactions

Migration `runtime_0007` adds explicit `execution_mode` (existing runs default to fixture), immutable `graph_plans`, run-bound graph input/limit/deadline records, scoped graph bodies and unique node activation identities. Runtime's service role can read/insert these records, update only named state fields, and cannot rewrite/delete plans or admitted input identity. Peer roles gain no access. Startup never migrates. Quiesce old Runtime implementations before graph mode is enabled: pre-0.3 completion code does not understand graph termination ownership.

Admission registers the canonical command, then takes the existing admission guard. Plan, run, scope, all root-body nodes, initially ready invocation rows, notification/audit and accepted receipt commit together. Any failure rolls back that transaction; the registered command remains retryable. Exact command replay returns the original receipt, creates no second run/node/budget reservation and does not refresh authority. Plan storage reapplies the wire types when comparing JSONB so exponent expansion cannot change numeric identity. Scope/run foreign keys and unique scope/node/activation keys prevent duplicates and cross-scope attachment.

Every body node is represented in the frontier. Roots start ready, successors waiting. Ready Invoke nodes are materialized into the existing `PreparedInvocation` protocol with their deterministic activation identity and plan order. Control-node advancement, successors, scatter membership freezing and loop feedback are still B2. Calling the initial planner twice produces the same immutable intents; an inserted invocation must retain the same specification and dispatch ordinal.

Materializing queued work costs no attempt budget. The existing claim transaction reserves one unit under the run lock, and terminal attempt settlement spends it exactly once. A graph can have more queued work than available units; it cannot issue more leases than its budget permits. Graph invokes use the earlier of their activation timeout and the admitted graph deadline. Claim order is dispatch ordinal then activation ID; legacy fixtures retain ordinal zero and their existing order.

Graph tool metadata is frozen once by exact binding, allowing later activations without mutating the run snapshot. Completion looks up the matching graph pin and rejects missing metadata; fixture lookup keeps its original invocation-key behavior. Worker success/failure cannot infer whole-graph completion from the currently materialized invocation rows. Graph completion remains running until its coordinator accepts Finish/terminal frontier; uncertainty and emergency cancellation remain fail-closed lifecycle authority. Fixture run terminalization is unchanged.

## Values, observations and identity

Graph command numbers use bounded plain decimal strings, for example `{kind: number, value: "0.25", unit: "g/mol"}`. This preserves the existing float-free `amphora-command-v1` identity and the pinned worker closure. Compiler numeric literals retain their existing wire representation; the value resolver converts them explicitly to plain decimal strings when producing committed graph values. No implicit unit/schema/representation conversion or arbitrary object packing exists. Collections preserve order and explicit missing-member reasons.

`ScopeAddress` hashes the plan and typed loop/scatter occurrences. `ActivationAddress` additionally binds the node. Parent-plan order, occurrence index and local order determine priority; hash ordering is not execution priority. These identities are unique within the run and are not attempts, leases or authorization grants. Human topology changes belong to later campaigns.

`GraphReads.run` requires a read principal and returns at most 100 node observations with a scoped keyset cursor. Counts, run budget and nodes share one repeatable-read snapshot; a missing/foreign run is indistinguishable. Pages are committed observations, not subscriptions or a guarantee that a worker remains authorized. No scientific payload bytes or credentials are exposed.

## Verification and remaining work

Owned suite: `services/campaign_runtime/tests/scheduling`, selected with `dev/run_tests.py --module runtime --area scheduling`; PostgreSQL cases require the labeled fixture opt-in. B1 scoped evidence: 18 scheduling cases pass. Coordinator-only coverage is 289/300 statements (96.33%) and 27/34 branches (79.41%); gaps include future output/result resolution, unused persisted-scope lookup and tool lookup that B2 will consume. The whole Runtime owner denominator remains available in the coverage report. Pure cases independently specify root frontier sets and nested occurrence priorities. Actual PostgreSQL cases cover atomic admission/replay, rejection with no run/frontier, rollback after insert, immutable service-role permissions, scoped paging, deterministic parallel-root claims with one budget unit, retained numeric plan identity and a real Runtime completion commit that leaves the graph open. That last test uses a scripted reservation peer; actual tool/Artifact process acceptance remains V1.

B2 must implement durable advancement/recovery and configured public hosting, including bounded active worker observations for graphs larger than the legacy 256-row snapshot and precise iteration/checkpoint behavior. B3 requires competing actual coordinator processes, restart after commit-before-notify, zero scatter/loop limits/blocked dependencies and independent progress. BP-04.03 owns richer partial/failure/external-wait policy; unsupported behavior must remain blocked, never reported successful. No current test establishes full graph execution, scientific validity or target-host deployment.
