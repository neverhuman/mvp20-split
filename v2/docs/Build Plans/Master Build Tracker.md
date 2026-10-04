# Master Build Tracker

## Purpose and Authority

Program-level source of truth for Amphora v2 build priority, dependency order, current position and delivery gates. Each activated plan owns its detailed canonical phase/task tracker and evidence; MBT mirrors that status without duplicating task history. [Development Process](../Development_Process.md) governs execution.

Structure adapted from the user-authorized read-only JARVIS MBT review on `2026-09-23 11:04:44`. JARVIS deployment policies, permissions, priorities and completion claims are not imported.

## Program Tracker

- Status: BP-06 closed100%; BP-07 primary active; BP-08/09 queued.
- Last refreshed: `2026-10-04 17:54:48` (America/Chicago).
- Baseline: [Product Requirements](../Architecture/Requirements/Product_Requirements.md), [Master Architecture](../../Architecture.md).
- Current priority: P6 / BP-07 - Autonomous LLM Campaign Supervision.
- Primary active task: BP-07.03/Build/B1.02a.iii actual Research compatibility.
- Next task: BP-07.03/B1.02b Registry/Runtime metadata.
- Implementation completion: BP-07=41.46%,8/20 closed gates; BP-08/09=0%. BP-06 closed24/24.
- Active focus: campaign context selection and immutable binding; completed extraction remains owner-authority bounded.
- Blockers: no owner decision blocks deterministic preparation. Live provider/model, egress and spend require explicit choices before real calls.
- Acceptance posture: BP-06 software accepted within synthetic scope; scientific and deployment claims remain separately gated.
- Active exception: none.

Queued successor: [SQ-01 Scientific Quality and Iteration Views](SQ-01%20Scientific%20Quality%20and%20Iteration%20Views.md), 0%, after BP-06 owner projections and BP-07.03 proposal contracts. Preserves closed BP-05; no change to active BP-06 denominator.

## Initial Delivery Boundary

Internal use and demos for the first many releases; one user and one active autonomous campaign, with concurrent tool invocations. Single-server target is DGX Spark or partner Threadripper. Keep the scientific engine general; bio-available polymers are a likely application, not a fixed implementation pathway. Human edits and human-initiated replacements apply between campaigns.

Strictly isolate primary services and independently packaged tools. Use Pydantic/JSON Schema contracts, PostgreSQL-owned state, immutable artifacts, a single Graph Runner execution authority, an indexed tool universe and durable LLM proposals. Module READMEs capture the boundary conditions for independent rebuilds. K3s/Kubernetes tool replication is a proposed deployment profile; cluster selection and installation are not yet authorized implementation work.

The initial program proves software behavior using deterministic/synthetic fixtures and narrowly reviewed v1 reuse. Validated biological/polymer evaluators, real laboratory integration and scientific efficacy require separate evidence and scoped successor work.

## Current In-Flight Work

BP-07.01/.02 are closed100%. BP-07.03 is primary active; implementation7.29%,Build9.72%,Acceptance0%.

| Parent | Overall | P1 | P2 | P3 | P4 | P5 |
|---|---:|---:|---:|---:|---:|---:|
| BP-07 | 41.46% | 100% | 100% | 7.29% | 0% | 0% |

| Active child | Overall | Build | Acceptance | Current task |
|---|---:|---:|---:|---|
| [BP-07.03](BP-07/BP-07.03%20Campaign%20proposals%20and%20context.md) | 7.29% | 9.72% | 0% | B1.02a.iii |

 BP-06 is [closed100%](Completed/BP-06%20Knowledge%20Evidence%20and%20Source%20Loop.md); completed parents are in the [archive](Completed/README.md).

## Queued Plans and Phase Mirrors

| Canonical plan | Status | Overall | P1 | P2 | P3 | P4 | P5 | P6 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| [BP-07 Autonomous LLM Campaign Supervision](BP-07%20Autonomous%20LLM%20Campaign%20Supervision.md) | Active | 41.46% | 100% | 100% | 7.29% | 0% | 0% | N/A |
| [BP-08 Evolutionary Search Integration](BP-08%20Evolutionary%20Search%20Integration.md) | Design specified | 0% | 0% | 0% | 0% | 0% | 0% | N/A |
| [BP-09 Single-Server Integrated Demo and Replacement Proof](BP-09%20Single-Server%20Integrated%20Demo%20and%20Replacement%20Proof.md) | Design specified | 0% | 0% | 0% | 0% | 0% | 0% | N/A |

Scoped milestone fractions measure verified work within their existing delivery weight; closed-gate counts remain separate. BP-06 is archived24/24. Do not treat milestone counts as effort estimates.

Each parent phase now maps to one canonical child with four verified deliveries (three build plus one acceptance). Parent denominators are BP-03: 16, BP-04: 24, BP-05: 16, BP-06: 24, BP-07: 20, BP-08: 20, BP-09: 20; trackers above own current percentages. N/A means unscoped. [Readiness/handoffs](Planning_Readiness.md) records engineering and external gates. Design writing earns no implementation credit.

The owning plan tracker is canonical for overall and per-phase percentages. Refresh this mirror whenever a gate, scope, completion estimate, blocker or checkpoint changes, before handoff/commit. Percentages measure scoped implementation; acceptance and operational readiness are separate. No in-flight plan may appear here without numeric overall and phase completion.


[BP-01](Completed/BP-01%20Contract%20and%20Service%20Foundations.md) and BP-01A remain complete and archived. The queue below links canonical parents; ordering does not waive child gates. [Planning readiness](Planning_Readiness.md) owns cross-plan dependencies and scoped external decisions.

## Prioritized Build Queue

BP-07.02/V1.02 is current; use the canonical phase mirror above for percentages. Remaining children retain their own prerequisite and acceptance gates.

| Order / ID | Completion | Proposed plan | Required predecessor gates | Bounded outcome / exit | Architecture owner |
|---|---|---|---|---|---|
| P6 / BP-07 | 41.46% | [Autonomous LLM Campaign Supervision](BP-07%20Autonomous%20LLM%20Campaign%20Supervision.md) | BP-03 tool discovery; BP-04 runner; BP-05 UI; BP-06 grounded context/receipts | Model-generated campaign proposals and text-to-graph extraction through validated contracts; durable scoped engagements, stale-proposal/fallback races, bounded repair and truthful terminal blockers; no routine human waits | [Planning](../Architecture/Agents/Planning.md), [Graph Runner](../Architecture/System/Graph_Runner.md) |
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
| 2026-10-04 17:54:48 | BP-07.03/B1.02a.ii verified; child7.29%,parent41.46%; a.iii active | Research_View_Reads.json;85 focused/228 installed; exact pages, legacy transport preserved |
| 2026-10-04 17:41:49 | BP-07.03/B1.02a.i verified; child6.77%,parent41.35%; a.ii active | Research_Record_Reads.json;135 focused/193 installed; old caps preserved, actual owner remains a.iii |
| 2026-10-04 17:28:41 | BP-07.03/B1.01 complete; child6.25%,parent41.25%; B1.02 active | Research_Context_Records.json;64 focused/143 installed,269 statements44 branches100% |
| 2026-10-04 17:18:21 | BP-07.03/B1.01a verified; child3.13%,parent40.63%; B1.01b active | Research_Selection.json;111 source/installed,67 statements8 branches100%;508 schemas |
| 2026-10-04 17:08:34 | BP-07.03 activated0%; parent40%; B1.01a active | [Coherence audit](../Audits/BP-07.03_Activation.md); actual public predecessors, ordered physical milestones |
| 2026-10-04 17:03:06 | BP-07.02 closed100%,4/4; parent40%,8/20; BP-07.03 activation next | [Scoped audit](../Audits/BP-07.02_Text_Decomposition_Closeout.md);930 tests,39 stages,two installs; actual-owner recovery |
| 2026-10-04 17:01:03 | BP-07.02/V1.01 verified; child87.50%,parent37.50%; V1.02 active | Final_Installation.json;930 tests,39 stages,two installs; exact runtime payload match |
| 2026-10-04 16:44:01 | BP-07.02/B3 complete; child75.00%,parent35.00%; V1.01 active | [Process failures](../Audits/Evidence/BP-07-Extraction/Process_Failure_Oracles.json);19 workers/6 owners; real leases and abrupt exits;39 scoped cases |
| 2026-10-04 16:15:15 | BP-07.02/B3.02 complete; child66.67%,parent33.33%; B3.03 active | [Semantic corpus](../Audits/Evidence/BP-07-Extraction/Semantic_Corpus.json);86 scoped/88 per install;54 reviewed synthetic responses, no live quality claim |
| 2026-10-04 15:56:11 | BP-07.02/B3.01 complete; child58.33%,parent31.67%; B3.02 active | [Trace oracles](../Audits/Evidence/BP-07-Extraction/Trace_Oracles.json);136 scoped cases53.24s; existing process evidence explicitly reused |
| 2026-10-04 15:50:14 | BP-07.02/B2 complete; child50.00%,parent30.00%; B3.01 active | [Combined owner acceptance](../Audits/Evidence/BP-07-Extraction/Combined_Owner_Acceptance.json);9 Planning workers/6 owner processes; historical correction rebuild and explicit future pin |
| 2026-10-04 15:27:08 | BP-07.02/B2.03b complete; child47.22%,parent29.44%; B2.03c active | [Owner coordinator](../Audits/Evidence/BP-07-Extraction/Owner_Handoff_Coordinator.json);36 scoped,844 installed39 stages;6 actual Research workers/2 hosts |
| 2026-10-04 14:42:29 | BP-07.02/B2.03b.iii.b complete; child46.91%,parent29.38%; b.iii.c active | [Handoff storage](../Audits/Evidence/BP-07-Extraction/Owner_Handoff_Storage.json);95 scoped,808 installed/39 process stages |
| 2026-10-04 14:10:32 | BP-07.02/B2.03b.iii.a complete; child46.60%,parent29.32%; b.iii.b active | [Handoff values](../Audits/Evidence/BP-07-Extraction/Owner_Handoff_Values.json);47 scoped,776 installed/35 existing replay stages |
| 2026-10-04 13:39:20 | BP-07.02/B2.03b.ii complete; child46.30%,parent29.26%; b.iii active | [Result producer](../Audits/Evidence/BP-07-Extraction/Result_Producer.json);720 installed+9 guards,7 actual workers/2 Data hosts |
| 2026-10-04 11:19:18 | BP-07.02/B2.03b.ii.b complete; child45.99%,parent29.20%; b.ii.c active | [Result workflow](../Audits/Evidence/BP-07-Extraction/Result_Workflow.json);705 installed cases/35 process stages |
| 2026-10-04 10:52:48 | BP-07.02/B2.03b.ii.a complete; child45.68%,parent29.14%; b.ii.b active | [Result storage](../Audits/Evidence/BP-07-Extraction/Result_Storage.json);54 scoped100% coverage,684 installed cases/32 process stages |
| 2026-10-04 10:22:31 | BP-07.02/B2.03b.i complete; child45.37%,parent29.07%; b.ii active | [Result payloads](../Audits/Evidence/BP-07-Extraction/Result_Payloads.json);24 focused100% coverage,654 installed cases/28 process stages |
| 2026-10-04 10:04:40 | BP-07.02/B2.03a.ii complete; child44.44%,parent28.89%; b active | [Research declarations](../Audits/Evidence/BP-07-Extraction/Research_Declarations.json);382 installed cases,2 actual process interruption/replacement stages |
| 2026-10-04 08:01:56 | BP-07.02/B2.02b complete; child38.89%,parent27.78%; c.i active | [Repair admission](../Audits/Evidence/BP-07-Extraction/Repair_Admission.json);588 source,570 installed25 processes; unsettled overage fenced |
| 2026-10-04 07:31:11 | BP-07.02/B2.02a.ii | Actual Research/Knowledge reads verified;560 source,542 installed tests. Child36.11%,parent27.22%; B2.02b active. |
| 2026-10-04 07:07:14 | BP-07.02/B2.02a.i verified; child34.72%,parent26.94%; a.ii active | [Research proposals](../Audits/Evidence/BP-07-Extraction/Research_Proposals.json);542 source,524 installed20 processes,504 predecessor schemas unchanged |
| 2026-10-04 06:45:26 | BP-07.02/B2.01 complete; child33.33%,parent26.67%; B2.02 active | [Knowledge reads](../Audits/Evidence/BP-07-Extraction/Knowledge_Read_Binding.json);497 installed20 processes,8 actual Planning/2 Knowledge hosts |
| 2026-10-04 06:28:33 | BP-07.02/B2.01b verified; child30.56%,parent26.11%; c active | [Proposal validation](../Audits/Evidence/BP-07-Extraction/Proposal_Validation.json);483 source,465 installed20 processes,36 pure cases |
| 2026-10-04 05:57:15 | BP-07.02/B2.01a verified; child27.78%,parent25.56%; b active | [Edit profile](../Audits/Evidence/BP-07-Extraction/Edit_Profile.json);447 source,429 installed20 processes,500 predecessor schemas unchanged |

Keep at most25 checkpoint rows. Update the owning plan, this mirror and Restore before commits.
