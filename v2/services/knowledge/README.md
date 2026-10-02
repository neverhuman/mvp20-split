# Knowledge Service

- Package: amphora-knowledge0.13.0; contracts0.6.0.
- Status: BP-06.02 closed; BP-06.03/B1 production reasoning/publication and installed replacement verified. Publication-specific process-death recovery verified; Research assessment remains.
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
| [Publication](src/amphora_knowledge/publication/README.md) | Exact reviewed result/inputs, fenced durable attempt journal, public Data publication/recovery and atomic synthetic logical receipts |
| [Transport](src/amphora_knowledge/transport/README.md) | Authenticated API, pinned-profile discovery and explicit local host configuration |

Dependencies are public tool-protocol SDK0.2.0, graph-runtime0.11.0, Commands0.2.0, Core0.1.0, Knowledge0.6.0, Artifacts0.2.0, evidence0.5.0 and Research0.2.0 contracts plus Pydantic/FastAPI/Uvicorn, SQLAlchemy/psycopg/Alembic and the standard library. No peer implementation imports, peer SQL, shared ORM, source payload storage, LLM calls or campaign execution exist. knowledge_0001/0002/0003/0004/0005/0006 are applied forward-only migrations; startup does not migrate. Stored graph profiles and accepted identities survive process replacement.

Scientific validity, question-criteria satisfaction, symbolic inference, model extraction and current-use permission are distinct from structural acceptance. Replay uses accepted operations and recorded metadata, never a fresh prompt or revoked source payload. Later source consumption rechecks Data rights. Scientific eligibility and text extraction remain in their named successor plans.

Tests are owned under tests/authoring, replay, persistence, validation, rebuild, reasoning, publication, api and acceptance. Select with dev/run_tests.py --module knowledge --area <area>; PostgreSQL requires explicit AMPHORA_TEST_POSTGRES=1. Scripted peer tests prove client rules; the actual three-owner process test proves public compatibility. Test-only crash barriers are excluded from wheels.

Reasoning inputs include every actually consumed artifact, including indirect conversion outputs and Research contexts, capped128 for publication. Authoring preserves its256-artifact profile. New publication always performs a fresh review of the exact historical graph snapshot, including for pre0.9 results whose old observations did not retain expanded inputs. Current Data rights gate new consumption; immutable historical metadata is not an access grant.

Publication persists the original actor/result/publisher/schema selection, reviewed payload, bounded attempt history and terminal artifact/logical receipt. Unknown PUTs are explicitly abandoned and replaced at most8 times; finalization always reconciles its original identity. Receipt purpose is synthetic entailment, never a caller-supplied scientific purpose. Runtime owns execution acceptance/retention; Research owns scientific sufficiency. Autonomous callers resume pending requests; no background publication scanner is implemented.

Verification at 2026-10-02 14:12:44:305 full source owner/dev tests (291 Knowledge +14 dev) and981 installed tests across8 isolated environments pass, zero failures/errors/skips. Installed suites include Data278+47, SDK94, initial Knowledge/contracts366 and replacement Knowledge196. Actual owner processes prove exact payload/input lineage, restart replay, Research outage/resume, and inherited source revocation. Nine additional installed publication kill barriers now pass; four rebuild kill regressions remain passing. Fault hosts use test-only five-second leases and replacements use production sixty seconds. No scientific or target-host power-loss claim is made.

[Workflow evidence](../../docs/Audits/Evidence/BP-06-Knowledge/Publication_Workflow.json) owns scoped coverage and actual owner identities; [installed evidence](../../docs/Audits/Evidence/BP-06-Knowledge/Publication_Installed.json) owns wheel hashes/isolation/replacement results. Earlier checkpoint history stays in the owning plan, evidence files and Git rather than this module contract.

[Publication process recovery](../../docs/Audits/Evidence/BP-06-Knowledge/Publication_Recovery.json) records all9 barriers, retained command identities and explicit uncertain-stream replacement. This extends the installed baseline without changing production0.13.0 code.
