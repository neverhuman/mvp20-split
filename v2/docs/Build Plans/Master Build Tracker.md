# Master Build Tracker

## Purpose and Authority

Program-level source of truth for Amphora v2 build priority, dependency order, current position and delivery gates. Each activated plan owns its detailed canonical phase/task tracker and evidence; MBT mirrors that status without duplicating task history. [Development Process](../Development_Process.md) governs execution.

Structure adapted from the user-authorized read-only JARVIS MBT review on `2026-09-23 11:04:44`. JARVIS deployment policies, permissions, priorities and completion claims are not imported.

## Program Tracker

- Status: LAN-01 primary active; UI-01 and LR-01 paused by owner direction; BP-01 through BP-09 and SQ-01 remain closed.
- Last refreshed: 2026-10-08 10:31:34 (America/Chicago).
- Baseline: [Product Requirements](../Architecture/Requirements/Product_Requirements.md), [Master Architecture](../../Architecture.md).
- Current priority: [LAN-01 Local Network Demo Access](LAN-01%20Local%20Network%20Demo%20Access.md); live HTTPS gateway and second-computer handoff.
- Primary active task: LAN-01 implementation100%, L1/L2/L3=100%; owner confirmed remote HTTPS reachability; authenticated walkthrough/trust pending.
- Next task: owner second-computer access check, then return to UI-01 remaining N2.2/N2.5; fine visual polish deferred.
- Implementation completion: LAN-01=100%, L1/L2/L3=100%; UI-01 paused55%, Build68.75%, Verification0%; LR-01 paused25%, Build33.33%, Acceptance0%.
- Blockers: no LAN implementation blocker; remote firewall path and client certificate trust require the other computer. UI scientific proposal binding remains unfinished; UI-01.01 is separate result-discovery scope.
- Acceptance posture: connected plan/execution/comparison/next-review actual served walkthrough passed; Studio0.21,314 tests. New-run browser action and V1 remain outstanding. Public result-index proposal remains separate.
- Active exception: owner reprioritized LAN access on2026-10-08. Preserve UI-01 percentages and LR-01/R2 receipt diagnosis; no automatic worker-diagnostic resumption when the demo closes.

## Initial Delivery Boundary

Internal use and demos for the first many releases; one user and one active autonomous campaign, with concurrent tool invocations. Owner selected the current local computer and computer-only access for this stage; DGX Spark/Threadripper remain future targets. Keep the scientific engine general; bio-available polymers are a likely application, not a fixed implementation pathway. Human edits and human-initiated replacements apply between campaigns.

Strictly isolate primary services and independently packaged tools. Use Pydantic/JSON Schema contracts, PostgreSQL-owned state, immutable artifacts, a single Graph Runner execution authority, an indexed tool universe and durable LLM proposals. Module READMEs capture the boundary conditions for independent rebuilds. K3s/Kubernetes tool replication is a proposed deployment profile; cluster selection and installation are not yet authorized implementation work.

The initial program proves software behavior using deterministic/synthetic fixtures and narrowly reviewed v1 reuse. Validated biological/polymer evaluators, real laboratory integration and scientific efficacy require separate evidence and scoped successor work.

## Current In-Flight Work

LAN-01 implementation100%, L1/L2/L3=100%; live and awaiting remote acceptance.
UI-01 is paused at55%, Build68.75%, Verification0%. G0 graph review/design
is a prerequisite and earns no implementation credit. G1/N1/N2/N3/V1 are five equal
delivery gates. Phase mirror: G0=100%, G1=100%, N1=100%, N2=75%, N3=0%, V1=0%.
LR-01 is paused at25%, Build33.33%, Acceptance0%; R1=100%, R2/R3/V1=0%.
Completed plans remain in the [completed index](Completed/README.md).

## Prioritized Successor Queue and Phase Mirrors

| Order | Canonical plan | Status | Overall | Build | Verification/Acceptance | Prerequisite |
|---|---|---|---:|---:|---:|---|
| 0 | [LAN-01 Local Network Demo Access](LAN-01%20Local%20Network%20Demo%20Access.md) | Implemented; remote acceptance pending | 100% | 100% | Remote pending | Owner LAN priority/firewall rule |
| 1 | [UI-01 Research Workspace Overhaul](UI-01%20Research%20Workspace%20Overhaul.md) | Paused for LAN access; connected demo delivered | 55% | 68.75% | 0% | Owner direction; bounded activation review recorded |
| 2 | [LR-01 Local Worker Reliability](LR-01%20Local%20Worker%20Reliability.md) | Paused by owner; R2 resume point | 25% | 33.33% | 0% | UI priority released; same-host diagnostic window |
| 3 | [UI-R01 Feedback Read Diagnostics](UI-R01%20Feedback%20Read%20Diagnostics.md) | Queued; pull forward if it blocks UI-01 | 0% | 0% | 0% | Bounded read diagnostic and activation review |
| 4 | [UI-02 Candidate Structure and Recommendation Views](UI-02%20Candidate%20Structure%20and%20Recommendation%20Views.md) | Queued by owner; P1/P2/P3/P4=0% | 0% | 0% | 0% | Typed retained candidate structures and explicit selection evidence; activation audit |

The owning tracker controls exact task/percentages; MBT controls priority and
mirrors current state. Complete each bounded gate before dependent implementation.
No completed-plan scope is reopened. [Selected profile handoff](../Audits/BP-09_Selected_Profile_Handoff.md)
names scientific, production and capacity successor triggers that are not activated.

## Cross-Plan Milestones

| Milestone | Plans | Done when | Status |
|---|---|---|---|
| M1 ? Replaceable typed foundation | BP-01/02/03 | One standalone tool is discovered and invoked through pinned contracts with durable acceptance and recovery | Synthetic software foundation complete: BP-01/02/03 contracts, durable invocation/recovery and standalone tools accepted |
| M2 ? Inspectable executing graph | BP-04/05 | A user can follow parallel work, joins, failures and evidence in a real running fixture, then author a subsequent campaign | Accepted within synthetic software scope: BP-04 execution/observation and BP-05 Studio closed |
| M3 ? Autonomous evidence-aware campaign | BP-06/07 | Pinned knowledge informs execution; durable LLM proposals are validated; stale or invalid responses cannot corrupt the run | Accepted: BP-06/07 closed; actual bounded model/context integration verified by BP-09 |
| M4 ? Evolution and module replacement | BP-08/09 | Search history/checkpoints are inspectable; target-host demo recovers and a replacement tool preserves its documented boundaries | Accepted: BP-08/09 closed; synthetic evolution, selected-host recovery and independent tool rebuild verified |

Milestones are acceptance outcomes, not additional work counted on top of their plans. No calendar dates or capacity promises are inferred.

## Decisions and Dependency Watchlist

BIND-01 is resolved by [closed BP-04.04A](BP-04/Completed/BP-04.04A%20Typed%20artifact%20and%20collection%20bindings.md). BP-04 subsequently closed24/24; the historical scope correction remains in its archived history.

| Item | Needed before | Disposition / owner |
|---|---|---|
| Initial schema/identity/publication policy | BP-01 complete; expand per successor | Initial wire subset/publication and durable command profiles accepted; expansion belongs to successors |
| API/development stack and initial service build layout | BP-01 complete | Foundation Decisions and independent package manifests now own the selected stack |
| Artifact reservations, cross-service receipts and revocation semantics | BP-02/06 dependent implementation | System/domain owners; required protocol fixtures |
| Branch/join/loop, bindings and recovery | BP-04 complete | Scoped child/parent audits and actual installed observation/replacement accepted |
| Bounded rule formalism and contradiction behavior | BP-06 implementation | Knowledge owner; examples/fixtures before inference code |
| Real scientific corpus, evaluators and lab provider | Scientific successor acceptance | TBA by owner; does not block synthetic engine proof |
| Actual host, accelerator availability, model endpoint and permitted data egress | Real-provider use / target deployment | Local host/loopback and bounded synthetic OpenAI use accepted; other hosts/data need selection |
| K3s choice and workload packaging | Future CP-01 cluster-specific proof | Proposed, not an installed dependency or a second graph scheduler |

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
| 2026-10-07 23:13:55 | UI-01.03 E1/E2/E3 complete; UI01=50%,Build62.50%,N2=50%. Owner review pending. | Two standalone scientific tools;21 isolated tests;108 Deployment tests;310 Studio tests; four Runtime-retained invocations and actual served1440/390 inspection. [Audit](../Audits/UI-01.03_Scientific_Execution.md). |
| 2026-10-07 18:07:35 | UI-01 planned and prioritized0%; graph review first, then research workflow. LR-01 paused25%. | Owner-reported graph failure; [UI-01](UI-01%20Research%20Workspace%20Overhaul.md) owns six ordered phases with G0 design separate from implementation. |
| 2026-10-07 14:49:53 | SQ-01 C2 complete; overall75%, Build90%, Verification66.67%. | Runtime175 tests; retained-only outcomes and old recipe bytes preserved. B3 proposal UI next. |
| 2026-10-07 14:02:37 | SQ-01 C2b complete; overall69.44%, Build94.44%, Verification66.67%. | 242 compatibility/SQL/recovery tests and5 final checks; C2=66.67%; Runtime next. |
| 2026-10-07 13:21:09 | SQ-01 C2a complete; overall63.89%, Build76.67%, Verification66.67%. | 153 domain/context/output tests; C2=33.33%, provider integration next. |
| 2026-10-07 12:59:32 | SQ-01 C1 complete69.44%, Build94.44%, Verification66.67%. | 110 contract/publication and183 consumer tests; all632 predecessor schema bytes unchanged; new profile inactive pendingC2. |
| 2026-10-07 12:44:11 | DEMO-01 closed100%; SQ-01/C1 resumes at41.67%. | Studio0.16.1 actual-owner walkthrough, seven-owner launch/drain, offline fallback; prior feedback read failure retained. |
| 2026-10-07 12:20:17 | SQ-01.01 approved; C1/C2 added, overall41.67%, Build50%, Verification66.67%. | 2.5 completed units preserved; denominator4 to6. C1 contracts active; C2 owners, B3 proposals and V1 follow. |
| 2026-10-07 11:51:00 | SQ-01 human focus complete; overall62.5%, Build94.44%, Verification66.67%. | 38 scoped tests; desktop/mobile export/browser proof; SQ-01.01 criterion-target profile awaits owner direction. |
| 2026-10-07 11:02:03 | BP-09 closed100%,20/20; SQ-01 next. | Frozen12gate ledger,391independent tests, actual original/successor/blocked smoke; LR-01 preserves unresolved worker faults. |
| 2026-10-07 10:42:02 | BP-09.04 closed100%;parent95%,19/20. BP-09.05 next. | Independent354Deployment/38evaluator tests, actual installed readback,337/337catalog refs and0pending; scoped audit preserves operational follow-ups. |
| 2026-10-07 10:26:15 | BP-09.04 B3 complete;child75%,Build100%,Acceptance0%;parent75%. | Actual backup-copy faults reject before allocation; wrong pins/policy reject; expired1->accepted2 fence and stale_attempt preserve result. V1 active. |
| 2026-10-07 10:07:55 | BP-09.04 B2 complete;child50%,Build66.67%,Acceptance0%;parent70%. | Independent evaluator0.4 installed/image proof; actual restored15/6/3cutover, exact old histories/browser. Earlier process faults retained; B3 next. |
| 2026-10-07 09:21:40 | BP-09.04 B1/B2.1 complete;child37.5%,Build50%,Acceptance0%;parent67.5%. | Cold backup e, separate restore b,237/237references,0pending retentions, exact original/corrected/blocked readbacks; Data0.31 independent audit. |
| 2026-10-07 08:26:45 | BP-09.04 B1.1 complete;child12.5%,Build16.67%,Acceptance0%;parent62.5%. | Deployment0.12 manifest/inventory,98 tests,159statements/14branches100%; owner recovery objective selected. |
| 2026-10-07 08:17:34 | BP-09.03 closed100%;parent60%,12/20; BP-09.04 B1 active0%. | Approved daemon outage, exact original/corrected/blocked readbacks, installed browser/owner proof and scoped audit; zero calls. |
| 2026-10-07 07:21:01 | BP-09.03 B3 two of three checkpoints; child66.67%,Build94.44%,Acceptance0%;parent53.33%,(10+2/3)/20,ten closed gates. | Actual job/TLS death and exact-turn recovery48.265s;65 tests; bounded idle process-tree memory; shared-daemon scope approval pending. |
| 2026-10-07 06:58:35 | BP-09.03 B2 complete; child50%,Build66.67%,Acceptance0%; parent50%,10/20 gates. | Actual future-only corrected interpretation/source/graph/successor, browser1440/390,45 scoped tests; no paid calls. |
| 2026-10-07 06:44:23 | BP-09.03 B1 complete; child25%,Build33.33%,Acceptance0%; parent45%,9/20 gates. | Studio0.13 actual successor carry/lineage/artifact proof, navigation regression and identical rebuilt assets; zero new model calls. |
| 2026-10-07 06:23:32 | BP-09.03 successor prerequisite; percentages unchanged. | Deployment0.11 independent294tests, dedicated Registry peer read/resolve/replay/denial, original vault preserved; no campaign admission. |
| 2026-10-07 06:11:09 | BP-09.03/B1.4c75%;child24.48%,parent44.95%. | Three of four same-weight browser checkpoints verified; actual Design validation and edit retention pass. Predecessor carry/successor remains. |
| 2026-10-07 05:54:33 | BP-09.03/B1.4c partial; percentages unchanged. | Studio0.11 actual graph/evidence navigation and foreign-link rejection pass; preserve binary-source limitation; Design/successor next. |
| 2026-10-07 05:40:02 | BP-09.03/B1.4c partial; percentages unchanged. | Actual localhost Studio0.10 execution/reasoning at1440/390 and owner API trace pass; no calls; full navigation remains. |
| 2026-10-07 05:22:21 | BP-09.03/B1.4b complete;child22.92%,parent44.58%. | Actual owner context/model abstention plus scientific15/6/3/15 and immutable restart; three calls totalUSD0.0520185; browser trace next. |
| 2026-10-07 04:24:49 | BP-09.03/B1.4a complete;child20.83%,parent44.17%. | Planning0.102 independent120tests; actual model-to-Runtime parameter7, reportedUSD0.01743525; immutable restart readback; scientific/context composition next. |
