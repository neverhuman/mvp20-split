# Studio contract boundary

Owner: [Studio](../../README.md). BP-05.02/B1 consumer of graph-runtime0.7.0; no schema authorship or execution authority.

`scripts/generate-contracts.mjs` reads ten canonical Python-owned serialization schemas: graph snapshot, node detail, value page, invalidation page, scope page, topology page, named-view catalog, successor lineage, Runtime completion record and ArtifactRef. It writes TypeScript declarations, the unchanged schema data and SHA-256 provenance under `generated/`. Generation is deterministic and `--check` compares exact output. Types express transport shape; domain policy belongs to page-model objects. Navigation/catalog roots are additive; predecessor schema bytes are unchanged. Lineage consumes the already published immutable successor contract.

`decodeObservation` validates unknown JSON using AJV's Draft2020-12 implementation and standard formats. Coercion, default insertion and unknown-property removal are disabled. Pydantic's OpenAPI `discriminator` metadata is registered as a non-validating annotation; the original JSON Schema `oneOf`/`const` branches still enforce the union. This avoids rewriting authoritative schemas for a validator-specific optimization.

No service implementation, Node builtins, database or scientific dependencies enter browser source. The source AST ownership test checks declared public imports and focused network ownership; it is a static engineering check, not an execution sandbox. Generated declarations are scoped per root so shared names do not create manually maintained copies.

Owned tests: `tests/contracts/`, including all ten roots, rejection examples, canonical byte digests and import ownership. Replacement regenerates from the same source hashes and passes these tests; intentional owner schema changes require an explicit version/compatibility review. No migration or local persistent state.

CompletionRecord and ArtifactRef consume existing Runtime/Core publications. This consumer extension changes no authoritative schema bytes or schema versions.

BP-05.03/B1 adds fourteen separate authoring roots under `generated/authoring`: save, validate, draft/page/result/receipt, draft admission, reviewed universe/schema bytes, Registry release page/snapshot, emergency cancel, execution receipt and command identity. `authoring.ts` validates these without widening the ten read-only observation roots. `reviewed_schema.ts` verifies scoped universe membership, full schema reference, canonical base64, the 64KiB decoded bound, SHA-256, fatal UTF-8 and object JSON before returning a schema document. It performs no reference fetching, form generation or scientific/current-eligibility decision. Unsupported form constructs remain the editor's responsibility.

Authoring contract tests pin all fourteen public schema hashes and reject mismatched identity/digest, malformed/oversize bytes and invalid documents. Independent Studio staging copies both manifests' published schemas. Owner publications remain unchanged; no server canonical-command fingerprint is computed in the browser.

BP-06.06 adds14 separate Knowledge/Research scientific roots under generated/knowledge and generated/research. Scientific validators preserve the existing Runtime groups and reproduce public owner hashes. See scientific/README.md for the bounded inspection contract.
