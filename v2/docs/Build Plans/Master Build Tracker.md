# Master Build Tracker

## Purpose and Authority

Program-level source of truth for Amphora v2 build priority, dependency order, current position and delivery gates. Each activated plan owns its detailed canonical phase/task tracker and evidence; MBT mirrors that status without duplicating task history. [Development Process](../Development_Process.md) governs execution.

Structure adapted from the user-authorized read-only JARVIS MBT review on `2026-09-23 11:04:44`. JARVIS deployment policies, permissions, priorities and completion claims are not imported.

## Program Tracker

- Status: BP-06 primary active; BP-06.01 through BP-06.05 closed; BP-07 through BP-09 queued; BP-05 closed.
- Last refreshed: `2026-10-03 22:49:16` (America/Chicago).
- Baseline: [Product Requirements](../Architecture/Requirements/Product_Requirements.md), [Master Architecture](../../Architecture.md).
- Current priority: P5 / BP-06 - Knowledge Evidence and Source Loop.
- Primary active task: BP-06.06/Build/B2.02 visible Explore views.
- Next task: BP-06.06/B2.02 visible Explore views.
- Implementation completion: BP-06 **88.54%** ((21+1/4)/24), 21/24 closed delivery gates. BP-06.01 through .05 closed100%; BP-06.06=31.25%. BP-07..09 remain0%.
- Active focus: exact material/sample/observation views, preserving scientific context and immutable Knowledge projections.
- Blockers: none requiring owner direction; future-only corrections and iterative-progress policy approved.
- Acceptance posture: BP-06.01 through .05 bounded software accepted; scientific/deployment gates remain separately scoped.
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
| [BP-06](BP-06%20Knowledge%20Evidence%20and%20Source%20Loop.md) | 88.54% ((21+1/4)/24) | 100% | 100% | 100% | 100% | 100% | 31.25% |

| Active canonical child | Overall | Build | Acceptance | Current task |
|---|---:|---:|---:|---|
| [BP-06.06](BP-06/BP-06.06%20Feedback%20integration%20and%20closeout.md) | 31.25% | 41.67% | 0% | B2.02 / Visible Explore |



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

BP-06 is primary_active at88.54% scoped completion (21/24 closed gates); BP-07 through BP-09 are `design_specified / queued`. The later roadmap has 34 canonical children. Each child names owned objects/contracts, algorithms, failure oracles and replacement acceptance. Completed plans remain in the archive.

| Order / ID | Completion | Proposed plan | Required predecessor gates | Bounded outcome / exit | Architecture owner |
|---|---|---|---|---|---|
| P5 / BP-06 | 88.54% | [Knowledge Evidence and Source Loop](BP-06%20Knowledge%20Evidence%20and%20Source%20Loop.md) | BP-01 contracts; BP-04 execution; BP-05 inspection | Minimal source/document/result ingestion, typed accepted-change replay, pinned knowledge revisions, bounded executable rules and explicit scientific acceptance receipts; demonstrate corrections affect later campaigns | [Knowledge](../Architecture/Knowledge/Knowledge_Architecture.md), [Data](../Architecture/Data/Data_Architecture.md), [experiments](../Architecture/Research/Experiments.md) |
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
| 2026-10-03 22:49:16 | B2.01 complete; child31.25%,parent88.54%; B2.02 active | [Explore model](../Audits/Evidence/BP-06-Feedback/Explore_Page_Model.json);182 source/independent,actual owner model proof |
| 2026-10-03 22:35:26 | B1 complete; child25.00%,parent87.50%; B2.01 active | [Actual integration](../Audits/Evidence/BP-06-Feedback/Integrated_Baseline.json);four installed owners,Qdrant,Runtime replacement,Studio readback |
| 2026-10-03 22:15:08 | B1.04b verified; child20.00%,parent86.67%; B1.05 active | [Studio provenance](../Audits/Evidence/BP-06-Feedback/Studio_Provenance.json);168 source/168 independent,18dev |
| 2026-10-03 21:51:08 | B1.04a verified; child17.50%,parent86.25%; B1.04b active | [Studio transport](../Audits/Evidence/BP-06-Feedback/Studio_Scientific_Transport.json);154 source/154 independent,14 scientific roots |
| 2026-10-03 21:34:15 | B1.03 complete; child15%,parent85.83%; B1.04a active | [Research HTTP](../Audits/Evidence/BP-06-Feedback/Research_Views_HTTP.json);35 source/275 installed,actual replacement |
| 2026-10-03 21:22:59 | B1.03a verified; child12.50%,parent85.42%; B1.03b active | [Research views](../Audits/Evidence/BP-06-Feedback/Research_Views.json);38 source/254 installed,466 schemas |
| 2026-10-03 21:07:50 | B1.02 complete; child10%,parent85%; B1.03a active | [Knowledge HTTP](../Audits/Evidence/BP-06-Feedback/Knowledge_Projection_HTTP.json);56 source/205 installed,actual process replacement |
| 2026-10-03 20:57:09 | B1.02a verified; child7.50%,parent84.58%; B1.02b active | [Projection proof](../Audits/Evidence/BP-06-Feedback/Knowledge_Projection.json);25 pure/174 installed,452 schemas |
| 2026-10-03 20:26:20 | BP-06.06 activated; B1.01 complete,child5%,parent84.17%; B1.02a active | [Scenario protocol](../Audits/Evidence/BP-06-Feedback/Scenario_Manifest.json);30 pure/18 dev,123statements16branches100% |
| 2026-10-03 20:03:23 | BP-06.05 closed100%; parent83.33%,20/24; BP-06.06 audit next | [Closeout](../Audits/BP-06.05_Representation_Retrieval_Closeout.md);649 installed+4 binding cases,11-wheel independent build |
| 2026-10-03 19:47:01 | B3 complete; child75%, parent79.17%; V1a active; gates3/4 and19/24 | [Failure closure](../Audits/Evidence/BP-06-Representations/Failure_Closure.json);158 installed retrieval,18 dev; QD-01 bounded recovery closed |
| 2026-10-03 19:36:53 | B3.02 complete; child66.67%, parent77.78%; B3.03 active | [Live authority](../Audits/Evidence/BP-06-Representations/Live_Authority_Barriers.json);5 source/5 installed actual process races |
| 2026-10-03 19:31:45 | B3.02a complete; child62.50%, parent77.08%; B3.02b active | [Process replay](../Audits/Evidence/BP-06-Representations/Process_Death_Replay.json);8 source/8 installed, actual PostgreSQL/Qdrant |
| 2026-10-03 19:15:58 | B3.01 complete; child58.33%, parent76.39%; B3.02a active | [Adversaries](../Audits/Evidence/BP-06-Representations/Adversarial_Boundaries.json);59 source/59 installed,actual expiry/corruption/publisher oracles |
| 2026-10-03 19:04:12 | B2 complete; child50%, parent75%; B3.01 active; gates2/4 and18/24 | [Installed retrieval HTTP](../Audits/Evidence/BP-06-Representations/Retrieval_HTTP_Replacement.json);source/installed public-only3process reconstruction and authority |
| 2026-10-03 18:56:17 | B2.04b complete; child47.92%, parent74.65%; c active | [Profile migration](../Audits/Evidence/BP-06-Representations/Profile_Migration.json);83 source/83 installed,18 dev;legacy v1 descriptors unchanged |
| 2026-10-03 18:46:24 | B2.04a complete; child45.83%, parent74.31%; b active | [Retrieval API/hosting](../Audits/Evidence/BP-06-Representations/Retrieval_API.json);41 source/41 installed,18 dev;117 statements/26 branches |
| 2026-10-03 18:34:23 | B2.03 complete; child43.75%, parent73.96%; B2.04a active | [Actual query reconstruction](../Audits/Evidence/BP-06-Representations/Qdrant_Query_Replacement.json);source/installed Data processes,actual backend/current-rights proofs |
| 2026-10-03 18:28:11 | B2.03b complete; child41.67%, parent73.61%; c active | [Query broker](../Audits/Evidence/BP-06-Representations/Query_Broker.json);76 source,547 installed plus28 corrected/added checks;36 tables preserved |
| 2026-10-03 18:09:05 | B2.03a complete; child39.58%, parent73.26%; b active | [Query contracts/policy](../Audits/Evidence/BP-06-Representations/Query_Policy.json);98 source/181 installed,18 dev;143 statements/14 branches |
| 2026-10-03 17:51:31 | B2.02 complete; child37.50%, parent72.92%; B2.03a active | [Actual generation replacement](../Audits/Evidence/BP-06-Representations/Qdrant_Generation_Replacement.json);source/installed isolated process and backend replacement,18 dev |
| 2026-10-03 17:41:19 | B2.02b complete; child35.42%, parent72.57%; c active | [Qdrant adapter](../Audits/Evidence/BP-06-Representations/Qdrant_Adapter.json);47 source/131 installed,18 dev; actual exact-vector oracle |
| 2026-10-03 17:20:22 | B2.02a complete; child33.33%, parent72.22%; b active | [Qdrant transport](../Audits/Evidence/BP-06-Representations/Qdrant_Transport.json);33 source/117 installed,18 dev; actual authenticated Qdrant1.19.1 |
| 2026-10-03 17:00:42 | B2.01 complete; child31.25%, parent71.88%; B2.02a active | [Generation publication](../Audits/Evidence/BP-06-Representations/Generation_Publication.json);37 source/508 installed,14 dev;0011 retained history |
| 2026-10-03 16:41:32 | B2.01c complete; child29.69%, parent71.61%; d active | [Generation state](../Audits/Evidence/BP-06-Representations/Generation_State.json);27 source/488 installed,14 dev;0010 retained history |

Keep at most 25 checkpoint rows. [Completed plans](Completed/README.md) remain outside active tables. Update the owning plan first, then this summary and Restore when their state changes.
