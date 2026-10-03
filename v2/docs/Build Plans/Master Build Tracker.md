# Master Build Tracker

## Purpose and Authority

Program-level source of truth for Amphora v2 build priority, dependency order, current position and delivery gates. Each activated plan owns its detailed canonical phase/task tracker and evidence; MBT mirrors that status without duplicating task history. [Development Process](../Development_Process.md) governs execution.

Structure adapted from the user-authorized read-only JARVIS MBT review on `2026-09-23 11:04:44`. JARVIS deployment policies, permissions, priorities and completion claims are not imported.

## Program Tracker

- Status: BP-06 primary active; BP-06.03 closed; BP-07 through BP-09 queued; BP-05 closed.
- Last refreshed: `2026-10-03 04:47:00` (America/Chicago).
- Baseline: [Product Requirements](../Architecture/Requirements/Product_Requirements.md), [Master Architecture](../../Architecture.md).
- Current priority: P5 / BP-06 - Knowledge Evidence and Source Loop.
- Primary active task: BP-06.04/Build/B2.03b pinned intents/results; B2.03a public projections complete.
- Next task: BP-06.04/B2 persistence and authenticated normalization/correction integration.
- Implementation completion: BP-06 **56.60%** ((12+1+(2+1/3)/4)/24),13/24 closed delivery gates. BP-06.01/.02/.03 closed100%; BP-06.04 at39.58%, later children0%. BP-07..09 remain0%.
- Active focus: laboratory returns/material-state/candidate eligibility boundary reconciliation.
- Blockers: none requiring owner direction; future-only corrections and iterative-progress policy approved.
- Acceptance posture: BP-06.03 bounded synthetic software accepted; scientific/deployment gates remain separately scoped.
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
| [BP-06](BP-06%20Knowledge%20Evidence%20and%20Source%20Loop.md) | 56.60% ((12+1+(2+1/3)/4)/24) | 100% | 100% | 100% | 39.58% | 0% | 0% |

| Active canonical child | Overall | Build | Acceptance | Current task |
|---|---:|---:|---:|---|
| [BP-06.04](BP-06/BP-06.04%20Laboratory%20returns%20and%20candidate%20eligibility.md) | 39.58% | 52.78% | 0% | B2.03b / Durable interpretations |



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

BP-06 is primary_active at56.60% scoped completion (13/24 closed gates); BP-07 through BP-09 are `design_specified / queued`. The later roadmap has 34 canonical children. Each child names owned objects/contracts, algorithms, failure oracles and replacement acceptance. Completed plans remain in the archive.

| Order / ID | Completion | Proposed plan | Required predecessor gates | Bounded outcome / exit | Architecture owner |
|---|---|---|---|---|---|
| P5 / BP-06 | 56.60% | [Knowledge Evidence and Source Loop](BP-06%20Knowledge%20Evidence%20and%20Source%20Loop.md) | BP-01 contracts; BP-04 execution; BP-05 inspection | Minimal source/document/result ingestion, typed accepted-change replay, pinned knowledge revisions, bounded executable rules and explicit scientific acceptance receipts; demonstrate corrections affect later campaigns | [Knowledge](../Architecture/Knowledge/Knowledge_Architecture.md), [Data](../Architecture/Data/Data_Architecture.md), [experiments](../Architecture/Research/Experiments.md) |
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
| 2026-10-03 04:47:00 | B2.03a complete; child39.58%, parent56.60%; B2.03b active | [Interpretation contracts](../Audits/Evidence/BP-06-Research/Interpretation_Contracts.json);674 source/674 installed,119 compatibility/dev;392 schemas |
| 2026-10-03 04:24:09 | BP-06.04/B2.02 complete; child37.50%, parent56.25%; B2.03 active | [Use/correction policies](../Audits/Evidence/BP-06-Research/Observation_Use_Policies.json);647 source/647 installed,14 dev |
| 2026-10-03 04:08:02 | BP-06.04/B2.01 complete; child31.25%, parent55.21%; B2.02 active | [Exact normalization](../Audits/Evidence/BP-06-Research/Exact_Normalization.json);633 source/633 installed,14 dev; original evidence preserved |
| 2026-10-03 03:53:36 | BP-06.04/B1 complete; child25%, parent54.17%; B2 active; gates1/4 and13/24 | [Actual scientific HTTP](../Audits/Evidence/BP-06-Research/Scientific_HTTP_Replacement.json); source/installed workflow, independent replacement/offline history |
| 2026-10-03 03:42:21 | BP-06.04/B1.08c complete; child24.22%, parent54.04%; d active | [Scientific hosting](../Audits/Evidence/BP-06-Research/Scientific_Hosting.json);827 source/827 installed,119 compatibility/dev |
| 2026-10-03 03:23:00 | BP-06.04/B1.08b complete; child23.44%, parent53.91%; c active | [Input orchestration](../Audits/Evidence/BP-06-Research/Scientific_Input_Orchestration.json);792 source/792 installed,119 compatibility/dev |
| 2026-10-03 02:52:45 | BP-06.04/B1.08a complete; child22.66%, parent53.78%; B1.08b active | [API contracts](../Audits/Evidence/BP-06-Research/Scientific_API_Contracts.json);758 source/758 installed,119 compatibility/dev;376 schemas preserve352 |
| 2026-10-03 02:32:17 | BP-06.04/B1.07 complete; child21.88%, parent53.65%; B1.08 active | [Scientific publication](../Audits/Evidence/BP-06-Research/Scientific_Artifact_Publication.json);717 source/717 installed,14 dev; actual Data Artifact-only output |
| 2026-10-03 02:09:43 | BP-06.04/B1.07b complete; child20.83%, parent53.47%; B1.07c active | [Decision stores](../Audits/Evidence/BP-06-Research/Scientific_Decision_Stores.json);656 source/656 installed,119 compatibility/dev; exact dependencies/impact/consumers |
| 2026-10-03 01:48:18 | BP-06.04/B1.07a complete; child19.79%, parent53.30%; B1.07b active | [Intake storage](../Audits/Evidence/BP-06-Research/Lab_Intake_Storage.json);619 source/619 installed,119 compatibility/dev; atomic batch/replay/grants |
| 2026-10-03 01:20:14 | BP-06.04/B1.06 complete; child18.75%, parent53.13%; B1.07 active | [Lab resolution](../Audits/Evidence/BP-06-Research/Lab_Report_Resolution.json);592 source/592 installed,119 compatibility/dev; actual Data auth/rights/outage |
| 2026-10-03 00:53:51 | BP-06.04/B1.05 complete; child15.63%, parent52.60%; B1.06 active | [Scientific stores](../Audits/Evidence/BP-06-Research/Scientific_Revision_Stores.json);552 source/552 installed,14 dev; PostgreSQL replay/links/grants |
| 2026-10-03 00:33:49 | BP-06.04/B1.04 complete; child12.50%, parent52.08%; B1.05 active | [Public documents](../Audits/Evidence/BP-06-Research/Scientific_Documents.json);458 source/458 installed,119 compatibility/dev;330 schemas preserve316 |
| 2026-10-03 00:13:55 | BP-06.04/B1.03 complete; child9.38%, parent51.56%; B1.04 active | [Purpose-bound policies](../Audits/Evidence/BP-06-Research/Synthesis_Eligibility_Policies.json);339 source/339 installed,898 statements/154 branches |
| 2026-10-02 23:58:49 | BP-06.04/B1.02 complete; child6.25%, parent51.04%; B1.03 active | [Context objects](../Audits/Evidence/BP-06-Research/Material_Experiment_Observation.json);236 source/236 installed,551 statements/110 branches |
| 2026-10-02 23:32:30 | BP-06.04/B1.01 complete; child3.13%, parent50.52%; B1.02 active | [Measurement values](../Audits/Evidence/BP-06-Research/Measurement_Values.json);97 source/97 installed,143 statements/48 branches |
| 2026-10-02 23:07:47 | BP-06.03 closed100%; BP-06 parent50%; .04 activation next | [Scoped audit](../Audits/BP-06.03_Reasoning_Receipts_Closeout.md);9 Research kill barriers, independent replacement, schema/isolation |
| 2026-10-02 22:49:43 | B3 complete; child75%, parent45.83%; V1 active | [Receipt recovery](../Audits/Evidence/BP-06-Research/Domain_Receipt_Recovery.json); both real owners, acknowledgement loss/replacement/exact retention |
| 2026-10-02 22:33:01 | B3.02 complete; child66.67%, parent44.44%; B3.03 active | [Partial progress](../Audits/Evidence/BP-06-Research/Partial_Campaign_Progress.json); retained report/two gaps;333 installed + clean rerun1 |
| 2026-10-02 22:08:29 | B3.01 complete; child58.33%, parent43.06%; B3.02 active | [Runtime domain receipts](../Audits/Evidence/BP-06-Research/Runtime_Domain_Receipts.json);334 installed; actual protection/confirmation/replacement |
| 2026-10-02 21:50:54 | B2 complete; child50%, parent41.67%; B3.01 active; gates2/4 and10/24 | [Actual corrections](../Audits/Evidence/BP-06-Research/Receipt_Correction_Transitions.json);334 installed +3 Runtime predicate tests |
| 2026-10-02 21:40:59 | B2.03 complete; B2 75%, child43.75%, parent40.63%; B2.04 active | [Knowledge corrections](../Audits/Evidence/BP-06-Knowledge/Receipt_Correction_Store_API.json);393+4 source/186 installed;316 schemas |
| 2026-10-02 21:29:29 | B2.02 complete; B2 50%, child37.50%, parent39.58%; B2.03 active | [Correction store/API](../Audits/Evidence/BP-06-Research/Receipt_Correction_Store_API.json);441 source/334 installed;312 schemas |
| 2026-10-02 21:09:13 | Owner chose future-campaign-only corrections; B2.01 active; progress unchanged | [Implementation](BP-06/BP-06.03%20Receipt%20correction%20implementation.md); active pins preserved |
| 2026-10-02 20:50:17 | B2 awaits receipt invalidation policy choice; B1 complete; child25%, parent37.50% unchanged | [Decision](BP-06/BP-06.03%20Receipt%20invalidation%20decision.md);2 boundary probes pass |

Keep at most 25 checkpoint rows. [Completed plans](Completed/README.md) remain outside active tables. Update the owning plan first, then this summary and Restore when their state changes.
