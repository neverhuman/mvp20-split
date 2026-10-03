# Master Build Tracker

## Purpose and Authority

Program-level source of truth for Amphora v2 build priority, dependency order, current position and delivery gates. Each activated plan owns its detailed canonical phase/task tracker and evidence; MBT mirrors that status without duplicating task history. [Development Process](../Development_Process.md) governs execution.

Structure adapted from the user-authorized read-only JARVIS MBT review on `2026-09-23 11:04:44`. JARVIS deployment policies, permissions, priorities and completion claims are not imported.

## Program Tracker

- Status: BP-06 primary active; BP-07 through BP-09 queued; BP-05 closed.
- Last refreshed: `2026-10-02 19:05:19` (America/Chicago).
- Baseline: [Product Requirements](../Architecture/Requirements/Product_Requirements.md), [Master Architecture](../../Architecture.md).
- Current priority: P5 / BP-06 - Knowledge Evidence and Source Loop.
- Primary active implementation plan / phase / task: BP-06 -> BP-06.03 / Build / B1.
- Current task: BP-06.03/B1.08 immutable assessment store; B1.09 artifact/receipt publication next. B1 milestones7/10 complete; child17.50%.
- Next task: B1.09 publication/receipts after B1.08 store, then B1.10 integrated API. Runtime integration is B3.
- Implementation completion: BP-05 closed100% (16/16); BP-06 at36.25% scoped completion ((8+0.7)/24); closed gates8/24 (33.33%); BP-07..09 remain0%.
- Active focus: BP-06.03/B1 Research assessment; B1 milestones7/10; child17.50%, parent36.25%; closed gates remain0/4 and8/24.
- Blockers: No owner blocker; derived-publication prerequisite accepted.
- Acceptance posture: BP-05 integrated Studio accepted within synthetic software scope; scientific and deployment acceptance remains later.
- Active exception: none.

## Initial Delivery Boundary

Internal use and demos for the first many releases; one user and one active autonomous campaign, with concurrent tool invocations. Single-server target is DGX Spark or partner Threadripper. Keep the scientific engine general; bio-available polymers are a likely application, not a fixed implementation pathway. Human edits and human-initiated replacements apply between campaigns.

Strictly isolate primary services and independently packaged tools. Use Pydantic/JSON Schema contracts, PostgreSQL-owned state, immutable artifacts, a single Graph Runner execution authority, an indexed tool universe and durable LLM proposals. Module READMEs capture the boundary conditions for independent rebuilds. K3s/Kubernetes tool replication is a proposed deployment profile; cluster selection and installation are not yet authorized implementation work.

The initial program proves software behavior using deterministic/synthetic fixtures and narrowly reviewed v1 reuse. Validated biological/polymer evaluators, real laboratory integration and scientific efficacy require separate evidence and scoped successor work.

## Current In-Flight Work

BP-06 is the sole active parent. BP-05 closed16/16; see [completed plans](Completed/README.md).

| Parent | Overall | P1 | P2 | P3 | P4 | P5 | P6 |
|---|---:|---:|---:|---:|---:|---:|---:|
| [BP-06](BP-06%20Knowledge%20Evidence%20and%20Source%20Loop.md) | 36.25% ((8+0.7)/24) | 100% | 100% | 17.50% | 0% | 0% | 0% |

| Active canonical child | Overall | Build | Acceptance | Current task |
|---|---:|---:|---:|---|
| [BP-06.03](BP-06/BP-06.03%20Reasoning%20and%20domain%20receipts.md) | 17.50% | 23.33% | 0% | B1.08 / Durable assessment store |



## Queued Plans and Phase Mirrors

| Canonical plan | Status | Overall | P1 | P2 | P3 | P4 | P5 | P6 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| [BP-07 Autonomous LLM Campaign Supervision](BP-07%20Autonomous%20LLM%20Campaign%20Supervision.md) | Design specified | 0% | 0% | 0% | 0% | 0% | 0% | N/A |
| [BP-08 Evolutionary Search Integration](BP-08%20Evolutionary%20Search%20Integration.md) | Design specified | 0% | 0% | 0% | 0% | 0% | 0% | N/A |
| [BP-09 Single-Server Integrated Demo and Replacement Proof](BP-09%20Single-Server%20Integrated%20Demo%20and%20Replacement%20Proof.md) | Design specified | 0% | 0% | 0% | 0% | 0% | 0% | N/A |

BP-06.03 B1 now credits its verified milestones fractionally:7/10, while closed delivery gates remain0/4. Its canonical table owns the computation; counts are not effort estimates. Other gates retain their existing weights and closure status.

Each parent phase now maps to one canonical child with four verified deliveries (three build plus one acceptance). Parent denominators are BP-03: 16, BP-04: 24, BP-05: 16, BP-06: 24, BP-07: 20, BP-08: 20, BP-09: 20; trackers above own current percentages. N/A means unscoped. [Readiness/handoffs](Planning_Readiness.md) records engineering and external gates. Design writing earns no implementation credit.

The owning plan tracker is canonical for overall and per-phase percentages. Refresh this mirror whenever a gate, scope, completion estimate, blocker or checkpoint changes, before handoff/commit. Percentages measure scoped implementation; acceptance and operational readiness are separate. No in-flight plan may appear here without numeric overall and phase completion.


[BP-01](Completed/BP-01%20Contract%20and%20Service%20Foundations.md) and BP-01A remain complete and archived. The queue below links canonical parents; ordering does not waive child gates. [Planning readiness](Planning_Readiness.md) owns cross-plan dependencies and scoped external decisions.

## Prioritized Build Queue

BP-06 is primary_active at36.25% scoped completion (8/24 closed gates); BP-07 through BP-09 are `design_specified / queued`. The later roadmap has 34 canonical children. Each child names owned objects/contracts, algorithms, failure oracles and replacement acceptance. Completed plans remain in the archive.

| Order / ID | Completion | Proposed plan | Required predecessor gates | Bounded outcome / exit | Architecture owner |
|---|---|---|---|---|---|
| P5 / BP-06 | 36.25% | [Knowledge Evidence and Source Loop](BP-06%20Knowledge%20Evidence%20and%20Source%20Loop.md) | BP-01 contracts; BP-04 execution; BP-05 inspection | Minimal source/document/result ingestion, typed accepted-change replay, pinned knowledge revisions, bounded executable rules and explicit scientific acceptance receipts; demonstrate corrections affect later campaigns | [Knowledge](../Architecture/Knowledge/Knowledge_Architecture.md), [Data](../Architecture/Data/Data_Architecture.md), [experiments](../Architecture/Research/Experiments.md) |
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
| 2026-10-02 19:05:19 | B1.07 complete; B1 7/10, child17.50%, parent36.25%; B1.08 active | [Resolution](../Audits/Evidence/BP-06-Research/Assessment_Resolution.json);374 source/257 installed tests;296 schemas preserve294 |
| 2026-10-02 16:45:56 | B1.07 Data reader partial; B1 6/10, child15%, parent35.83% unchanged | [Reader](../Audits/Evidence/BP-06-Research/Assessment_Reader.json);184 Research/dev tests; actual peers remain |
| 2026-10-02 16:33:50 | B1.06 complete; B1 6/10, child15%, parent35.83%; B1.07 active | [Assessment wire](../Audits/Evidence/BP-06-Research/Assessment_Wire.json);294 source/177 installed tests;286 predecessor schemas preserved |
| 2026-10-02 16:18:15 | Owner-approved milestone accounting: B1 5/10, child12.50%, parent35.42%; closed gates unchanged0/4 and8/24; B1.06 next | [Canonical milestones](BP-06/BP-06.03%20Reasoning%20and%20domain%20receipts.md#canonical-b1-milestones); evidence-backed reclassification only |
| 2026-10-02 14:24:10 | B1 Knowledge publication process recovery verified; Research assessment next; child0/4,parent8/24 | 9 installed kill barriers;4 rebuild regressions;14 dev checks |
| 2026-10-02 14:12:44 | B1 installed publication/replacement verified; process-death proof next; child0/4,parent8/24 | Knowledge0.13.0;981 tests;8 isolated environments |
| 2026-10-02 13:58:34 | B1 production publication verified; installed replacement next; child0/4,parent8/24 | Knowledge0.13.0;305 owner/dev tests;actual three-owner publication |
| 2026-10-02 13:45:00 | B1 atomic publication terminals verified; SDK workflow next; child0/4,parent8/24 | Knowledge0.12.0;knowledge_0006;166 scoped tests |
| 2026-10-02 13:34:04 | B1 durable payload/attempt journal verified; terminal receipts next; child0/4,parent8/24 | Knowledge0.11.0;knowledge_0005;145 scoped tests |
| 2026-10-02 13:03:31 | B1 pure upload-attempt policy verified; durable journal next; child0/4,parent8/24 | 157 publication/SDK/dev tests; no additional migration |
| 2026-10-02 12:53:49 | B1 publication intent/lease store verified; durable attempts next; child0/4,parent8/24 | Knowledge0.10.0;knowledge_0004;110 scoped tests |
| 2026-10-02 12:34:14 | B1 publication contracts/values verified; durable store next; child0/4,parent8/24 | contracts0.6.0;100 tests;286 schemas preserve282 |
| 2026-10-02 12:17:19 | B1 consumed-input projection verified; publication contract/store next; child0/4,parent8/24 | Knowledge0.9.0;99 focused/actual-peer tests;282 schemas unchanged |
| 2026-10-02 12:04:52 | DER-01 closed4/4 (100%); B1 Knowledge publication resumed; child0/4, parent8/24 | [Audit](../Audits/DER-01_Derived_Publication_Closeout.md);712 installed tests,8 isolated installs |
| 2026-10-02 11:44:40 | DER-01 D3 complete3/4 (75%); D4 active; child0/4, parent8/24 | SDK0.2.0;141 Data/SDK tests;94 SDK and26 derivation coverage runs |
| 2026-10-02 11:35:16 | DER-01 D2 complete2/4 (50%); D3 active; child0/4, parent8/24 | Data0.11.0;artifact_0007;266 owner +36 contract/dev tests |
| 2026-10-02 11:14:56 | DER-01 approved; D1 complete1/4 (25%); D2 active; child0/4, parent8/24 | contracts0.2.0;282 schemas preserve272;92 tests |
| 2026-10-02 09:54:48 | DER-01 proposed prerequisite; BP-06.03/B1 awaits owner direction, percentages unchanged | [Decision](BP-06/BP-06.03%20Derived%20publication%20prerequisite.md);1 PostgreSQL probe |
| 2026-10-02 09:39:22 | BP-06.03/B1 Knowledge public/durable boundary verified; child0/4; parent8/24 | [Evidence](../Audits/Evidence/BP-06-Knowledge/Reasoning_Boundary.json);189+62+14 tests |
| 2026-10-01 21:13:35 | BP-06.03/B1 kernel and input binding verified; child0/4; parent8/24 | [Evidence](../Audits/Evidence/BP-06-Knowledge/Reasoning_Kernel.json);161 owner +14 dev tests |
| 2026-10-01 21:01:42 | BP-06.02 closed100%; parent33.33%; successor .03 audit next | [Closeout](../Audits/BP-06.02_Knowledge_Replay_Closeout.md);169+39 installed tests |
| 2026-10-01 20:50:22 | BP-06.02/B3 complete; child75%, parent33.33%; V1 active | [Failure matrix](../Audits/Evidence/BP-06-Knowledge/Failure_Matrix.json);130 owner tests;4 process scenarios |
| 2026-10-01 20:43:08 | BP-06.02/B2 complete; child50%, parent25%; B3 active | [Rebuild proof](../Audits/Evidence/BP-06-Knowledge/Rebuild_Publication.json);122 owner tests;264 schemas |
| 2026-10-01 20:13:10 | BP-06.02/B2 cursor partial; child25%, parent20.83% unchanged | [Cursor proof](../Audits/Evidence/BP-06-Knowledge/Rebuild_Cursor.json);112 owner tests |
| 2026-10-01 20:05:58 | BP-06.02/B1 complete; child25%, parent20.83%; B2 active | [Public API/peer proof](../Audits/Evidence/BP-06-Knowledge/Public_API.json);104 owner tests;260 schemas |

Keep at most 25 checkpoint rows. [Completed plans](Completed/README.md) remain outside active tables. Update the owning plan first, then this summary and Restore when their state changes.