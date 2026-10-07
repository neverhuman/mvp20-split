# Master Build Tracker

## Purpose and Authority

Program-level source of truth for Amphora v2 build priority, dependency order, current position and delivery gates. Each activated plan owns its detailed canonical phase/task tracker and evidence; MBT mirrors that status without duplicating task history. [Development Process](../Development_Process.md) governs execution.

Structure adapted from the user-authorized read-only JARVIS MBT review on `2026-09-23 11:04:44`. JARVIS deployment policies, permissions, priorities and completion claims are not imported.

## Program Tracker

- Status: BP-08 closed100%; BP-09.01/.02 closed; BP-09.03 B1.3 active.
- Last refreshed: `2026-10-07 00:32:46` (America/Chicago).
- Baseline: [Product Requirements](../Architecture/Requirements/Product_Requirements.md), [Master Architecture](../../Architecture.md).
- Current priority: P8 / BP-09 - Single-Server Integrated Demo and Replacement Proof.
- Primary active task: BP-09.03/B1.3 TLS tool connectivity, workers and owner records.
- Next task: BP-09.03/B1.4 actual-model browser/API trace.
- Implementation completion: BP-09=42.5%,8.5/20 verified delivery weight, eight closed gates; completed plans are in the archive.
- Active focus: scoped TLS container-to-host connectivity; selected model adapter/allowance independently verified.
- Blockers: none for local installation engineering. Provider/integrated demonstration gates remain scoped to later children.
- Acceptance posture: BP-08 synthetic engineering accepted20/20; BP-09.01/.02 local preflight/infrastructure accepted; full autonomous campaign/model integration pending.
- Active exception: none.

Queued successor: [SQ-01 Scientific Quality and Iteration Views](SQ-01%20Scientific%20Quality%20and%20Iteration%20Views.md), 0%, after BP-06 owner projections and BP-07.03 proposal contracts. Preserves closed BP-05; no change to active BP-06 denominator.

## Initial Delivery Boundary

Internal use and demos for the first many releases; one user and one active autonomous campaign, with concurrent tool invocations. Owner selected the current local computer and computer-only access for this stage; DGX Spark/Threadripper remain future targets. Keep the scientific engine general; bio-available polymers are a likely application, not a fixed implementation pathway. Human edits and human-initiated replacements apply between campaigns.

Strictly isolate primary services and independently packaged tools. Use Pydantic/JSON Schema contracts, PostgreSQL-owned state, immutable artifacts, a single Graph Runner execution authority, an indexed tool universe and durable LLM proposals. Module READMEs capture the boundary conditions for independent rebuilds. K3s/Kubernetes tool replication is a proposed deployment profile; cluster selection and installation are not yet authorized implementation work.

The initial program proves software behavior using deterministic/synthetic fixtures and narrowly reviewed v1 reuse. Validated biological/polymer evaluators, real laboratory integration and scientific efficacy require separate evidence and scoped successor work.

## Current In-Flight Work

BP-09.01/.02 closed100%; BP-09.03 active12.5%,Build16.67%,Acceptance0%; parent42.5%,8.5/20 weight/eight closed gates. BP-08 closed100%,20/20; see [completed plans](Completed/README.md).

## Queued Plans and Phase Mirrors

| Canonical plan | Status | Overall | P1 | P2 | P3 | P4 | P5 | P6 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| [BP-09 Single-Server Integrated Demo and Replacement Proof](BP-09%20Single-Server%20Integrated%20Demo%20and%20Replacement%20Proof.md) | Active | 42.5% | 100% | 100% | 12.5% | 0% | 0% | N/A |

Scoped milestone fractions measure verified work within their existing delivery weight; closed-gate counts remain separate. BP-06 is archived24/24. Do not treat milestone counts as effort estimates.

Each parent phase now maps to one canonical child with four verified deliveries (three build plus one acceptance). Parent denominators are BP-03: 16, BP-04: 24, BP-05: 16, BP-06: 24, BP-07: 20, BP-08: 20, BP-09: 20; trackers above own current percentages. N/A means unscoped. [Readiness/handoffs](Planning_Readiness.md) records engineering and external gates. Design writing earns no implementation credit.

The owning plan tracker is canonical for overall and per-phase percentages. Refresh this mirror whenever a gate, scope, completion estimate, blocker or checkpoint changes, before handoff/commit. Percentages measure scoped implementation; acceptance and operational readiness are separate. No in-flight plan may appear here without numeric overall and phase completion.


[BP-01](Completed/BP-01%20Contract%20and%20Service%20Foundations.md) and BP-01A remain complete and archived. The queue below links canonical parents; ordering does not waive child gates. [Planning readiness](Planning_Readiness.md) owns cross-plan dependencies and scoped external decisions.

## Prioritized Build Queue

BP-09 activation follows accepted BP-08. Completed scope stays archived; remaining child gates remain sequential.

| Order / ID | Completion | Proposed plan | Required predecessor gates | Bounded outcome / exit | Architecture owner |
|---|---|---|---|---|---|
| P8 / BP-09 | 42.5% | [Single-Server Integrated Demo and Replacement Proof](BP-09%20Single-Server%20Integrated%20Demo%20and%20Replacement%20Proof.md) | Selected host/model policy; BP-05/06/07 plus BP-08 for evolutionary demo claims | Reproducible target-host deployment, model/tool eligibility, restore/reconciliation, end-to-end autonomous demo and one independently rebuilt/replaced tool; prove replicated workloads if K3s is selected | [Topology](../Architecture/System/Runtime_Topology.md), [tool services](../Architecture/Capabilities/Tool_Services.md) |

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
| 2026-10-07 00:32:46 | BP-09.03/B1.1-B1.2 complete; child12.5%,parent42.5%,8.5/20 weight. | Planning0.101 exact envelope, configured provider, durable scope costs;220regressions/114independent tests, no paidcalls. |
| 2026-10-06 22:46:13 | BP-09.02/B1 complete;child25%,parent25%,5/20. | Independent gateway/Studio, actual browser sessions and responsive Monitor fixture;27Python/241Node checks; CSP repaired. |
| 2026-10-06 22:21:57 | BP-09.02/B1.03 complete;child18.75%,parent23.75%. | Actual supervisor commands, installed Registry failure/restart, Windows job cleanup, fixed startup/status race;92checks. |
| 2026-10-06 22:07:00 | BP-09.02/B1.02 complete; child12.5%, parent22.5%. | Dedicated loopback stores, DPAPI vault,12restricted identities,Qdrant auth and stable resume;63regressions. |
| 2026-10-06 21:41:09 | BP-09.01 closed100%;parent20%,4/20. Local computer/local access selected. | Actual local storage/socket/CLI and clean independent package;47isolated tests1.305s. BP-09.02 next. |
| 2026-10-06 20:09:20 | BP-09.01 B1/B2 complete; child50%,Build66.67%,parent10%. B3 awaits selected host/access/exposure. | Strict profiles,read-only probes,policy,CLI and nonexecuting drain/restart order;59checks plus47final regressions. |
| 2026-10-06 19:57:27 | BP-08 closed100%,20/20; BP-09 activation next. | All five audits aligned; corrected successor/recovery and exact-source images;632schemas/import guards;28final checks19.46s; zero paid calls. |
| 2026-10-06 19:47:13 | BP-08.05/B2.01 complete;child37.5%,parent87.5%. |29correction/manifest checks; explicit new revision, old fitness/resume rejected, original ranks preserved. |
| 2026-10-06 19:27:13 | BP-08.05/B1 complete;child25%,parent85%,17/20. | Actual partial evaluation kill/fresh Runtime/rebuilt worker; six equivalent checkpoints,30completions/31attempts,108unique reservations. |
| 2026-10-06 19:18:08 | BP-08.05/B1.02 complete;child16.67%,parent83.33%. | Reconstructed adapter28workspace/11isolated checks; public kernel/contracts/SDK only; partial-evaluation HTTP next. |
| 2026-10-06 19:12:48 | BP-08.05/B1.01 complete;child8.33%,parent81.67%. |84checks; manifest59statements6branches100%; byte/chain/revision/restore oracles. |
| 2026-10-06 19:06:28 | BP-08.04 closed100%;parent80%,16/20. | Image-matched fresh Planning/Runtime/worker replacement, history/new execution,28 regressions and aligned scoped audit. |
| 2026-10-06 19:02:07 | BP-08.04/V1.01 complete;child83.33%,parent76.67%. | Two actual Linux images, exact installed closures/schema bytes, offline golden and nonroot isolation; fresh replacements building. |
| 2026-10-06 18:58:33 | BP-08.04/B3 complete;child75%,parent75%,15/20. |155 failure/accounting regressions;14 process/boundary checks; actual kills before/after combined commit. |
| 2026-10-06 18:53:43 | BP-08.04/B2 complete;child50%,parent70%,14/20. | Actual public topology handoff, exact carry/new worker, retained comparison and restart replay;28 regressions. |
| 2026-10-06 18:36:16 | BP-08.04/B2.02i complete;child43.75%,parent68.75%. |Approved draft-successor correction;205tests,632schemas/630preserved, independent installs; actual topology handoff next. |
| 2026-10-06 16:44:02 | BP-08.04/B2.01 complete;child37.5%,parent67.5%. |44tests/10pairs/320CLI evaluations, zero paid calls; B2.02 draft-successor decision pending. |
| 2026-10-06 16:22:40 | BP-08.04/B1 complete;child25%,parent65%,13/20. | Planning0.98 topologyAPI/host;153checks;438statements30branches100%; faircomparison next. |
| 2026-10-06 16:15:33 | BP-08.04/B1.03i complete;child20.83%,parent64.17%. | Planning0.97/0020;128regressions+71focused;immutable record/current readers; API/host next. |
| 2026-10-06 16:01:13 | BP-08.04/B1.02 complete;child16.67%,parent63.33%. | 88checks; pure bounded topology policy163statements/eightbranches100%; owner persistence next. |
| 2026-10-06 15:53:23 | BP-08.04/B1.01 complete;child8.33%,parent61.67%. | 29wire/schema/boundary checks;630schemas preserve622; pure policy next. |
| 2026-10-06 15:46:56 | BP-08.03 closed100%;parent60%,12/20. | Scoped audit aligned; image/Registry/replacement/history accepted; BP-08.04/B1 active. |
| 2026-10-06 15:44:05 | BP-08.03/V1.02 complete;child91.67%,parent58.33%. | 7Registryprofiles,15closures,18invocations;retainedhistory/replacement/currentdenial passed. |
| 2026-10-06 15:29:16 | BP-08.03/V1.01 complete;child83.33%,Acceptance33.33%,parent56.67%. | 4Linuximages/7profiles;offlinegoldens/nonroot/schema/isolation;Registryreplacement next. |
| 2026-10-06 15:21:45 | BP-08.03/B3 complete;child75%,Build100%,parent55%,11/20. | 217checks;POL01..04/comparison/gates/recovery matrix; image/Registry/audit next. |
