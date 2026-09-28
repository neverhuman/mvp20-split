# Master Build Tracker

## Purpose and Authority

Program-level source of truth for Amphora v2 build priority, dependency order, current position and delivery gates. Each activated plan owns its detailed canonical phase/task tracker and evidence; MBT mirrors that status without duplicating task history. [Development Process](../Development_Process.md) governs execution.

Structure adapted from the user-authorized read-only JARVIS MBT review on `2026-09-23 11:04:44`. JARVIS deployment policies, permissions, priorities and completion claims are not imported.

## Program Tracker

- Status: BP-02 primary active; BP-03 through BP-09 decomposed/design-specified; BP-01/BP-01A closed
- Last refreshed: `2026-09-28 13:00:03` (America/Chicago)
- Baseline: [Product Requirements](../Architecture/Requirements/Product_Requirements.md), [Master Architecture](../../Architecture.md), and current System/Capability contracts
- Current priority: P0 / BP-02 - completion and delivery
- Primary active implementation plan / phase / task: BP-02 -> BP-02.05 / V2 / D6.
- Current task: actual runtime/artifact public process acceptance and component-scoped drift audit.
- Next task: BP-02.06 R1 fault orchestration after D6 closeout.
- Implementation completion: BP-01/BP-01A closed at 100%; BP-02 81.25% (26/32 implementation deliveries), children .01-.04 closed at 100%, .05 83.33%, .06 0%; BP-03..09 scoped parents at 0%. No effort estimate inferred.
- Active focus: durable state, artifact publication/reservations and claim/completion foundation after the completed contract slice
- Blockers: Git identity configured; no implementation blocker for BP-02.05; predecessor/host/provider gates of later plans remain explicit
- Acceptance posture: BP-01 boundary/API subset accepted; no durable graph execution or scientific acceptance claimed
- Active exception: none; user-authorized implementation resumed after reference refinement.

## Initial Delivery Boundary

Internal use and demos for the first many releases; one user and one active autonomous campaign, with concurrent tool invocations. Single-server target is DGX Spark or partner Threadripper. Keep the scientific engine general; bio-available polymers are a likely application, not a fixed implementation pathway. Human edits and human-initiated replacements apply between campaigns.

Strictly isolate primary services and independently packaged tools. Use Pydantic/JSON Schema contracts, PostgreSQL-owned state, immutable artifacts, a single Graph Runner execution authority, an indexed tool universe and durable LLM proposals. Module READMEs capture the boundary conditions for independent rebuilds. K3s/Kubernetes tool replication is a proposed deployment profile; cluster selection and installation are not yet authorized implementation work.

The initial program proves software behavior using deterministic/synthetic fixtures and narrowly reviewed v1 reuse. Validated biological/polymer evaluators, real laboratory integration and scientific efficacy require separate evidence and scoped successor work.

## Current In-Flight Work

BP-02 is the sole primary active plan. Later plans are design-specified with canonical child trackers; predecessor and activation gates remain mandatory.

| Parent | Implementation | .01 Contracts | .02 Persistence | .03 Artifacts | .04 Invocations | .05 Completion | .06 Recovery |
|---|---:|---:|---:|---:|---:|---:|---:|
| [BP-02](BP-02%20Durable%20Runtime%20and%20Artifact%20Foundation.md) | 81.25% | 100% | 100% | 100% | 100% | 83.33% | 0% |

| Active canonical child | Overall | V1 Build | V2 Acceptance | Current task |
|---|---:|---:|---:|---|
| [BP-02.05](BP-02/BP-02.05%20Completion%20and%20Delivery.md) | 83.33% | 100% | 0% | D6 integrated acceptance/audit |

Authorized rebaseline: original 8.33% counted protocol design. Design credit remains complete; implementation counts 32 deliveries, twenty-six verified. Pure design gates S1/A1 remain mandatory without implementation credit; the preliminary 34-task count was explicitly corrected. [Parent history](BP-02%20History.md) preserves prior scope. Progress counts deliverables, not engineer-hours; child trackers are canonical.

## Queued Plans and Phase Mirrors

| Canonical plan | Status | Overall | P1 | P2 | P3 | P4 | P5 | P6 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| [BP-03 Tool Index and Standalone Execution](BP-03%20Tool%20Index%20and%20Standalone%20Execution.md) | Design specified | 0% | 0% | 0% | 0% | 0% | N/A | N/A |
| [BP-04 Deterministic Graph Runner](BP-04%20Deterministic%20Graph%20Runner.md) | Design specified | 0% | 0% | 0% | 0% | 0% | 0% | N/A |
| [BP-05 Graph Studio First Vertical Slice](BP-05%20Graph%20Studio%20First%20Vertical%20Slice.md) | Design specified | 0% | 0% | 0% | 0% | 0% | N/A | N/A |
| [BP-06 Knowledge Evidence and Source Loop](BP-06%20Knowledge%20Evidence%20and%20Source%20Loop.md) | Design specified | 0% | 0% | 0% | 0% | 0% | 0% | 0% |
| [BP-07 Autonomous LLM Campaign Supervision](BP-07%20Autonomous%20LLM%20Campaign%20Supervision.md) | Design specified | 0% | 0% | 0% | 0% | 0% | 0% | N/A |
| [BP-08 Evolutionary Search Integration](BP-08%20Evolutionary%20Search%20Integration.md) | Design specified | 0% | 0% | 0% | 0% | 0% | 0% | N/A |
| [BP-09 Single-Server Integrated Demo and Replacement Proof](BP-09%20Single-Server%20Integrated%20Demo%20and%20Replacement%20Proof.md) | Design specified | 0% | 0% | 0% | 0% | 0% | 0% | N/A |

Each parent phase now maps to one canonical child with four verified deliveries (three build plus one acceptance). Parent denominators are BP-03: 16, BP-04: 20, BP-05: 16, BP-06: 24, BP-07: 20, BP-08: 20, BP-09: 20; all remain 0%. N/A means unscoped. [Readiness/handoffs](Planning_Readiness.md) records engineering and external gates. Design writing earns no implementation credit.

The owning plan tracker is canonical for overall and per-phase percentages. Refresh this mirror whenever a gate, scope, completion estimate, blocker or checkpoint changes, before handoff/commit. Percentages measure scoped implementation; acceptance and operational readiness are separate. No in-flight plan may appear here without numeric overall and phase completion.


[BP-01](Completed/BP-01%20Contract%20and%20Service%20Foundations.md) and BP-01A remain complete and archived. The queue below links canonical parents; ordering does not waive child gates. [Planning readiness](Planning_Readiness.md) owns cross-plan dependencies and scoped external decisions.

## Prioritized Build Queue

BP-02 is `primary_active`; BP-03 through BP-09 are `design_specified / queued`, with 34 canonical children. Each child names owned objects/contracts, algorithms, failure oracles and replacement acceptance. Completed plans remain in the archive.

| Order / ID | Completion | Proposed plan | Required predecessor gates | Bounded outcome / exit | Architecture owner |
|---|---|---|---|---|---|
| P0 / BP-02 | 81.25% | [Durable Runtime and Artifact Foundation](BP-02%20Durable%20Runtime%20and%20Artifact%20Foundation.md) - active child .05/D6 | BP-01 contracts/build boundary | Runtime-owned run/attempt/command state, audit/outbox, artifact finalization/reservation interface, minimal claim/completion protocol and restart/idempotency proof; no complete graph interpreter claimed | [State/consistency](../Architecture/System/State_and_Consistency.md) |
| P2 / BP-03 | 0% | [Tool Index and Standalone Execution](BP-03%20Tool%20Index%20and%20Standalone%20Execution.md) | BP-01; BP-02 claim/artifact protocols | Versioned descriptors and deployment inventory, standalone synthetic tools, shared execution SDK, exact-version routing, two-worker claim/fence proof; narrow solvency reuse only after applicability review | [Tool services](../Architecture/Capabilities/Tool_Services.md), [catalog](../Architecture/Capabilities/Catalog.md) |
| P3 / BP-04 | 0% | [Deterministic Graph Runner](BP-04%20Deterministic%20Graph%20Runner.md) | BP-02 durable state; BP-03 callable tools | Compile and execute typed branch/join/scatter/loop graphs; aggregate committed results; handle scoped failures, external waits, restart and successor campaigns with no LLM required for deterministic control; pass the source-derived v1 solver orchestration scenarios using synthetic adapters | [Graph Runner](../Architecture/System/Graph_Runner.md), [execution model](../Architecture/System/Graph_Execution_Model.md) |
| P4 / BP-05 | 0% | [Graph Studio First Vertical Slice](BP-05%20Graph%20Studio%20First%20Vertical%20Slice.md) | BP-04 runnable fixture and read/command contracts | Inspect actual live/historical execution, evidence, parallel branches and failures; edit next-campaign drafts, compare revisions and observe emergency termination; preserve autonomous progress | [Studio](../Architecture/Experience/Studio.md), [UI rules](../UI_Coding_Guidelines.md) |
| P5 / BP-06 | 0% | [Knowledge Evidence and Source Loop](BP-06%20Knowledge%20Evidence%20and%20Source%20Loop.md) | BP-01 contracts; BP-04 execution; BP-05 inspection | Minimal source/document/result ingestion, typed accepted-change replay, pinned knowledge revisions, bounded executable rules and explicit scientific acceptance receipts; demonstrate corrections affect later campaigns | [Knowledge](../Architecture/Knowledge/Knowledge_Architecture.md), [Data](../Architecture/Data/Data_Architecture.md), [experiments](../Architecture/Research/Experiments.md) |
| P6 / BP-07 | 0% | [Autonomous LLM Campaign Supervision](BP-07%20Autonomous%20LLM%20Campaign%20Supervision.md) | BP-03 tool discovery; BP-04 runner; BP-05 UI; BP-06 grounded context/receipts | Model-generated campaign proposals and text-to-graph extraction through validated contracts; durable scoped engagements, stale-proposal/fallback races, bounded repair and truthful terminal blockers; no routine human waits | [Planning](../Architecture/Agents/Planning.md), [Graph Runner](../Architecture/System/Graph_Runner.md) |
| P7 / BP-08 | 0% | [Evolutionary Search Integration](BP-08%20Evolutionary%20Search%20Integration.md) | BP-04 iteration/checkpoints; BP-06 applicability/evidence; BP-07 for LLM-guided topology | Adapt reusable numerical kernels to explicit generation/checkpoint history, separate representation fixtures and evidence-bound selection; parameter search precedes bounded topology proposals under successor-campaign rules | [Search](../Architecture/Campaigns/Search.md), [reuse baseline](../Architecture/Evolutionary_Code_Reuse_Baseline.md) |
| P8 / BP-09 | 0% | [Single-Server Integrated Demo and Replacement Proof](BP-09%20Single-Server%20Integrated%20Demo%20and%20Replacement%20Proof.md) | Selected host/model policy; BP-05/06/07 plus BP-08 for evolutionary demo claims | Reproducible target-host deployment, model/tool eligibility, restore/reconciliation, end-to-end autonomous demo and one independently rebuilt/replaced tool; prove replicated workloads if K3s is selected | [Topology](../Architecture/System/Runtime_Topology.md), [tool services](../Architecture/Capabilities/Tool_Services.md) |

This is the default sequencing, not nine permanent file-ownership buckets. Each plan owns a delivery step; later plans may refine earlier contracts with explicit compatibility evidence. BP-01 records packaging constraints early; BP-03 tests tool images/protocols locally. BP-09 integrates target-host operation rather than postponing all deployment design to the end. Synthetic fixtures/receipts stand in for unavailable scientific services until BP-06 and are labeled as such.

## Cross-Plan Milestones

| Milestone | Plans | Done when | Status |
|---|---|---|---|
| M1 ? Replaceable typed foundation | BP-01/02/03 | One standalone tool is discovered and invoked through pinned contracts with durable acceptance and recovery | Partial: BP-01 contract/validation foundation complete |
| M2 ? Inspectable executing graph | BP-04/05 | A user can follow parallel work, joins, failures and evidence in a real running fixture, then author a subsequent campaign | Not started |
| M3 ? Autonomous evidence-aware campaign | BP-06/07 | Pinned knowledge informs execution; durable LLM proposals are validated; stale or invalid responses cannot corrupt the run | Not started |
| M4 ? Evolution and module replacement | BP-08/09 | Search history/checkpoints are inspectable; target-host demo recovers and a replacement tool preserves its documented boundaries | Not started |

Milestones are acceptance outcomes, not additional work counted on top of their plans. No calendar dates or capacity promises are inferred.

## Decisions and Dependency Watchlist

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

[Completed plan index](Completed/README.md) owns the three closed architecture-documentation plans and their audits. They remain complete for their historical scope and do not contribute runtime implementation credit. BP-01 is the first completed implementation-foundation plan; its narrow completion does not establish runtime/scientific readiness.

## Recent Checkpoints

| Timestamp | Checkpoint | Evidence |
|---|---|---|
| 2026-09-28 13:00:03 | BP-02.05 D5 passed; child 83.33%, V1 100%, parent 81.25%; next D6 | 297 tests/eight builds; scoped history and signed pinned pages |
| 2026-09-28 12:45:25 | BP-02.05 D4 passed; child 66.67%, V1 80%, parent 78.13%; next D5 | 288 tests/eight builds; both journals, stale-ack fences, replay and exhaustion |
| 2026-09-28 12:35:03 | BP-02.05 D3 passed; child 50%, V1 60%, parent 75%; next D4 | 278 full tests/eight builds, final 36 scoped; retention proof and bounded recovery |
| 2026-09-28 12:23:58 | BP-02.05 D2 passed; child 33.33%, V1 40%, parent 71.88%; next D3 | 270 tests/eight builds; atomic acceptance/rollback, retry and independent branches |
| 2026-09-28 12:13:10 | BP-02.05 D1 passed; child 16.67%, V1 20%, parent 68.75%; next D2 | 259 tests/eight builds; immutable intent and partial reservation recovery |
| 2026-09-28 12:01:48 | BP-02.04 closed/audited 100%; parent 65.63% (21/32); .05/D1 activated at 0% | 243 tests/eight builds, installed HTTP-only worker proof; [audit](../Audits/BP-02.04_Invocation_Lifecycle_Closeout.md) |
| 2026-09-28 11:51:08 | BP-02.04 I5 passed; child 83.33%, V1 100%, parent 62.50%; next I6 | 239 tests; atomic cancel/revoke and policy journal; f8a8f94 pushed |
| 2026-09-28 11:37:28 | BP-02.04 I4 passed; child 66.67%, V1 80%, parent 59.38%; next I5 | Budget/rollback/prepared-intent guards; 229 full tests, 41 scoped |
| 2026-09-28 11:28:20 | BP-02.04 I3 passed; child 50%, V1 60%, parent 56.25%; next I4 | Two-process claims/live-clock renewal; 224 tests/eight builds |
| 2026-09-28 11:18:55 | BP-02.04 I2 passed; child 33.33%, V1 40%, parent 53.13%; next I3 | Admission contention/replay/rollback; 218 tests/eight builds |
| 2026-09-28 11:11:49 | BP-02.04 I1 passed; child 16.67%, V1 20%, parent 50%; next I2 | 21 pure policy tests; full gate 209/eight builds |
| 2026-09-28 11:05:08 | BP-02.03 closed/audited at 100%; parent 46.88%; .04 I1 activated | 188 tests/eight independent builds; installed HTTP artifact acceptance |
| 2026-09-28 10:56:19 | BP-02.03 A5 complete; child 80%, V1 100%, parent 43.75%; next A6 | 182 tests/eight builds; crash-safe cleanup and bounded reconciliation |
| 2026-09-26 16:31:31 | BP-02.03 A4 complete; child 60%, V1 75%, parent 40.63%; next A5 | 172 tests, eight independent builds; scripted authenticated runtime proof; Git identity pending |
| 2026-09-25 17:12:21 | BP-02.03 A3 complete; child 40%, V1 50%, parent 37.50%; next A4 | 158 tests, eight independent builds; finalizer crash/replay and atomic publication verified |
| 2026-09-25 16:59:22 | BP-02.03 A2 complete; child 20%, V1 25%, parent 34.38%; next A3 | 141 tests, eight independent builds; artifact suite 30, two-process fencing |
| 2026-09-25 13:54:17 | Amphora Lab insights incorporated into ten BP-05/06/07/08 children; authority, trace, material identity and view tests specified; percentages unchanged | [Reference/ownership map](References/Amphora_Lab_Insights.md) |
| 2026-09-25 13:40:55 | Roadmap maturation: 34 canonical children added, four open BP-02 children deepened; implementation percentages unchanged | [Planning review](../Audits/Planning_Maturity_Review.md), [readiness/handoffs](Planning_Readiness.md) |
| 2026-09-25 08:49:41 | BP-02 decomposed; contracts and isolated persistence children closed; parent 31.25% (10/32), next .03/A1 | [Persistence audit](../Audits/BP-02.02_Persistence_Closeout.md); 119 tests, eight independent builds |
| 2026-09-24 12:10:07 | User UI references mapped to Studio modes and BP-05/06/08 prototype tasks; percentages unchanged, BP-02 remains P1/T2 | [Reference map](../Architecture/Experience/Interaction_References.md) |
| 2026-09-24 12:06:07 | BP-03 through BP-09 first drafts published at 0%; BP-02 authorized and T1 complete, P1 50% / overall 8.33%; next T2 | Canonical plan links above; [protocol decisions](../Architecture/System/Runtime_Command_Protocol.md) |
| 2026-09-24 09:10:34 | BP-02 draft authored for user review: six phases, twelve tasks, all implementation percentages 0%; no activation | [Canonical draft](BP-02%20Durable%20Runtime%20and%20Artifact%20Foundation.md) |
| 2026-09-24 09:01:20 | BP-01A complete at 100%, all four phases 100%; module test ownership, granular coverage, extracted v1 graph and scaffold; 44 tests pass | [Plan](Completed/BP-01A%20Module%20Tests%20and%20V1%20Graph%20Baseline.md), [audit](../Audits/BP-01A_Test_and_Graph_Baseline_Closeout.md) |
| 2026-09-23 19:55:48 | BP-01 complete: 39 tests, four independent wheel installs, strict schema/API boundary and replacement docs; archived after scoped audit | [Plan](Completed/BP-01%20Contract%20and%20Service%20Foundations.md), [audit](../Audits/BP-01_Foundation_Closeout.md) |
| 2026-09-23 11:04:44 | Expanded MBT into initial program dashboard with nine queued planning areas, dependency gates, four milestones and exact next planning task; implementation unactivated | This tracker; [plan template](../Templates/Build%20Plan%20Template.md) |

Keep at most 25 checkpoint rows. [Completed plans](Completed/README.md) remain outside active tables. Update the owning plan first, then this summary and Restore when their state changes.
