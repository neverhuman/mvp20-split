# Acquisition Provenance

- Status: BP-06.01/B1 partial; exact-byte verification and private acquisition ledger implemented. No ingestion route or adapter yet.
- Owner: Data/Artifacts; design [Acquisition](../../../../../docs/Architecture/Data/Acquisition.md).

`SourceDocument` verifies a scoped SourceRevisionRef against at most4MiB of exact bytes. `extract(SourceSpan)` checks full source identity, half-open byte bounds and digest. It does not translate character offsets or decode/execute instructions. `TraceDocument.verify(trace, source, output)` validates matching scope/schema/source identities, output content, unique target paths, ordered-transform references and copied/converted/inferred/missing field policy. Missing or inferred values cannot receive `normalized` disposition. No disposition grants scientific acceptance.

Verified traces expose deterministic UTF-8 canonical bytes (sorted keys, compact JSON, no NaN; offsets/indices are bounded integers). Their public ConversionTraceRef is SHA-256 over those bytes. The acquisition ledger rejects an existing scoped trace ID with different canonical bytes; the pure provenance objects alone provide no persistence. It changes no existing command encoding.

Pure provenance depends only on public Core/evidence contracts and standard-library hashing/JSON. The private ledger additionally uses SQLAlchemy and the existing Data principal/catalog boundary, within the same service. No peer service imports or SQL are allowed. Callers must obtain bytes through authorized publication/read boundaries and check current rights before using these pure objects. Successful byte verification is not proof of authorization, sample identity, declared conversion algorithm execution or scientific validity.

`tests/acquisition/` owns exact-byte, UTF-8 offset, cross-scope, changed-content and origin-policy cases. The scope is independently runnable via `run_tests.py --module data-artifacts --area acquisition`. Replacement must preserve error codes, canonical bytes and immutable references. Persistence, rights fencing, bounded adapters and actual owner integration remain B1-B3/V1 work; this README must expand when those behaviors arrive.

Verification checkpoint:25 owned tests,100% lines (64/64) and branches (10/10) for provenance.py. Isolated wheel installation repeats all25 without Runtime installed. This focused suite does not measure the rest of the service or prove ingestion persistence.


## Private Acquisition Ledger

AcquisitionLedger.register requires the acquire action, matching source/rights scope and a SourceDocument with verified raw bytes. It verifies the entire ArtifactRef against the finalized local catalog. Rights references are historical provenance only at this stage; no current rights grant or scientific-use claim is made.

Delivery uniqueness is scope/issuer/delivery, independent of source ID. Exact canonical replay returns the original revision even after newer corrections. Changed metadata or bytes under a delivery key conflict; another delivery cannot overwrite a source revision. Corrections name the exact previous reference and must match the persisted source head. Stable, sorted transaction advisory locks serialize delivery/source races; source revision and head commit together. Canonical records are bounded to256KiB.

retain_trace verifies source/output bytes and provenance before storing an immutable trace, requires the exact registered source and finalized output reference, and rejects changed content under the same trace ID. Changed conversions require a new trace ID. history/trace_history require source_history and return exact historical records, never evidence usability. No raw document text is copied into these records.

artifact_0004 adds private source_revisions/source_heads/conversion_traces with scoped catalog/source foreign keys. artifact_service has SELECT/INSERT and only head-column UPDATE, no historical UPDATE/DELETE. Infrastructure errors propagate; retrying identical records reconciles uncertain commits. Public routes, current rights/expiry fencing, adapters, Research identity matching and process-kill acceptance remain pending B1-B3/V1 work.

Owned PostgreSQL tests use actual upload/finalization, concurrent cross-source delivery contention, correction/replay, trace collision, catalog forgery/missing artifact, head-write rollback, scope and role denial. Pure-source spans retain their existing25 tests. The fixture never resets retained PostgreSQL state.
