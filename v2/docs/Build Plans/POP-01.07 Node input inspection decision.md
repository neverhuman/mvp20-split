# POP-01.07 Node input inspection decision

- Status: owner-approved; implemented and independently qualified in Runtime0.70/node_inputs0.1.
- Reviewed: 2026-10-15 13:05:02 America/Chicago. Owner: POP-01.01/E2.2 collection prerequisite.
- Recommendation: one generic, read-only Runtime input observation endpoint.

## Verified gap

Successful method collection can use the existing AcceptedToolExecution producer
endpoint, including exact prepared inputs. It deliberately returns404 for failed,
pending and absent producers. Current graph detail exposes attempts/output summaries;
scope navigation exposes topology, not retained scope-input bindings. A failed or
skipped method can therefore have no output Artifact from which to recover candidate
identity. Guessing it from dispatch/page order would violate POP-01's no-cross-wiring
requirement, especially after conditional execution or exhausted retries.

The actual Runtime execution_proofs SQL suite passes9 tests, including both retryable
and terminal accepted failures remaining producer_unavailable. Evidence:
.test-results/pop01-closure-sql-e1f73a3b/pytest.log. Successful producer semantics must
remain unchanged. Do not add a worker-owned execution ledger or infer missing fitness0.

## Proposed exact boundary

GET `/v1/graph-observations/{run_id}/nodes/{activation_id}/inputs`.
Require existing scoped `read` AND `inspect_receipts`; no new permission or command.
This is an input observation, never an execution grant or scientific verdict.

Separate public package `node_inputs`0.1 (`amphora_contracts_node_inputs`) avoids
changing existing graph/runtime contract releases. One response family:

| NodeInputObservation field | Shape |
|---|---|
| schema_version / profile | `1` / `runtime-node-inputs-v1` |
| scope / run_id / activation_id / scope_key | Exact owner tenant/project/run/node/scope identities |
| observed_run_revision | Correlation only; no lease or acceptance authority |
| scope_inputs | At most64 original input summaries: port, kind, item_count, missing_count, optional ArtifactRef |
| invocation | Existing PreparedInvocation DTO, or null if no invocation was materialized |

Summaries expose the ArtifactRef for an Artifact input; scalar values and collection
contents remain summarized. PreparedInvocation already contains the exact stored
input bindings/tool/checkpoint and excludes lease/fence/grant credentials. The owner
checks every returned Artifact scope. Collections are not expanded or silently
truncated. Bound serialized response to262144 bytes; malformed owner state fails closed.

Read only existing Runtime graph_nodes, graph_scopes.inputs and activations.specification
in one repeatable-read transaction. No new ledger, table, counter, Data I/O, claim,
completion, scheduling or mutation. Return404 for unknown/scoped-away nodes,403 for
missing grants; no-store responses. The response records the original retained
scope bindings and available prepared invocation, not a synthesized latest binding.

Unlike changing-state output pagination, immutable input retrieval does not require
a currently fresh snapshot token. Its observed revision is explicit; callers use
existing graph snapshots/history to establish terminal/skipped state. Null invocation
alone never proves failure. Non-instantiated branches still require the frozen
branch policy; the collector must reject any candidate association it cannot prove.

## Verification and authorization gate

Preserve all748 predecessor schema bytes and every existing route/receipt. Qualify
scope/grants, queued/success/failed/expired/skipped nodes, exact successful-producer
input agreement, no credentials, response bounds, stale/later run progress, worker
revocation and independent Runtime restart. Then qualify collection through real
owner APIs, including failed required evaluation and conditional-not-taken coverage.

POP-01.06 states: "any further public route or changed legacy semantics returns to
review." Owner explicitly approved the proposed boundary. Implement that exact boundary;
normal-path numerical worker qualification continues independently. E1/E2.1 remain
complete and E2 remains25%; no parent progress credit or extra scientific authority.

Verification complete: [owner boundary evidence](../Audits/POP-01_Node_Input_Inspection.md).
