# Master Build Tracker

## Purpose and Authority

Program-level source of truth for Amphora v2 build priority, dependency order, current position and delivery gates. Each activated plan owns its detailed canonical phase/task tracker and evidence; MBT mirrors that status without duplicating task history. [Development Process](../Development_Process.md) governs execution.

Structure adapted from the user-authorized read-only JARVIS MBT review on `2026-09-23 11:04:44`. JARVIS deployment policies, permissions, priorities and completion claims are not imported.

## Program Tracker

- Status: BP-07 closed100%; BP-08.02 closed100%; BP-08.03/B2.03b active; BP-09 queued.
- Last refreshed: `2026-10-06 14:40:30` (America/Chicago).
- Baseline: [Product Requirements](../Architecture/Requirements/Product_Requirements.md), [Master Architecture](../../Architecture.md).
- Current priority: P7 / BP-08 - Evolutionary Search Integration.
- Primary active task: BP-08.03/B2.03b.ii synthetic evaluation and producer-proof reuse.
- Next task: BP-08.03/B3 failure/recovery after B2.03.
- Implementation completion: BP-07 closed100%,20/20; BP-08=49.44%,9/20 plus8/9;BP-09=0%.
- Active focus: graph-driven numeric execution; preserve closed BP-07 evaluation history and scoped handoffs.
- Blockers: none for BP-08.03 activation. Selected host and integrated live deployment remain BP-09 decisions/gates.
- Acceptance posture: BP-06 software accepted within synthetic scope; scientific and deployment claims remain separately gated.
- Active exception: none.

Queued successor: [SQ-01 Scientific Quality and Iteration Views](SQ-01%20Scientific%20Quality%20and%20Iteration%20Views.md), 0%, after BP-06 owner projections and BP-07.03 proposal contracts. Preserves closed BP-05; no change to active BP-06 denominator.

## Initial Delivery Boundary

Internal use and demos for the first many releases; one user and one active autonomous campaign, with concurrent tool invocations. Single-server target is DGX Spark or partner Threadripper. Keep the scientific engine general; bio-available polymers are a likely application, not a fixed implementation pathway. Human edits and human-initiated replacements apply between campaigns.

Strictly isolate primary services and independently packaged tools. Use Pydantic/JSON Schema contracts, PostgreSQL-owned state, immutable artifacts, a single Graph Runner execution authority, an indexed tool universe and durable LLM proposals. Module READMEs capture the boundary conditions for independent rebuilds. K3s/Kubernetes tool replication is a proposed deployment profile; cluster selection and installation are not yet authorized implementation work.

The initial program proves software behavior using deterministic/synthetic fixtures and narrowly reviewed v1 reuse. Validated biological/polymer evaluators, real laboratory integration and scientific efficacy require separate evidence and scoped successor work.

## Current In-Flight Work

BP-08.01/.02 closed100%, four deliveries each; parent49.44%,9/20 plus8/9. BP-08.03/B2.03b active, child47.22%, Build62.96%, Acceptance0%.

## Queued Plans and Phase Mirrors

| Canonical plan | Status | Overall | P1 | P2 | P3 | P4 | P5 | P6 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| [BP-08 Evolutionary Search Integration](BP-08%20Evolutionary%20Search%20Integration.md) | Active | 49.44% | 100% | 100% | 47.22% | 0% | 0% | N/A |
| [BP-09 Single-Server Integrated Demo and Replacement Proof](BP-09%20Single-Server%20Integrated%20Demo%20and%20Replacement%20Proof.md) | Design specified | 0% | 0% | 0% | 0% | 0% | 0% | N/A |

Scoped milestone fractions measure verified work within their existing delivery weight; closed-gate counts remain separate. BP-06 is archived24/24. Do not treat milestone counts as effort estimates.

Each parent phase now maps to one canonical child with four verified deliveries (three build plus one acceptance). Parent denominators are BP-03: 16, BP-04: 24, BP-05: 16, BP-06: 24, BP-07: 20, BP-08: 20, BP-09: 20; trackers above own current percentages. N/A means unscoped. [Readiness/handoffs](Planning_Readiness.md) records engineering and external gates. Design writing earns no implementation credit.

The owning plan tracker is canonical for overall and per-phase percentages. Refresh this mirror whenever a gate, scope, completion estimate, blocker or checkpoint changes, before handoff/commit. Percentages measure scoped implementation; acceptance and operational readiness are separate. No in-flight plan may appear here without numeric overall and phase completion.


[BP-01](Completed/BP-01%20Contract%20and%20Service%20Foundations.md) and BP-01A remain complete and archived. The queue below links canonical parents; ordering does not waive child gates. [Planning readiness](Planning_Readiness.md) owns cross-plan dependencies and scoped external decisions.

## Prioritized Build Queue

BP-08.03/B2.03b is current; use the canonical phase mirror above for percentages. Remaining children retain their own prerequisite and acceptance gates.

| Order / ID | Completion | Proposed plan | Required predecessor gates | Bounded outcome / exit | Architecture owner |
|---|---|---|---|---|---|
| P7 / BP-08 | 49.44% | [Evolutionary Search Integration](BP-08%20Evolutionary%20Search%20Integration.md) | BP-04 iteration/checkpoints; BP-06 applicability/evidence; BP-07 for LLM-guided topology | Adapt reusable numerical kernels to explicit generation/checkpoint history, separate representation fixtures and evidence-bound selection; parameter search precedes bounded topology proposals under successor-campaign rules | [Search](../Architecture/Campaigns/Search.md), [reuse baseline](../Architecture/Evolutionary_Code_Reuse_Baseline.md) |
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
| 2026-10-06 14:40:30 | BP-08.03/B2.03b.ii Runtime producer proof verified; percentages unchanged. | 32 checks; read-only canonical-success evidence;606 schemas/604 unchanged. |
| 2026-10-06 14:24:11 | BP-08.03/B2.03b.i complete;child47.22%,Build62.96%,parent49.44%. | 137checks; three public canonicalize capabilities;604schemas/602predecessors unchanged. |
| 2026-10-06 14:15:54 | BP-08.03/B2.03a complete;child45.83%,Build61.11%,parent49.17%. | Isolated actualData/Research fitness,14sources,restart/currentdenial/history;12boundarychecks. |
| 2026-10-06 14:05:50 | BP-08.03/B2.02 complete;child41.67%,Build55.56%,parent48.33%. | 177checks; immutable Research fitness/API,0015;602schemas/590predecessors unchanged. |
| 2026-10-06 13:54:04 | BP-08.03/B2.02a complete;child37.5%,Build50%,parent47.5%. | 184 checks; owner policy composition, explicit unavailable outcomes and exact multi-objective comparison. |
| 2026-10-06 13:46:49 | BP-08.03/B2.01 complete; child33.33%,Build44.44%,parent46.67%. | 60 checks; context-complete identity only,590schemas/584predecessors unchanged. |
| 2026-10-06 13:29:20 | BP-08.03/B1 complete;child25%,Build33.33%,parent45.83%,9/20 plus1/6. | Three isolated operators,70 owner checks,actual Runtime/Data/Research handoff and source denial/history preservation. |
| 2026-10-06 12:48:45 | BP-08.02 closed100%,4/4; parent45.83%,9/20 plus1/6. | Five active Registry profiles, independent Runtime/tool replacements, two recovered campaigns; scoped audit aligned. |
| 2026-10-06 12:17:13 | BP-08.02/V1.01 verified;child81.25%,Acceptance25%,parent36.25%. |Two actual Linuxamd64images,5capabilityprofiles,offlinegolden/isolation/schemahashes. |
| 2026-10-06 12:10:23 | BP-08.02/B3 complete;child75%,Build100%,parent35%,7/20. |Actual killed worker/Runtime restart; identical replay, stale attempt rejected,108confirmedreservationsacrosspair. |
| 2026-10-06 11:52:51 | BP-08.02/B2 complete;child50%,Build66.67%,parent30%,6/20. |Actual independent workers/Runtime/Data;15 invocations,6evaluations,54confirmed retention reservations. |
| 2026-10-06 11:42:43 | BP-08.02/B2.01 complete;child37.5%,Build50%,parent27.5%. |Five Runtime transaction scenarios;79 publication/boundary checks; Data0.30 exact-root-URN repair. |
| 2026-10-06 11:34:01 | BP-08.02/B1 complete; child25%,Build33.33%,parent25%,5/20. |149 compiler+14 graph+12 boundary checks; Runtime0.63 exact-root-URN compatibility; B2 next. |
| 2026-10-06 11:20:45 | BP-08.02/B1.02 complete; child16.67%,Build22.22%,parent23.33%. |169 numeric-adapter checks;144 evaluator/multi-input/legacy-SDK checks; graph/compiler next. |
| 2026-10-06 10:22:13 | BP-08.01 closed100%,4/4;parent20%,4/20. |Two installations133 tests each; retained numeric state/replay; scoped audit aligned. |
| 2026-10-06 10:14:08 | BP-08.01/B2 complete;child50%,Build66.67%,parent10%,2/20. |107checks;two-process128-member replay;duplicates and budget-limited attempts retained. |
| 2026-10-06 10:04:32 | BP-08.01/B2.01 verified; child33.33%, Build44.44%, parent6.67%. | 69 checks; original-spec pins and independently calculated RNG vectors. |
| 2026-10-06 09:56:31 | BP-08.01/B1 complete;child25%,Build33.33%,parent5%,1/20. | Numeric selection30checks;contracts40+20checks;564schemas/556unchanged. |
| 2026-10-06 09:22:33 | BP-07 closed100%,20/20; BP-08 activation next. | v5live12/12pass;twoisolated130-testinstalls;allpriorfailures/costsretained;scoped/parentaudits. |
| 2026-10-06 08:54:13 | BP-07.05 B2 complete; child50%,Build66.67%,parent90%,18/20. B3 active. | v2 live12settled,4pass; original failures retained; v3 correction frozen, all reservations$0.995328/$1. |
| 2026-10-06 08:49:02 | BP-07.05/B2.02 complete;child37.5%,Build50%,parent87.5%. |49offline SQL/boundary checks;12-call corpus frozen;$0.36864 reservation,$1 ceiling. |
| 2026-10-06 08:28:21 | BP-07.05/B2.01 complete;child31.25%,Build41.67%,parent86.25%. | OpenAI adapter80offline tests; no paid calls; initial$1 estimated ceiling. |
| 2026-10-06 04:39:43 | BP-07.05/B1 complete; child25%,Build33.33%,parent85%,17/20. | Studio0.8;237 independent tests; fixture/installed-owner browsers; B2 live choices required. |
| 2026-10-06 04:26:08 | BP-07.05/B1.03 complete; child18.75%,parent83.75%. |33SQL/API/boundary tests;217statements12branches100%;4installed process passes and retained continuation. |
| 2026-10-06 04:04:54 | BP-07.05/B1.03a verified | Public supervision0.10;124tests;556schemas/548unchanged;child14.0625%,parent82.8125%. |
