# Master Build Tracker

## Purpose and Authority

Program-level source of truth for Amphora v2 build priority, dependency order, current position and delivery gates. Each activated plan owns its detailed canonical phase/task tracker and evidence; MBT mirrors that status without duplicating task history. [Development Process](../Development_Process.md) governs execution.

Structure adapted from the user-authorized read-only JARVIS MBT review on `2026-09-23 11:04:44`. JARVIS deployment policies, permissions, priorities and completion claims are not imported.

## Program Tracker

- Status: BP-06 closed100%; BP-07 primary active; BP-08/09 queued.
- Last refreshed: `2026-10-04 03:01:54` (America/Chicago).
- Baseline: [Product Requirements](../Architecture/Requirements/Product_Requirements.md), [Master Architecture](../../Architecture.md).
- Current priority: P6 / BP-07 - Autonomous LLM Campaign Supervision.
- Primary active task: BP-07.01/Build/B3.03 process-death recovery.
- Next task: BP-07.01/V1.01 final independent verification.
- Implementation completion: BP-07=13.33%,2/20 closed gates; BP-08/09=0%. BP-06 closed24/24.
- Active focus: public model/context/provider contracts and Runtime engagement authority.
- Blockers: no owner decision blocks deterministic preparation. Live provider/model, egress and spend require explicit choices before real calls.
- Acceptance posture: BP-06 software accepted within synthetic scope; scientific and deployment claims remain separately gated.
- Active exception: none.

Queued successor: [SQ-01 Scientific Quality and Iteration Views](SQ-01%20Scientific%20Quality%20and%20Iteration%20Views.md), 0%, after BP-06 owner projections and BP-07.03 proposal contracts. Preserves closed BP-05; no change to active BP-06 denominator.

## Initial Delivery Boundary

Internal use and demos for the first many releases; one user and one active autonomous campaign, with concurrent tool invocations. Single-server target is DGX Spark or partner Threadripper. Keep the scientific engine general; bio-available polymers are a likely application, not a fixed implementation pathway. Human edits and human-initiated replacements apply between campaigns.

Strictly isolate primary services and independently packaged tools. Use Pydantic/JSON Schema contracts, PostgreSQL-owned state, immutable artifacts, a single Graph Runner execution authority, an indexed tool universe and durable LLM proposals. Module READMEs capture the boundary conditions for independent rebuilds. K3s/Kubernetes tool replication is a proposed deployment profile; cluster selection and installation are not yet authorized implementation work.

The initial program proves software behavior using deterministic/synthetic fixtures and narrowly reviewed v1 reuse. Validated biological/polymer evaluators, real laboratory integration and scientific efficacy require separate evidence and scoped successor work.

## Current In-Flight Work

BP-07.01 is primary active; child66.67%,Build88.89%,Acceptance0%.

| Parent | Overall | P1 | P2 | P3 | P4 | P5 |
|---|---:|---:|---:|---:|---:|---:|
| BP-07 | 13.33% | 66.67% | 0% | 0% | 0% | 0% |

| Active child | Overall | Build | Acceptance | Current task |
|---|---:|---:|---:|---|
| [BP-07.01](BP-07/BP-07.01%20Model%20and%20engagement%20contracts.md) | 66.67% | 88.89% | 0% | B3.03 |

 BP-06 is [closed100%](Completed/BP-06%20Knowledge%20Evidence%20and%20Source%20Loop.md); completed parents are in the [archive](Completed/README.md).

## Queued Plans and Phase Mirrors

| Canonical plan | Status | Overall | P1 | P2 | P3 | P4 | P5 | P6 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| [BP-07 Autonomous LLM Campaign Supervision](BP-07%20Autonomous%20LLM%20Campaign%20Supervision.md) | Active | 13.33% | 66.67% | 0% | 0% | 0% | 0% | N/A |
| [BP-08 Evolutionary Search Integration](BP-08%20Evolutionary%20Search%20Integration.md) | Design specified | 0% | 0% | 0% | 0% | 0% | 0% | N/A |
| [BP-09 Single-Server Integrated Demo and Replacement Proof](BP-09%20Single-Server%20Integrated%20Demo%20and%20Replacement%20Proof.md) | Design specified | 0% | 0% | 0% | 0% | 0% | 0% | N/A |

Scoped milestone fractions measure verified work within their existing delivery weight; closed-gate counts remain separate. BP-06 is archived24/24. Do not treat milestone counts as effort estimates.

Each parent phase now maps to one canonical child with four verified deliveries (three build plus one acceptance). Parent denominators are BP-03: 16, BP-04: 24, BP-05: 16, BP-06: 24, BP-07: 20, BP-08: 20, BP-09: 20; trackers above own current percentages. N/A means unscoped. [Readiness/handoffs](Planning_Readiness.md) records engineering and external gates. Design writing earns no implementation credit.

The owning plan tracker is canonical for overall and per-phase percentages. Refresh this mirror whenever a gate, scope, completion estimate, blocker or checkpoint changes, before handoff/commit. Percentages measure scoped implementation; acceptance and operational readiness are separate. No in-flight plan may appear here without numeric overall and phase completion.


[BP-01](Completed/BP-01%20Contract%20and%20Service%20Foundations.md) and BP-01A remain complete and archived. The queue below links canonical parents; ordering does not waive child gates. [Planning readiness](Planning_Readiness.md) owns cross-plan dependencies and scoped external decisions.

## Prioritized Build Queue

BP-07.01/B2.01b is active; BP-07 is5.83%, BP-08/09 remain0%. Remaining children retain their own prerequisite and acceptance gates.

| Order / ID | Completion | Proposed plan | Required predecessor gates | Bounded outcome / exit | Architecture owner |
|---|---|---|---|---|---|
| P6 / BP-07 | 5.83% | [Autonomous LLM Campaign Supervision](BP-07%20Autonomous%20LLM%20Campaign%20Supervision.md) | BP-03 tool discovery; BP-04 runner; BP-05 UI; BP-06 grounded context/receipts | Model-generated campaign proposals and text-to-graph extraction through validated contracts; durable scoped engagements, stale-proposal/fallback races, bounded repair and truthful terminal blockers; no routine human waits | [Planning](../Architecture/Agents/Planning.md), [Graph Runner](../Architecture/System/Graph_Runner.md) |
| P7 / BP-08 | 0% | [Evolutionary Search Integration](BP-08%20Evolutionary%20Search%20Integration.md) | BP-04 iteration/checkpoints; BP-06 applicability/evidence; BP-07 for LLM-guided topology | Adapt reusable numerical kernels to explicit generation/checkpoint history, separate representation fixtures and evidence-bound selection; parameter search precedes bounded topology proposals under successor-campaign rules | [Search](../Architecture/Campaigns/Search.md), [reuse baseline](../Architecture/Evolutionary_Code_Reuse_Baseline.md) |
| P8 / BP-09 | 0% | [Single-Server Integrated Demo and Replacement Proof](BP-09%20Single-Server%20Integrated%20Demo%20and%20Replacement%20Proof.md) | Selected host/model policy; BP-05/06/07 plus BP-08 for evolutionary demo claims | Reproducible target-host deployment, model/tool eligibility, restore/reconciliation, end-to-end autonomous demo and one independently rebuilt/replaced tool; prove replicated workloads if K3s is selected | [Topology](../Architecture/System/Runtime_Topology.md), [tool services](../Architecture/Capabilities/Tool_Services.md) |

This is the default sequencing, not nine permanent file-ownership buckets. Each plan owns a delivery step; later plans may refine earlier contracts with explicit compatibility evidence. BP-01 records packaging constraints early; BP-03 tests tool images/protocols locally. BP-09 integrates target-host operation rather than postponing all deployment design to the end. Synthetic fixtures/receipts stand in for unavailable scientific services until BP-06 and are labeled as such.

## Cross-Plan Milestones

| Milestone | Plans | Done when | Status |
|---|---|---|---|
| M1 ? Replaceable typed foundation | BP-01/02/03 | One standalone tool is discovered and invoked through pinned contracts with durable acceptance and recovery | Synthetic software foundation complete: BP-01/02/03 contracts, durable invocation/recovery and standalone tools accepted |
| M2 ? Inspectable executing graph | BP-04/05 | A user can follow parallel work, joins, failures and evidence in a real running fixture, then author a subsequent campaign | Accepted within synthetic software scope: BP-04 execution/observation and BP-05 Studio closed |
| M3 ? Autonomous evidence-aware campaign | BP-06/07 | Pinned knowledge informs execution; durable LLM proposals are validated; stale or invalid responses cannot corrupt the run | BP-06 evidence/pins accepted; BP-07 supervision pending |
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

[Completed plan index](Completed/README.md) owns the three closed architecture-documentation plans and their audits. They remain complete for their historical scope and do not contribute runtime implementation credit. BP-01/BP-01A/BP-02 are completed implementation foundations; durable graph execution is accepted; scientific readiness remains separately scoped.


## Recent Checkpoints

| Timestamp | Checkpoint | Evidence |
|---|---|---|
| 2026-10-04 02:25:10 | B2.01a complete; child29.17%,parent5.83%; B2.01b active; MBT mirror corrected | [Budget policy](../Audits/Evidence/BP-07-Planning/Budget_Policy.json);40 source/dev,108 installed |
| 2026-10-04 02:17:10 | B1complete; child25%,parent5%; B2.01 active; gates1/4 and1/20 | [Installed journal](../Audits/Evidence/BP-07-Planning/Installed_Journal.json);86 installed,4 processes,2 installs |
| 2026-10-04 02:08:10 | B1.03 complete; child18.75%,parent3.75%; B1.04 active | [Attempt journal](../Audits/Evidence/BP-07-Planning/Attempt_Journal.json);104 tests incl11 actual PostgreSQL cases |
| 2026-10-04 02:00:10 | B1.02 complete; child12.50%,parent2.50%; B1.03 active | [Provider port](../Audits/Evidence/BP-07-Planning/Provider_Port.json);87 source/dev,69 independent;488 schemas |
| 2026-10-04 01:53:10 | BP-07.01/B1.01 complete; child6.25%, parent1.25%; B1.02 active | [Context contracts](../Audits/Evidence/BP-07-Planning/Context_Contracts.json);60 source/dev,42 independent;484 schemas |
| 2026-10-04 01:46:10 | BP-06 closed100%,24/24; BP-07 activation review next | [Parent audit](../Audits/BP-06_Knowledge_Evidence_Closeout.md);six accepted children, actual source/independent consumer proof |
| 2026-10-04 01:42:10 | V1.01 complete; child87.50%, parent97.92%; V1.02 active | [Final verification](../Audits/Evidence/BP-06-Feedback/Final_Verification.json);210.37s,222 independent Studio, real feedback browser |
| 2026-10-04 01:25:10 | B3 complete; child 75%, parent 95.83%; V1.01 active; gates 3/4 and23/24 | [Failure recovery](../Audits/Evidence/BP-06-Feedback/Failure_Recovery.json); 203.38s, 222 clean Studio tests, actual timeout/late/query recovery |
| 2026-10-04 01:18:09 | B3.04a complete; child 71.88%, parent 95.31%; B3.04b active | [Independent reconstruction](../Audits/Evidence/BP-06-Feedback/Independent_Reconstruction.json); 164.81s; 222 clean Studio tests and actual browser |
| 2026-10-04 01:09:35 | B3.03 complete; child 68.75%, parent 94.79%; B3.04 active | [Specimen adversaries](../Audits/Evidence/BP-06-Feedback/Specimen_Adversaries.json); 1 test, 129.50s; actual policy/model/browser and reviewed screenshots |
| 2026-10-04 01:03:42 | B3.02 complete; child62.50%,parent93.75%; B3.03 active | [Correction races](../Audits/Evidence/BP-06-Feedback/Correction_Races.json);1test123.50s, actual competing writers and open wait |
| 2026-10-04 00:56:34 | B3.01 complete; child56.25%,parent92.71%; B3.02 active | [Actual Explore](../Audits/Evidence/BP-06-Feedback/Explore_Actual_Browser.json);1test96.91s, actual owner windows/browser, reviewed screenshots |
| 2026-10-04 00:46:37 | B2 complete; child50%,parent91.67%; B3.01 active; gates2/4 and22/24 | [Owner reuse](../Audits/Evidence/BP-06-Feedback/Scientific_Reuse_Actual.json);actual1test93.51s, exact context and optional quality |
| 2026-10-03 23:17:26 | B2.02 complete; child37.50%,parent89.58%; B2.03 active | [Visible Explore](../Audits/Evidence/BP-06-Feedback/Explore_Visible_Views.json);186 independent,9 browser,actual model,reviewed screenshots |
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

Keep at most 25 checkpoint rows. [Completed plans](Completed/README.md) remain outside active tables. Update the owning plan first, then this summary and Restore when their state changes.
