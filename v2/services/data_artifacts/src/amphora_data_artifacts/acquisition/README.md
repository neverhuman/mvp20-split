# Acquisition Provenance

- Status: BP-06.01/B1 partial; pure exact-byte verification implemented. No ingestion route, ledger or adapter yet.
- Owner: Data/Artifacts; design [Acquisition](../../../../../docs/Architecture/Data/Acquisition.md).

`SourceDocument` verifies a scoped SourceRevisionRef against at most4MiB of exact bytes. `extract(SourceSpan)` checks full source identity, half-open byte bounds and digest. It does not translate character offsets or decode/execute instructions. `TraceDocument.verify(trace, source, output)` validates matching scope/schema/source identities, output content, unique target paths, ordered-transform references and copied/converted/inferred/missing field policy. Missing or inferred values cannot receive `normalized` disposition. No disposition grants scientific acceptance.

Verified traces expose deterministic UTF-8 canonical bytes (sorted keys, compact JSON, no NaN; offsets/indices are bounded integers). Their public ConversionTraceRef is SHA-256 over those bytes. A future store must reject an existing scoped trace ID with different canonical bytes; this module alone does not provide deduplication, persistence or delivery idempotency. It changes no existing command encoding.

Dependencies are only public Core/evidence contracts and standard-library hashing/JSON. No network, credentials, database, filesystem or owner imports. Callers must obtain bytes through authorized publication/read boundaries and check current rights before using these pure objects. Successful byte verification is not proof of authorization, sample identity, declared conversion algorithm execution or scientific validity.

`tests/acquisition/` owns exact-byte, UTF-8 offset, cross-scope, changed-content and origin-policy cases. The scope is independently runnable via `run_tests.py --module data-artifacts --area acquisition`. Replacement must preserve error codes, canonical bytes and immutable references. Persistence, rights fencing, bounded adapters and actual owner integration remain B1-B3/V1 work; this README must expand when those behaviors arrive.

Verification checkpoint:25 owned tests,100% lines (64/64) and branches (10/10) for provenance.py. Isolated wheel installation repeats all25 without Runtime installed. This focused suite does not measure the rest of the service or prove ingestion persistence.
