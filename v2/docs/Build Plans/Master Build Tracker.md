# Master Build Tracker

## Purpose and Authority

Program-level source of truth for Amphora v2 build priority, dependency order, current position and delivery gates. Each activated plan owns its detailed canonical phase/task tracker and evidence; MBT mirrors that status without duplicating task history. [Development Process](../Development_Process.md) governs execution.

Structure adapted from the user-authorized read-only JARVIS MBT review on `2026-09-23 11:04:44`. JARVIS deployment policies, permissions, priorities and completion claims are not imported.

## Program Tracker

- Status: BP-06 closed100%; BP-07 implementing approved B2 checkpoint correction; BP-08/09 queued.
- Last refreshed: `2026-10-05 23:44:42` (America/Chicago).
- Baseline: [Product Requirements](../Architecture/Requirements/Product_Requirements.md), [Master Architecture](../../Architecture.md).
- Current priority: P6 / BP-07 - Autonomous LLM Campaign Supervision.
- Primary active task: BP-07.04/B2.03b.iii.iii capture network workflow.
- Next task: BP-07.04/B2.03 autonomous delivery/repair/fallback.
- Implementation completion: BP-07=69.38%,13/20 closed gates; BP-08/09=0%. BP-06 closed24/24.
- Active focus: B1 verified and pushed; approved scalar target correction in implementation.
- Blockers: none for deterministic implementation. Approved B2.01 correction: scalar adjustments must reconcile Artifact-only Invoke inputs; see [scalar checkpoint decision](BP-07/BP-07.04%20Scalar%20checkpoint%20decision.md). Live provider/model, egress and spend choices separately govern real calls.
- Acceptance posture: BP-06 software accepted within synthetic scope; scientific and deployment claims remain separately gated.
- Active exception: none.

Queued successor: [SQ-01 Scientific Quality and Iteration Views](SQ-01%20Scientific%20Quality%20and%20Iteration%20Views.md), 0%, after BP-06 owner projections and BP-07.03 proposal contracts. Preserves closed BP-05; no change to active BP-06 denominator.

## Initial Delivery Boundary

Internal use and demos for the first many releases; one user and one active autonomous campaign, with concurrent tool invocations. Single-server target is DGX Spark or partner Threadripper. Keep the scientific engine general; bio-available polymers are a likely application, not a fixed implementation pathway. Human edits and human-initiated replacements apply between campaigns.

Strictly isolate primary services and independently packaged tools. Use Pydantic/JSON Schema contracts, PostgreSQL-owned state, immutable artifacts, a single Graph Runner execution authority, an indexed tool universe and durable LLM proposals. Module READMEs capture the boundary conditions for independent rebuilds. K3s/Kubernetes tool replication is a proposed deployment profile; cluster selection and installation are not yet authorized implementation work.

The initial program proves software behavior using deterministic/synthetic fixtures and narrowly reviewed v1 reuse. Validated biological/polymer evaluators, real laboratory integration and scientific efficacy require separate evidence and scoped successor work.

## Current In-Flight Work

BP-07.01/.02/.03 are closed100%. BP-07.04 is primary active at B2.03b.iii.iii; implementation46.91%,Build62.55%,Acceptance0%.

| Parent | Overall | P1 | P2 | P3 | P4 | P5 |
|---|---:|---:|---:|---:|---:|---:|
| BP-07 | 69.38% | 100% | 100% | 100% | 46.91% | 0% |

| Active child | Overall | Build | Acceptance | Current task |
|---|---:|---:|---:|---|
| [BP-07.04](BP-07/BP-07.04%20Durable%20supervisor%20and%20races.md) | 46.91% | 62.55% | 0% | B2.03b.iii.iii |

 BP-06 is [closed100%](Completed/BP-06%20Knowledge%20Evidence%20and%20Source%20Loop.md); completed parents are in the [archive](Completed/README.md).

## Queued Plans and Phase Mirrors

| Canonical plan | Status | Overall | P1 | P2 | P3 | P4 | P5 | P6 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| [BP-07 Autonomous LLM Campaign Supervision](BP-07%20Autonomous%20LLM%20Campaign%20Supervision.md) | Active | 69.38% | 100% | 100% | 100% | 46.91% | 0% | N/A |
| [BP-08 Evolutionary Search Integration](BP-08%20Evolutionary%20Search%20Integration.md) | Design specified | 0% | 0% | 0% | 0% | 0% | 0% | N/A |
| [BP-09 Single-Server Integrated Demo and Replacement Proof](BP-09%20Single-Server%20Integrated%20Demo%20and%20Replacement%20Proof.md) | Design specified | 0% | 0% | 0% | 0% | 0% | 0% | N/A |

Scoped milestone fractions measure verified work within their existing delivery weight; closed-gate counts remain separate. BP-06 is archived24/24. Do not treat milestone counts as effort estimates.

Each parent phase now maps to one canonical child with four verified deliveries (three build plus one acceptance). Parent denominators are BP-03: 16, BP-04: 24, BP-05: 16, BP-06: 24, BP-07: 20, BP-08: 20, BP-09: 20; trackers above own current percentages. N/A means unscoped. [Readiness/handoffs](Planning_Readiness.md) records engineering and external gates. Design writing earns no implementation credit.

The owning plan tracker is canonical for overall and per-phase percentages. Refresh this mirror whenever a gate, scope, completion estimate, blocker or checkpoint changes, before handoff/commit. Percentages measure scoped implementation; acceptance and operational readiness are separate. No in-flight plan may appear here without numeric overall and phase completion.


[BP-01](Completed/BP-01%20Contract%20and%20Service%20Foundations.md) and BP-01A remain complete and archived. The queue below links canonical parents; ordering does not waive child gates. [Planning readiness](Planning_Readiness.md) owns cross-plan dependencies and scoped external decisions.

## Prioritized Build Queue

BP-07.04/B2.03b.iii.iii is current; use the canonical phase mirror above for percentages. Remaining children retain their own prerequisite and acceptance gates.

| Order / ID | Completion | Proposed plan | Required predecessor gates | Bounded outcome / exit | Architecture owner |
|---|---|---|---|---|---|
| P6 / BP-07 | 69.38% | [Autonomous LLM Campaign Supervision](BP-07%20Autonomous%20LLM%20Campaign%20Supervision.md) | BP-03 tool discovery; BP-04 runner; BP-05 UI; BP-06 grounded context/receipts | Model-generated campaign proposals and text-to-graph extraction through validated contracts; durable scoped engagements, stale-proposal/fallback races, bounded repair and truthful terminal blockers; no routine human waits | [Planning](../Architecture/Agents/Planning.md), [Graph Runner](../Architecture/System/Graph_Runner.md) |
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
| 2026-10-05 23:44:42 | BP-07.04 capture journal complete | Planning0.83/0017 immutable upload/response, fences/rollback/replay;7SQL396statements24branches100%+75regression. |
| 2026-10-05 23:31:16 | BP-07.04 capture domain verified | Planning0.82 exact primary/late bytes, ancestry and response;7cases104statements2branches100%;18expiry/boundary checks. |
| 2026-10-05 23:06:40 | BP-07.04/B2.03b.ii complete | Planning0.81 original packet, fresh rights, absolute deadline and history-first recovery;126 scoped+12 boundary tests. |
| 2026-10-05 22:56:16 | BP-07.04/B2.03b.i verified | Planning0.80 acyclic template/exact context;72tests131statements4branches100%;original ledger policy bytes unchanged. |
| 2026-10-05 22:47:15 | BP-07.04/B2.03a complete | Actual Data publication,7processing reads,restart;94scoped+11commit-race checks;next Planning execution. |
| 2026-10-05 22:32:48 | BP-07.04 context projection verified | 109 contract/context/schema/boundary cases;115 context statements4branches100%;544schemas preserve542;actual publication bridge next. |
| 2026-10-05 22:22:33 | BP-07.04/B2.03a.ii complete | Runtime0.48/runtime0026 atomic request/outbox/call reservation;155 regression+61 refined checks;next actual context preparation. |
| 2026-10-05 22:13:13 | BP-07.04 recipe admission verified | Runtime0.47/runtime0025;120 scoped cases and8 corruption/pin checks;immutable recipe retained before frontier;reservation SQL next. |
| 2026-10-05 22:08:16 | BP-07.04/B2.03a.i verified | Immutable recipe and conservative call reservations;27 pure cases,84 statements/4 branches100%;next SQL binding. |
| 2026-10-05 21:55:23 | BP-07.04/B2.02 complete |Selected fields reach conversion without changing plan;86 scoped+18 relocation checks;child41.67%,parent68.33%;next autonomous loop. |
| 2026-10-05 21:47:39 | BP-07.04/B2.02c complete |Committed review/fallback gates frontier;25SQL+16release/boundary;child39.58%,parent67.92%;next conversion. |
| 2026-10-05 21:43:41 | BP-07.04/B2.02c.i verified |Atomic winner/audit/effect rollback and replay;164 cases;child38.54%,parent67.71%;next coordinator release. |
| 2026-10-05 21:32:22 | BP-07.04/B2.02b verified |Explicit effect profiles;336 scoped and1056 installed cases;child37.50%,parent67.50%;next atomic winner. |
| 2026-10-05 21:17:04 | BP-07.04/B2.02a verified |Exact scalar selection/replay;70 cases;child35.42%,parent67.08%;next versioned exchange. |
| 2026-10-05 21:11:53 | BP-07.04/B2.01 complete |Selected freshness/issuance/membership fences pass local and isolated SQL;child33.33%,parent66.67%;next B2.02. |
| 2026-10-05 20:55:37 | BP-07.04/B2.01d.a verified |802 isolated cases;42/32 prior migrations unchanged;child31.94%,parent66.39%;next process barriers. |
| 2026-10-05 20:49:33 | BP-07.04/B2.01c complete |111 coordinator/70 scalar/18 legacy cases;child31.25%,parent66.25%;next independent verification. |
| 2026-10-05 20:41:28 | BP-07.04/B2.01c.iii.b verified |146 SQL/12 boundary cases;runtime0023;child31.02%,parent66.20%;next coordinator creation. |
| 2026-10-05 20:36:30 | BP-07.04/B2.01c.iii.a verified |84 cases;68 new statements100%;child30.79%,parent66.16%;next slot storage. |
| 2026-10-05 20:32:40 | BP-07.04/B2.01c.ii complete |80 scoped/22 compatibility cases;child30.56%,parent66.11%;next concrete checkpoints. |
| 2026-10-05 20:27:27 | BP-07.04/B2.01c.ii.b verified |63 cases;runtime0022 immutable pins;child30.32%,parent66.06%;next admission integration. |
| 2026-10-05 20:23:57 | BP-07.04/B2.01c.ii.a verified |132 cases;538 schemas preserve536;child30.09%,parent66.02%;next atomic pin storage. |
| 2026-10-05 20:19:49 | BP-07.04/B2.01c.i verified |111 cases;171 statements26 branches100%;child29.86%,parent65.97%;next atomic pinning. |
| 2026-10-05 20:04:57 | BP-07.04/B2.01b complete |668 installed cases;11 actual-owner stages/6 hosts/2 lost replies;child29.17%,parent65.83%;next admission pinning. |
| 2026-10-05 19:24:50 | BP-07.04/B2.01a verified | Approved correction;66 scope/request and34 target/boundary cases;child27.08%,parent65.42%;next versioned exchange. |

Keep at most25 checkpoint rows. Update the owning plan, this mirror and Restore before commits.
