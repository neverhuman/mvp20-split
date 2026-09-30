# Studio contract boundary

Owner: [Studio](../../README.md). BP-05.01/B1 consumer of graph-runtime0.5.0; no schema authorship or execution authority.

`scripts/generate-contracts.mjs` reads four canonical Python-owned serialization schemas: graph snapshot, node detail, value page and invalidation page. It writes TypeScript declarations, the unchanged schema data and SHA-256 provenance under `generated/`. Generation is deterministic and `--check` compares exact output. Types express transport shape; domain policy belongs to page-model objects.

`decodeObservation` validates unknown JSON using AJV's Draft2020-12 implementation and standard formats. Coercion, default insertion and unknown-property removal are disabled. Pydantic's OpenAPI `discriminator` metadata is registered as a non-validating annotation; the original JSON Schema `oneOf`/`const` branches still enforce the union. This avoids rewriting authoritative schemas for a validator-specific optimization.

No service implementation, Node builtins, database or scientific dependencies enter browser source. The source AST ownership test checks declared public imports and focused network ownership; it is a static engineering check, not an execution sandbox. Generated declarations are scoped per root so shared names do not create manually maintained copies.

Owned tests: `tests/contracts/`, including all four roots, rejection examples, canonical byte digests and import ownership. Replacement regenerates from the same source hashes and passes these tests; intentional owner schema changes require an explicit version/compatibility review. No migration or local persistent state.
