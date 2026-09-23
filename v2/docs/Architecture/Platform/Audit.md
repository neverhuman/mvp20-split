# Audit Lineage and Reconstruction

- Design status: detailed proposed contract; implementation and scientific acceptance pending
- Naming note: component/record/operation names below are proposed logical design, not implemented APIs or selected deployment technology
- Last reviewed: `2026-09-22 18:56:40` (America/Chicago)
- Parent: [Domain overview](Platform_Architecture.md)
- Requirement source: [Product Requirements](../Product_Requirements.md#cross-domain-ui-and-functional-auditability)

## Owned Contract

Immutable event envelopes record event/schema identity, order/time, correlation/causation, actor/delegation, tenant/object scope, requested/performed action, prior/result revision/hash, reason/policy/approval and input/tool/model/knowledge/code bindings. Outputs, costs, errors and external effects reference protected artifacts. Domains define transition meaning; Platform owns durable audit and reconstruction mechanisms.

Consequential changes require atomic audit binding or a recoverable outbox equivalent. Delivery may be asynchronous, but missing commitment yields failure or non-final state. Detect and reconcile duplicated, reordered, missing, corrupted and misbound events.

## Boundary and Projections

Execution/provenance graphs, timelines and search indexes are derived. Support version comparison, affected-consumer analysis and deterministic recomputation with explicit provider/nondeterminism limits. Export packages pin manifests, inventories, hashes, redactions, omissions and authority ceilings. Corrections produce new linked snapshots.

## Invariants and Verification

Administrators cannot rewrite scientific evidence/approvals. Deletion preserves permitted tombstones without forbidden payloads. Verify result-to-evidence traversal, failed audit writes, tampering, restart/order, access isolation and export integrity. Product runtime audit is separate from repository SDLC drift audits.

## Component and Record Design

| Proposed component | Owned responsibility |
|---|---|
| Event commitment adapter | Atomic domain-change/audit binding or recoverable outbox interface |
| Immutable event ledger | Ordered identities, integrity metadata and retained event revisions |
| Projection/reconstruction service | Domain timelines and derived lineage from committed records |
| Impact index | Reverse references from sources/rules/models to decisions and consumers |
| Export verifier | Scoped snapshot manifest, integrity checks and omission/redaction statements |

An event's sequence is scoped to an explicitly identified stream/aggregate; wall-clock timestamps alone are insufficient for ordering. Cross-stream causation links establish dependency, not an invented global total order. Large/private payloads live behind protected artifact references while searchable metadata remains policy-scoped.

## Commit and Reconstruction Flow

The domain transaction records its state change and durable audit commitment together. Projection consumers maintain resumable positions, deduplicate event IDs and detect missing sequences. Reconstruction requests specify object/version or a documented consistent cut across related objects; historical reads must not combine incompatible snapshots silently.

Exports bind event/object inventories, artifacts, policy/redaction state and generation identity. Integrity verification distinguishes content hashes, identity/authenticity and scientific validity; a hash proves neither authorship nor truth. Corrected assertions and redacted payloads preserve permitted lineage/tombstones.

## Failure and Boundary Example

A state update succeeds but its required event cannot commit: the action must roll back or remain explicitly non-final according to the transaction design. A projection falls behind: show its watermark/freshness and rebuild from the ledger rather than claim missing events mean no activity. Missing external artifacts yield a documented replay limitation.

## Design Basis and Open Decisions

Cross-domain audit requirements govern this layer. Remaining decisions: event schema registry, stream partitioning, integrity/signature mechanisms, retention and consistent-cut reconstruction. Recovery tests must cover out-of-order delivery and cross-object references, not just individual rows. SDLC closeout audits remain separate documentation controls.
