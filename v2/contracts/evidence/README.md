# Acquisition Evidence Contracts

- Package: `amphora-contracts-evidence` 0.2.0; wire version1.
- Status: BP-06.01/B1 boundary subset; persistence, adapters and authority checks remain unimplemented.
- Design: [Source acquisition](../../docs/Architecture/Data/Acquisition.md).

Public imports come only from `amphora_contracts_evidence`. Frozen, strict, extra-forbidden DTOs describe immutable source revisions, exact byte spans, rights-revision references and conversion traces. Only Core and Pydantic are dependencies. This package has no I/O, credentials, storage, conversion algorithms or scientific acceptance authority.

SourceRevision binds scoped raw ArtifactRef, issuer/delivery identity, reviewed connector/configuration, rights revision and optional superseded source revision. Delivery uniqueness includes the reference's scope. Completeness never implies acceptance. Rights references identify historical provenance; callers must ask the owner for current access policy.

SourceSpan uses a zero-based, end-exclusive byte range over the exact raw artifact. It records a digest of that span, not a character offset. The acquisition owner must verify start/end ordering, artifact bounds, source identity and byte digest after an authorized content read. Empty spans are possible; shape validity does not prove the bytes exist.

ConversionTrace preserves source/target schemas, converter/configuration versions, ordered transform steps, output ArtifactRef, field origins and warning codes. Missing values are explicit; no raw source text or free-form output values are copied into the trace. `normalized` means a conversion disposition, never scientific usability. An inference step cannot gain scientific authority through confidence (there is no confidence/acceptance field). Artifact hashes bind source/output content; ConversionTraceRef binds the separately canonicalized trace record without a self-referential digest.

The owner must enforce matching scopes, target schema/output agreement, source schema/raw agreement, immutable trace identity/content, unique field paths, valid step references, origin/step compatibility and span provenance. These cross-record rules belong to domain objects, not parallel Pydantic/JSON Schema validators. Reference syntax alone cannot establish authorization or entity existence. B1 is still open until owner implementation and persistence exist.

Tests in `tests/` compare Pydantic JSON parsing with independent Draft2020-12 validation, exercise strict bounded shapes and preserve explicit missing/inferred provenance. Both schema modes are published by `dev/export_schemas.py`. Existing contract roots remain byte-identical. Replacement must preserve public roots, schema fixtures and explicit absence of authority.

Version0.2.0 adds PreparedDocument and PreparedLabRecord outputs plus prepared_schema(profile), which pins published validation schema bytes. The lab profile preserves strings/nulls and grants no identity or scientific acceptance. The original source/span/trace schema roots are unchanged.
