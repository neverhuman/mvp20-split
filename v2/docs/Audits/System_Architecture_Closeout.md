# System Architecture Proposal Closeout

- Audit type: documentation/design consistency and scenario review
- Timestamp: `2026-09-22 20:30:31` (America/Chicago)
- Scope: proposed system construction, five focused protocols, master navigation and historical implementation-reference posture in the uncommitted v2 working tree
- Plan: [System Architecture Plan](../Build%20Plans/Completed/System%20Architecture%20Plan.md)
- Disposition: coherent proposal for implementation planning; no executable-system acceptance claimed
- Confirmed user decision: single server, separate worker processes, remote scientific tools as needed

## Decisions Reviewed

One execution authority, graph compilation plus durable interpretation, modular control code rather than one service per domain, proposed PostgreSQL transactional state, separate immutable payloads, rebuildable projections, at-least-once dispatch with fenced acceptance, and explicit successor runs for topology amendments. The database's isolation behavior was checked against its official documentation; application locking/retry/effect protocols remain implementation work.

## Paper Scenarios

| Scenario | Defined resolution | Remaining implementation proof |
|---|---|---|
| Two workers complete one activation | Current fence/expected revision and accepted-result uniqueness determine the winner | Concurrent commit test with stale completion retained but not applied |
| Crash after result commit, before notification | Durable outbox/state recovers readiness; no second accepted result | Kill/restart at commit/ack boundaries |
| Provider accepted a lab job but response was lost | Recorded intent becomes uncertain; reconcile instead of blind retry | Fake-provider acknowledgement-loss fixture |
| Lab result corrected after selection | New result revision, affected-consumer record and explicit reevaluation | Retained historical selection plus successor comparison |
| Knowledge publication during an iteration | Existing projection stays pinned; adoption is explicit | Concurrent graph rebuild/publication and run read fixture |
| Human topology edit while workers run | New plan and successor run; explicit carried state and reconciliation | Reject incompatible checkpoint mapping and stale commands |
| Shared budget concurrently consumed | Run/budget transaction boundary serializes admissible reservations | Concurrent budget exhaustion test |
| UI/retrieval projection is stale or unavailable | Display revision/freshness and query committed source; no substitution of authority | Reconnect, projection rebuild and access-revocation fixture |

These are design walkthroughs, not passing runtime tests. The diagrams were reviewed as Mermaid source, not rendered. Structural/link verification is recorded at the design handoff.

## Reconciliation and Limits

The master now has nine direct children: System construction and eight functional domains. The older Implementation Architecture is marked historical, including its assumptions that identity/audit could be added later. Current v2 construction carries those constraints from the first runtime slice. Requirements remain unchanged.

Proposed language/framework, physical schema, provider choices, vector/index technology, deployment packaging, service targets and recovery objectives are not approved implementation facts. They are named next decisions, not concealed gaps. No v1 code or active runtime was changed.

No blocking internal documentation contradiction remains within this proposed scope. Close the design plan at 100% for the defined deliverable while keeping technical approval, implementation, performance, scientific validation and user acceptance separate. Next work is a bounded implementation plan for the graph-runtime vertical slice, not a claim of a finished system.
