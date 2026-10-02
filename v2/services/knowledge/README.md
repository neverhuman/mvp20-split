# Knowledge Service

- Package: amphora-knowledge0.1.0; BP-06.02/B1 partial, pure authoring/replay boundary implemented.
- Design: [Knowledge](../../docs/Architecture/Knowledge/Knowledge_Architecture.md), [activation](../../docs/Audits/BP-06.02_Activation.md).

Knowledge owns domain entity/assertion identity, typed structural edits and deterministic accepted-history reconstruction. This first package implements pure [authoring](src/amphora_knowledge/authoring/README.md) and [replay](src/amphora_knowledge/replay/README.md). No PostgreSQL ledger, authenticated HTTP service, public peer validator or publication worker is implemented yet. Domain evaluation and a valid accepted-change DTO are not durable acceptance.

Dependencies are public Core0.1.0, Knowledge0.1.0, evidence0.5.0 and Research0.2.0 contracts plus the standard library. There are no private Data/Research imports, cross-owner SQL, shared ORM, source payload storage, LLM calls or campaign execution. Actor authorization, actual rights-scoped Data reads and Research reference checks remain the forthcoming owning adapter's duties.

Structural acceptance preserves reported/hypothesized/unresolved assertions; it grants no scientific truth, constraint eligibility or permission to consume source payloads. Questions and evidence needs remain Research declarations. Typed operations retain corrections, aliases, contradictory contexts and retractions; replay never reinterprets descriptive prose. Graph publication must not change a campaign's pinned knowledge revision.

Tests are module-owned under tests/authoring and tests/replay; use dev/run_tests.py --module knowledge, optionally --area authoring or --area replay. B1 persistence/API, B2 rebuild publication, B3 actual concurrency/crash cases and V1 independent service/peer replacement remain required gates. Replacements must preserve canonical hashes, exact prior references, nonpromotion, safe failure codes and independently specified history semantics, not merely DTO validity.

Verification checkpoint:36 owner tests and36 independent installed-owner tests pass;26 authoring and10 replay cases. Combined measured coverage319/334 statements and124/140 branches; remaining defensive error branches are listed in the committed Domain_Replay evidence. No transaction or scientific-authority coverage is inferred from this pure suite.
