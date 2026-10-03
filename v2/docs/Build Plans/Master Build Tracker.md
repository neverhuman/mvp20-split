# Master Build Tracker

## Purpose and Authority

Program-level source of truth for Amphora v2 build priority, dependency order, current position and delivery gates. Each activated plan owns its detailed canonical phase/task tracker and evidence; MBT mirrors that status without duplicating task history. [Development Process](../Development_Process.md) governs execution.

Structure adapted from the user-authorized read-only JARVIS MBT review on `2026-09-23 11:04:44`. JARVIS deployment policies, permissions, priorities and completion claims are not imported.

## Program Tracker

- Status: BP-06 primary active; BP-06.01 through BP-06.04 closed; BP-07 through BP-09 queued; BP-05 closed.
- Last refreshed: `2026-10-03 17:20:22` (America/Chicago).
- Baseline: [Product Requirements](../Architecture/Requirements/Product_Requirements.md), [Master Architecture](../../Architecture.md).
- Current priority: P5 / BP-06 - Knowledge Evidence and Source Loop.
- Primary active task: BP-06.05/Build/B2.02b projection/search adapter.
- Next task: BP-06.05/B2.02b projection/search adapter.
- Implementation completion: BP-06 **72.22%** ((17+1/3)/24), 17/24 closed delivery gates. BP-06.01 through .04 closed100%; BP-06.05=33.33%; BP-06.06=0%. BP-07..09 remain0%.
- Active focus: generation manifest/lifecycle and expected-head publication; representation boundary verified.
- Blockers: none requiring owner direction; future-only corrections and iterative-progress policy approved.
- Acceptance posture: BP-06.01 through .04 bounded software accepted; scientific/deployment gates remain separately scoped.
- Active exception: none.

Queued successor: [SQ-01 Scientific Quality and Iteration Views](SQ-01%20Scientific%20Quality%20and%20Iteration%20Views.md), 0%, after BP-06 owner projections and BP-07.03 proposal contracts. Preserves closed BP-05; no change to active BP-06 denominator.

## Initial Delivery Boundary

Internal use and demos for the first many releases; one user and one active autonomous campaign, with concurrent tool invocations. Single-server target is DGX Spark or partner Threadripper. Keep the scientific engine general; bio-available polymers are a likely application, not a fixed implementation pathway. Human edits and human-initiated replacements apply between campaigns.

Strictly isolate primary services and independently packaged tools. Use Pydantic/JSON Schema contracts, PostgreSQL-owned state, immutable artifacts, a single Graph Runner execution authority, an indexed tool universe and durable LLM proposals. Module READMEs capture the boundary conditions for independent rebuilds. K3s/Kubernetes tool replication is a proposed deployment profile; cluster selection and installation are not yet authorized implementation work.

The initial program proves software behavior using deterministic/synthetic fixtures and narrowly reviewed v1 reuse. Validated biological/polymer evaluators, real laboratory integration and scientific efficacy require separate evidence and scoped successor work.

## Current In-Flight Work

BP-06 is the sole active parent. BP-05 closed16/16; see [completed plans](Completed/README.md).

| Parent | Overall | P1 | P2 | P3 | P4 | P5 | P6 |
|---|---:|---:|---:|---:|---:|---:|---:|
| [BP-06](BP-06%20Knowledge%20Evidence%20and%20Source%20Loop.md) | 72.22% ((17+1/3)/24) | 100% | 100% | 100% | 100% | 33.33% | 0% |

| Active canonical child | Overall | Build | Acceptance | Current task |
|---|---:|---:|---:|---|
| [BP-06.05](BP-06/BP-06.05%20Representation%20reuse%20and%20retrieval.md) | 33.33% | 44.44% | 0% | B2.02b / Projection/search adapter |



## Queued Plans and Phase Mirrors

| Canonical plan | Status | Overall | P1 | P2 | P3 | P4 | P5 | P6 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| [BP-07 Autonomous LLM Campaign Supervision](BP-07%20Autonomous%20LLM%20Campaign%20Supervision.md) | Design specified | 0% | 0% | 0% | 0% | 0% | 0% | N/A |
| [BP-08 Evolutionary Search Integration](BP-08%20Evolutionary%20Search%20Integration.md) | Design specified | 0% | 0% | 0% | 0% | 0% | 0% | N/A |
| [BP-09 Single-Server Integrated Demo and Replacement Proof](BP-09%20Single-Server%20Integrated%20Demo%20and%20Replacement%20Proof.md) | Design specified | 0% | 0% | 0% | 0% | 0% | 0% | N/A |

Scoped milestone fractions measure verified work within their existing delivery weight; closed-gate counts remain separate. BP-06.03 is now archived4/4. Do not treat milestone counts as effort estimates.

Each parent phase now maps to one canonical child with four verified deliveries (three build plus one acceptance). Parent denominators are BP-03: 16, BP-04: 24, BP-05: 16, BP-06: 24, BP-07: 20, BP-08: 20, BP-09: 20; trackers above own current percentages. N/A means unscoped. [Readiness/handoffs](Planning_Readiness.md) records engineering and external gates. Design writing earns no implementation credit.

The owning plan tracker is canonical for overall and per-phase percentages. Refresh this mirror whenever a gate, scope, completion estimate, blocker or checkpoint changes, before handoff/commit. Percentages measure scoped implementation; acceptance and operational readiness are separate. No in-flight plan may appear here without numeric overall and phase completion.


[BP-01](Completed/BP-01%20Contract%20and%20Service%20Foundations.md) and BP-01A remain complete and archived. The queue below links canonical parents; ordering does not waive child gates. [Planning readiness](Planning_Readiness.md) owns cross-plan dependencies and scoped external decisions.

## Prioritized Build Queue

BP-06 is primary_active at72.22% scoped completion (17/24 closed gates); BP-07 through BP-09 are `design_specified / queued`. The later roadmap has 34 canonical children. Each child names owned objects/contracts, algorithms, failure oracles and replacement acceptance. Completed plans remain in the archive.

| Order / ID | Completion | Proposed plan | Required predecessor gates | Bounded outcome / exit | Architecture owner |
|---|---|---|---|---|---|
| P5 / BP-06 | 72.22% | [Knowledge Evidence and Source Loop](BP-06%20Knowledge%20Evidence%20and%20Source%20Loop.md) | BP-01 contracts; BP-04 execution; BP-05 inspection | Minimal source/document/result ingestion, typed accepted-change replay, pinned knowledge revisions, bounded executable rules and explicit scientific acceptance receipts; demonstrate corrections affect later campaigns | [Knowledge](../Architecture/Knowledge/Knowledge_Architecture.md), [Data](../Architecture/Data/Data_Architecture.md), [experiments](../Architecture/Research/Experiments.md) |
| P6 / BP-07 | 0% | [Autonomous LLM Campaign Supervision](BP-07%20Autonomous%20LLM%20Campaign%20Supervision.md) | BP-03 tool discovery; BP-04 runner; BP-05 UI; BP-06 grounded context/receipts | Model-generated campaign proposals and text-to-graph extraction through validated contracts; durable scoped engagements, stale-proposal/fallback races, bounded repair and truthful terminal blockers; no routine human waits | [Planning](../Architecture/Agents/Planning.md), [Graph Runner](../Architecture/System/Graph_Runner.md) |
| P7 / BP-08 | 0% | [Evolutionary Search Integration](BP-08%20Evolutionary%20Search%20Integration.md) | BP-04 iteration/checkpoints; BP-06 applicability/evidence; BP-07 for LLM-guided topology | Adapt reusable numerical kernels to explicit generation/checkpoint history, separate representation fixtures and evidence-bound selection; parameter search precedes bounded topology proposals under successor-campaign rules | [Search](../Architecture/Campaigns/Search.md), [reuse baseline](../Architecture/Evolutionary_Code_Reuse_Baseline.md) |
| P8 / BP-09 | 0% | [Single-Server Integrated Demo and Replacement Proof](BP-09%20Single-Server%20Integrated%20Demo%20and%20Replacement%20Proof.md) | Selected host/model policy; BP-05/06/07 plus BP-08 for evolutionary demo claims | Reproducible target-host deployment, model/tool eligibility, restore/reconciliation, end-to-end autonomous demo and one independently rebuilt/replaced tool; prove replicated workloads if K3s is selected | [Topology](../Architecture/System/Runtime_Topology.md), [tool services](../Architecture/Capabilities/Tool_Services.md) |

This is the default sequencing, not nine permanent file-ownership buckets. Each plan owns a delivery step; later plans may refine earlier contracts with explicit compatibility evidence. BP-01 records packaging constraints early; BP-03 tests tool images/protocols locally. BP-09 integrates target-host operation rather than postponing all deployment design to the end. Synthetic fixtures/receipts stand in for unavailable scientific services until BP-06 and are labeled as such.

## Cross-Plan Milestones

| Milestone | Plans | Done when | Status |
|---|---|---|---|
| M1 ? Replaceable typed foundation | BP-01/02/03 | One standalone tool is discovered and invoked through pinned contracts with durable acceptance and recovery | Synthetic software foundation complete: BP-01/02/03 contracts, durable invocation/recovery and standalone tools accepted |
| M2 ? Inspectable executing graph | BP-04/05 | A user can follow parallel work, joins, failures and evidence in a real running fixture, then author a subsequent campaign | Accepted within synthetic software scope: BP-04 execution/observation and BP-05 Studio closed |
| M3 ? Autonomous evidence-aware campaign | BP-06/07 | Pinned knowledge informs execution; durable LLM proposals are validated; stale or invalid responses cannot corrupt the run | Not started |
| M4 ? Evolution and module replacement | BP-08/09 | Search history/checkpoints are inspectable; target-host demo recovers and a replacement tool preserves its documented boundaries | Not started |

Milestones are acceptance outcomes, not additional work counted on top of their plans. No calendar dates or capacity promises are inferred.

## Decisions and Dependency Watchlist

BIND-01 is resolved by [closed BP-04.04A](BP-04/Completed/BP-04.04A%20Typed%20artifact%20and%20collection%20bindings.md). BP-04 subsequently closed24/24; the historical scope correction remains in its archived history.

| Item | Needed before | Disposition / owner |
|---|---|---|
| Initial schema/identity/publication policy | BP-01 complete; expand per successor | Initial wire subset and portable publication verified; durable command hashing remains BP-02 |
| API/development stack and initial service build layout | BP-01 complete | Foundation Decisions and independent package manifests now own the selected stack |
| Artifact reservations, cross-service receipts and revocation semantics | BP-02/06 dependent implementation | System/domain owners; required protocol fixtures |
| Branch/join/loop, bindings and recovery | BP-04 complete | Scoped child/parent audits and actual installed observation/replacement accepted |
| Bounded rule formalism and contradiction behavior | BP-06 implementation | Knowledge owner; examples/fixtures before inference code |
| Real scientific corpus, evaluators and lab provider | Scientific successor acceptance | TBA by owner; does not block synthetic engine proof |
| Actual host, accelerator availability, model endpoint and permitted data egress | Real-provider use / target deployment | Environment decision; local mocks are not provider validation |
| K3s choice and workload packaging | BP-09 cluster-specific proof | Proposed, not an installed dependency or a second graph scheduler |

## Deferred and Successor Scope

Keep these outside the initial active queue until a concrete trigger exists: validated domain packs for actual polymer/biological research; production laboratory/CRO integrations; Qdrant/embedding retrieval and representation quality once corpus/workload requires it; cross-project learning and model training/promotion; broad catalog-scale acceptance; multi-user/concurrent-campaign operation; customer/enterprise deployment, commercial features and formal service-level targets.

Deferral changes delivery sequence, not the requirement authority. Each successor must name the relevant acceptance obligations and its own baseline. Stable identity/scope, bounded resource use, scientific provenance and basic recovery remain first-slice correctness requirements.

## Update and Execution Rules

1. Select the highest-priority eligible plan, then the owning tracker's earliest unmet phase/task. Default to one active implementation plan, phase and task.
2. Before activation, author and audit the owning plan using the [template](../Templates/Build%20Plan%20Template.md). Record prerequisites, numeric phase progress, accounting basis, verification, exit gates and exact resume point. A queue row alone cannot activate work.
3. Update owning task/phase evidence first, then synchronize MBT priority/state and Restore. Track implementation completion separately from human acceptance and operational confidence; do not invent a weighted overall percentage before child scopes exist.
4. Complete each phase's required gates before dependent work. Human acceptance gates apply only when explicitly defined for SDLC delivery; they must not be confused with the autonomous product's campaign behavior.
5. Record scope additions, dependency changes and interruptions explicitly. Revise progress when remaining work changes; no hidden workstream or gate weakening.
6. On plan completion, conduct the component-scoped architecture drift audit, resolve acceptance-blocking findings, archive the plan/history and repair links. Closed plans stay closed; rewrites and regressions use bounded successors.
7. Keep MBT compact: latest 25 checkpoints maximum, current priorities and gates here; detailed history stays in owning plans/history and Git.

## Completed Plans

[Completed plan index](Completed/README.md) owns the three closed architecture-documentation plans and their audits. They remain complete for their historical scope and do not contribute runtime implementation credit. BP-01/BP-01A/BP-02 are completed implementation foundations; general graph execution and scientific readiness remain later gates.

## Recent Checkpoints

| Timestamp | Checkpoint | Evidence |
|---|---|---|
| 2026-10-03 17:20:22 | B2.02a complete; child33.33%, parent72.22%; b active | [Qdrant transport](../Audits/Evidence/BP-06-Representations/Qdrant_Transport.json);33 source/117 installed,18 dev; actual authenticated Qdrant1.19.1 |
| 2026-10-03 17:00:42 | B2.01 complete; child31.25%, parent71.88%; B2.02a active | [Generation publication](../Audits/Evidence/BP-06-Representations/Generation_Publication.json);37 source/508 installed,14 dev;0011 retained history |
| 2026-10-03 16:41:32 | B2.01c complete; child29.69%, parent71.61%; d active | [Generation state](../Audits/Evidence/BP-06-Representations/Generation_State.json);27 source/488 installed,14 dev;0010 retained history |
| 2026-10-03 16:23:38 | B2.01b complete; child28.13%, parent71.35%; c active | [Generation contracts](../Audits/Evidence/BP-06-Representations/Generation_Contracts.json);57 source/200 installed,14 dev |
| 2026-10-03 16:16:12 | B2.01a complete; child26.56%, parent71.09%; b active | [Generation models](../Audits/Evidence/BP-06-Representations/Generation_Models.json);179 source/179 installed,14 dev |
| 2026-10-03 15:52:35 | B1 complete; child25%, parent70.83%; B2.01 active; gates1/4 and17/24 | [Actual HTTP](../Audits/Evidence/BP-06-Representations/HTTP_Replacement.json);source/installed isolated-server public-only replay/revocation |
| 2026-10-03 15:44:22 | B1.05 complete; child20.83%, parent70.14%; B1.06 active | [API/hosting](../Audits/Evidence/BP-06-Representations/API_Hosting.json);185 source/452 installed;126 new statements/14 branches covered |
| 2026-10-03 15:26:02 | B1.04 complete; child16.67%, parent69.44%; B1.05 active | [Convergence](../Audits/Evidence/BP-06-Representations/Binding_Convergence.json);160 source/160 installed;independent rights,one compute,attributed publishers |
| 2026-10-03 15:18:21 | B1.04c complete; child15.63%, parent69.27%; B1.04d active | [Workflow](../Audits/Evidence/BP-06-Representations/Binding_Workflow.json);229+2 source;435+2 installed;no schema/migration change |
| 2026-10-03 15:00:03 | B1.04b complete; child14.58%, parent69.10%; B1.04c active | [Binding state](../Audits/Evidence/BP-06-Representations/Binding_State.json);147 source;420 distinct installed;artifact_0009 |
| 2026-10-03 14:15:48 | B1.04a complete; child13.54%, parent68.92%; B1.04b active | [Binding models](../Audits/Evidence/BP-06-Representations/Binding_Models.json);121 source/121 installed; no schema/migration change |
| 2026-10-03 13:57:14 | BP-06.05/B1.03 complete; child12.50%, parent68.75%; B1.04 active | [Profile/cache storage](../Audits/Evidence/BP-06-Representations/Profile_Cache_Storage.json);113 source/391 installed;artifact_0008 |
| 2026-10-03 13:32:03 | BP-06.05/B1.02 complete; child8.33%, parent68.06%; B1.03 active | [Public contracts](../Audits/Evidence/BP-06-Representations/Public_Contracts.json);103 source/103 installed;420 schemas preserve406 |
| 2026-10-03 13:18:06 | BP-06.05/B1.01 complete; child4.17%, parent67.36%; B1.02 active | [Domain identities](../Audits/Evidence/BP-06-Representations/Domain_Identities.json);64 source/64 final wheel; repaired startup probes6+6 |
| 2026-10-03 12:46:50 | BP-06.05 activated0%; B1.01 active; parent66.67% unchanged | [Activation audit](../Audits/BP-06.05_Activation.md);independent source rights, future-only scientific corrections, bounded fixture and index design |
| 2026-10-03 12:31:31 | BP-06.04 closed100%; parent66.67%,16/24; BP-06.05 activation next | [Closeout audit](../Audits/BP-06.04_Laboratory_Eligibility_Closeout.md);fresh build919 tests,2 cutovers,9 publisher +6 intake/interpretation barriers |
| 2026-10-03 12:24:23 | V1.02 complete; child91.67%, parent65.28%; V1.03 active | [Replacement/recovery](../Audits/Evidence/BP-06-Research/Laboratory_Replacement_Recovery.json);2 fresh cutovers and9 publisher process barriers |
| 2026-10-03 12:11:37 | V1.01 complete; child83.33%, parent63.89%; V1.02 active | [Independent build](../Audits/Evidence/BP-06-Research/Laboratory_Independent_Build.json);fresh Research0.31.0,919 installed tests,9 separate opt-ins |
| 2026-10-03 12:06:32 | B3 complete; child75%, parent62.50%; V1.01 active; gates3/4 and15/24 | [Defensive failures](../Audits/Evidence/BP-06-Research/Scientific_Defensive_Failures.json);108 source/108 installed,351 statements/55 of56 branches |
| 2026-10-03 11:58:32 | B3.02 complete; child66.67%, parent61.11%; B3.03 active; gates2/4 and14/24 | [Process recovery](../Audits/Evidence/BP-06-Research/Scientific_Process_Recovery.json);6 source/6 installed actual kill cases,14 dev |
| 2026-10-03 06:14:19 | B3.01 complete; child58.33%, parent59.72%; B3.02 active; gates2/4 and14/24 | [Scientific context matrix](../Audits/Evidence/BP-06-Research/Scientific_Context_Matrix.json);source/installed actual MAT-01..05 and consumer/correction proof |
| 2026-10-03 05:59:25 | B2 complete; child50%, parent58.33%; B3.01 active; gates2/4 and14/24 | [Actual interpretation HTTP](../Audits/Evidence/BP-06-Research/Interpretation_HTTP_Replacement.json);source/installed independent correction/offline replacement workflows |
| 2026-10-03 05:46:33 | B2.04b complete; child47.92%, parent57.99%; c active | [Interpretation hosting](../Audits/Evidence/BP-06-Research/Interpretation_Hosting.json);882 source/882 installed,14 dev |
| 2026-10-03 05:30:56 | B2.04a complete; child45.83%, parent57.64%; b active | [Interpretation workflow](../Audits/Evidence/BP-06-Research/Interpretation_Workflow.json);762 source/762 installed,119 compatibility/dev;406 schemas |
| 2026-10-03 05:18:56 | B2.03 complete; child43.75%, parent57.29%; B2.04a active | [Correction/impacts](../Audits/Evidence/BP-06-Research/Correction_Views_Impacts.json);808 source/808 installed,119 compatibility/dev;616 backfilled dependencies |

Keep at most 25 checkpoint rows. [Completed plans](Completed/README.md) remain outside active tables. Update the owning plan first, then this summary and Restore when their state changes.
