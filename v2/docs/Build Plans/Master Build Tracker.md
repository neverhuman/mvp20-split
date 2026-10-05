# Master Build Tracker

## Purpose and Authority

Program-level source of truth for Amphora v2 build priority, dependency order, current position and delivery gates. Each activated plan owns its detailed canonical phase/task tracker and evidence; MBT mirrors that status without duplicating task history. [Development Process](../Development_Process.md) governs execution.

Structure adapted from the user-authorized read-only JARVIS MBT review on `2026-09-23 11:04:44`. JARVIS deployment policies, permissions, priorities and completion claims are not imported.

## Program Tracker

- Status: BP-06 closed100%; BP-07 active supervisor contracts; BP-08/09 queued.
- Last refreshed: `2026-10-05 14:21:10` (America/Chicago).
- Baseline: [Product Requirements](../Architecture/Requirements/Product_Requirements.md), [Master Architecture](../../Architecture.md).
- Current priority: P6 / BP-07 - Autonomous LLM Campaign Supervision.
- Primary active task: BP-07.04/B1.02c independent compatibility.
- Next task: BP-07.04/B1.03 durable journal/outbox.
- Implementation completion: BP-07=62.08%,12/20 closed gates; BP-08/09=0%. BP-06 closed24/24.
- Active focus: scoped public supervisor contracts; scope/read-set boundary independently verified.
- Blockers: none for deterministic implementation. Approved declaration publication correction verified; live provider/model, egress and spend choices still govern real calls.
- Acceptance posture: BP-06 software accepted within synthetic scope; scientific and deployment claims remain separately gated.
- Active exception: none.

Queued successor: [SQ-01 Scientific Quality and Iteration Views](SQ-01%20Scientific%20Quality%20and%20Iteration%20Views.md), 0%, after BP-06 owner projections and BP-07.03 proposal contracts. Preserves closed BP-05; no change to active BP-06 denominator.

## Initial Delivery Boundary

Internal use and demos for the first many releases; one user and one active autonomous campaign, with concurrent tool invocations. Single-server target is DGX Spark or partner Threadripper. Keep the scientific engine general; bio-available polymers are a likely application, not a fixed implementation pathway. Human edits and human-initiated replacements apply between campaigns.

Strictly isolate primary services and independently packaged tools. Use Pydantic/JSON Schema contracts, PostgreSQL-owned state, immutable artifacts, a single Graph Runner execution authority, an indexed tool universe and durable LLM proposals. Module READMEs capture the boundary conditions for independent rebuilds. K3s/Kubernetes tool replication is a proposed deployment profile; cluster selection and installation are not yet authorized implementation work.

The initial program proves software behavior using deterministic/synthetic fixtures and narrowly reviewed v1 reuse. Validated biological/polymer evaluators, real laboratory integration and scientific efficacy require separate evidence and scoped successor work.

## Current In-Flight Work

BP-07.01/.02/.03 are closed100%. BP-07.04 is primary active at B1.02c; implementation10.42%,Build13.89%,Acceptance0%.

| Parent | Overall | P1 | P2 | P3 | P4 | P5 |
|---|---:|---:|---:|---:|---:|---:|
| BP-07 | 62.08% | 100% | 100% | 100% | 10.42% | 0% |

| Active child | Overall | Build | Acceptance | Current task |
|---|---:|---:|---:|---|
| [BP-07.04](BP-07/BP-07.04%20Durable%20supervisor%20and%20races.md) | 10.42% | 13.89% | 0% | B1.02c |

 BP-06 is [closed100%](Completed/BP-06%20Knowledge%20Evidence%20and%20Source%20Loop.md); completed parents are in the [archive](Completed/README.md).

## Queued Plans and Phase Mirrors

| Canonical plan | Status | Overall | P1 | P2 | P3 | P4 | P5 | P6 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| [BP-07 Autonomous LLM Campaign Supervision](BP-07%20Autonomous%20LLM%20Campaign%20Supervision.md) | Active | 62.08% | 100% | 100% | 100% | 10.42% | 0% | N/A |
| [BP-08 Evolutionary Search Integration](BP-08%20Evolutionary%20Search%20Integration.md) | Design specified | 0% | 0% | 0% | 0% | 0% | 0% | N/A |
| [BP-09 Single-Server Integrated Demo and Replacement Proof](BP-09%20Single-Server%20Integrated%20Demo%20and%20Replacement%20Proof.md) | Design specified | 0% | 0% | 0% | 0% | 0% | 0% | N/A |

Scoped milestone fractions measure verified work within their existing delivery weight; closed-gate counts remain separate. BP-06 is archived24/24. Do not treat milestone counts as effort estimates.

Each parent phase now maps to one canonical child with four verified deliveries (three build plus one acceptance). Parent denominators are BP-03: 16, BP-04: 24, BP-05: 16, BP-06: 24, BP-07: 20, BP-08: 20, BP-09: 20; trackers above own current percentages. N/A means unscoped. [Readiness/handoffs](Planning_Readiness.md) records engineering and external gates. Design writing earns no implementation credit.

The owning plan tracker is canonical for overall and per-phase percentages. Refresh this mirror whenever a gate, scope, completion estimate, blocker or checkpoint changes, before handoff/commit. Percentages measure scoped implementation; acceptance and operational readiness are separate. No in-flight plan may appear here without numeric overall and phase completion.


[BP-01](Completed/BP-01%20Contract%20and%20Service%20Foundations.md) and BP-01A remain complete and archived. The queue below links canonical parents; ordering does not waive child gates. [Planning readiness](Planning_Readiness.md) owns cross-plan dependencies and scoped external decisions.

## Prioritized Build Queue

BP-07.04/B1.02c is current; use the canonical phase mirror above for percentages. Remaining children retain their own prerequisite and acceptance gates.

| Order / ID | Completion | Proposed plan | Required predecessor gates | Bounded outcome / exit | Architecture owner |
|---|---|---|---|---|---|
| P6 / BP-07 | 62.08% | [Autonomous LLM Campaign Supervision](BP-07%20Autonomous%20LLM%20Campaign%20Supervision.md) | BP-03 tool discovery; BP-04 runner; BP-05 UI; BP-06 grounded context/receipts | Model-generated campaign proposals and text-to-graph extraction through validated contracts; durable scoped engagements, stale-proposal/fallback races, bounded repair and truthful terminal blockers; no routine human waits | [Planning](../Architecture/Agents/Planning.md), [Graph Runner](../Architecture/System/Graph_Runner.md) |
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
| 2026-10-05 14:21:10 | BP-07.04/B1.02b verified |129 combined/42 wire/78 legacy;528schemas;child10.42%,parent62.08%;next independent compatibility. |
| 2026-10-05 14:02:22 | BP-07.04/B1.02a verified |62 scoped/54 legacy-boundary;520schemas;child8.33%,parent61.67%;next response/command profiles. |
| 2026-10-05 13:49:47 | BP-07.04/B1.01 verified |26 scoped/111 installed;child6.25%,parent61.25%;next public supervisor contracts. |
| 2026-10-05 13:36:19 | BP-07.03 closed100% |Scoped audit aligned;child archived4/4,parent60%,12/20;next BP-07.04/B1.01 scope/read-set boundary. |
| 2026-10-05 13:32:31 | BP-07.03/V1.01 verified |1262 isolated/49 replacement cases;child87.5%,parent57.5%;next scoped audit/archive. |
| 2026-10-05 13:19:41 | BP-07.03/B3 complete |300-descriptor scale passes declared budgets;child75%,parent55%,Build100%;next independent closeout. |
| 2026-10-05 13:11:39 | BP-07.03/B3.02 verified |10 actual rights stages/116 installed failure cases;child66.67%,parent53.33%;next catalog scale. |
| 2026-10-05 13:04:28 | BP-07.03/B3.01 verified |7 QEV/405 isolated cases;child58.33%,parent51.67%;next source rights/failure acceptance. |
| 2026-10-05 12:54:52 | BP-07.03/B2 complete | Actual tool compilation;2 worker kills and exact peer restart history. Child50%,parent50%;next B3.01. |
| 2026-10-05 12:38:41 | BP-07.03/B2.03c.iii verified |8 scoped/8 installed SQL+HTTP;child47.92%,parent49.58%. Next actual owners/crash. |
| 2026-10-05 12:23:42 | BP-07.03/B2.03c.ii verified | Bounded progression;36 installed SQL;child47.22%,parent49.44%. Next SQL/HTTP failures. |
| 2026-10-05 12:02:44 | BP-07.03/B2.03c.i verified | Guarded dispatch;23 scoped/23 installed SQL;child46.53%,parent49.31%. Next progression. |
| 2026-10-05 11:33:10 | BP-07.03 compatibility verified | Approved v2 declaration;63 focused/333 isolated/12 SQL;actual Data publication and restart. Next c.i guarded dispatch. |
| 2026-10-05 00:23:06 | BP-07.03/B2.03b.iii verified |41 installed SQL cases;child45.83%,parent49.17%. Next declaration compatibility decision before coordinator. |
| 2026-10-05 00:15:06 | BP-07.03/B2.03b.ii verified | Operation/event journal;36 installed SQL cases. Child45.14%,parent49.03%;next SQL races/replacement. |
| 2026-10-04 23:41:51 | BP-07.03/B2.03b.i verified | Stored origin/selections/leases;14 SQL/26 installed SQL. Child44.44%,parent48.89%;next operation/event journal. |
| 2026-10-04 23:32:44 | BP-07.03/B2.03a.iii verified | Typed outcomes/events;53 scoped/198 installed. Child43.75%,parent48.75%;next owned history/leases. |
| 2026-10-04 23:25:51 | BP-07.03/B2.03a.ii verified | Exact command payloads;33 scoped/178 installed. Child43.06%,parent48.61%;next bounded events. |
| 2026-10-04 23:20:15 | BP-07.03/B2.03a.i verified | One original-attempt selection;18 focused/285 installed. Child42.36%,parent48.47%;next exact effect payloads. |
| 2026-10-04 23:14:22 | BP-07.03/B2.02d verified | Actual Runtime/Registry compatibility across restart/drain. Child41.67%,parent48.33%;next durable handoff values. |
| 2026-10-04 23:08:46 | BP-07.03/B2.02c.iii verified | Stored origin/combined preparation;267 isolated compiler and12 installed SQL. Child39.58%,parent47.92%;next actual-owner compatibility. |
| 2026-10-04 22:49:32 | BP-07.03/B2.02c.ii verified | Current-use/relevant-input refresh;17 focused/435 installed. Child38.89%,parent47.78%;next retained accounting. |
| 2026-10-04 22:32:16 | BP-07.03/B2.02c.i verified | Exact expiring eligibility;29 focused/418 installed. Child38.19%,parent47.64%;next current-use refresh. |
| 2026-10-04 22:20:11 | BP-07.03/B2.02b verified | Bounded compiler exchanges;41 loopback/389 installed cases. Child37.50%,parent47.50%;next eligibility observations. |
| 2026-10-04 22:08:25 | BP-07.03/B2.02a verified | Exact authoring commands/readback;30 focused/348 installed. Child35.42%,parent47.08%;next bounded transport. |

Keep at most25 checkpoint rows. Update the owning plan, this mirror and Restore before commits.
