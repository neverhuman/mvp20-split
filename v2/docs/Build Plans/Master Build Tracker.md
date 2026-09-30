# Master Build Tracker

## Purpose and Authority

Program-level source of truth for Amphora v2 build priority, dependency order, current position and delivery gates. Each activated plan owns its detailed canonical phase/task tracker and evidence; MBT mirrors that status without duplicating task history. [Development Process](../Development_Process.md) governs execution.

Structure adapted from the user-authorized read-only JARVIS MBT review on `2026-09-23 11:04:44`. JARVIS deployment policies, permissions, priorities and completion claims are not imported.

## Program Tracker

- Status: BP-05 primary active; BP-06 through BP-09 queued; BP-01/BP-01A/BP-02/BP-03/BP-04 closed.
- Last refreshed: `2026-09-30 14:58:42` (America/Chicago).
- Baseline: [Product Requirements](../Architecture/Requirements/Product_Requirements.md), [Master Architecture](../../Architecture.md).
- Current priority: P4 / BP-05 - Graph Studio first vertical slice.
- Primary active implementation plan / phase / task: BP-05 -> BP-05.03 / Build / B1.
- Current task: BP-05.03/B1 actual-owner authoring/cancellation proof; Design and emergency consumer/browser checkpoints verified. Next: B2 conflict/revalidation/activation policy.
- Next task: BP-05.03/B2 conflict, revalidation and safe activation.
- Implementation completion: BP-04 closed100% (24/24); BP-05 active50% (8/16), .01/.02 closed100%, .03 active0% (Build0% / Acceptance0%); BP-06..09 queued0%.
- Active focus: reconcile definition draft persistence, registry-driven editing and Runtime safe-command boundaries.
- Blockers: no user decision pending; remaining actual-owner proof is B1 engineering work. Scientific/provider/host decisions remain later gates.
- Acceptance posture: deterministic Runtime and independent public observation/replacement accepted. Browser/UI and next-campaign authoring remain BP-05.
- Active exception: none.

## Initial Delivery Boundary

Internal use and demos for the first many releases; one user and one active autonomous campaign, with concurrent tool invocations. Single-server target is DGX Spark or partner Threadripper. Keep the scientific engine general; bio-available polymers are a likely application, not a fixed implementation pathway. Human edits and human-initiated replacements apply between campaigns.

Strictly isolate primary services and independently packaged tools. Use Pydantic/JSON Schema contracts, PostgreSQL-owned state, immutable artifacts, a single Graph Runner execution authority, an indexed tool universe and durable LLM proposals. Module READMEs capture the boundary conditions for independent rebuilds. K3s/Kubernetes tool replication is a proposed deployment profile; cluster selection and installation are not yet authorized implementation work.

The initial program proves software behavior using deterministic/synthetic fixtures and narrowly reviewed v1 reuse. Validated biological/polymer evaluators, real laboratory integration and scientific efficacy require separate evidence and scoped successor work.

## Current In-Flight Work

BP-05 is the sole primary active plan. Child trackers own delivery evidence; completed plans remain in the archive.

| Parent | Implementation | P1 Interaction | P2 Inspection | P3 Drafts | P4 Acceptance |
|---|---:|---:|---:|---:|---:|
| [BP-05](BP-05%20Graph%20Studio%20First%20Vertical%20Slice.md) | 50% (8/16) | 100% | 100% | 0% | 0% |

| Active canonical child | Overall | Build | Acceptance | Current task |
|---|---:|---:|---:|---|
| [BP-05.03](BP-05/BP-05.03%20Drafts%20and%20safe%20commands.md) | 0% | 0% | 0% | B1 authoring boundary |

BP-02 closed32/32, BP-03 closed18/16, BP-04 closed24/24. See [completed plans](Completed/README.md). New parent progress counts only its own deliveries.

## Queued Plans and Phase Mirrors

| Canonical plan | Status | Overall | P1 | P2 | P3 | P4 | P5 | P6 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| [BP-06 Knowledge Evidence and Source Loop](BP-06%20Knowledge%20Evidence%20and%20Source%20Loop.md) | Design specified | 0% | 0% | 0% | 0% | 0% | 0% | 0% |
| [BP-07 Autonomous LLM Campaign Supervision](BP-07%20Autonomous%20LLM%20Campaign%20Supervision.md) | Design specified | 0% | 0% | 0% | 0% | 0% | 0% | N/A |
| [BP-08 Evolutionary Search Integration](BP-08%20Evolutionary%20Search%20Integration.md) | Design specified | 0% | 0% | 0% | 0% | 0% | 0% | N/A |
| [BP-09 Single-Server Integrated Demo and Replacement Proof](BP-09%20Single-Server%20Integrated%20Demo%20and%20Replacement%20Proof.md) | Design specified | 0% | 0% | 0% | 0% | 0% | 0% | N/A |

Each parent phase now maps to one canonical child with four verified deliveries (three build plus one acceptance). Parent denominators are BP-03: 16, BP-04: 24, BP-05: 16, BP-06: 24, BP-07: 20, BP-08: 20, BP-09: 20; trackers above own current percentages. N/A means unscoped. [Readiness/handoffs](Planning_Readiness.md) records engineering and external gates. Design writing earns no implementation credit.

The owning plan tracker is canonical for overall and per-phase percentages. Refresh this mirror whenever a gate, scope, completion estimate, blocker or checkpoint changes, before handoff/commit. Percentages measure scoped implementation; acceptance and operational readiness are separate. No in-flight plan may appear here without numeric overall and phase completion.


[BP-01](Completed/BP-01%20Contract%20and%20Service%20Foundations.md) and BP-01A remain complete and archived. The queue below links canonical parents; ordering does not waive child gates. [Planning readiness](Planning_Readiness.md) owns cross-plan dependencies and scoped external decisions.

## Prioritized Build Queue

BP-05 is `primary_active`; BP-06 through BP-09 are `design_specified / queued`. The later roadmap has 34 canonical children. Each child names owned objects/contracts, algorithms, failure oracles and replacement acceptance. Completed plans remain in the archive.

| Order / ID | Completion | Proposed plan | Required predecessor gates | Bounded outcome / exit | Architecture owner |
|---|---|---|---|---|---|
| P4 / BP-05 | 50% | [Graph Studio First Vertical Slice](BP-05%20Graph%20Studio%20First%20Vertical%20Slice.md) | BP-04 runnable fixture and read/command contracts | Inspect actual live/historical execution, evidence, parallel branches and failures; edit next-campaign drafts, compare revisions and observe emergency termination; preserve autonomous progress | [Studio](../Architecture/Experience/Studio.md), [UI rules](../UI_Coding_Guidelines.md) |
| P5 / BP-06 | 0% | [Knowledge Evidence and Source Loop](BP-06%20Knowledge%20Evidence%20and%20Source%20Loop.md) | BP-01 contracts; BP-04 execution; BP-05 inspection | Minimal source/document/result ingestion, typed accepted-change replay, pinned knowledge revisions, bounded executable rules and explicit scientific acceptance receipts; demonstrate corrections affect later campaigns | [Knowledge](../Architecture/Knowledge/Knowledge_Architecture.md), [Data](../Architecture/Data/Data_Architecture.md), [experiments](../Architecture/Research/Experiments.md) |
| P6 / BP-07 | 0% | [Autonomous LLM Campaign Supervision](BP-07%20Autonomous%20LLM%20Campaign%20Supervision.md) | BP-03 tool discovery; BP-04 runner; BP-05 UI; BP-06 grounded context/receipts | Model-generated campaign proposals and text-to-graph extraction through validated contracts; durable scoped engagements, stale-proposal/fallback races, bounded repair and truthful terminal blockers; no routine human waits | [Planning](../Architecture/Agents/Planning.md), [Graph Runner](../Architecture/System/Graph_Runner.md) |
| P7 / BP-08 | 0% | [Evolutionary Search Integration](BP-08%20Evolutionary%20Search%20Integration.md) | BP-04 iteration/checkpoints; BP-06 applicability/evidence; BP-07 for LLM-guided topology | Adapt reusable numerical kernels to explicit generation/checkpoint history, separate representation fixtures and evidence-bound selection; parameter search precedes bounded topology proposals under successor-campaign rules | [Search](../Architecture/Campaigns/Search.md), [reuse baseline](../Architecture/Evolutionary_Code_Reuse_Baseline.md) |
| P8 / BP-09 | 0% | [Single-Server Integrated Demo and Replacement Proof](BP-09%20Single-Server%20Integrated%20Demo%20and%20Replacement%20Proof.md) | Selected host/model policy; BP-05/06/07 plus BP-08 for evolutionary demo claims | Reproducible target-host deployment, model/tool eligibility, restore/reconciliation, end-to-end autonomous demo and one independently rebuilt/replaced tool; prove replicated workloads if K3s is selected | [Topology](../Architecture/System/Runtime_Topology.md), [tool services](../Architecture/Capabilities/Tool_Services.md) |

This is the default sequencing, not nine permanent file-ownership buckets. Each plan owns a delivery step; later plans may refine earlier contracts with explicit compatibility evidence. BP-01 records packaging constraints early; BP-03 tests tool images/protocols locally. BP-09 integrates target-host operation rather than postponing all deployment design to the end. Synthetic fixtures/receipts stand in for unavailable scientific services until BP-06 and are labeled as such.

## Cross-Plan Milestones

| Milestone | Plans | Done when | Status |
|---|---|---|---|
| M1 ? Replaceable typed foundation | BP-01/02/03 | One standalone tool is discovered and invoked through pinned contracts with durable acceptance and recovery | Synthetic software foundation complete: BP-01/02/03 contracts, durable invocation/recovery and standalone tools accepted |
| M2 ? Inspectable executing graph | BP-04/05 | A user can follow parallel work, joins, failures and evidence in a real running fixture, then author a subsequent campaign | In progress: BP-04 execution/observation closed; BP-05 Studio active |
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
| 2026-09-30 14:58:42 | BP-05.03/B1 Design editor; child0%, parent50% | 88 scoped/118 isolated Studio tests;8 Design/10 navigation/7 Monitor browser scenarios |
| 2026-09-30 14:34:07 | BP-05.03/B1 emergency control; child0%, parent50% | 82 scoped/112 isolated Studio tests;5 emergency/7 Monitor browser cases |
| 2026-09-30 14:25:13 | BP-05.03/B1 comparison/scalar-form models; child0%, parent50% | 76 scoped/106 isolated Studio tests; rendering and owner proof remain |
| 2026-09-30 13:53:50 | BP-05.03/B1 numeric correction verified; child0%, parent50% unchanged | 1315 Python/96 Node/19 installs/REC-01..09;legacy replay and200 schemas preserved |
| 2026-09-30 11:59:37 | BP-05.03/B1 discovery partial; child0%, parent50% unchanged | 95 isolated Node tests;numeric literal encoding mismatch documented for direction |
| 2026-09-30 11:50:01 | BP-05.03/B1 command-loader partial; child0%, parent50% unchanged | 87 isolated Node tests;lost acknowledgement/exact-record/late-denial cases |
| 2026-09-30 11:45:52 | BP-05.03/B1 draft-state partial; child0%, parent50% unchanged | 82 isolated Node tests;7 owned state cases;save/edit race and denial fences |
| 2026-09-30 11:39:50 | BP-05.03/B1 consumer partial; child0%, parent50% unchanged | 75 isolated Node tests;14 authoring roots;exact schema bytes;original command receipts |
| 2026-09-30 11:27:45 | BP-05.03/B1 editor metadata partial; child0%, parent50% unchanged | 118 scoped tests;catalog100% statements/branches;8 isolated wheels;200 schemas preserve196 predecessors |
| 2026-09-29 23:33:01 | BP-05.03/B1 admission/publication partial; child0%, parent50% unchanged | 27 owned/87 scoped;1286 Python,65 Node,19 installs,REC-01..09; Studio authoring next |
| 2026-09-29 23:12:03 | BP-05.03/B1 retained material/contract partial; child0%, parent50% unchanged | 110 scoped tests,8 isolated wheels;196 schemas/194 predecessor bytes preserved; admission wiring next |
| 2026-09-29 23:03:28 | BP-05.03/B1 pinned validation partial; child0%, parent50% unchanged | 18 owned tests;1272 Python,65 Node,19 installs,REC-01..09; publication/UI remain |
| 2026-09-29 22:38:36 | BP-05.03/B1 partial; child0%, parent50% unchanged | Draft save/read;1263 Python,65 Node,19 installs,REC-01..09; validation/UI remain |
| 2026-09-29 22:06:45 | BP-05.02 closed100%; parent50% (8/16); .03 activation review | Final-source real-owner replacement scopee222d4cf32604d729ef12146860bc49c;65 tests per independent build; audit aligned |
| 2026-09-29 22:01:49 | BP-05.02/B3 verified75%; parent43.75% (7/16); V1 active | Actual-owner topology/evidence/replacement scope5be3aa3cba1445448eafffe060d2a124; dense browser and denial repair |
| 2026-09-29 21:53:46 | BP-05.02/B2 verified50%; parent37.5% (6/16); B3 active | 65 Node tests,24 browser cases, isolated Studio; bounded history/hidden policy/comparison |
| 2026-09-29 21:23:21 | BP-05.02/B1 verified25%; parent31.25% (5/16); B2 active | 1245 Python,53 Node,19 installs,REC-01..09;21 scripted browser cases, isolated Studio; B1 evidence retained |
| 2026-09-29 20:55:43 | BP-05.02/B1 catalog/lineage partial; percentages unchanged | 111 Python,45 Node, seven navigation browser cases, isolated consumer; full inspector journey pending |
| 2026-09-29 20:41:57 | BP-05.02/B1 navigation consumer partial; percentages unchanged | 39 Node tests, navigation + Monitor browser cases, isolated Studio build; catalog/evidence journey pending |
| 2026-09-29 20:32:51 | BP-05.02/B1 partial; child0%, parent25% unchanged | Authored topology/occurrence reads;109 Python +34 Node tests, isolated Studio build; full B1 remains open |
| 2026-09-29 20:06:20 | BP-05.01 closed100%; parent25% (4/16); .02/B1 active0% | Two isolated Studio builds;actual12/28-node Runtime browser proof,three replacements;scoped audit aligned |
| 2026-09-29 19:54:04 | BP-05.01 B3 verified75%; parent18.75% (3/16); V1 active | Seven browser failure cases,14 viewport scans; native fetch receiver repaired;30 Node tests, isolated build |
| 2026-09-29 19:43:46 | BP-05.01 B2 verified50%; parent12.50% (2/16); B3 active | Two actual browser candidates;200/10000 bounded scene, keyboard/viewport preservation;30 Node tests, isolated build |
| 2026-09-29 19:29:14 | BP-05.01 B1 verified25%; parent6.25% (1/16); B2 active | 28 Node tests; independent Node build; 1223 Python tests, 19 installs, REC-01..09 |
| 2026-09-29 18:50:04 | BP-04 closed100% (24/24); BP-05/.01 B1 active0% | Installed observer/Runtime replacement and all solver assertions passed; scoped/parent audits aligned |

Keep at most 25 checkpoint rows. [Completed plans](Completed/README.md) remain outside active tables. Update the owning plan first, then this summary and Restore when their state changes.
