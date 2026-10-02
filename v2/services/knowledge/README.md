# Knowledge Service

- Package: amphora-knowledge0.7.0; contracts0.4.0.
- Status: BP-06.02 closed; BP-06.03/B1 private reasoning kernel and state binding implemented; public reasoning/receipts pending.
- Design: [Knowledge](../../docs/Architecture/Knowledge/Knowledge_Architecture.md), [activation](../../docs/Audits/BP-06.02_Activation.md).

Knowledge owns typed domain graph edits, immutable accepted history and snapshot reconstruction. It preserves source/Research links and conflicting interpretations without promoting them into scientifically accepted facts. Publication never changes a campaign's pinned revision.

| Module | Replacement boundary |
|---|---|
| [Authoring](src/amphora_knowledge/authoring/README.md) | Vocabulary/policy, entity/assertion histories, aliases, corrections and bounded typed edits |
| [Replay](src/amphora_knowledge/replay/README.md) | Exact accepted-operation replay and immutable watermark catch-up cursor |
| [Persistence](src/amphora_knowledge/persistence/README.md) | Scoped intent/receipt reconciliation and atomic accepted log/snapshot/head transactions |
| [Validation](src/amphora_knowledge/validation/README.md) | Bounded public Data/Research reads, exact provenance and current payload access |
| [Rebuild](src/amphora_knowledge/rebuild/README.md) | Durable private candidates and bounded compare-and-set materialization publication |
| [Transport](src/amphora_knowledge/transport/README.md) | Authenticated API, pinned-profile discovery and explicit local host configuration |

Dependencies are public Core0.1.0, Knowledge0.4.0, evidence0.5.0 and Research0.2.0 contracts plus FastAPI/Uvicorn, SQLAlchemy/psycopg/Alembic and the standard library. No peer implementation imports, peer SQL, shared ORM, source payload storage, LLM calls or campaign execution exist. knowledge_0001/0002 are applied forward-only migrations; startup does not migrate. Stored graph profiles and accepted identities survive process replacement.

Scientific validity, question-criteria satisfaction, symbolic inference, model extraction and current-use permission are distinct from structural acceptance. Replay uses accepted operations and recorded metadata, never a fresh prompt or revoked source payload. Later source consumption rechecks Data rights. Scientific eligibility and text extraction remain in their named successor plans.

Tests are owned under tests/authoring, replay, persistence, validation, rebuild, api and acceptance. Select with dev/run_tests.py --module knowledge --area <area>; PostgreSQL requires explicit AMPHORA_TEST_POSTGRES=1. Scripted peer tests prove client rules; the actual three-owner process test proves public compatibility. Test-only crash barriers are excluded from wheels.

B3 verification:130 owner tests pass (44 PostgreSQL cases), including three rebuild process-death barriers and a correction/publication race.39 contract tests cover264 published schemas. [Failure matrix](../../docs/Audits/Evidence/BP-06-Knowledge/Failure_Matrix.json) records exact identities, coverage gaps and QEV-02/03/04/TRACE-04 mapping. Earlier checkpoints remain in owning evidence/history rather than this replacement contract. independent installed replacement accepted (169 initial / 39 replacement tests); no scientific or target-host power-loss claim is made.

The [reasoning module](src/amphora_knowledge/reasoning/README.md) adds a finite private signed-rule evaluator and exact owner-state/context binding.161 owner tests pass (31 reasoning,44 PostgreSQL); no public reasoning endpoint, scientific adjudicator or receipt publisher is implemented. [Current evidence](../../docs/Audits/Evidence/BP-06-Knowledge/Reasoning_Kernel.json) owns coverage and gaps. Earlier installed replacement proof applies to the closed0.6.0 authoring/replay boundary.
