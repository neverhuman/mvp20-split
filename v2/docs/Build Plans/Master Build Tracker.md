# Master Build Tracker

## Purpose and Authority

Program-level source of truth for Amphora v2 build priority, dependency order, current position and delivery gates. Each activated plan owns its detailed canonical phase/task tracker and evidence; MBT mirrors that status without duplicating task history. [Development Process](../Development_Process.md) governs execution.

Structure adapted from the user-authorized read-only JARVIS MBT review on `2026-09-23 11:04:44`. JARVIS deployment policies, permissions, priorities and completion claims are not imported.

## Program Tracker

- Status: BP-04 primary active; BP-05 through BP-09 queued; BP-01/BP-01A/BP-02/BP-03 closed.
- Last refreshed: `2026-09-29 15:52:36` (America/Chicago).
- Baseline: [Product Requirements](../Architecture/Requirements/Product_Requirements.md), [Master Architecture](../../Architecture.md).
- Current priority: P3 / BP-04 - deterministic graph runner.
- Primary active implementation plan / phase / task: BP-04 -> BP-04.04A / Build / B3.
- Current task: BP-04.04A/B3 actual process failure/concurrency proof; B1/B2 verified.
- Next task: BP-04.04A/V1 installed peer/replacement proof; .04 follows .04A acceptance, then .05.
- Implementation completion: BP-02 closed 100% (32/32), BP-03 closed 100% (16/16); BP-04 active 58.33% (14/24), .01/.02/.03 closed 100%; .04A active 50% (Build 66.67%/Acceptance 0%); .04/.05 and BP-05..09 queued 0%.
- Active focus: owner-approved BIND-01 remediation; new four-delivery prerequisite activates before solver parity. All completed credit preserved under 24-delivery denominator.
- Blockers: none for active prerequisite; scientific/target-host choices remain at their named later gates.
- Acceptance posture: scheduling, aggregation/waits, actual process and installed issuer/Artifact replacement accepted. Solver parity awaits BIND-01 resolution; scientific/target-host claims remain later gates.
- Active exception: none.

## Initial Delivery Boundary

Internal use and demos for the first many releases; one user and one active autonomous campaign, with concurrent tool invocations. Single-server target is DGX Spark or partner Threadripper. Keep the scientific engine general; bio-available polymers are a likely application, not a fixed implementation pathway. Human edits and human-initiated replacements apply between campaigns.

Strictly isolate primary services and independently packaged tools. Use Pydantic/JSON Schema contracts, PostgreSQL-owned state, immutable artifacts, a single Graph Runner execution authority, an indexed tool universe and durable LLM proposals. Module READMEs capture the boundary conditions for independent rebuilds. K3s/Kubernetes tool replication is a proposed deployment profile; cluster selection and installation are not yet authorized implementation work.

The initial program proves software behavior using deterministic/synthetic fixtures and narrowly reviewed v1 reuse. Validated biological/polymer evaluators, real laboratory integration and scientific efficacy require separate evidence and scoped successor work.

## Current In-Flight Work

BP-04 is the sole primary active plan. Child trackers own delivery evidence; completed plans remain in the archive.

| Parent | Implementation | P1 Compiler | P2 Scheduling | P3 Aggregation | P4 Bindings | P5 Baselines | P6 Recovery |
|---|---:|---:|---:|---:|---:|---:|---:|
| [BP-04](BP-04%20Deterministic%20Graph%20Runner.md) | 58.33% (14/24) | 100% | 100% | 100% | 50% | 0% | 0% |

| Active canonical child | Overall | Build | Acceptance | Current task |
|---|---:|---:|---:|---|
| [BP-04.04A](BP-04/BP-04.04A%20Typed%20artifact%20and%20collection%20bindings.md) | 50% | 66.67% | 0% | B3 process proof |

BP-02 is closed at 32/32; BP-03 at 16/16 with all children audited. See [completed plans](Completed/README.md). New parent progress counts only its own deliveries.

## Queued Plans and Phase Mirrors

| Canonical plan | Status | Overall | P1 | P2 | P3 | P4 | P5 | P6 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| [BP-05 Graph Studio First Vertical Slice](BP-05%20Graph%20Studio%20First%20Vertical%20Slice.md) | Design specified | 0% | 0% | 0% | 0% | 0% | N/A | N/A |
| [BP-06 Knowledge Evidence and Source Loop](BP-06%20Knowledge%20Evidence%20and%20Source%20Loop.md) | Design specified | 0% | 0% | 0% | 0% | 0% | 0% | 0% |
| [BP-07 Autonomous LLM Campaign Supervision](BP-07%20Autonomous%20LLM%20Campaign%20Supervision.md) | Design specified | 0% | 0% | 0% | 0% | 0% | 0% | N/A |
| [BP-08 Evolutionary Search Integration](BP-08%20Evolutionary%20Search%20Integration.md) | Design specified | 0% | 0% | 0% | 0% | 0% | 0% | N/A |
| [BP-09 Single-Server Integrated Demo and Replacement Proof](BP-09%20Single-Server%20Integrated%20Demo%20and%20Replacement%20Proof.md) | Design specified | 0% | 0% | 0% | 0% | 0% | 0% | N/A |

Each parent phase now maps to one canonical child with four verified deliveries (three build plus one acceptance). Parent denominators are BP-03: 16, BP-04: 24, BP-05: 16, BP-06: 24, BP-07: 20, BP-08: 20, BP-09: 20; trackers above own current percentages. N/A means unscoped. [Readiness/handoffs](Planning_Readiness.md) records engineering and external gates. Design writing earns no implementation credit.

The owning plan tracker is canonical for overall and per-phase percentages. Refresh this mirror whenever a gate, scope, completion estimate, blocker or checkpoint changes, before handoff/commit. Percentages measure scoped implementation; acceptance and operational readiness are separate. No in-flight plan may appear here without numeric overall and phase completion.


[BP-01](Completed/BP-01%20Contract%20and%20Service%20Foundations.md) and BP-01A remain complete and archived. The queue below links canonical parents; ordering does not waive child gates. [Planning readiness](Planning_Readiness.md) owns cross-plan dependencies and scoped external decisions.

## Prioritized Build Queue

BP-04 is `primary_active`; BP-05 through BP-09 are `design_specified / queued`. The later roadmap has 34 canonical children. Each child names owned objects/contracts, algorithms, failure oracles and replacement acceptance. Completed plans remain in the archive.

| Order / ID | Completion | Proposed plan | Required predecessor gates | Bounded outcome / exit | Architecture owner |
|---|---|---|---|---|---|
| P3 / BP-04 | 40% | [Deterministic Graph Runner](BP-04%20Deterministic%20Graph%20Runner.md) | BP-02 durable state; BP-03 callable tools | Compile and execute typed branch/join/scatter/loop graphs; aggregate committed results; handle scoped failures, external waits, restart and successor campaigns with no LLM required for deterministic control; pass the source-derived v1 solver orchestration scenarios using synthetic adapters | [Graph Runner](../Architecture/System/Graph_Runner.md), [execution model](../Architecture/System/Graph_Execution_Model.md) |
| P4 / BP-05 | 0% | [Graph Studio First Vertical Slice](BP-05%20Graph%20Studio%20First%20Vertical%20Slice.md) | BP-04 runnable fixture and read/command contracts | Inspect actual live/historical execution, evidence, parallel branches and failures; edit next-campaign drafts, compare revisions and observe emergency termination; preserve autonomous progress | [Studio](../Architecture/Experience/Studio.md), [UI rules](../UI_Coding_Guidelines.md) |
| P5 / BP-06 | 0% | [Knowledge Evidence and Source Loop](BP-06%20Knowledge%20Evidence%20and%20Source%20Loop.md) | BP-01 contracts; BP-04 execution; BP-05 inspection | Minimal source/document/result ingestion, typed accepted-change replay, pinned knowledge revisions, bounded executable rules and explicit scientific acceptance receipts; demonstrate corrections affect later campaigns | [Knowledge](../Architecture/Knowledge/Knowledge_Architecture.md), [Data](../Architecture/Data/Data_Architecture.md), [experiments](../Architecture/Research/Experiments.md) |
| P6 / BP-07 | 0% | [Autonomous LLM Campaign Supervision](BP-07%20Autonomous%20LLM%20Campaign%20Supervision.md) | BP-03 tool discovery; BP-04 runner; BP-05 UI; BP-06 grounded context/receipts | Model-generated campaign proposals and text-to-graph extraction through validated contracts; durable scoped engagements, stale-proposal/fallback races, bounded repair and truthful terminal blockers; no routine human waits | [Planning](../Architecture/Agents/Planning.md), [Graph Runner](../Architecture/System/Graph_Runner.md) |
| P7 / BP-08 | 0% | [Evolutionary Search Integration](BP-08%20Evolutionary%20Search%20Integration.md) | BP-04 iteration/checkpoints; BP-06 applicability/evidence; BP-07 for LLM-guided topology | Adapt reusable numerical kernels to explicit generation/checkpoint history, separate representation fixtures and evidence-bound selection; parameter search precedes bounded topology proposals under successor-campaign rules | [Search](../Architecture/Campaigns/Search.md), [reuse baseline](../Architecture/Evolutionary_Code_Reuse_Baseline.md) |
| P8 / BP-09 | 0% | [Single-Server Integrated Demo and Replacement Proof](BP-09%20Single-Server%20Integrated%20Demo%20and%20Replacement%20Proof.md) | Selected host/model policy; BP-05/06/07 plus BP-08 for evolutionary demo claims | Reproducible target-host deployment, model/tool eligibility, restore/reconciliation, end-to-end autonomous demo and one independently rebuilt/replaced tool; prove replicated workloads if K3s is selected | [Topology](../Architecture/System/Runtime_Topology.md), [tool services](../Architecture/Capabilities/Tool_Services.md) |

This is the default sequencing, not nine permanent file-ownership buckets. Each plan owns a delivery step; later plans may refine earlier contracts with explicit compatibility evidence. BP-01 records packaging constraints early; BP-03 tests tool images/protocols locally. BP-09 integrates target-host operation rather than postponing all deployment design to the end. Synthetic fixtures/receipts stand in for unavailable scientific services until BP-06 and are labeled as such.

## Cross-Plan Milestones

| Milestone | Plans | Done when | Status |
|---|---|---|---|
| M1 ? Replaceable typed foundation | BP-01/02/03 | One standalone tool is discovered and invoked through pinned contracts with durable acceptance and recovery | Synthetic software foundation complete: BP-01/02/03 contracts, durable invocation/recovery and standalone tools accepted |
| M2 ? Inspectable executing graph | BP-04/05 | A user can follow parallel work, joins, failures and evidence in a real running fixture, then author a subsequent campaign | In progress: BP-04 Runtime execution; BP-05 Studio remains queued |
| M3 ? Autonomous evidence-aware campaign | BP-06/07 | Pinned knowledge informs execution; durable LLM proposals are validated; stale or invalid responses cannot corrupt the run | Not started |
| M4 ? Evolution and module replacement | BP-08/09 | Search history/checkpoints are inspectable; target-host demo recovers and a replacement tool preserves its documented boundaries | Not started |

Milestones are acceptance outcomes, not additional work counted on top of their plans. No calendar dates or capacity promises are inferred.

## Decisions and Dependency Watchlist

BIND-01: [approved BP-04.04A](BP-04/BP-04.04A%20Typed%20artifact%20and%20collection%20bindings.md) is active after explicit owner direction. Parent is 12/24 (50%); no completed work is removed. Order: .03 -> .04A -> .04 -> .05.

| Item | Needed before | Disposition / owner |
|---|---|---|
| Initial schema/identity/publication policy | BP-01 complete; expand per successor | Initial wire subset and portable publication verified; durable command hashing remains BP-02 |
| API/development stack and initial service build layout | BP-01 complete | Foundation Decisions and independent package manifests now own the selected stack |
| Artifact reservations, cross-service receipts and revocation semantics | BP-02/06 dependent implementation | System/domain owners; required protocol fixtures |
| Branch/join/loop and cancellation transition tables | BP-04 implementation | Runtime owner; include empty/partial/skipped input cases |
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
| 2026-09-29 15:52:36 | BP-04.04A B2 passed; child 50%, parent 58.33% (14/24); B3 active | 1079 tests/thirteen installs/REC-01..09; dynamic round trip, exact protected conversions; peer/process proof remains |
| 2026-09-29 13:25:53 | BP-04.04A B1 passed; child 25%, parent 54.17% (13/24); B2 active | 1041 tests/thirteen installs/REC-01..09; 134 predecessor schemas unchanged; v4 execution gated |
| 2026-09-29 12:52:29 | Owner approved .04A; active B1 at 0%; parent rebaselined 12/24 (50%) | Four added prerequisite deliveries; phases P4 bindings/P5 baseline/P6 recovery; completed .01-.03 preserved |
| 2026-09-29 09:04:11 | BP-04.03 closed/audited 100%; parent 60% (12/20); .04 activation audit next | Five installed issuer/Artifact/replacement cases; [audit](../Audits/BP-04.03_Aggregation_Closeout.md); scope 1a07a70db37f43e3a106e9abca2edbc9 |
| 2026-09-29 08:56:15 | BP-04.03 B3 passed; child 75%, parent 55% (11/20); V1 active | Six actual process cases; 74 waits/83 aggregation cases across scoped runs; [evidence](../Audits/Evidence/BP-04-Aggregation/README.md) |
| 2026-09-28 22:09:45 | BP-04.03 B2 passed; child 50%, parent 50% (10/20); B3 active | 68 focused/1,001 total tests, thirteen installs, REC-01..09 b85109f93d704848af90f46f04bf89fe; Runtime 0.7.0 wait execution/protection |
| 2026-09-28 21:32:01 | BP-04.03 B2 collection slice verified; child stays 25%, parent 45%; external waits next | 84 focused/970 total tests, thirteen installs, REC-01..09 scope 182014083a85488981dbd08e1bbda122; Runtime 0.6.0 immutable all/partial/deadline decisions; canonical history repair |
| 2026-09-28 20:50:52 | BP-04.03 B1 passed; child 25%, parent 45% (9/20); B2 active | 920 tests/thirteen installs/REC-01..09; await wire-v3, 116 frozen predecessor schemas, isolated wait retention preparation; scope 5083de960e9142f1be186e0d77f4cf3e |
| 2026-09-28 20:11:30 | BP-04.03 B1 aggregate snapshot/storage slice verified; parent 40%, child 0 complete gates | 33 owned cases; 842 tests/thirteen installs/REC-01..09; Runtime 0.4.1/runtime_0008; external-wait boundary remains |
| 2026-09-28 19:47:08 | BP-04.02 closed/audited 100%; parent 40% (8/20); .03 B1 activated 0% | Eight installed graph/peer/replacement/polling/retention cases; scope bab36cf644df43e59a370437d68c94d1; [audit](../Audits/BP-04.02_Scheduling_Closeout.md) |
| 2026-09-28 19:30:50 | BP-04.02 B3 passed; child 75%, parent 35% (7/20); V1 active | 60 scheduling tests/eight actual coordinator-process cases; exact frontier/race/kill/replay/feedback/budget proof; [evidence](../Audits/Evidence/BP-04-Scheduling/README.md) |
| 2026-09-28 19:21:42 | BP-04.02 B2 passed; child 50%, parent 30% (6/20); B3 active | 799 tests/thirteen installs/REC-01..09; durable controls/checkpoints, HTTP/polling and active-worker window; scope 4beb3aa18a6b41818bdd97a0620bc674 |
| 2026-09-28 18:45:36 | BP-04.02 B1 passed; child 25%, parent 25% (5/20); B2 active | 765 tests/thirteen installs/REC-01..09; scoped graph admission, migration and completion guard; scope 0aabef6b736c4a7a82a3772c1c892a77 |
| 2026-09-28 18:20:22 | BP-04.01 closed/audited 100%; parent 20% (4/20); .02 B1 active 0% | Five actual installed plans/two tools, fresh compiler/Registry replacement; scope 498bc3389bca4a96b0d7f7690bd39577 |
| 2026-09-28 18:11:10 | BP-04.01 B3 passed; child 75%, parent 15% (3/20); V1 active | 111 compiler cases, 52 independent rejections; 100% scoped statements/branches; 23 contract and 6 legacy graph cases |
| 2026-09-28 18:02:52 | BP-04.01 B2 passed; child 50%, parent 10% (2/20); B3 active | 35 compiler cases; manual plan exact; 653 regression tests/twelve builds/REC-01..09, scope 7602f26a6cfb4a3aa7824ede61371e7f |
| 2026-09-28 17:40:35 | BP-04.01 B1 passed; child 25%, parent 5% (1/20); B2 active | 619 tests/twelve builds/REC-01..09; explicit wire-v2, unchanged v1 bytes; 23 owned wire cases |
| 2026-09-28 17:23:58 | BP-03 closed/audited 100% (16/16); BP-04.01/B1 active at 0% | Eight actual replica/replacement cases; [parent audit](../Audits/BP-03_Tool_Execution_Closeout.md) |
| 2026-09-28 17:19:54 | BP-03.04 B3 passed; child 75%, parent 93.75% (15/16) | Duplicate/checkpoint/failed replacement/budget/fresh-install cases; scope 7f160a8548e2488d821103017b8fbc8d |
| 2026-09-28 17:12:18 | BP-03.04 B2 passed; child 50%, parent 87.50% (14/16); B3 active | Actual death/expiry/reclaim, stale report and 0.2.0/0.3.0 cutover; [evidence](../Audits/Evidence/BP-03-Replicas/README.md) |
| 2026-09-28 17:04:34 | BP-03.04 B1 passed; child 25%, parent 81.25% (13/16); B2 active | Actual registry selection, concurrent workers and lost completion; [evidence](../Audits/Evidence/BP-03-Replicas/README.md) |
| 2026-09-28 16:52:45 | BP-03.03 closed/audited 100%; parent 75% (12/16); .04 B1 activated | Eleven live cases, fresh worker installs and unchanged retained history; [audit](../Audits/BP-03.03_Worker_Closeout.md) |
| 2026-09-28 16:47:03 | BP-03.03 B3 passed; child 75%, parent 68.75% (11/16); V1 active | Nine actual worker/owner cases and two Linux image goldens; [evidence](../Audits/Evidence/BP-03-Workers/README.md) |
| 2026-09-28 16:11:58 | BP-03.03 B2 passed; child 50%, parent 62.50% (10/16); next B3 | 117 focused tests/twelve isolated builds; exact-attempt authority and failure classification; SDK 100% scoped coverage |
| 2026-09-28 15:58:51 | BP-03.03 B1 passed; child 25%, parent 56.25% (9/16); next B2 | 529 tests/twelve builds/REC-01..09; isolated SDK and two actual standalone kernels with distinct payload schemas |

Keep at most 25 checkpoint rows. [Completed plans](Completed/README.md) remain outside active tables. Update the owning plan first, then this summary and Restore when their state changes.
