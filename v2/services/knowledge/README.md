# Knowledge Service

BP-07.02/B2.03a.i has verified current processing authorization for new Knowledge consumption. Closed BP-06 deliveries remain closed; their historical evidence is retained below.

- Package: amphora-knowledge0.18.0; public contracts0.8.0. No new migration or public schema change.
- Status: new validation/reasoning/publication reviews use Data0.29 processing-content; installed and actual-peer verification passed. Committed decisions and accepted-log rebuild remain historical operations.
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
| [Corrections](src/amphora_knowledge/corrections/README.md) | Immutable chain revisions and separately granted future-campaign selection |
| [Exploration](src/amphora_knowledge/exploration/README.md) | Bounded exact-snapshot search, neighborhood, selected detail and schema-pinned catalog; authenticated owner/API reads through the exact-revision ledger |
| [Transport](src/amphora_knowledge/transport/README.md) | Authenticated API, pinned-profile discovery and explicit local host configuration |

Dependencies are public tool-protocol SDK and Commands/Core/Knowledge/Artifacts/Evidence/Research/Graph Runtime contracts plus Pydantic/FastAPI/Uvicorn, SQLAlchemy/psycopg/Alembic and the standard library. Exact pins are canonical in pyproject.toml and uv.lock. No peer implementation imports, peer SQL, shared ORM, source payload storage, LLM calls or campaign execution exist. knowledge_0001/0002/0003/0004/0005/0006/0007 are applied forward-only migrations; startup does not migrate. Stored graph profiles and accepted identities survive process replacement.

Scientific validity, question-criteria satisfaction, symbolic inference, model extraction and current-use permission are distinct from structural acceptance. Replay uses accepted operations and recorded metadata, never a fresh prompt or revoked source payload. Later source consumption rechecks Data rights. Scientific eligibility and text extraction remain in their named successor plans.

Tests are owned under tests/exploration, authoring, replay, persistence, validation, rebuild, reasoning, publication, corrections, api and acceptance. Select with dev/run_tests.py --module knowledge --area <area>; PostgreSQL requires explicit AMPHORA_TEST_POSTGRES=1. Scripted peer tests prove client rules; the actual three-owner process test proves public compatibility. Test-only crash barriers are excluded from wheels.

Reasoning inputs include every actually consumed artifact, including indirect conversion outputs and Research contexts, capped128 for publication. Authoring preserves its256-artifact profile. New publication always performs a fresh review of the exact historical graph snapshot, including for pre0.9 results whose old observations did not retain expanded inputs. Current Data rights gate new consumption; immutable historical metadata is not an access grant.

Publication persists the original actor/result/publisher/schema selection, reviewed payload, bounded attempt history and terminal artifact/logical receipt. Unknown PUTs are explicitly abandoned and replaced at most8 times; finalization always reconciles its original identity. Receipt purpose is synthetic entailment, never a caller-supplied scientific purpose. Runtime owns execution acceptance/retention; Research owns scientific sufficiency. Autonomous callers resume pending requests; no background publication scanner is implemented.

Verification at 2026-10-02 14:12:44:305 full source owner/dev tests (291 Knowledge +14 dev) and981 installed tests across8 isolated environments pass, zero failures/errors/skips. Installed suites include Data278+47, SDK94, initial Knowledge/contracts366 and replacement Knowledge196. Actual owner processes prove exact payload/input lineage, restart replay, Research outage/resume, and inherited source revocation. Nine additional installed publication kill barriers now pass; four rebuild kill regressions remain passing. Fault hosts use test-only five-second leases and replacements use production sixty seconds. No scientific or target-host power-loss claim is made.

[Workflow evidence](../../docs/Audits/Evidence/BP-06-Knowledge/Publication_Workflow.json) owns scoped coverage and actual owner identities; [installed evidence](../../docs/Audits/Evidence/BP-06-Knowledge/Publication_Installed.json) owns wheel hashes/isolation/replacement results. Earlier checkpoint history stays in the owning plan, evidence files and Git rather than this module contract.

[Publication process recovery](../../docs/Audits/Evidence/BP-06-Knowledge/Publication_Recovery.json) records all9 barriers, retained command identities and explicit uncertain-stream replacement. This extends the installed baseline without changing production0.13.0 code.

BP-06.03/B1.06 compatibility patch: dependency pins now consume additive Research contracts0.3.0 (Evidence0.5.1/Knowledge contracts0.6.1 where applicable). Existing public schema bytes and owner behavior are unchanged; earlier installed/recovery evidence remains tied to its recorded versions.

BP-06.03/B1.07 compatibility patch: exact pins now consume Research contracts0.4.0 and corresponding Evidence0.5.2/Knowledge contracts0.6.2. The only added wire root is Research synthetic evidence; peer behavior and all294 predecessor schema bytes remain unchanged.

B1.10 compatibility patch updates exact Research0.5.0 contract dependency closure; no owner behavior, migration or existing schema changes.

BP-06.04/B1.04 compatibility release0.15.1 updates exact public Research/Evidence/Knowledge dependency pins only. This release changes no service behavior or migration; earlier actual-peer acceptance remains recorded at its tested version.

BP-06.04/B1.06 compatibility release0.15.2 updates exact public contract dependencies only; no service implementation or migration change. Actual peer evidence remains tied to the recorded tested version.

BP-06.06 Knowledge0.17 adds read-only bounded graph-explore routes. Public Knowledge0.8 contracts and452 schemas remain unchanged; no migration or new grant. See exploration module for exact history, pagination and failure semantics.

Verified 2026-10-04 09:44:02:42 focused validation cases,325 installed owner/contract cases and actual Data0.29/Research0.33 acceptance across two Knowledge0.18 installations. Read-only source rights deny new graph/reasoning work while ordinary read, historical decisions and accepted-log rebuild retain their distinct behavior. Regrant leaves old rejections unchanged; nine existing publication interruption stages remain passing. [Evidence](../../docs/Audits/Evidence/BP-07-Extraction/Knowledge_Processing.json).

Cutover: replace all authoring, reasoning and publication-review workers with Knowledge0.18 before relying on the processing fence; older consumers still use ordinary reads. This is an application replacement requirement, not a rewrite of historical decisions or migrations.
