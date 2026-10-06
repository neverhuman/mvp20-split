# Numeric search graph-step contracts

- Owner: BP-08.02/B1.01, wire/publication checks verified; owner adapter integration next.
- Design: [Search](../../docs/Architecture/Campaigns/Search.md); [activation](../../docs/Audits/BP-08.02_Activation.md).

This package owns graph-step transport DTOs only. SearchStepContext carries the separately pinned original specification, an inline checkpoint and its original Artifact reference. The numerical owner validates their semantic and canonical-byte relationship; Runtime/Data own actual admission, retention, access and accepted history.

EvaluationRequestBatch exposes bounded requests for explicit Artifact projection and scatter. CollectedEvaluations carries the same checkpoint context plus all ordered terminal result slots. Missing slots reuse the public graph-runtime MissingValue contract; a missing result never becomes a zero fitness. Scope, identity, exact frozen membership, source bytes and stop/transition policy are owner behavior, not DTO validation.

The dependency on graph-runtime is kept here, outside the domain-neutral contracts/search package. Production imports only declared public contract roots. This package performs no I/O, model calls, numerical algorithms, dispatch or scientific promotion. Existing search DTO/schema bytes remain unchanged. Module-owned tests cover transport shapes and actual published-schema compatibility; integration belongs to tools/evolution_search and Runtime.

Verified 2026-10-06 10:38:13:40 owned/publication/boundary checks19.23s; six additive schemas,570 total,564 predecessor schema bytes unchanged. Structural fixtures intentionally do not claim valid Artifact/checkpoint authority.
