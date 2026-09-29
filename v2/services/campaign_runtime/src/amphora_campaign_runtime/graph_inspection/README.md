# Graph inspection

Implementation: BP-04.05/B1; focused PostgreSQL/HTTP and public contract tests pass. Foundation verification passed1202 tests/19 installs; process/replacement gates remain open. Focused coverage:217/217 statements,12/12 branches (72 contract/PG/HTTP/policy tests); code coverage does not establish process-cut or scientific correctness. Architecture: [Graph observation protocol](../../../../../docs/Architecture/System/Graph_Observation_Protocol.md).

## Rebuild boundary

This Runtime-owned module observes execution without advancing it. `GraphSnapshots` captures a run/plan/revision/budget and bounded node selection; `GraphDetails` projects activation scope, output summaries, collection members and attempt/completion lineage; `GraphInvalidations` exposes consecutive durable revision notifications. `ObservedCut`, `SnapshotSelection`, `ObservedNode`, `OutputMembers` and `InvalidationWindow` own the projection rules. Public graph-runtime 0.5.0 DTOs serialize those results.

It does not schedule, mutate owner state, decide scientific validity, fetch Artifact bytes, expose lease credentials or grant execution authority. Original command receipts, completion reports and immutable audit pages remain owned by [inspection](../inspection/README.md). There is no new journal, migration or broker.

## Interfaces and state

Configured Runtime 0.11.0 mounts these authenticated GET routes only when both graph execution and inspection history are configured:

| Route below `/v1/graph-observations/{run}` | Result |
|---|---|
| `/nodes` | Snapshot, node page, next page token and initial invalidation cursor |
| `/nodes/{activation}` | Node/containing scope, parent activation, bounded output summaries and attempt page |
| `/nodes/{activation}/outputs/{port}` | Bounded scalar/Artifact/collection-member page; explicit missing slots |
| `/invalidations` | Consecutive immutable event identities/revisions, continuation and `has_more` |

All reads require the authenticated principal's `read` action and tenant/project. Every request uses a read-only repeatable-read transaction against Runtime's own run, graph, activation, attempt, accepted-completion and audit tables. Artifact references are projected, never dereferenced. Dependencies are public contracts, SQLAlchemy and existing Runtime authentication/cursor/domain modules; HTTP adds FastAPI. No cross-service SQL or private imports.

Pages accept 1–100 entries. Node selection supports an exact containing `scope_key` and/or `frontier_only` (waiting/ready/issued). It is not a recursive arbitrary traversal language. Page tokens bind query, mode, scope, run, revision, position and expiry using the existing HMAC codec. Snapshot tokens bind the whole run cut: filtering node membership does not restrict which authorized activation detail may be read at that same cut. Attempts order by fence/attempt identity; values preserve original collection indices and missing members.

## Consistency and failure semantics

Later node, attempt and value pages require the captured run revision to remain current. Committed mutations produce `snapshot_unavailable` (HTTP 409, `resnapshot=true`), never a mixed-revision success. This is a refresh protocol over mutable state, not retained historical frontier snapshots. Immutable plans/cuts/receipts/reports/audit history remain the comparison evidence. Clients can finish paging terminal runs without live-run churn.

Snapshot expiry remains fixed across its pages. Invalidation polling renews the returned continuation's bounded lifetime. The initial cursor is produced in the snapshot transaction, so changes between snapshot and poll are included. Events derive from ordinal-zero audit records, require consecutive revisions, and carry only `run_changed`; duplicates are safe to deduplicate by immutable event ID. Transport order/exhaustion cannot establish completeness. Missing history, restored state behind a cursor, signature/key changes or mode/scope mismatch request resnapshot; expired cursors return 410. Missing authorized resources return 404; invalid page requests return 422. Every page rechecks authorization independently of token possession.

## Verification and replacement

Owned tests: [graph inspection tests](../../../tests/graph_inspection/README.md). Contract tests and eight additive schema artifacts define the wire boundary; the 168 predecessor schema artifacts must remain unchanged. Focused tests cover revision/filter/mode/expiry rejection, missing audit revisions, retry/canonical attempt pagination, missing value slots, opt-in HTTP and authentication. Process-cut and independently installed observer/Runtime replacement proof remain B2/B3/V1, not established by these tests.

Replacement must retain original command/history endpoints and persisted owner records, stable cursor key/mode encoding or explicit resnapshot behavior, bounded projections and unchanged authority. No migration is required for this implementation. Target-host throughput, power-loss recovery, Studio rendering and scientific correctness are outside this module's acceptance claim.

B2 verified checkpoint: actual kills after activation INSERT/before commit, join commit and iteration checkpoint commit; readers preserve one cut or explicitly resnapshot, feedback/history and original receipts survive replacement.32 focused/process tests pass. V1 still owns independently installed observer replacement.
