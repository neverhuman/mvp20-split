# Candidate canonicalization receipt

- Owner: BP-08.03/B2.03b.i; version0.1.0, verified 2026-10-06 14:24:11.
- Design: [Representation and fitness](../../docs/Architecture/Campaigns/Representation_Fitness.md#producer-backed-synthetic-reuse).

CanonicalCandidate binds scope, representation kind, semantic/equivalence profiles, exact source-byte SHA-256 and canonical SHA-256. Authority is restricted to synthetic_encoding. There is no source Artifact identity, tool identity, scientific verdict or cache permission asserted by this receipt alone. A consumer must authenticate its accepted Runtime producer/input/output and read exact current Data bytes before trusting its claimed origin.

Each representation tool owns legal parsing and canonicalization. The contract has no implementation, shared domain algorithm, storage or I/O; it depends only on public Core and Pydantic. Direct-design inputs remain the existing candidate-space schemas. Proposed-change wrappers require an explicit projection to a supported design input. Owned tests cover wire shape and schema parity; each tool owns semantic/adapter verification. Replacements preserve this schema and profile pins or explicitly version them.

Five wire/parity cases and complete137-check tool/publication/boundary run passed. Two new published schemas preserve602predecessors. Canonical receipt DTO validation is not producer authentication.
