# BP-07 Planning History

Archived first draft at `2026-09-25 13:35:12`. Historical task pairs/percentages are not the active execution tracker. The parent and linked children now own progress. Original scope is preserved below for traceability.

# BP-07 Autonomous LLM Campaign Supervision

## Archived draft tracker (non-canonical)

- Status: **proposed / first draft for user review**; implementation not activated.
- Last refreshed: `2026-09-24 12:01:26` (America/Chicago).
- Owner/scope: Agent Planning plus runtime-owned engagement and decision modules.
- Parent: [Master Build Tracker](Master%20Build%20Tracker.md); baseline: local architecture and BP-01/BP-01A completed foundation, BP-02 active protocol work.
- Overall implementation: **0%**; 10 equally weighted verified tasks, two per phase. Overall = completed tasks / 10; phase = completed tasks / 2. Drafting earns no implementation credit.
- Current phase/task: none; proposed plan.
- Next task: incorporate review, then verify predecessor gates and run the bounded pre-activation coherence audit before P1/T1.
- Prerequisites: Completed BP-03 discovery, BP-04 runner, BP-05 UI and BP-06 source/knowledge receipts.
- Completed implementation/evidence: none. All phase gates remain pending.
- Blockers: predecessor gates are not complete; decisions below block only their dependent tasks.
- Human acceptance: draft is available for review; no approval inferred for dependent deployment/provider actions. Campaigns remain autonomous with human changes between campaigns.
- Active exception: none.
- Draft coherence check: `2026-09-24 12:01:26`; ownership, ordering, scoped tests and handoffs checked against [owning architecture](../Architecture/Agents/Planning.md). This is not the implementation activation audit.

| Phase / status | Completion | Dependency | Required exit |
|---|---:|---|---|
| P1 Model and engagement contracts / proposed | 0% | Completed predecessor gates and activation audit | T1-T2: Contract tests reject unsupported actions and authority escalation; secrets/data limits apply at the adapter; fake-model success is not live-model acceptance. |
| P2 Reliable text decomposition / proposed | 0% | P1 exit | T3-T4: Pass predeclared per-case semantic criteria, not only JSON validation; unsupported assertions and replaying stale prose cannot overwrite accepted corrections. |
| P3 Campaign proposals and context / proposed | 0% | P2 exit | T5-T6: Invented tools, conflicting constraints and invalid representations reject; irrelevant retrieved text cannot authorize tool calls; missing evidence yields truthful abstention or blocked proposals. |
| P4 Durable supervisor and races / proposed | 0% | P3 exit | T7-T8: At most one accepted decision per scope/revision; unrelated branch progress continues; stale/late proposals cannot reopen closed work; lost acknowledgements may repeat calls but account for budget. |
| P5 Live evaluation and closeout / proposed | 0% | P4 exit | T9-T10: Actual live-model evidence is required for completion; unavailable provider/egress choice blocks that gate, not earlier deterministic work. No routine human wait and no scientific-validity claim from model fluency. |

## Outcome and Boundaries

Let an LLM propose bounded campaigns and knowledge decompositions while runtime and domain owners retain acceptance authority.

Included: Context assembly, versioned prompts/models, typed proposals, extraction evaluation, durable engagements, relevance-aware staleness, bounded repairs/fallbacks and autonomous terminal outcomes.

Excluded: Model-created tools executing without review, widened permissions, arbitrary code execution, human approval waits during campaigns and unbounded recursive model loops.

Primary services retain private state, dependencies, migrations and module READMEs. Public contracts/clients are the only cross-owner dependencies. Any new schema identifies its consumer/migration impact. No broad backend or shared business/ORM package. Later phases refine earlier boundaries under the current task without reopening closed plans.

## Child Work-Package Register

This parent owns outcomes and sequencing. The named packages below are **scoped, not implementation-ready**. The existing task pairs are requirements for child decomposition, not sufficiently detailed coding instructions. Before activating a package, author its canonical child plan with owned objects/API/storage, transition/algorithm decisions, failure/recovery matrix, named fixtures and replacement gates. Parent progress then rolls up verified child deliverables; do not count these task pairs again. No implementation credit is earned here.

| Child / bounded ownership | Implementation | Prerequisite | Scope to decompose |
|---|---:|---|---|
| BP-07.01 / Model and engagement contracts | 0% | Parent predecessor gates | Define provider/attempt versus logical engagement identity, prompt/context provenance, decision scope, relevant input revisions, allowed actions and bounded budgets. Implement a provider port and deterministic adversarial fake; record the live model/provider/egress decision before any real call and preserve omitted context metadata. |
| BP-07.02 / Reliable text decomposition | 0% | BP-07.01 exit | Build versioned extraction prompts against BP-06 operations using reviewed source-text/expected-meaning fixtures, identity resolution and human-readable semantic diffs. Evaluate source grounding, ambiguity, negation, causality/correlation, merges, contradictions and biological/polymer context; invalid proposals remain uncommitted and repair is bounded. |
| BP-07.03 / Campaign proposals and context | 0% | BP-07.02 exit | Assemble rights-eligible context through public retrieval/graph APIs with exact versions and explicit missing inputs; present registered capability descriptions and applicability limits. Generate campaign/parameter/successor proposals and run deterministic compilation, scientific eligibility and budget/authority checks before acceptance. |
| BP-07.04 / Durable supervisor and races | 0% | BP-07.03 exit | Persist request/outbox before model calls; implement engagement lifecycle and scoped decision commit through the same runtime committer. Handle relevant versus unrelated frontier changes, concurrent independent scopes, overlapping decisions, deterministic fallback races, timeout/cancel and bounded repair exhaustion. |
| BP-07.05 / Live evaluation and closeout | 0% | BP-07.04 exit | Using an explicitly selected model and permitted data, run the bounded campaign/extraction evaluation pack and compare actual outcomes with deterministic fixtures. Expose engagement/context/rejection lineage in Studio, preserve next-campaign topology changes and terminal failure reasons, then audit and archive. |

Readiness gaps are the unresolved decisions below plus concrete storage/API contracts, algorithm choices, test oracles and migration/recovery obligations for each package. Decompose the nearest eligible package first; do not invent distant provider, ontology or deployment decisions merely to fill templates. Child scope remains here until a linked execution plan replaces the register entry. The parent's existing percentages remain 0% because no implementation has occurred.

## Ordered Tasks

### P1 ? Model and engagement contracts

**T1.** Define provider/attempt versus logical engagement identity, prompt/context provenance, decision scope, relevant input revisions, allowed actions and bounded budgets.

**T2.** Implement a provider port and deterministic adversarial fake; record the live model/provider/egress decision before any real call and preserve omitted context metadata.

**Exit:** Contract tests reject unsupported actions and authority escalation; secrets/data limits apply at the adapter; fake-model success is not live-model acceptance.

### P2 ? Reliable text decomposition

**T3.** Build versioned extraction prompts against BP-06 operations using reviewed source-text/expected-meaning fixtures, identity resolution and human-readable semantic diffs.

**T4.** Evaluate source grounding, ambiguity, negation, causality/correlation, merges, contradictions and biological/polymer context; invalid proposals remain uncommitted and repair is bounded.

**Exit:** Pass predeclared per-case semantic criteria, not only JSON validation; unsupported assertions and replaying stale prose cannot overwrite accepted corrections.

### P3 ? Campaign proposals and context

**T5.** Assemble rights-eligible context through public retrieval/graph APIs with exact versions and explicit missing inputs; present registered capability descriptions and applicability limits.

**T6.** Generate campaign/parameter/successor proposals and run deterministic compilation, scientific eligibility and budget/authority checks before acceptance.

**Exit:** Invented tools, conflicting constraints and invalid representations reject; irrelevant retrieved text cannot authorize tool calls; missing evidence yields truthful abstention or blocked proposals.

### P4 ? Durable supervisor and races

**T7.** Persist request/outbox before model calls; implement engagement lifecycle and scoped decision commit through the same runtime committer.

**T8.** Handle relevant versus unrelated frontier changes, concurrent independent scopes, overlapping decisions, deterministic fallback races, timeout/cancel and bounded repair exhaustion.

**Exit:** At most one accepted decision per scope/revision; unrelated branch progress continues; stale/late proposals cannot reopen closed work; lost acknowledgements may repeat calls but account for budget.

### P5 ? Live evaluation and closeout

**T9.** Using an explicitly selected model and permitted data, run the bounded campaign/extraction evaluation pack and compare actual outcomes with deterministic fixtures.

**T10.** Expose engagement/context/rejection lineage in Studio, preserve next-campaign topology changes and terminal failure reasons, then audit and archive.

**Exit:** Actual live-model evidence is required for completion; unavailable provider/egress choice blocks that gate, not earlier deterministic work. No routine human wait and no scientific-validity claim from model fluency.

## Test Ownership and Evidence

Proposed suite locations (create with their modules):

- `services/agent_planning/tests/context/`.
- `services/agent_planning/tests/proposals/`.
- `services/agent_planning/tests/extraction/`.
- `services/campaign_runtime/tests/supervision/`.
- `tests/integration/autonomous_supervision/`.

Each owning README maps public behavior, invariants, failure scenarios and measured source paths to module-local test suites. Register source/suite ownership in `dev/test_scopes.json`; extend granular selectors as modules arrive. Run changed-module tests first, affected consumers next, and separate public-boundary integration/E2E only for cross-owner outcomes. Record line and branch coverage with gaps; coverage percentages are not evidence of scientific correctness.

Keep scenario evidence with absolute timestamps, implementation revision, fixture/schema identity, relevant run/artifact IDs and observed outcomes. Unit mocks do not replace required database, process, browser or provider evidence. Record independent build/install and replacement tests for new service/tool boundaries.

## Decisions and Handoff

Provider/model and egress policy are user-dependent before live calls. Define evaluation cases and acceptance criteria before tuning prompts. BP-08 consumes bounded topology proposals; changing the model requires versioned reevaluation rather than silently reusing earlier evidence.

## Progress, Scope Changes and Closeout

The canonical tracker owns overall and P1-P5 percentages; mirror them in MBT at every completed task or changed scope and before commit/handoff. Do not activate downstream phases before their predecessor gate. Record review changes and denominator adjustments here; substantial newly discovered scope gets a named successor.

Final phase includes a component-scoped architecture drift audit. Fix blocking drift, explicitly assign nonblocking follow-ups, update module READMEs/inventories and archive only after all defined gates pass. Synchronize MBT, plan index and Restore and repair moved links. Preserve separate acceptance/operational/scientific readiness status; 100% measures this bounded implementation, not the whole product.

Closeout evidence: pending. No implementation, deployment or scientific validation is claimed by this draft.

## Reference refinement 2026-09-25 13:54:17

BP-07.02/.03 now preserve extraction/repair provenance, distinguish inferred from source-stated values, and bind proposed experiment steps to exact unmet question criteria. Model answers cannot self-certify scientific sufficiency or bypass between-campaign human changes. Existing implementation deliveries extended with required acceptance cases; all 0%, denominator unchanged. [Reference assessment](References/Amphora_Lab_Insights.md) owns provenance and limitations.

## 2026-10-04 01:53:10 - Activation and B1.01

BP-06 closed90cda1c; corrected-ready activation preserves Runtime/domain authority. New planning0.1/Agent Planning0.1 pure context and attempt boundary.42 source/42 independent;60 including dev;84 statements/8 branches100%;484 schemas preserve466 predecessor bytes.8-wheel isolated closure excludes private peers. Child6.25%,parent1.25%, Build8.33%,Acceptance0%; B1.02 provider port active.

## 2026-10-04 02:00:10 - B1.02 deterministic provider

Additive planning0.2/Agent Planning0.2, bounded64KiB/256-chunk capture and distinct policy/invalid/unavailable/unknown/abstain/proposed outcomes. Reference-only profile cannot invent or substitute selected Artifact identity; actual task payload generation remains later profiles.69 source/69 independent tests,87 with dev;233 statements/42 branches100%;488 schemas preserve484 old bytes. Child12.50%,parent2.50%,Build16.67%; B1.03 persistence active.

## 2026-10-04 02:08:10 - B1.03 private journal

Agent Planning0.3, planning_0001 applied idempotently with separate migrator/service roles. Immutable request, attempt intent and observation/capture records; no public dispatch/budget permission.104 tests25.45s,11 actual PostgreSQL plus6 record-boundary cases;398/399 statements63/64 branches, migration CLI uncovered. Initial FK declaration failed and rolled back; fixed before migration acceptance, no retained peer state reset. Child18.75%,parent3.75%,Build25%; B1.04 independent process/install remains.

## 2026-10-04 02:17:10 - B1 boundary complete

B1.04 reusable installed verifier:8-wheel closure,2 independent installs,86 owned tests5.87s and4 process stages. Original unknown usage/capture preserved across successor proposal and replay; CLI migration explicit. No bytecode copied or private peers installed.18 dev13.87s;488 schemas unchanged. Initial tooling pin for absent optional greenlet corrected, then source-only staging verified. B1=100%,child25%,parent5%,Build33.33%,gates1/4 and1/20. B2.01 durable reservations next; no budget/dispatch or live provider claim.

## 2026-10-04 02:25:10 - B2.01a policy and tracker reconciliation

Agent Planning0.4 private reviewed budget policy/demand:22 source,40 with dev,108 independent cases/four processes;65 statements/2 branches100%. No actual reservation or dispatch claim. Child29.17%,parent5.83%,Build38.89%,gates1/4 and1/20. MBT child/build rows had drifted through substring numeric replacement while canonical child/parent trackers stayed correct; rewrote full rows and asserted readback against canonical values. All future updates use exact rows/fields, never unbounded percentage replacement.

## 2026-10-04 02:37:29 ? B2.01b atomic reservations

Planning0.5/planning_0002 stores policy and conservative holds atomically with intents.47 source cases,116 installed cases,6 processes/2 installations and18 dev cases pass. New ledger75 statements/14 branches100%; combined persistence/budget287/288 statements,33/34 branches (migration CLI independently exercised). Scoped dev-config lint passes. Child33.33%,Build44.44%,parent6.67%; next B2.02. Evidence: [Reservations](../Audits/Evidence/BP-07-Planning/Reservations.json).

## 2026-10-04 02:43:09 ? B2.02 conservative settlements

Planning0.6/planning_0003 preserves policy-v1 bytes and immutable observations. Reserved-floor charges never refund unknown/low usage; exact overage blocks new admission. Prior settlement is required before retry.65 source cases3.89s,134 independent cases/eight processes/two installs,18 dev14.54s and scoped lint pass. Pure charge23 statements100%; settlement59 statements/8 branches100%; combined372/373 statements41/42 branches (migration CLI independently exercised). Child41.67%,Build55.56%,parent8.33%; next B2.03 dispatch/outcomes. [Evidence](../Audits/Evidence/BP-07-Planning/Settlements.json).

## 2026-10-04 02:54:55 ? B2.03 durable dispatch and bounded outcomes

Planning0.7/planning_0004 adds once-only issuance, database-clock deadlines, immutable recovery and separate late evidence. Per-component charge maxima prevent late undercount/double charge. PlanningRunner preserves context/permissions and enforces bounded retries with pending/outcome/budget stops.156 source10.85s,156 installed/11 processes/two installations,18 dev16.63s. Dispatch108 statements/14 branches100%; runner64/66 statements14/16 branches (exception propagation branches remain for B3); total800/803 statements115/118 branches. Installed replacement recovers pending issued first attempt, calls only second, then replays both without dispatch. B1/B2complete; child50%,Build66.67%,parent10%,closed2/4 and2/20. [Evidence](../Audits/Evidence/BP-07-Planning/Orchestration.json). Next B3.01.

## 2026-10-04 02:58:15 ? B3.01 adversarial runner oracles

13 additional actual-PostgreSQL full-runner cases;24 orchestration cases5.11s, runner propagation branches now exercised. Output bounds, schema/action/scope protection, immutable retries, partial usage overage and non-provider storage failures verified. Source/production unchanged; final independent test installation remains V1. Child58.33%,Build77.78%,parent11.67%; next B3.02.

## 2026-10-04 03:01:54 ? B3.02 barrier proof

15 actual PostgreSQL cases9.89s pass, including independent engagement progress while three contenders observe pending, and recovery-first/return-first/simultaneous expiry races. Immutable original outcome, separate late evidence and single charge preserved. Child66.67%,Build88.89%,parent13.33%; next B3.03 abrupt process exit.

## 2026-10-04 03:06:50 ? B3.03 abrupt process-exit proof

Five committed boundaries across15 installed processes passed: reservation, issuance, provider return, observation, settlement. Same-attempt exclusive synthetic call markers never duplicate; fresh replacement preserves pending uncertainty/charges/output hashes and final replay calls nothing. Actual PostgreSQL, no remote/power-loss claim. Child75%,Build100%,parent15%,closed3/4 and3/20; V1.01 active. [Evidence](../Audits/Evidence/BP-07-Planning/Crash_Recovery.json).

## 2026-10-04 03:14:24 ? V1 acceptance and BP-07.01 closeout

V1.01 verified173 source/installed cases,18 dev,11 replay processes and15 abrupt-exit processes on final installations; V1.02 scoped audit aligned after consolidating stale persistence README. Child100%,Build100%,Acceptance100%; parent20%,4/20. Archive child and rebase links; BP-07.02 activation audit next. [Audit](../Audits/BP-07.01_Model_Engagement_Closeout.md). MBT redundant queue had stale5.83%; corrected to20% and removed numeric duplication from navigation prose. Future tracker refresh must include all active phase/queue mirrors, not historical checkpoint rows.

## 2026-10-04 03:20:21 ? BP-07.02 activation

[Coherence audit](../Audits/BP-07.02_Activation.md) reconciles Planning0.7, public Knowledge0.8/Research0.14/Evidence0.5.13 and actual owner boundaries. Reuse byte spans, Data traces, typed Knowledge proposals and interpretation Artifact linkage; preserve structural-only acceptance and future-campaign correction policy. Physical design sets ordered B1/B2/B3/V1 milestones. Child0%,Build0%,Acceptance0%; parent20%,4/20. B1.01 active; no live provider choice required for deterministic work.

## 2026-10-04 03:37:23 ? BP-07.02/B1.01 extraction inputs

Planning0.8/public Planning0.3 add immutable task/source/head/reference binding, exact raw UTF-8 quotation geometry, distinct graph/Research candidate DTOs and reviewed prompt/data compartments.52 source/dev19.96s,207 installed/11 processes/two installs;154 statements20 branches100%.492 schemas preserve488 prior bytes. Fixture generation lost Greek characters through Windows shell piping; corrected literal UTF-8 fixture and pinned prompt LF bytes in .gitattributes. Child6.25%,Build8.33%,parent21.25%; B1.02 active. [Evidence](../Audits/Evidence/BP-07-Extraction/Input_Contracts.json).

## 2026-10-04 03:54:55 ? BP-07.02/B1.02 typed output compatibility

Planning0.9/public Planning0.4 add closed profile catalog, TypedProposal/v1 and observation/v2 while retaining legacy v1 bytes. Conditional planning_0005 allows256KiB encoded v2 overhead only; raw capture/canonical payload remain64KiB.233 source23.52s,233 installed/14 processes/two installs incl retained0.7 readback,18 dev14.82s. Golden0.8 canonical v1 bytes unchanged.496 schemas preserve492 predecessors; profiles53 statements14 branches100%, decoder17 statements100%; service1026/1027 statements151/152 branches (CLI separately executed). Child12.50%,Build16.67%,parent22.50%; B1.03 active. [Evidence](../Audits/Evidence/BP-07-Extraction/Task_Output.json).

## 2026-10-04 04:07:44 - BP-07.02/B1.03a trace projection

Planning0.10/public0.5 adds interpretation-only trace/ref roots and pure immutable projection. Failed/repaired output digests, exact source/target/model/prompt/policy pins, source-claimed/inferred/missing origins retained. Transform steps claim only verified local transformations.263 source/contract/dev tests32.37s;64 statements14 branches100%;500 schemas preserve496 predecessor bytes. Child14.58%,Build19.44%,parent22.92%; B1.03b next. No Data publication or scientific acceptance claim.

Archived MBT checkpoint references (original relative evidence links retained relative to this directory):

| 2026-10-03 20:03:23 | BP-06.05 closed100%; parent83.33%,20/24; BP-06.06 audit next | [Closeout](../Audits/BP-06.05_Representation_Retrieval_Closeout.md);649 installed+4 binding cases,11-wheel independent build |

## 2026-10-04 04:16:09 - BP-07.02/B1.03b durable extraction journal

planning_0006 adds own immutable task and observed-attempt trace tables with source/target-bound prior lineage. Exact byte/time replay, request/task uniqueness, actor/grants, pending rejection, competing writers and replacement connections verified.272 owner/contract/dev cases33.47s; final10 PostgreSQL cases5.13s,102 statements8 branches100%. Explicit original-type guard rejects forged bool ordinals before Pydantic serialization can normalize them. Planning0.11/public0.5;500 schemas unchanged. Child16.67%,Build22.22%,parent23.33%; B1.03c corpus/independent proof next.

Archived MBT checkpoints:

| 2026-10-03 20:26:20 | BP-06.06 activated; B1.01 complete,child5%,parent84.17%; B1.02a active | [Scenario protocol](../Audits/Evidence/BP-06-Feedback/Scenario_Manifest.json);30 pure/18 dev,123statements16branches100% |

## 2026-10-04 04:24:20 - BP-07.02/B1.03 complete

Eighteen agent-reviewed synthetic passages and distinct expected-meaning/alternative/rejection oracles cover9 categories in calibration/held-out splits. Integrity checks pin source and oracle bytes, no adapter-output-derived labels.274 source/contract/dev46.68s;256 installed17 processes/two installations incl failed/repaired/replay trace history and retained Planning0.7 v1 readback.1194/1195 statements173/174 branches, migrationCLI separately executed. Child18.75%,Build25%,parent23.75%; B1.04a explicit processing-content read is next. Current Data content checks read, not process; rights owner already supports process internally. Additive public processing-content route is a bounded prerequisite within planned current-rights integration; closed BP-06 stays closed.

Archived MBT checkpoints:

| 2026-10-03 20:57:09 | B1.02a verified; child7.50%,parent84.58%; B1.02b active | [Projection proof](../Audits/Evidence/BP-06-Feedback/Knowledge_Projection.json);25 pure/174 installed,452 schemas |

## 2026-10-04 04:31:33 - BP-07.02/B1.04a processing-content prerequisite

Data0.29 exposes GET /v1/artifacts/{id}/processing-content with existing scoped read action and current source process ancestry captured/rechecked around storage I/O. Ordinary /content keeps read semantics; historical source/rights remain unchanged, no continuing lease or provider egress permission.176 regression99.95s,actual installed HTTP/replacement+focused7 cases31.55s,final7 read cases4.02s (37 statements4 branches100%),18 dev15.66s. Independent package closure excludes peer implementations. artifact0012 and500 public schemas unchanged. Child20.31%,Build27.08%,parent24.06%; B1.04b current.

Archived MBT checkpoints:

| 2026-10-03 21:07:50 | B1.02 complete; child10%,parent85%; B1.03a active | [Knowledge HTTP](../Audits/Evidence/BP-06-Feedback/Knowledge_Projection_HTTP.json);56 source/205 installed,actual process replacement |

## 2026-10-04 04:43:42 - BP-07.02/B1.04b bounded source review

Planning0.12 consumes public Evidence directly. Own source_access module uses configured loopback Data processing-content,exact source/trace/span/Artifact/prompt binding and complete consumed inputs<=128. Every review reacquires bytes; partial/quarantined metadata remains explicit.20s whole-review deadline interrupts stalled/trickled headers/body,512 calls32MiB maximum; safe denied/missing versus transient classification,no redirects/proxies/implicit retries.55 focused2.78s,194/196 statements28/28 branches (defensive shutdown catch only),329 owner/contract/dev36.34s. Child21.88%,Build29.17%,parent24.38%; c.i payload/transitions next. Actual owner integration d remains required.

Archived MBT checkpoints:

| 2026-10-03 21:22:59 | B1.03a verified; child12.50%,parent85.42%; B1.03b active | [Research views](../Audits/Evidence/BP-06-Feedback/Research_Views.json);38 source/254 installed,466 schemas |

## 2026-10-04 04:54:02 - BP-07.02 publication values

B1.04c.i verified:351 tests51.04s,22 pure publication cases,158 statements2 branches100%. Exact canonical trace content,self-contained schema,full ancestry,stable commands and bounded upload transitions. Child22.40%,Build29.86%,parent24.48%; c.ii journal next.

Archived MBT checkpoints:

| 2026-10-03 21:34:15 | B1.03 complete; child15%,parent85.83%; B1.04a active | [Research HTTP](../Audits/Evidence/BP-06-Feedback/Research_Views_HTTP.json);35 source/275 installed,actual replacement |

MBT checkpoint archive 2026-10-04 05:11:45:

| 2026-10-03 21:51:08 | B1.04a verified; child17.50%,parent86.25%; B1.04b active | [Studio transport](../Audits/Evidence/BP-06-Feedback/Studio_Scientific_Transport.json);154 source/154 independent,14 scientific roots |

## 2026-10-04 05:11:45 - B1.04c.ii publication journal

Planning0.14 adds planning_0007 immutable intents, payloads and transition history with separately mutable lease/control columns. Original actor, exact trace/task, configured publisher/schema and historical metadata are reconstructed on every read. Lease expiry is checked at the actual position write; inserted events/payload roll back together on expiry or failure. No peer I/O or fresh authorization is claimed by historical readback.375 regression cases65.55s;469 publication statements28 branches100%. Child22.92%,Build30.56%,parent24.58%; c.iii SDK workflow/recovery next, d actual installed peers remains required.

MBT archive 2026-10-04 05:23:21:

| 2026-10-03 22:15:08 | B1.04b verified; child20.00%,parent86.67%; B1.05 active | [Studio provenance](../Audits/Evidence/BP-06-Feedback/Studio_Provenance.json);168 source/168 independent,18dev |

## 2026-10-04 05:23:21 - B1.04c.iii public SDK workflow

Planning0.15/public0.5/SDK0.2;421 owner/contract/dev cases109.26s;92 publication cases.602/608 statements58/62 branches covered; residuals explicitly documented in module README. Actual SQL plus public SDK scripted Data peer and loopback transport verify finite receipt-first command recovery, no repeated uncertain PUT, stable finalize identities, derivation binding, durable rejection, interruption at each local transition and stale lease denial. Dependency boundaries and Ruff pass. Child23.44%,Build31.25%,parent24.69%; d actual installed Data/Planning proof remains required before B1 closes.

MBT archive 2026-10-04 05:38:25:

| 2026-10-03 22:35:26 | B1 complete; child25.00%,parent87.50%; B2.01 active | [Actual integration](../Audits/Evidence/BP-06-Feedback/Integrated_Baseline.json);four installed owners,Qdrant,Runtime replacement,Studio readback |

## 2026-10-04 05:38:25 - B1 actual publication accepted

Planning0.15/public0.5/SDK0.2 and Data0.29 actual installed integration passed20 Planning processes/2 Data processes. Independent Planning closure403 tests17 process readbacks/two installations also passed;18 dev cases16.14s. Six actual public input Artifacts, source revision/conversion trace and exact published interpretation bytes/ancestry verified. Four abrupt os._exit boundaries preserve committed history, allocate a new upload only for uncertain stream intent and reconcile an already remotely finalized Artifact under its original command. Data process replacement preserves source/conversion/catalog history.

Two exploratory acceptance runs exposed incorrect test assumptions about HTTP403, not a production workflow defect. Rights denial can return command_request_denied while Data already retains a terminal rights_use_denied receipt. Planning truthfully stays prepared/finalizing until observing that receipt; retry then retains rejection. Final acceptance explicitly reads the original Data receipt, verifies terminal rejection survives regrant, and uses separately identified future publications after rights restore. No fabricated failure/success or rewrite of previously finalized history. Actual scope is synthetic software behavior, not live model quality or Knowledge acceptance.

B1=100%,child25%,Build33.33%,parent25%,closed1/4 and5/20. B2.01a active; three substeps scoped in Graph proposal validation companion without added parent weight. Exact v1 task/draft/schema/trace bytes remain compatibility requirements.

MBT archive 2026-10-04 05:57:15:

| 2026-10-03 22:49:16 | B2.01 complete; child31.25%,parent88.54%; B2.02 active | [Explore model](../Audits/Evidence/BP-06-Feedback/Explore_Page_Model.json);182 source/independent,actual owner model proof |

## 2026-10-04 05:57:15 - B2.01a typed edit profile

Planning0.16/public0.6 introduces task/v2 selected assertion revisions, explicit entity context and attributed correction/retraction/merge/context-revision candidates. The closed provider catalog binds exact schema, keeps selected/scope/action guards and retains typed edits in immutable trace paths. Core SchemaRef only permits version1; a separate planning.extraction-edit-draft/v1 profile carries schema_version2 payload without changing shared schemas. An initial attempted version2 reference failed strict validation, resolved before verification by the separate identity. All500 predecessor validation/serialization hashes unchanged,504 total. No SQL migration or raw output bound increase; a separate LF-pinned v2 prompt leaves v1 bytes intact.

447 source owner/contract/dev cases136.96s,299 extraction/profile statements62 branches100%;429 owned cases in two independent installs plus20 processes including failed/repaired v2 traces and retained0.7 history. This is typed shape/provenance compatibility, not semantic edit acceptance. B2.01a100%,b/c0%;B2.01=33.33%,B2=11.11%,child27.78%,Build37.04%,parent25.56%. B2.01b deterministic validation is current; actual owner read binding is c.

## Archived MBT checkpoint 2026-10-04 06:28:33

| Timestamp | Checkpoint | Evidence |
|---|---|---|
| 2026-10-03 23:17:26 | B2.02 complete; child37.50%,parent89.58%; B2.03 active | [Visible Explore](../Audits/Evidence/BP-06-Feedback/Explore_Visible_Views.json);186 independent,9 browser,actual model,reviewed screenshots |

## 2026-10-04 06:28:33 - BP-07.02/B2.01b verified

Planning0.17 adds decomposed deterministic graph proposal validation and direct public Knowledge dependency.483 source tests,465 independent tests20 process stages,36 pure validation cases;409 statements116 branches at98%. Child30.56%,Build40.74%,parent26.11%; c public owner reads next. Canonical closed counts remain1/4 and5/20. See [evidence](../Audits/Evidence/BP-07-Extraction/Proposal_Validation.json). No Knowledge contact/acceptance or scientific validity claim. Source-adjacent README consolidated to current behavior; granular Planning selectors now include source_access/publication/proposals.

## Archived MBT checkpoint 2026-10-04 06:45:26

| Timestamp | Checkpoint | Evidence |
|---|---|---|
| 2026-10-04 00:46:37 | B2 complete; child50%,parent91.67%; B3.01 active; gates2/4 and22/24 | [Owner reuse](../Audits/Evidence/BP-06-Feedback/Scientific_Reuse_Actual.json);actual1test93.51s, exact context and optional quality |

## 2026-10-04 06:45:26 - BP-07.02/B2.01c verified

Planning0.18 public Knowledge reads and graph packet preparation verified.513 regression plus2 additional focused cases;497 independently installed cases20 process stages; actual public reads8 Planning workers/2 Knowledge hosts, with2 synthetic Knowledge-local fixture processes. Old pins survive future retraction and owner restart; new tasks see the new revision; denials/missing exact records are explicit. Child33.33%,Build44.44%,parent26.67%,closed1/4 and5/20. [Evidence](../Audits/Evidence/BP-07-Extraction/Knowledge_Read_Binding.json). B2.02 starts with explicit aggregate repair admission design; no credit for design.
