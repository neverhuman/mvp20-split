# Knowledge Service

- Package: amphora-knowledge0.13.0; contracts0.6.0.
- Status: BP-06.02 closed; BP-06.03/B1 configured reasoning, durable results and optional HTTP implemented; production artifact/synthetic-logical-receipt publication and optional HTTP implemented; installed/process-death acceptance and Research integration pending.
- Design: [Knowledge](../../docs/Architecture/Knowledge/Knowledge_Architecture.md), [activation](../../docs/Audits/BP-06.02_Activation.md).

Knowledge owns typed domain graph edits, immutable accepted history and snapshot reconstruction. It preserves source/Research links and conflicting interpretations without promoting them into scientifically accepted facts. Publication never changes a campaign's pinned revision.

| Module | Replacement boundary |
|---|---|
| [Authoring](src/amphora_knowledge/authoring/README.md) | Vocabulary/policy, entity/assertion histories, aliases, corrections and bounded typed edits |
| [Replay](src/amphora_knowledge/replay/README.md) | Exact accepted-operation replay and immutable watermark catch-up cursor |
| [Persistence](src/amphora_knowledge/persistence/README.md) | Scoped intent/receipt reconciliation and atomic accepted log/snapshot/head transactions |
| [Validation](src/amphora_knowledge/validation/README.md) | Bounded public Data/Research reads, exact provenance and current payload access |
| [Rebuild](src/amphora_knowledge/rebuild/README.md) | Durable private candidates and bounded compare-and-set materialization publication |
| [Reasoning](src/amphora_knowledge/reasoning/README.md) | Bounded signed rules, exact context/snapshot binding, immutable profile/request/result history and fresh provenance review |
| [Publication](src/amphora_knowledge/publication/README.md) | Exact result/input values, immutable publication selection, fenced leases and durable attempt journal; uploads/receipts pending |
| [Transport](src/amphora_knowledge/transport/README.md) | Authenticated API, pinned-profile discovery and explicit local host configuration |

Dependencies are public tool-protocol SDK0.2.0, graph-runtime0.11.0, Commands0.2.0, Core0.1.0, Knowledge0.6.0, Artifacts0.2.0, evidence0.5.0 and Research0.2.0 contracts plus Pydantic/FastAPI/Uvicorn, SQLAlchemy/psycopg/Alembic and the standard library. No peer implementation imports, peer SQL, shared ORM, source payload storage, LLM calls or campaign execution exist. knowledge_0001/0002/0003/0004/0005/0006 are applied forward-only migrations; startup does not migrate. Stored graph profiles and accepted identities survive process replacement.

Scientific validity, question-criteria satisfaction, symbolic inference, model extraction and current-use permission are distinct from structural acceptance. Replay uses accepted operations and recorded metadata, never a fresh prompt or revoked source payload. Later source consumption rechecks Data rights. Scientific eligibility and text extraction remain in their named successor plans.

Tests are owned under tests/authoring, replay, persistence, validation, rebuild, reasoning, publication, api and acceptance. Select with dev/run_tests.py --module knowledge --area <area>; PostgreSQL requires explicit AMPHORA_TEST_POSTGRES=1. Scripted peer tests prove client rules; the actual three-owner process test proves public compatibility. Test-only crash barriers are excluded from wheels.

Current verification:189 owner baseline tests,58 final focused reasoning tests,62 contract tests and14 dev tests pass. [Reasoning boundary evidence](../../docs/Audits/Evidence/BP-06-Knowledge/Reasoning_Boundary.json) owns coverage/gaps, schema compatibility and actual peer identities. Applied migrations are immutable. Earlier installed replacement proof covers the closed0.6.0 authoring/replay boundary; BP-06.03 installed replacement remains pending. No scientific or target-host power-loss claim is made.

BP-06.03/B1 Knowledge0.9.0 retains every actually consumed reasoning artifact in its existing validation observation, including indirect trace outputs and Research contexts.128 distinct reasoning inputs is the publication bound; authoring keeps its existing256-artifact transport/direct-observation profile.99 validation/reasoning/actual-peer tests pass. Stored historical decisions and282 schema files remain unchanged. Durable publication always needs a fresh complete review; pre0.9 historical observations are not complete publication declarations.

B1 [publication values](src/amphora_knowledge/publication/README.md) now bind actor/result, canonical bytes, exact input declaration and configured payload schema.100 contract/value/dev tests pass; four additive schemas preserve282 predecessors. Durable store, leases, upload orchestration, receipt policy and HTTP are the next work; no migration or endpoint added in this checkpoint.

Knowledge0.10.0 adds publication intent/lease persistence under knowledge_0004;110 scoped tests pass. Durable payload/attempt state and actual upload/receipt workflow remain B1. See the publication README and Publication_Store.json for the implemented boundary and unproven acceptance.

The publication module also owns the pure upload-attempt transition policy and exact command construction (157 publication/SDK/dev tests). Its durable journal, logical receipt policy and production Data orchestration remain unimplemented.

Knowledge0.11.0 retains exact reviewed payloads and bounded append-only upload attempts in knowledge_0005.145 scoped tests pass; journal ends at finalizing. Atomic terminal receipt and production upload recovery remain B1.

Knowledge0.12.0 adds atomic immutable derived-artifact/logical-receipt outcomes under knowledge_0006 (166 scoped tests). Purpose is synthetic entailment; scientific sufficiency remains Research-owned. Production SDK/HTTP workflow and its process-recovery proof remain next.

Knowledge0.13.0 composes the durable publication journal and public Data SDK behind optional publication routes.305 owner/dev tests pass, including actual three-owner result publication/current rights/restart evidence. Runtime delivery and Research sufficiency remain separate, unimplemented B1 gates; no scientific acceptance is inferred.
