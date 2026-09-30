# Consistent Graph Observation Protocol

Design status: BP-04.05 accepted and closed; BP-05.02 additive navigation implementation in progress. Parent: [Graph Execution Model](Graph_Execution_Model.md).

## Authority and ownership

Runtime owns graph observations; clients never reconstruct execution authority from notification delivery or cached page membership. A focused `graph_inspection` module reads owner tables and reuses the existing authenticated inspection cursor codec. Command receipts, accepted completion reports and immutable audit history stay in `inspection`; attempts and worker authority stay in lifecycle. No second event journal, shared ORM, scientific payload fetch or independent scheduler is introduced.

The first profile is one active campaign, with concurrent workers. Existing graph page endpoints remain compatible but do not gain implied snapshot guarantees. New additive DTOs and explicitly named snapshot/detail/invalidation routes provide the stronger contract when graph hosting and an inspection signing key are configured. Default validation-only hosting remains unchanged.

## Snapshot and pagination

A read-only repeatable-read transaction captures scope, run/plan identity, run revision, frontier revision, run status/budget, bounded query and matching node count. Query supports an optional exact containing scope key and a frontier-only view; neither is an arbitrary SQL or graph traversal expression. Pages order immutable activation identities and return at most 100 nodes. Tokens bind mode, authenticated scope, run, query, revision, position and expiry with the existing HMAC profile.

Later pages and activation detail require the same current run revision as the snapshot. If the run advanced, return an explicit resnapshot response instead of mixing old and new node state. The profile does not pretend to retain historical mutable frontier rows: historical comparisons use immutable plan/cut/receipt/completion/audit evidence. A client can pin a completed campaign or refresh a live one. Snapshot expiry, filter/scope mismatch, key rotation, restored database behind a cursor and missing source records never silently fall back to a new snapshot.

Detail exposes the node/path/containing-scope boundary, public value summaries and bounded attempt lineage. Collections expose counts/missing counts and Artifact references through bounded pages, not an unbounded nested JSON dump. Credentials, delivery/lease tokens, arbitrary internal node state and Artifact payload bytes are excluded. Attempt/detail pagination obeys the same snapshot revision; existing accepted-completion routes provide immutable scientific-tool output references separately. Read access is checked on every page and cannot be granted by possession of a cursor.

## Resumable invalidations

The snapshot transaction returns an invalidation cursor positioned after its captured run revision, closing the race between reading and subscribing. Polling returns at most 100 durable run invalidations derived from the existing ordinal-zero audit event for each subsequent revision. Each entry identifies the immutable event and run revision and means "refresh authoritative state"; it is not an instruction, a patch, a completion claim or a scientific fact.

Require consecutive run revisions. A missing ordinal-zero event, cursor beyond restored history, expiry or mismatched run/scope requests resnapshot explicitly. Duplicate pages are safe because event IDs/revisions are immutable; clients deduplicate and retain their last accepted cursor. Bounded pages and the next cursor support reconnect without trusting transport delivery order. The terminal run remains readable. No claim of exactly-once network delivery is made, and notification-outbox exhaustion does not erase durable invalidations.

Snapshot pagination preserves its original expiry. Successful invalidation polling may issue a fresh bounded lifetime for the returned continuation, with the exact last observed position. Missing history must be detected before exposing a continuation; no empty successful response may skip a committed revision. Scope and filter checks occur before results are projected, and response sizes stay bounded independently of campaign size.

## Verification and replacement

Preserve all 168 predecessor schema artifacts. B1 adds owned contracts, routes/domain projections, consistent SQL reads, failure examples and module-local tests. B2/B3 use actual PostgreSQL and process barriers to prove activation/join/iteration recovery, reader consistency, duplicate/reordered invalidations, missing history, expiry and the one-active-run guard. V1 independently installs/replaces the observer and Runtime while retaining original plans, scoped cursors, receipts and committed lineage, then audits the complete BP-04 outcome. Target-host throughput, power-loss, Studio presentation and scientific validation remain separate plans.

## Authored topology and occurrence navigation

BP-05.02 adds Runtime-owned `graph_navigation` projections under graph-runtime0.6.0/Runtime0.12.0. Scope pages select roots or immediate children of an exact activation, preserving definition path and loop/scatter occurrence addresses. Topology reads resolve the immutable retained authored body inside Runtime and match each authored node to its activation in that occurrence scope. Activation order never creates links. Optional focus/radius0..2 bounds neighborhood discovery; returned links retain original direction/route.

Both reads reuse the authenticated snapshot cut and signed query-bound continuation policy. At most100 nodes/scopes per page; one authored scope is bounded at256 nodes/1024 links. A link belongs to its source node's page; an unloaded target is explicit omitted context until fetched. Browser scenes remain independently bounded at200 nodes and expose additional windows. Read-only repeatable-read transactions and public contracts preserve owner isolation; no new persistence migration or second graph authority. Consumer and PostgreSQL regressions pass; named-view integration and independent navigation replacement remain BP-05.02 gates.
