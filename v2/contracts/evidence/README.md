# Acquisition Evidence Contracts

- Package: `amphora-contracts-evidence` 0.5.7; wire version1.
- Status: BP-06.01/B1 boundary subset; public transport shapes; Data/Artifacts owns implemented persistence and bounded preparation, with rights/scientific policy still open.
- Design: [Source acquisition](../../docs/Architecture/Data/Acquisition.md).

Public imports come only from `amphora_contracts_evidence`. Frozen, strict, extra-forbidden DTOs describe immutable source revisions, exact byte spans, rights-revision references and conversion traces. Dependencies are Core, Pydantic and the public Research identity contract; no Research implementation is imported. This package has no I/O, credentials, storage, conversion algorithms or scientific acceptance authority.

SourceRevision binds scoped raw ArtifactRef, issuer/delivery identity, reviewed connector/configuration, rights revision and optional superseded source revision. Delivery uniqueness includes the reference's scope. Completeness never implies acceptance. Rights references identify historical provenance; callers must ask the owner for current access policy.

SourceSpan uses a zero-based, end-exclusive byte range over the exact raw artifact. It records a digest of that span, not a character offset. The acquisition owner must verify start/end ordering, artifact bounds, source identity and byte digest after an authorized content read. Empty spans are possible; shape validity does not prove the bytes exist.

ConversionTrace preserves source/target schemas, converter/configuration versions, ordered transform steps, output ArtifactRef, field origins and warning codes. Missing values are explicit; no raw source text or free-form output values are copied into the trace. `normalized` means a conversion disposition, never scientific usability. An inference step cannot gain scientific authority through confidence (there is no confidence/acceptance field). Artifact hashes bind source/output content; ConversionTraceRef binds the separately canonicalized trace record without a self-referential digest.

The owner must enforce matching scopes, target schema/output agreement, source schema/raw agreement, immutable trace identity/content, unique field paths, valid step references, origin/step compatibility and span provenance. These cross-record rules belong to domain objects, not parallel Pydantic/JSON Schema validators. Reference syntax alone cannot establish authorization or entity existence. B1 now has verified owner ingress and durable lookup results; policy and replacement acceptance remain separate B2-B3/V1 gates.

Tests in `tests/` compare Pydantic JSON parsing with independent Draft2020-12 validation, exercise strict bounded shapes and preserve explicit missing/inferred provenance. Both schema modes are published by `dev/export_schemas.py`. Existing contract roots remain byte-identical. Replacement must preserve public roots, schema fixtures and explicit absence of authority.

Version0.2.0 adds PreparedDocument and PreparedLabRecord outputs plus prepared_schema(profile), which pins published validation schema bytes. The lab profile preserves strings/nulls and grants no identity or scientific acceptance. The original source/span/trace schema roots are unchanged.

Version0.3.0 adds PreparedSource and RetainPreparedSource. Preparation returns exact canonical output as content_json_utf8 plus digest/schema/disposition/warnings. Consumers UTF-8 encode that string verbatim for artifact upload; parsing and reserializing can change the digest. Preparation has no output artifact ID or publication receipt. Retention requires the complete original SourceRevision, chosen immutable trace ID and actual finalized output ArtifactRef; cross-record correctness belongs to the owner. Existing224 schema bytes are unchanged.

Version0.4.0 adds ObserveSourceIdentity, SourceIdentityObservation and SourceIdentityStatus. A scoped observation ID binds one exact immutable ConversionTraceRef. Status carries a nullable result: null means pending, not an unknown candidate/sample. Completed records preserve a local not_applicable/unresolved result or the exact public Research IdentityResolution. scientific_authority is always none. Research is a public DTO dependency so these records reuse its identity-only response rather than duplicate or reinterpret it; this extends the initial Core-only contract packaging without introducing peer implementation/state dependencies. All228 predecessor schema files remain byte-identical.

Version0.5.0 adds SourceRightsRevision: historical reference/predecessor, granted/revoked status, read/process uses, aware expiry and explicit retain_audit_payload retention. DTO shape does not grant access; Data owns sequence, combinations, current-head checks and read/commit fences. Unsupported retention profiles are rejected, not silently treated as permission to retain. All234 predecessor schema files are unchanged.

BP-06.03/B1.06 compatibility patch: dependency pins now consume additive Research contracts0.3.0 (Evidence0.5.1/Knowledge contracts0.6.1 where applicable). Existing public schema bytes and owner behavior are unchanged; earlier installed/recovery evidence remains tied to its recorded versions.

BP-06.03/B1.07 compatibility patch: exact pins now consume Research contracts0.4.0 and corresponding Evidence0.5.2/Knowledge contracts0.6.2. The only added wire root is Research synthetic evidence; peer behavior and all294 predecessor schema bytes remain unchanged.

B1.10 compatibility patch updates exact Research0.5.0 contract dependency closure; no owner behavior, migration or existing schema changes.

Compatibility0.5.6 pins Research contracts0.7.0; acquisition schemas and implementation are unchanged.

Compatibility0.5.7 pins Research contracts0.8.0; existing acquisition schemas are unchanged.
