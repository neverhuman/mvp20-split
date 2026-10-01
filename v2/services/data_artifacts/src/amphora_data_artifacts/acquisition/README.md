# Acquisition Provenance

- Status: BP-06.01/B1 partial; exact-byte verification and private acquisition ledger implemented. Bounded document and synthetic lab preparation implemented; no ingestion route yet.
- Owner: Data/Artifacts; design [Acquisition](../../../../../docs/Architecture/Data/Acquisition.md).

`SourceDocument` verifies a scoped SourceRevisionRef against at most4MiB of exact bytes. `extract(SourceSpan)` checks full source identity, half-open byte bounds and digest. It does not translate character offsets or decode/execute instructions. `TraceDocument.verify(trace, source, output)` validates matching scope/schema/source identities, output content, unique target paths, ordered-transform references and copied/converted/inferred/missing field policy. Missing or inferred values cannot receive `normalized` disposition. No disposition grants scientific acceptance.

Verified traces expose deterministic UTF-8 canonical bytes (sorted keys, compact JSON, no NaN; offsets/indices are bounded integers). Their public ConversionTraceRef is SHA-256 over those bytes. The acquisition ledger rejects an existing scoped trace ID with different canonical bytes; the pure provenance objects alone provide no persistence. It changes no existing command encoding.

Pure provenance depends only on public Core/evidence contracts and standard-library hashing/JSON. The private ledger additionally uses SQLAlchemy and the existing Data principal/catalog boundary, within the same service. No peer service imports or SQL are allowed. Callers must obtain bytes through authorized publication/read boundaries and check current rights before using these pure objects. Successful byte verification is not proof of authorization, sample identity, declared conversion algorithm execution or scientific validity.

`tests/acquisition/` owns exact-byte, UTF-8 offset, cross-scope, changed-content and origin-policy cases. The scope is independently runnable via `run_tests.py --module data-artifacts --area acquisition`. Replacement must preserve error codes, canonical bytes and immutable references. Rights fencing and actual owner integration remain B1-B3/V1 work; this README must expand when those behaviors arrive.

Verification checkpoint:25 owned tests,100% lines (64/64) and branches (10/10) for provenance.py. Isolated wheel installation repeats all25 without Runtime installed. This focused suite does not measure the rest of the service or prove ingestion persistence.


## Private Acquisition Ledger

AcquisitionLedger.register requires the acquire action, matching source/rights scope and a SourceDocument with verified raw bytes. It verifies the entire ArtifactRef against the finalized local catalog. Rights references are historical provenance only at this stage; no current rights grant or scientific-use claim is made.

Delivery uniqueness is scope/issuer/delivery, independent of source ID. Exact canonical replay returns the original revision even after newer corrections. Changed metadata or bytes under a delivery key conflict; another delivery cannot overwrite a source revision. Corrections name the exact previous reference and must match the persisted source head. Stable, sorted transaction advisory locks serialize delivery/source races; source revision and head commit together. Canonical records are bounded to256KiB.

retain_trace verifies source/output bytes and provenance before storing an immutable trace, requires the exact registered source and finalized output reference, and rejects changed content under the same trace ID. Changed conversions require a new trace ID. history/trace_history require source_history and return exact historical records, never evidence usability. No raw document text is copied into these records.

artifact_0004 adds private source_revisions/source_heads/conversion_traces with scoped catalog/source foreign keys. artifact_service has SELECT/INSERT and only head-column UPDATE, no historical UPDATE/DELETE. Infrastructure errors propagate; retrying identical records reconciles uncertain commits. Public routes, current rights/expiry fencing, Research identity matching and process-kill acceptance remain pending B1-B3/V1 work.

Owned PostgreSQL tests use actual upload/finalization, concurrent cross-source delivery contention, correction/replay, trace collision, catalog forgery/missing artifact, head-write rollback, scope and role denial. Pure-source spans retain their existing25 tests. The fixture never resets retained PostgreSQL state.


## Bounded Preparation Profiles

prepare_document accepts verified UTF-8 bytes and emits PreparedDocument JSON with original text intact, including embedded instructions as inert data. Its one conversion field points to the complete raw byte span; empty documents are unresolved. Raw and prepared outputs each have a4MiB limit, including JSON escaping expansion.

prepare_lab accepts at most64KiB of a flat JSON object with exactly the supported field universe: candidate_id/candidate_revision, sample_id/sample_revision, method, context, value and unit. Values are strings (at most2048 characters) or null; revisions and decimal measurements remain lexical strings, never binary floats. Absent fields emit null with missing provenance; explicit null retains its exact source token span. Numeric JSON values, nested structures, unknown or duplicate/escaped-duplicate keys, trailing content, invalid UTF-8 and unpaired surrogates are rejected. This is an explicitly synthetic input profile, not a general instrument/LIMS parser.

The focused flat_json scanner delegates string decoding to the standard JSON decoder and retains byte offsets for each original token. Repeated values and Unicode before a token cannot confuse span attribution. The parser never executes document contents. It preserves censored/malformed measurement text, marks warnings and does no unit conversion or inference. Every lab result remains quarantined with identity_reconciliation_required, even when syntactically complete; public Research matching and scientific interpretation are still separate gates.

PreparedAcquisition owns trace construction after independent output artifact finalization. It requires the exact published preparation schema/media type and matching output bytes. Public prepared_schema pins the exporter's validation bytes; publication must use those trusted deployment profiles. Converter IDs utf8-document and synthetic-lab-json are fixed version1 with empty configuration. A behavior change requires a new converter/profile version; no caller-defined code or transform is loaded.

Tests cover instruction preservation, empty/invalid documents, output expansion, wrong-schema binding, missing versus null units, censoring, unsafe identity/revisions, duplicate keys and escaped Unicode/repeated-value spans. The independent wheel probe runs the pure provenance/preparation suites without Research or Runtime installed. This is not live scientific ingestion acceptance.


## Public Research Client

ResearchClient consumes only amphora-contracts-research DTOs over a configured loopback HTTP endpoint; no Research implementation import or SQL connection. The endpoint must explicitly name127.0.0.1 and a port, without credentials/path/query/fragment. The opaque token is supplied by trusted configuration. Requests and responses carry exact scoped candidate/sample revisions. Responses are limited to16KiB, strict JSON, matching scope/identities, and consistent disposition/reason; redirects are not followed. Default timeout is5 seconds, bounded to30. Denial, unavailable transport and malformed response remain distinct safe errors, never synthesized unknown-sample answers. No automatic retry or authority widening occurs.

lab_identity_query derives explicit candidate/sample references from prepared lexical strings only when IDs and safe positive integer revisions validate. Missing/malformed references return no query; document profiles are rejected. A successful match grants identity_only and does not change the prepared lab's quarantine/scientific status.

Scripted TCP tests cover valid/unknown identity, denial, redirects, loss, bounds, wrong media, malformed/duplicate JSON and response substitution. Separately installed Data and Research wheels communicate through the actual Research HTTP process and PostgreSQL owner. Neither environment has the peer implementation installed. Known, unknown and stopped-peer cases pass; the lab preparation stays quarantined. That probe uses synthetic in-memory raw references: complete finalized-source/output ingestion orchestration remains the next B1 task.
