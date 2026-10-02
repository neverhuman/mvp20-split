# BP-06 Planning History

## B1 complete - 2026-10-01 20:05:58

B1 complete: Knowledge0.4.0/contracts0.3.0 expose authenticated proposal/status/profile/head/snapshot/change reads and explicit owner hosting.104 owner tests pass (26 PostgreSQL cases), plus35 contracts/14 dev tests. Actual Data/Research/Knowledge HTTP proves exact provenance, restart replay, outage recovery and revoked-rights rejection.260 schemas preserve all258 predecessors. Child1/4 (25%), Build33.33%, Acceptance0%; parent5/24 (20.83%). [Evidence](../Audits/Evidence/BP-06-Knowledge/Public_API.json). Public profile discovery is observational for new graphs and pinned for stored graphs; it does not perform migration. Existing accepted receipts remain historical after rights revocation while new reviews fail. Independent wheel replacement and mid-build crashes remain V1/B3.

## Knowledge persistence checkpoint - 2026-10-01 19:34:51

B1 partial: Knowledge contracts/service0.2.0 add durable proposal status, immutable stored profiles and atomic accepted-log/snapshot/head/decision persistence.47 owner tests (11 actual PostgreSQL),47 contract/dev tests and80 isolated owner/contract tests pass with0 skipped in the final explicit PG run.258 schemas preserve all256 predecessors. Actual public peer validation and authenticated HTTP remain; child0/4, parent4/24 (16.67%) unchanged. [Evidence](../Audits/Evidence/BP-06-Knowledge/Persistence.json). knowledge_0001 persists graph definitions as well as refs and mutually binds accepted entries/snapshots. History admission caps avoid committing state outside the bounded replay reader. Race/rollback and role tests use the retained labeled fixture; observations remain synthetic until public validation. Initial isolated build omitted PG opt-in and skipped11; a separate explicit opt-in run passed all80 and is the authoritative proof.

## Knowledge pure authoring and replay - 2026-10-01 19:09:58

B1 partial: Knowledge0.1.0 implements pure structural edits, exact reference collection, immutable correction/alias/retraction history and bounded deterministic accepted-log replay.36 owner tests,36 isolated owner tests and14 dev tests pass. No persistence/authenticated peer or HTTP acceptance yet; child0/4 (0%), parent4/24 (16.67%) unchanged. [Evidence](../Audits/Evidence/BP-06-Knowledge/Domain_Replay.json). Independent installation excludes peer implementations and SQLAlchemy. Structural revision factories require exact observation shapes but do not prove real peer reads; those remain the next adapter gates. Scope errors now precede reference-equivocation checks. No B1 delivery credit until persistence/public boundary exists.

## Knowledge public contracts - 2026-10-01 18:51:58

B1 partial: Knowledge contracts0.1.0 publishes typed edits, scoped provenance/Research links, distinct proposals/structural decisions and immutable snapshot shapes.44 contract/dev tests and30 isolated contract tests pass;256 schemas preserve all236 predecessor bytes. No Knowledge domain/persistence/HTTP behavior exists yet; child0/4 (0%), parent4/24 (16.67%) unchanged. [Evidence](../Audits/Evidence/BP-06-Knowledge/Contracts.json). Vocabulary/policy refs are separate from JSON Schema refs. Typed receipts have structural_only authority; scientific promotion is unavailable in this profile. Cross-record semantics remain owner gates and synthetic shape fixtures are not durable receipts.

## Knowledge activation - 2026-10-01 18:40:42

[Coherence audit](../Audits/BP-06.02_Activation.md) activates BP-06.02/B1 at0/4; parent4/24 (16.67%) unchanged. Typed structural acceptance and atomic log/snapshot publication are distinct from scientific eligibility and LLM extraction. Predecessor public contracts are pinned; a stale dev Research pin is a bounded tooling correction. No owner decision pending.

## Source/evidence closeout - 2026-10-01 18:34:28

BP-06.01 accepted4/4 (100%):139 independently installed Data acquisition/rights tests,70 installed Research tests and36 replacement API tests pass. Two builds/four isolated environments preserve exact history through actual peer HTTP and separate replacement processes. Scoped drift audit aligned; parent4/24 (16.67%). BP-06.02 activation audit is next; scientific authority remains separate. [Audit](../Audits/BP-06.01_Source_Evidence_Closeout.md). Private fixture seeding remains distinct from public scientific approval. No schemas or durable formats changed in V1; no v1/JARVIS access.

## B3 named failure proof complete - 2026-10-01 18:23:10

B3 complete: Research0.4.0 adds scoped immutable question/need reads; QEV-01 passes through actual Research/Data HTTP and finalized bytes with separate credentials.123 acquisition,70 Research and52 contract/dev tests pass. Four process interruption cases and TRACE-01/02/03 are mapped in the evidence matrix. Child3/4 (75%), Build100%, parent3/24 (12.5%); V1 independent installed-owner replacement and audit remain. [Evidence](../Audits/Evidence/BP-06-Acquisition/Failure_Matrix.json). The QEV gap required an additive read-only Research API with a distinct grant; contracts0.2.0 and all236 schemas stay unchanged. Reference access does not grant Data access or accept science. V1 remains mandatory before successor activation.

## B3 process recovery checkpoint - 2026-10-01 18:16:05

B3 partial: Data0.10.0 adds scoped source-history reconciliation; four actual PostgreSQL/HTTP process-kill cases preserve original source/trace/observation identities.17 targeted and246 full artifact tests pass. QEV-01 public declaration reads and consolidated named trace matrix remain; child50%, Build66.67%, parent8.33% unchanged. [Evidence](../Audits/Evidence/BP-06-Acquisition/Process_Recovery.json). The source-history route reuses SourceRevision; no wire schemas or durable formats changed. Test-only barriers are excluded from production configuration. Replacement uses the development environment; independent wheel cutover remains V1.

## B2 rights and transition completion - 2026-10-01 18:00:06

B2 complete: evidence0.5.0/Data0.9.0 current rights/expiry and lineage fences verified.240 artifact tests,118 acquisition tests,16 rights tests,30 contract/schema tests,28 isolated contract tests and16 isolated rights tests pass.236 schemas preserve all234 predecessors. Child2/4 (50%); Build2/3 (66.67%); parent2/24 (8.33%). B3 named failure/recovery proof is next; scientific authority remains unchanged. [Evidence](../Audits/Evidence/BP-06-Acquisition/Source_Rights.json). Explicit grants replace historical-reference assumptions; migration0006 invents no rights for old sources. Exact predecessor/current-head checks, PostgreSQL-clock expiry and pre/post-I/O or transactional fences protect registered raw/derived data. Old source/trace/observation metadata remains immutable. Retention is explicitly limited to retained audit payloads; mandatory-erasure licenses remain unsupported. Existing deterministic/inferred/missing-field, corrected-delivery and trace-identity tests pass. B3 crash/race evidence and V1 independent integrated acceptance remain open; this does not close the child.

## B1 boundary completion - 2026-10-01 17:24:59

B1 complete: evidence0.4.0/Data0.8.0 durable identity observations verified with actual Research HTTP and retained PostgreSQL.118 acquisition tests,224 full artifact tests,22 contract/schema tests and20 isolated contract tests pass.234 schemas preserve all228 predecessors. Child1/4 (25%); parent1/24 (4.17%). B2 rights/expiry/transition policy is next; no scientific-use authority granted. [Evidence](../Audits/Evidence/BP-06-Acquisition/Identity_Observations.json). Immutable lookup intents and first-committed results complete the remaining B1 owner integration. Delivery credit is now1/4 (25%), Build1/3 (33.33%), parent1/24 (4.17%). B2 current rights/expiry and B3/V1 failure/replacement gates remain open; B1 completion is not child closeout. The public evidence contract now depends on the public Research identity DTO to retain exact responses; independent Data installation proves no Research implementation dependency. Historical unknown results remain unchanged after later identities become known.

## Staged ingestion HTTP - 2026-10-01 12:42:29

B1 partial: evidence0.3.0/Data0.7.0 staged ingestion HTTP and explicit host activation verified.108 acquisition tests,213 artifact regression tests before the added live-process case, and21 contract/schema tests pass. Actual initial/replacement HTTP processes preserve quarantined lab trace receipts.228 schemas preserve all224 predecessor bytes. Durable Research lookup/result observations remain; child0/4 and parent0/24 unchanged. [Evidence](../Audits/Evidence/BP-06-Acquisition/Ingestion_HTTP.json). Routes use original delivery/source/trace identities rather than new command bytes. Explicit host activation installs pinned output validators, checks migrated tables and preserves default-disabled compatibility. The live test starts two actual host processes against retained PostgreSQL/local bytes; it is not an isolated-wheel replacement or crash-during-write claim.

## Finalized ingestion stages - 2026-10-01 12:30:47

B1 partial: Data/Artifacts0.6.0 verified finalized ingestion stages;94 acquisition tests and200 full artifact-owner tests pass. Raw reads, delivery registration, reviewed preparation and immutable trace retention now compose against actual finalized artifacts. Public ingestion routes and durable Research lookup observations remain; child0/4 and parent0/24 unchanged. [Evidence](../Audits/Evidence/BP-06-Acquisition/Ingestion_Stages.json). Integration exposed missing prepared-output validators; explicit installed profile rules now validate the exact public DTOs without changing generic JSON Schema restrictions. Failed conversion retains the delivery identity; retry cannot substitute corrected bytes under that identity. Replacement here is a new owner object against retained PostgreSQL, not an independent process acceptance claim.

## Public Research client - 2026-10-01 12:06:09

B1 partial: Data/Artifacts0.5.0 public Research client verified;83 acquisition tests and189 full artifact-owner tests pass. Separate Data/Research wheel environments prove known, unknown and unavailable HTTP outcomes without private peer imports. Lab preparation remains quarantined. Finalized ingestion orchestration remains; child0/4 and parent0/24 unchanged. [Evidence](../Audits/Evidence/BP-06-Acquisition/Public_Research_Client.json). Response substitution, redirects, scope mismatch, oversize/malformed bodies and denial never become successful identity observations. The independent peer probe uses a synthetic raw reference; it does not replace final artifact ingestion proof.


## Research HTTP boundary - 2026-10-01 11:58:34

B1 partial: Research0.3.0 authenticated identity-only HTTP lookup/loopback host verified.61 owner tests and24 contract/dev tests pass; independently installed initial/replacement processes preserve lookup with401/403 denials.224 schemas preserve all220 predecessors. Data public client and ingestion operations remain; child0/4 and parent0/24 unchanged. [Evidence](../Audits/Evidence/BP-06-Acquisition/Research_HTTP.json). The lookup authenticates all nested scopes before SQL, preserves unknown versus unavailable, and exposes no artifact/scientific authority. Identity publication remains owner-private. Shared Research fixture moved to its test root to support granular API/persistence suites.


## Bounded preparation checkpoint - 2026-10-01 11:46:20

B1 partial: evidence0.2.0 and Data/Artifacts0.4.0 bounded preparation verified;58 acquisition tests,164 full artifact tests,31 contract/dev tests and52 pure tests in isolated wheels pass.220 schemas preserve all216 predecessors. Lab outputs stay quarantined pending Research reconciliation. Public owner integration remains; child0/4 and parent0/24 unchanged. [Evidence](../Audits/Evidence/BP-06-Acquisition/Preparation.json). Exact raw-token spans preserve Unicode, duplicates are rejected, missing/null units remain distinct, and no instruction or unit-conversion inference executes. Windows pytest long-parameter-ID failure was fixed with bounded IDs; production behavior unchanged.


## Acquisition ledger - 2026-10-01 11:37:03

B1 partial: Data/Artifacts0.3.0 acquisition ledger and artifact_0004 verified;31 acquisition tests and137 full artifact-owner tests pass with PostgreSQL. Exact delivery/trace replay, correction heads, finalized catalog binding, contention and rollback covered. No public acquisition route, rights fence or adapters yet; child0/4 and parent0/24 unchanged. Tests use actual public upload/finalization before registration; missing/forged catalog references fail. No scientific-use permission or current rights granted by metadata history. Independent installed acquisition/process-kill integration remains acceptance work.


## Research persistence checkpoint - 2026-09-30 18:01:56

B1 partial: Research0.2.0 private PostgreSQL ledger verified;34 owner tests (8 persistence) and13 dev tests pass. Two separately installed processes preserved original/successor revisions and replay. Forward research_0002 fixes NULL predecessor checks without rewriting applied history. Public API/artifact-rights and Data acquisition ledger/adapters remain; child0/4 and parent0/24 unchanged. [Evidence](../Audits/Evidence/BP-06-Acquisition/Research_Ledger.json). Tests cover concurrent conflicting writers, immutable history, unknown references, cross-scope/role denial, rollback before head commit and SQL null-predecessor bypass. No process-kill or public endpoint acceptance claimed.


## Research identity boundary - 2026-09-30 17:52:58

B1 partial: Research contracts0.1.0 and independent Research0.1.0 identity/question policies verified;9 contract and26 domain tests pass from isolated wheels. Candidate/sample unknowns quarantine; exact question revision and predeclared criteria required.216 schemas preserve all208 predecessors. Persistence, adapters and public owner integration remain; child0/4 and parent0/24 unchanged. [Evidence](../Audits/Evidence/BP-06-Acquisition/Research_Identity.json). No new API/database or scientific acceptance claim. Pure policies check chain shape; predecessor existence and current rights remain owner persistence/public-client obligations.


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

## 2026-10-01 19:50:16 - B1 reference validation checkpoint

B1 partial: Knowledge0.3.0 adds bounded public Data/Research clients, exact provenance/declaration review and durable review workflow.83 owner tests pass, including13 actual PostgreSQL cases; scripted HTTP covers routes, failure classes, byte/call limits and whole-review deadlines. Actual Data/Research owner integration and authenticated Knowledge API remain. Child0/4; parent4/24 (16.67%) unchanged. Connection-close transport tests exposed a closed-socket timeout update; fixed by stopping reads when the response closes. No schema/migration changes. See [validation proof](../Audits/Evidence/BP-06-Knowledge/Validation.json).
