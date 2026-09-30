# BP-06 Planning History

## Initial acquisition boundary - 2026-09-30 17:44:31

B1 partial: evidence0.1.0 contracts and Data/Artifacts0.2.0 pure provenance checks verified.15 contract and25 acquisition tests pass in isolated wheel installs;28 combined dev/contract tests and131 artifact-owner regression tests (PostgreSQL enabled) pass. Provenance64/64 lines and10/10 branches covered.208 published schemas preserve all200 predecessors. No ledger/adapters/Research identity yet; no delivery credit. [Activation audit](../Audits/BP-06.01_Activation.md); [wheel evidence](../Audits/Evidence/BP-06-Acquisition/Initial_Boundary.json). Source schemas are additive; old command profiles and artifact routes are unchanged. Package inventory refreshed from manifests, not a full foundation reacceptance. Next: Research identity/question/evidence-need boundary; then ingestion adapters and actual PostgreSQL ledger.


Archived first draft at `2026-09-25 13:35:12`. Historical task pairs/percentages are not the active execution tracker. The parent and linked children now own progress. Original scope is preserved below for traceability.

# BP-06 Knowledge Evidence and Source Loop

## Canonical Execution Tracker

- Status: **proposed / first draft for user review**; implementation not activated.
- Last refreshed: `2026-09-24 12:10:07` (America/Chicago).
- Owner/scope: Knowledge, Research and focused Data/Artifacts modules.
- Parent: [Master Build Tracker](Master%20Build%20Tracker.md); baseline: local architecture and BP-01/BP-01A completed foundation, BP-02 active protocol work.
- Overall implementation: **0%**; 12 equally weighted verified tasks, two per phase. Overall = completed tasks / 12; phase = completed tasks / 2. Drafting earns no implementation credit.
- Current phase/task: none; proposed plan.
- Next task: incorporate review, then verify predecessor gates and run the bounded pre-activation coherence audit before P1/T1.
- Prerequisites: Completed BP-04 receipt/wait seams and BP-05 inspection; BP-01/02/03 public contracts and tool execution.
- Completed implementation/evidence: none. All phase gates remain pending.
- Blockers: predecessor gates are not complete; decisions below block only their dependent tasks.
- Human acceptance: draft is available for review; no approval inferred for dependent deployment/provider actions. Campaigns remain autonomous with human changes between campaigns.
- Active exception: none.
- Draft coherence check: `2026-09-24 12:01:26`; ownership, ordering, scoped tests and handoffs checked against [owning architecture](../Architecture/Knowledge/Knowledge_Architecture.md). This is not the implementation activation audit.

| Phase / status | Completion | Dependency | Required exit |
|---|---:|---|---|
| P1 Source and evidence contracts / proposed | 0% | Completed predecessor gates and activation audit | T1-T2: Duplicate delivery does not duplicate evidence; cross-scope/rights failures reject; source ingestion is not scientific acceptance. |
| P2 Typed graph authoring and replay / proposed | 0% | P1 exit | T3-T4: Concurrent edits/rebuilds, duplicate IDs, semantic conflicts and crash recovery pass; replay uses accepted operations rather than rerunning a prompt. |
| P3 Reasoning and domain receipts / proposed | 0% | P2 exit | T5-T6: No cross-owner transaction/table access; invalid or superseded receipts cannot satisfy dependencies; rule replay retains pinned inputs and policy revisions. |
| P4 Laboratory returns and candidate eligibility / proposed | 0% | P3 exit | T7-T8: Unmatched samples, partial batches and incompatible units/methods do not enter fitness; corrected results mark affected decisions and create successor feedback without rewriting history. |
| P5 Representation reuse and retrieval / proposed | 0% | P4 exit | T9-T10: Equal dimensions do not imply compatibility; text/molecule/sequence spaces remain separate; concurrent generation, revocation and stale index exposure tests pass. No retrieval-quality claim from synthetic vectors. |
| P6 Feedback integration and closeout / proposed | 0% | P5 exit | T11-T12: Source/receipt lineage is inspectable; pending acceptance is never shown as accepted; single-campaign autonomy and next-campaign human edits preserved; owned tests and public integration gates pass. |

## Outcome and Boundaries

Turn source documents and experimental returns into versioned, replayable knowledge and purpose-specific evidence that a later campaign can use.

Included: One document/source connector and synthetic lab-return adapter; typed graph changes and rebuilds; bounded symbolic rules; evidence/sample identity; reusable representation profiles; versioned feedback receipts.

Excluded: Live LIMS/CRO integration, universal ontology, validated biological inference, unrestricted autonomous extraction, model training/promotion and a complete commercial data marketplace.

Primary services retain private state, dependencies, migrations and module READMEs. Public contracts/clients are the only cross-owner dependencies. Any new schema identifies its consumer/migration impact. No broad backend or shared business/ORM package. Later phases refine earlier boundaries under the current task without reopening closed plans.

## Child Work-Package Register

This parent owns outcomes and sequencing. The named packages below are **scoped, not implementation-ready**. The existing task pairs are requirements for child decomposition, not sufficiently detailed coding instructions. Before activating a package, author its canonical child plan with owned objects/API/storage, transition/algorithm decisions, failure/recovery matrix, named fixtures and replacement gates. Parent progress then rolls up verified child deliverables; do not count these task pairs again. No implementation credit is earned here.

| Child / bounded ownership | Implementation | Prerequisite | Scope to decompose |
|---|---:|---|---|
| BP-06.01 / Source and evidence contracts | 0% | Parent predecessor gates | Define source revision/rights/spans, candidate/sample/method/units/context identity, evidence status and purpose-bound acceptance receipts with separate owners. Implement bounded document and synthetic lab-file ingestion preserving raw bytes and immutable corrected deliveries; unknown identity is quarantined. |
| BP-06.02 / Typed graph authoring and replay | 0% | BP-06.01 exit | Implement stable entity/assertion identities and accepted typed change operations with narrative rationale, source spans and base-head preconditions; accept reviewed fixture proposals initially. Build isolated graph snapshots through a watermark, catch up bounded changes and publish with compare-and-set; preserve overrides, merges, retractions and contradictions. |
| BP-06.03 / Reasoning and domain receipts | 0% | BP-06.02 exit | Implement a small versioned rule set with explicit applicability/authority and derivation provenance; unknown or contradictory evidence never becomes certainty. Publish Knowledge and Research acceptance receipts independently of runtime completion; connect declared receipt waits and inspectable graph views through public APIs. |
| BP-06.04 / Laboratory returns and candidate eligibility | 0% | BP-06.03 exit | Implement sample/result reconciliation, replicate/control/method metadata and numeric/categorical/censored/series observations; preserve raw and superseding reports. Produce purpose-specific eligibility and feedback proposals; represent synthesis route/accessibility evidence, missing method and uncertainty explicitly without inventing a universal score. |
| BP-06.05 / Representation reuse and retrieval | 0% | BP-06.04 exit | Implement immutable encoding profiles and result-affecting cache keys including content, preprocessing, chunking, model/revision, task and normalization; preserve separate rights/provenance bindings. Use a deterministic fixture encoder and bounded retrieval adapter to test deduplication, profile compatibility and build/verify/publish index generations; document the later real-backend selection gate. |
| BP-06.06 / Feedback integration and closeout | 0% | BP-06.05 exit | Run a source-to-graph-to-campaign receipt flow and corrected-lab-result scenario; campaigns pin immutable knowledge/evaluator revisions, with explicit adoption at permitted boundaries. Extend Studio minimally for real evidence/knowledge traversal, document module boundaries and remaining extraction/model/backend needs, then audit and archive. |

Readiness gaps are the unresolved decisions below plus concrete storage/API contracts, algorithm choices, test oracles and migration/recovery obligations for each package. Decompose the nearest eligible package first; do not invent distant provider, ontology or deployment decisions merely to fill templates. Child scope remains here until a linked execution plan replaces the register entry. The parent's existing percentages remain 0% because no implementation has occurred.

## Ordered Tasks

### P1 ? Source and evidence contracts

**T1.** Define source revision/rights/spans, candidate/sample/method/units/context identity, evidence status and purpose-bound acceptance receipts with separate owners.

**T2.** Implement bounded document and synthetic lab-file ingestion preserving raw bytes and immutable corrected deliveries; unknown identity is quarantined.

**Exit:** Duplicate delivery does not duplicate evidence; cross-scope/rights failures reject; source ingestion is not scientific acceptance.

### P2 ? Typed graph authoring and replay

**T3.** Implement stable entity/assertion identities and accepted typed change operations with narrative rationale, source spans and base-head preconditions; accept reviewed fixture proposals initially.

**T4.** Build isolated graph snapshots through a watermark, catch up bounded changes and publish with compare-and-set; preserve overrides, merges, retractions and contradictions.

**Exit:** Concurrent edits/rebuilds, duplicate IDs, semantic conflicts and crash recovery pass; replay uses accepted operations rather than rerunning a prompt.

### P3 ? Reasoning and domain receipts

**T5.** Implement a small versioned rule set with explicit applicability/authority and derivation provenance; unknown or contradictory evidence never becomes certainty.

**T6.** Publish Knowledge and Research acceptance receipts independently of runtime completion; connect declared receipt waits and inspectable graph views through public APIs.

**Exit:** No cross-owner transaction/table access; invalid or superseded receipts cannot satisfy dependencies; rule replay retains pinned inputs and policy revisions.

### P4 ? Laboratory returns and candidate eligibility

**T7.** Implement sample/result reconciliation, replicate/control/method metadata and numeric/categorical/censored/series observations; preserve raw and superseding reports.

**T8.** Produce purpose-specific eligibility and feedback proposals; represent synthesis route/accessibility evidence, missing method and uncertainty explicitly without inventing a universal score.

**Exit:** Unmatched samples, partial batches and incompatible units/methods do not enter fitness; corrected results mark affected decisions and create successor feedback without rewriting history.

### P5 ? Representation reuse and retrieval

**T9.** Implement immutable encoding profiles and result-affecting cache keys including content, preprocessing, chunking, model/revision, task and normalization; preserve separate rights/provenance bindings.

**T10.** Use a deterministic fixture encoder and bounded retrieval adapter to test deduplication, profile compatibility and build/verify/publish index generations; document the later real-backend selection gate.

**Exit:** Equal dimensions do not imply compatibility; text/molecule/sequence spaces remain separate; concurrent generation, revocation and stale index exposure tests pass. No retrieval-quality claim from synthetic vectors.

### P6 ? Feedback integration and closeout

**T11.** Run a source-to-graph-to-campaign receipt flow and corrected-lab-result scenario; campaigns pin immutable knowledge/evaluator revisions, with explicit adoption at permitted boundaries.

**T12.** Extend Studio minimally for real evidence/knowledge traversal, document module boundaries and remaining extraction/model/backend needs, then audit and archive.

**Exit:** Source/receipt lineage is inspectable; pending acceptance is never shown as accepted; single-campaign autonomy and next-campaign human edits preserved; owned tests and public integration gates pass.

## Test Ownership and Evidence

Proposed suite locations (create with their modules):

- `services/data_artifacts/tests/acquisition/`.
- `services/data_artifacts/tests/representations/`.
- `services/knowledge/tests/authoring/`.
- `services/knowledge/tests/replay/`.
- `services/knowledge/tests/reasoning/`.
- `services/research/tests/experiments/`.
- `tests/integration/knowledge_feedback/`.

Each owning README maps public behavior, invariants, failure scenarios and measured source paths to module-local test suites. Register source/suite ownership in `dev/test_scopes.json`; extend granular selectors as modules arrive. Run changed-module tests first, affected consumers next, and separate public-boundary integration/E2E only for cross-owner outcomes. Record line and branch coverage with gaps; coverage percentages are not evidence of scientific correctness.

Keep scenario evidence with absolute timestamps, implementation revision, fixture/schema identity, relevant run/artifact IDs and observed outcomes. Unit mocks do not replace required database, process, browser or provider evidence. Record independent build/install and replacement tests for new service/tool boundaries.

## UI Reference Refinement

`2026-09-24 12:10:07`: Use the [interaction reference map](../Architecture/Experience/Interaction_References.md) for P6 evidence/knowledge traversal: search-first bounded exploration and source details, without requiring manual predicate authoring. Implementation and all phase percentages remain 0%; this refines existing tasks.

## Decisions and Handoff

BP-07 owns reliable LLM text decomposition using these typed operations and reviewed corpus fixtures. BP-06 implements a deterministic profile/retrieval reference, not a selected production encoder/vector store. Qdrant integration requires a scoped backend decision; external JARVIS access is not authorized by this draft.

## Progress, Scope Changes and Closeout

The canonical tracker owns overall and P1-P6 percentages; mirror them in MBT at every completed task or changed scope and before commit/handoff. Do not activate downstream phases before their predecessor gate. Record review changes and denominator adjustments here; substantial newly discovered scope gets a named successor.

Final phase includes a component-scoped architecture drift audit. Fix blocking drift, explicitly assign nonblocking follow-ups, update module READMEs/inventories and archive only after all defined gates pass. Synchronize MBT, plan index and Restore and repair moved links. Preserve separate acceptance/operational/scientific readiness status; 100% measures this bounded implementation, not the whole product.

Closeout evidence: pending. No implementation, deployment or scientific validation is claimed by this draft.

## Reference refinement 2026-09-25 13:54:17

BP-06.01/.02/.03/.04/.06 now include Research-owned questions/evidence needs, conversion traces, accepted claim/answer links, purpose-bound evidence sufficiency, processing-sensitive tested-material identity and real-view integration. Research, Knowledge and Data retain separate write authority. Existing implementation deliveries extended with required acceptance cases; all 0%, denominator unchanged. [Reference assessment](References/Amphora_Lab_Insights.md) owns provenance and limitations.
