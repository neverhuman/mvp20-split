# Master Build Tracker

## Purpose and Authority

Program-level source of truth for Amphora v2 build priority, dependency order, current position and delivery gates. Each activated plan owns its detailed canonical phase/task tracker and evidence; MBT mirrors that status without duplicating task history. [Development Process](../Development_Process.md) governs execution.

Structure adapted from the user-authorized read-only JARVIS MBT review on `2026-09-23 11:04:44`. JARVIS deployment policies, permissions, priorities and completion claims are not imported.

## Program Tracker

- Status: UI-01 primary active; LAN-01 accepted/archived. LR-01 remains conditional; completed plans remain closed.
- Last refreshed: 2026-10-12 21:35:47 (America/Chicago).
- Baseline: [Product Requirements](../Architecture/Requirements/Product_Requirements.md), [Master Architecture](../../Architecture.md).
- Current priority: schedule UI-01 Knowledge/run/LLM integration and UI-02 formula/structure views for2026-10-12 through2026-10-16; preserve the live demo.
- Primary active task: UI-01/N3/I1, implementing approved [UI-01.08](UI-01.08%20Campaign%20curation%20boundary%20decision.md), P1=100%, P2=100%, P3=100%,P4=100%,P5=87.5%, child97.5%. N2=100%; launch/provenance remain closed. UI-01.05 K1/R1=100%, I1=97.5%, child99.17%.
- Next task: UI-01.08/P5.4; UI-01.08j/M3 scoped credentials, existing-demo backup/migration and local/LAN delivery.
- Implementation completion: LAN-01=100%; UI-01 active79.5%, Build99.375%, Verification0%; UI-02=0%, P1/P2/P3/P4=0%; LR-01 paused25%, Build33.33%, Acceptance0%.
- Blockers/dependencies: Supported model/actual successor/browser qualified via08i100%; no owner decision needed. Managed demo lifecycle/cutover remains. $9.25 of additional authority unreserved; no more qualification calls.
- Latest checkpoint: 2026-10-12 21:35:47: Deployment0.20.0 M1/M2 complete;54 source and54 installed tests pass; actual idle force-stop/recovery80941 passed/drained, receipts/allowance unchanged.08j50%, M3 next.
- Acceptance posture: Supported live synthetic case and missing-capability case qualified; managed demo cutover and parent V1 remain. Three new calls estimated$0.149689500, $.75 held; demo unchanged.
- Active exception: owner scheduled four targets for next week. Preserve earned phase credit; sequence the bounded cross-plan handoffs below. Pull LR-01/UI-R01 forward only when their faults block the scheduled integration, with exact return points.

## Initial Delivery Boundary

Internal use and demos for the first many releases; one user and one active autonomous campaign, with concurrent tool invocations. Owner selected the current local computer and computer-only access for this stage; DGX Spark/Threadripper remain future targets. Keep the scientific engine general; bio-available polymers are a likely application, not a fixed implementation pathway. Human edits and human-initiated replacements apply between campaigns.

Strictly isolate primary services and independently packaged tools. Use Pydantic/JSON Schema contracts, PostgreSQL-owned state, immutable artifacts, a single Graph Runner execution authority, an indexed tool universe and durable LLM proposals. Module READMEs capture the boundary conditions for independent rebuilds. K3s/Kubernetes tool replication is a proposed deployment profile; cluster selection and installation are not yet authorized implementation work.

The initial program proves software behavior using deterministic/synthetic fixtures and narrowly reviewed v1 reuse. Validated biological/polymer evaluators, real laboratory integration and scientific efficacy require separate evidence and scoped successor work.

## Current In-Flight Work

LAN-01 complete100%, archived in Completed; deployed viewer preserved.
UI-01 is active at79.5%, Build99.375%, Verification0%. G0 graph review/design
is a prerequisite and earns no implementation credit. G1/N1/N2/N3/V1 are five equal
delivery gates. Phase mirror: G0=100%, G1=100%, N1=100%, N2=100%, N3=97.5%, V1=0%.
LR-01 is paused at25%, Build33.33%, Acceptance0%; R1=100%, R2/R3/V1=0%.
Completed plans remain in the [completed index](Completed/README.md).

## Prioritized Successor Queue and Phase Mirrors

| Order | Canonical plan | Status | Overall | Build | Verification/Acceptance | Prerequisite |
|---|---|---|---:|---:|---:|---|
| 1 | [UI-01 Research Workspace Overhaul](UI-01%20Research%20Workspace%20Overhaul.md) | N2=100%; N3/I1 approved; UI-01.08/P5 active; P3 complete; P4 complete; P5 live qualification active | 79.5% | 99.375% | 0% | Additive curation/capability/successor boundaries |
| 2 | [UI-02 Candidate Structure and Recommendation Views](UI-02%20Candidate%20Structure%20and%20Recommendation%20Views.md) | Scheduled next week; P1/P2/P3/P4=0% | 0% | 0% | 0% | Typed retained candidate structures and explicit selection evidence; activation audit |
| 3 | [POP-01 Population Campaign Execution and Experience](POP-01%20Population%20Campaign%20Execution%20and%20Experience.md) | Queued; Execution/Experience/Qualification=0% | 0% | 0% | 0% | Knowledge/LLM workflow UI-01/V1 and UI-02/P4 complete |
| 4 | [ML-01 Inherited Scientific Model Integration](ML-01%20Inherited%20Scientific%20Model%20Integration.md) | Standalone queued; M1/M2/M3/M4/V1=0% | 0% | 0% | 0% | UI-01/V1 + UI-02/P4, then POP-01 complete; qualified population/tool handoff |
| 5 | [LR-01 Local Worker Reliability](LR-01%20Local%20Worker%20Reliability.md) | Paused; pull R2 forward for blocking run failure | 25% | 33.33% | 0% | UI priority released or UI-01.05/R1 blocked; same-host diagnostic window |
| 6 | [UI-R01 Feedback Read Diagnostics](UI-R01%20Feedback%20Read%20Diagnostics.md) | Queued; pull forward if it blocks UI-01 | 0% | 0% | 0% | Bounded read diagnostic and activation review |

The owning tracker controls exact task/percentages; MBT controls priority and
mirrors current state. Complete each bounded gate before dependent implementation.
No completed-plan scope is reopened. [Selected profile handoff](../Audits/BP-09_Selected_Profile_Handoff.md)
names scientific, production and capacity successor triggers that are not activated.

## Owner targets: October 12-16, 2026 (America/Chicago)

Delivery targets for one integrated internal demo, not unconditional completion or
scientific-validation promises. Work one bounded task at a time; an unmet dependency
moves its downstream date and must be surfaced, never bypassed for a calendar target.
Track implementation in owning plans, not as a second percentage in this schedule.

| Target date | Owner / canonical scope | Demonstrable exit |
|---|---|---|
| Mon2026-10-12 | UI-01.05/K1 -> UI-01 N2.2/N2.4; then UI-02/P1 producer inventory | Real Knowledge owner available in demo; inspect claims/evidence and traverse campaign/domain links. Identify actual structure/formula producer contracts and missing pieces. |
| Tue2026-10-13 | UI-01.05/R1 -> N2.5 and remaining N2 comparison gates | Run starts a new campaign through Runtime/managed workers; nodes visibly transition, parallel work/failure/retry and resulting artifacts remain traceable. Resolve blocking LR-01 faults rather than hide them. |
| Wed2026-10-14 | UI-01.05/I1 -> N3, after N2; UI-02/P1/P2 handoff | Real LLM consumes pinned Knowledge and eligible node inventory, proposes a validated graph diff, and retains an explicit request for a missing capability. Preserve active/predecessor history. Complete structure/formula producer and explicit selection-or-unranked evidence handoff. |
| Thu2026-10-15 | UI-02/P3 after P1/P2 | Results opens the exact candidate's chemical formula and2D molecular/repeat-unit view, properties, provenance and recommendation rationale or explicit unranked status. |
| Fri2026-10-16 | UI-02/P4 and UI-01/V1, after owning gates | Actual browser question -> Knowledge + node inventory -> LLM graph curation/new-capability request -> new Run/live nodes -> formula/structure -> next iteration; isolated module tests, scoped audits and localhost/LAN regression. |

UI-01.05 refines existing unfinished N2/N3 scope; UI-02/P1 explicitly owns its
scientific representation/formula producer dependency. No plan-writing credit,
reopening of completed phases, or invented ranking.3D conformational modeling stays
outside this week's bounded target. LLM runs must record concrete budget caps and
usage/cost; existing provider authorization does not imply unlimited spend.

Per-node publication belongs to UI-01/N2.4 and V1: publish measured execution
outcomes separately from benchmarked scientific performance. Current synthetic run
has4/4 accepted scientific invocations (Hansen2/2, Arrhenius2/2), not100% accuracy.
No experimental accuracy percentage is available. Show Not scientifically
benchmarked until a relevant versioned dataset, method, sample count and error/
classification metric support a claim. See UI-01.05 for evidence and metric rules.

## Post-demo sequence: populations before inherited ML nodes

Owner direction2026-10-08 20:19:11: complete Knowledge/LLM campaign interaction and
UI-02 first, preserving next-week demonstration material. Then give
[POP-01](POP-01%20Population%20Campaign%20Execution%20and%20Experience.md) precedence:
multiple candidate generations, bounded scheduling/global selection, checkpoint
recovery and population-oriented visualization. Only after POP-01 qualification
activate [ML-01](ML-01%20Inherited%20Scientific%20Model%20Integration.md).

POP-01 overall0%, Build0%, Verification0%; phase mirrors:
Execution0% (POP-01.01 E1/E2/E3/E4=0%), Experience0% (POP-01.02 U1/U2/U3/U4=0%),
Qualification0% (POP-01.03 Q1/Q2/Q3/Q4=0%). Twelve equal child gates counted once.
Existing BP-08 generation/recovery implementation remains closed and reusable;
legacy population128/retained-attempt256/262144-byte bounds are not evidence of
1000-candidate scale. New profile and actual scale qualification belong to POP-01.

Owner topology addition2026-10-08 20:58:22: repeated process widening/convergence
is distinct from candidate scatter/selection. UI-01.05/I1 owns LLM authoring of
multi-input/output staged graphs; POP-01.01 owns typed intermediates, local joins,
bounded pairing and recovery; POP-01.02 owns stage/lineage visualization; POP-01.03
qualifies a19-stage synthetic process with repeated width changes. A control join
does not chemically combine materials. All affected queued phases remain0%; no
change to the Knowledge/LLM -> UI-02 -> POP-01 -> ML-01 priority sequence.

ML-01 remains standalone0%, Build0%, Verification0%; M1/M2/M3/M4/V1=0%.
It recovers inherited ML pipelines, reproduces corrected benchmarks and publishes
independent graph tools into the already qualified population workflow. The gate
follows actual acceptance, not demo date or calendar-week expiry.

The generic node-inventory-to-LLM mechanism and durable requests for unavailable
capabilities stay in UI-01.05/I1 before POP-01. Adding an existing tool instance and
requesting a new capability are separate operations; a request is not an executable
release. Minimal UI-02 structure/formula support stays in the demo scope. LR-01/UI-R01
may interrupt only for blocking faults with a named return point. No closed phase
is reopened, no app implementation changed by this planning checkpoint, and existing
implementation percentages are unchanged.

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
| 2026-10-12 11:20:06 | UI-01.08/P5.2 remains unmet; child90/P5=50. | Seventh original indeterminate;0 reported tokens. Diagnostic90 checks, five replays and actual browser pass. Seven/$1.75 held; UI-01.08c proposed. |
| 2026-10-12 09:06:13 | UI-01.08=90/P5=50; parent78/Build97.5. | Missing capability and actual browser passed; supported graph failed. Six/$1.50 holds exhausted. UI-01.08b pending. |
| 2026-10-12 08:54:22 | Approved UI-01.08a correction66.67%; parent85/P5=25 unchanged. | Planning0.128.0:124 scoped checks, isolated install, original v1 replay and actual-owner v2 preparation pass. Exact scope6/$1.50 retains four old holds; two new slots remain. |
| 2026-10-12 06:01:28 | UI-01.08/P5.2 blocked; child85%, parent77/Build96.25 unchanged. | Two original live outputs failed schema validation; exact replay/browser1440/390 pass. All four slots/$1 held, reported live$0.157331250. UI-01.08a proposes additive input repair and scoped budget extension; no cutover. |
| 2026-10-12 05:43:13 | UI-01.08/P5.1 complete; child85%, parent77/Build96.25. | One frozen scope/configuration, actual original allowance check and independent live worker preflight; zero paid calls at freeze. |
| 2026-10-12 05:34:30 | UI-01.08/P4 complete; child80%, parent76/Build95. | Actual-owner browser1440/390 proposal, successor/original, next-context and reload pass without new intent. |
| 2026-10-12 05:27:40 | UI-01.08/P4.4a/b complete; child78.33%,parent75.67/Build94.58. | Actual compiler/successor seed/carry integration and two-process receipt/conflict/stale-predecessor rejection pass. 98 schema/compiler checks; immutable schema cache32.5s->6.6s. P4.4c browser next;0paid calls. |
| 2026-10-12 05:02:01 | UI-01.08/P4.4a actual compiler composition repaired; percentages unchanged. |136initial +2focused source checks; independentPlanning0.127.1 resumes exact proposal and saves draft. Compiler pending diagnosis remains;0paid calls. |
| 2026-10-12 04:13:30 | UI-01.08/P4.4a isolated preparation and blocking Deployment configuration repair; percentages unchanged. |178 lifecycle/launch checks; independent0.19.1 wheel; actual Planning curation readiness. No live-demo or paid-model change. |
| 2026-10-11 22:52:39 | UI-01.08/P2.3b complete; P2=66.67%, child33.33%; UI01=66.67%/Build83.33%. |55initial/67final linkage and legacy journal checks; exact crash recovery/fencing; managed worker/compiler next;0paid calls. |
| 2026-10-11 22:43:52 | UI-01.08 public context complete; b.2=50%, P2=64.58%, child32.92%; UI01=66.58%/Build83.23%. |41 combined/4 focused assembly checks; original mixed context and denial retained; durable linkage next;0paid calls. |
| 2026-10-11 22:38:23 | UI-01.08/P2.3b.2 exact Runtime context checkpoint; percentages unchanged. |96 scoped Runtime/HTTP/replay/boundary checks; complete assembly and durable linkage next;0paid calls. |
| 2026-10-11 22:33:48 | UI-01.08/P2.3b.2 Knowledge/intent checkpoint; percentages unchanged. |83 Knowledge checks,114 policy regressions and1 exact compiler integration; Runtime/linkage remain;0paid calls. |
| 2026-10-11 22:24:28 | UI-01.08/P2.3b.2 partial context checkpoint; percentages unchanged. |78 multi-graph/replay and69 intent/context/boundary checks; public reads/linkage remain;0paid calls. |
| 2026-10-11 22:17:36 | UI-01.08/P2.3b.1 complete; P2=62.50%, child32.50%; UI01=66.50%/Build83.13%. |46 job/intake/HTTP/boundary checks; fenced replacement, immutable progress/original receipts;0paid calls. |
| 2026-10-11 22:05:19 | UI-01.08/P2.3a complete; P2=58.33%, child31.67%; UI01=66.33%/Build82.92%, N3/I1=31.67%. |55 cost/dispatch/boundary checks;4-call/$1 fixed-scope guard, exact bounded transport,0paid calls. |
| 2026-10-11 21:53:16 | UI-01.08/P2.2 complete; P2=50%, child30%; UI01=66%/Build82.5%, N3/I1=30%. | Distinct curation envelope/output;92 replay +108 SQL/compiler/provenance +13 boundary checks. Original graph/capture preserved;0paid calls. |
| 2026-10-11 21:34:41 | UI-01.08/P2.1 complete; P2=25%, child25%; UI01=65%/Build81.25%, N3/I1=25%. | Original receipt survives actual process replacement/read-only recovery;72 SQL/API +35 boundary/host +23 final intake checks.0paid calls. |
| 2026-10-11 21:24:47 | UI-01.08 approved; P1=100%, P2 active0%, child20%; UI01=64%/Build80%, N3/I1=20%. |219 contract/schema,74 boundary and38 actual-SQL policy/API tests; legacy schemas preserved,0paid calls. |
| 2026-10-11 20:04:00 | N2.4=100%, N2=100%, UI01=60%/Build75%; N3/I1 awaits UI-01.08 direction. | [Audit](../Audits/UI-01_N2.4_Recorded_Model_Inspection.md);362tests, actual retained OpenAI rationale/outcome, restored LAN unavailable-history check.0new paid calls. |
| 2026-10-11 19:50:00 | UI-01/N2.3 complete100%; N2=93.75%; UI01=58.75%/Build73.44%. N2.4 next. | [Audit](../Audits/UI-01_N2.3_Generation_Comparison.md);362 tests, actual generations0/2 and restored LAN regression. |
| 2026-10-11 19:26:42 | UI-01.07 closed100%; N2.2=100%, N2=87.5%; UI01=57.5%/Build71.88%. N2.3 next. | [Audit](../Audits/UI-01.07_Campaign_Provenance.md); actual compiler/draft/Research/Knowledge, original-run local/LAN1440/390, negative reads and process replacement.264 isolated owner and349 Studio tests. |
| 2026-10-11 18:51:49 | UI-01.07 P1/P2/P3=100%, P4 active0%, child75%; parent N2.2 remains50%. | Planning0.107/Gateway0.5 API; Studio0.24 with349 tests and scripted1440/390 provenance/launch regression. Actual owners and isolated install next. |
| 2026-10-09 10:20:00 | UI-01.06/R1=100%; UI-01.05=66.67%. N2.5=100%, N2=81.25%; parent56.25%/Build70.31%. | Actual local/LAN launch/results, same-run/container outage recovery and Knowledge traversal pass. Deployment502 installed tests/four probes, Studio337 checks. Scoped audit aligned; N2.2 resumes. |
| 2026-10-09 09:17:45 | UI-01.06=60%, L3 complete100%, L4 active0%; UI-01.05=53.33%, R1=60%. Parent55% unchanged. |335 Studio/125 owner checks; browser launch/reload/pinned plan/node polling at1440/390. [Audit](../Audits/UI-01.06_Launch_UI.md). Actual owners/workers next. |

## 2026-10-12 09:06:13 live evaluation checkpoint

P5.3 missing-capability original and actual browser1440/390 passed; returned to P5.2 supported graph correction. Six original slots/$1.50 held; zero calls remain. UI-01.08b proposes constrained generation and one additional $0.25 supported call. No serving cutover. Four live calls reported $0.242380500 cumulatively; new calls $0.085049250. Evidence: [retained results](../Audits/Evidence/UI-01.08-Live-v2/README.md). Earlier checkpoints describe historical allowance and status.

2026-10-12 12:14:25: First08c returned HTTP200 incomplete/max_output_tokens, no refusal, empty output and zero reported usage. Eight original holds/$2 retained; one conditional/$0.25 remains. Planning0.131.0 v4 selects reasoning none with same8192 ceiling, schema and prompt. 85 offline checks and independent installation g pass; new freeze pending. UI-01.08c83.33%; supported successor0%, parent90/P5=50; no cutover.

2026-10-12 12:16:59: Planning0.131.0 v4 passes85 offline checks, independent installationg, six exact prior replays and actual-owner stage2 freeze46893; drained. Eight/$2 original holds retained; final approved original/$0.25 ready. No live v4 request yet. UI-01.08c83.33%; parent90/P5=50 unchanged.

2026-10-12 12:58:36: Planning0.132.0 passes153 focused checks, independent installationh, seven byte-exact original replays and actual-owner extended freeze11742; drained. Nine/$2.25 holds retained; one approved16,384-output original/$0.30 remains. No new inference.08d66.67%; parent90/P5=50 unchanged.
