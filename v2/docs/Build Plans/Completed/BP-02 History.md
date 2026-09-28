# BP-02 Historical Scope and Rebaseline

Original task accounting is superseded by the child tracker below; retained protocol deliverables remain complete.

# BP-02 Durable Runtime and Artifact Foundation

## Canonical Execution Tracker

- Status: **primary_active**; user authorized BP-02 work while later drafts are reviewed.
- Last refreshed: `2026-09-24 12:06:07` (America/Chicago).
- Scope/baseline: draft 1; completed BP-01 contracts/validation and BP-01A module tests/source-graph baseline; uncommitted working tree after `99d219c`.
- Owner: Campaign Runtime integration; Data/Artifacts owns artifact state and publication independently.
- Parent: program roadmap; [Master Build Tracker](../Master%20Build%20Tracker.md).
- Overall implementation: **8.33%** (1/12 verified tasks, rounded to two decimals). Twelve equally weighted tasks, two per phase; a task earns credit when its stated verification passes. Overall = completed tasks / 12; each phase = completed tasks / 2. Report rounding explicitly if needed. Drafting/review does not earn implementation credit.
- Current phase/task: P1 / T2 - publish narrow contracts and conformance fixtures.
- Next task: finish T2 contract/golden fixtures and P1 exit; only then start P2 / T3 local PostgreSQL stores.
- Remaining exit gate: P1-P6 gates, public-boundary crash/concurrency proof, independent builds and scoped closeout audit.
- Completed deliverables/evidence: T1 protocol decisions and bounded coherence review; [Runtime Command Protocol](../../Architecture/System/Runtime_Command_Protocol.md), [Artifact Publication Protocol](../../Architecture/System/Artifact_Publication_Protocol.md). Contract/database execution evidence remains pending.
- Blockers: none identified for planning; actual PostgreSQL availability and protocol decisions are P1/P2 gates, not assumed passed.
- Human acceptance: current user instruction authorizes BP-02 progression; no additional review gate for routine work. Later plans remain proposed for review; target host/provider decisions still gate dependent work.
- Active exception: user-directed BP-03 through BP-09 draft preparation completed alongside independent BP-02 T1; return point P1/T2.
- Pre-activation coherence review: `2026-09-24 12:06:07`, **corrected_ready**. User progression authorized; predecessor BP-01/BP-01A gates recorded. T1 resolves reservation-release race, canonical digest and cancellation/completion ordering; stale stack wording reconciled. No predecessor/owner conflict remains; later contracts and real PostgreSQL gates are not waived.

| Phase / status | Implementation | Prerequisites | Bounded deliverable | Required exit evidence |
|---|---:|---|---|---|
| P1 Protocol contracts / active | 50% | BP-01 and BP-01A complete; activation audit passed | Command, artifact and attempt semantics with versioned boundary contracts | T1-T2: reviewed transition/race tables and contract fixtures |
| P2 Isolated durable stores / pending | 0% | P1 gate | Runtime and artifact schemas/roles, migrations and transaction adapters | T3-T4: actual PostgreSQL tests, private-state denial and rollback/idempotency proof |
| P3 Artifact publication / pending | 0% | P2 gate | Standalone artifact process, immutable bytes and durable retention handshake | T5-T6: finalization/reservation/crash tests through owned boundaries |
| P4 Invocation lifecycle / pending | 0% | P3 gate | Fixture run admission, claims, leases, fencing, budget and cancellation | T7-T8: two-worker and cancellation/budget races |
| P5 Completion and outbox / pending | 0% | P4 gate | Atomic accepted completion and replayable dispatch/notification | T9-T10: duplicate/stale/conflicting completion and acknowledgement-loss tests |
| P6 Recovery and closeout / pending | 0% | P5 gate | Restart/reconciliation proof, replacement docs and scoped audit | T11-T12: process-kill matrix, independent builds, evidence and archival |

One phase and one task are active at a time after activation. Update this tracker first, then mirror overall and P1-P6 percentages in MBT at every completed task or scope change and before handoff/commit. Do not count integration tests again as duplicate implementation credit in later plans.

## Outcome for Review

A locally running runtime process and an independently running artifact process can accept a **synthetic prepared invocation**, claim it from competing worker processes, bind verified immutable outputs exactly once as an accepted runtime result, and recover after interrupted publication or completion. Duplicate transport delivery is allowed; duplicate accepted state is not. Operator queries expose authoritative receipts and state after restart.

This is the durable substrate for the Graph Runner. It does not yet compile/execute arbitrary campaign graphs, discover/deploy scientific tools or prove that a molecule can be synthesized. The current graph validation API continues reporting execution unavailable for arbitrary definitions.

### Architecture inputs

- [State and Consistency](../../Architecture/System/State_and_Consistency.md): runtime transactions, artifacts, idempotency and recovery.
- [Service Isolation](../../Architecture/System/Service_Isolation.md): private schemas/roles and independent services.
- [Foundation Decisions](../../Architecture/System/Foundation_Decisions.md): Python/Pydantic, PostgreSQL access/migrations and package boundaries.
- [Interfaces and Code Boundaries](../../Architecture/System/Interfaces_and_Code_Boundaries.md): command/query direction and public contracts.
- [Graph Runner](../../Architecture/System/Graph_Runner.md): future coordination/aggregation/supervision consumer.
- [Runtime README](../../../services/campaign_runtime/README.md) and [v1 solver baseline](../../../services/campaign_runtime/tests/fixtures/v1_solver/README.md): actual starting implementation and future behavior reference.

The older unresolved-stack wording in Interfaces is superseded by Foundation Decisions; P1 reconciles touched statements instead of reopening stack selection. Scientific/domain acceptance receipts remain Research/Knowledge-owned BP-06 work; runtime acceptance must not claim those receipts already exist.

## Scope and Ownership

| Boundary | Owns in BP-02 | Explicitly outside this boundary |
|---|---|---|
| `services/campaign_runtime/` | Run/activation/attempt state; command receipts; lease/fence; finite execution budget; accepted result/checkpoint references; audit/outbox; recovery | Artifact bytes/catalog; identity-service database; research/knowledge acceptance; registry business logic |
| `services/data_artifacts/` | Narrow artifact submodule only: provisional upload, verified publication, manifests, scoped access, reservation/retention and reconciliation | Dataset/model/source registries, scientific evidence eligibility and general ingestion |
| Public contract packages | Versioned command/receipt/artifact protocol DTOs and published schemas | Domain behavior, ORM entities, shared repositories or mutable global state |
| `deploy/local/` | Bounded developer composition: one PostgreSQL installation, separate runtime/artifact processes and owned volumes | K3s/k8s, Caddy/public exposure, target-host production provisioning |
| Verification tooling | Module selection/coverage plus explicitly owned public-boundary integration harness | An E2E-only development loop or a production scheduler hidden in test code |

Runtime internals decompose by behavior: command receipts, runs, invocations, completion, outbox and persistence adapters. Artifact internals separate publication, retention and storage. Each meaningful module gets a nearby README capturing invariants, failure modes and replacement constraints. Introduce folders when their phase implements them; do not pre-scaffold the rest of the service fleet.

One local PostgreSQL installation may host separate runtime and artifact schemas. Migration credentials and service credentials are distinct; production service roles cannot access each other's tables or apply migrations. No shared ORM, cross-private-schema joins/foreign keys or cross-service database transaction. Network calls and payload hashing stay outside short runtime transactions.

### Explicit exclusions

General graph scheduling/joins/scatter/iteration; tool registry and real scientific adapters; LLM supervision; Studio; knowledge/vector indexing; laboratory/provider submission; enterprise identity; real currency accounting; target-host performance promises. BP-02 records conservative uncertainty but does not implement real-world external-effect reconciliation. No edits to frozen v1 and no claim of v1 execution parity.

## Ordered Tasks and Gates

### P1 ? Protocol decisions and contract fixtures

**T1. Specify the command and state protocols.** Define proposed operations for fixture-run preparation, invocation claim/renewal/completion, cancellation, artifact upload/finalize/reserve/confirm/release and status/receipt queries. Define request canonicalization/digest rules, scope and actor binding, command identity uniqueness, same-ID/different-payload rejection, persisted terminal receipt semantics and retriable infrastructure errors. Define legal run/activation/attempt transitions, lease expiry/fence authority, checkpoint revision checks, finite integer budget reservation/settlement and stable reason codes. Assign every record/transition to exactly one owner. Produce transition and race tables in focused design leaves, linked here; resolve choices below.

**T2. Publish the narrow contracts and fixtures.** Extend existing contract families or add a focused artifact/runtime family where ownership warrants it. Preserve existing public behavior or explicitly version breaking wire changes, update schema manifests and name affected consumers. Contract fixtures cover valid and invalid scope/identity/version/digest/state combinations. Keep policy in domain objects and DTO construction behind explicit mappers. Define public-boundary integration scenarios before adapters are written.

**P1 gate:** deterministic JSON/Pydantic conformance passes; source-to-contract-to-owner map and failure tables have no unspecified commit/retention windows. Published contracts make synthetic-only authority and missing scientific acceptance explicit. No unreviewed runtime semantics hidden in a DTO.

### P2 ? Real PostgreSQL and isolated persistence

**T3. Establish local stores and migrations.** Pin a supported PostgreSQL image/version/digest for this developer profile after checking compatibility at implementation time. Use psycopg 3, SQLAlchemy 2 and Alembic per Foundation Decisions. Give each service independent migration history, credentials, health/configuration and disposable test database setup. Verify fresh creation and restart without losing state. Bound reset commands to named test resources; normal startup never deletes data. Record the chosen volume/filesystem assumptions.

**T4. Implement transaction and command receipt primitives.** Build runtime-owned repositories/units of work and artifact-owned counterparts without private cross-imports. Persist scope, immutable bindings, command digests/dispositions, per-run revisions and audit/outbox commitments. Specify consistent lock order, bounded whole-transaction retries and unique constraints. Prove same-command contention and rollback using multiple real database connections. A failed transaction must not leave a successful receipt or event; retry cannot repeat an external action.

**P2 gate:** migrations and service-role negative tests pass on PostgreSQL, never SQLite substitutes; separate connections establish conflict/rollback behavior; restarting processes retains receipts. No remote artifact operation occurs inside runtime transactions.

### P3 ? Artifact publication and retention

**T5. Implement the independent artifact process.** Provide the narrow public API and durable local-volume adapter. Stream provisional bytes with configured bounds; validate scope, size, digest and schema/media identity; publish an immutable reference only after verified durable storage and catalog commit. IDs cannot become arbitrary filesystem paths. Reject overwrite, corruption, cross-scope access and unsupported metadata. Same-content reuse must preserve scoped authorization. Document atomic file publication and the limit of process-crash versus host/power-loss evidence.

**T6. Implement retention reservations and reconciliation.** Runtime obtains a durable reservation receipt before attempting acceptance. Bind it to artifact, scope and intended runtime completion identity. Runtime stores the receipt with accepted output and emits a confirmation intent in its atomic outbox. Artifact owner confirms retention idempotently after commit. Pending reservations remain protective across timeout/acknowledgement loss: do not delete on a TTL alone. Resolve abandoned reservations only from an authoritative runtime outcome; unresolved uncertainty retains bytes. Test stale/released receipts and reconciliation races. Provisional-upload cleanup is bounded and testable; automatic deletion of finalized payloads is deferred unless its no-reference proof is included and tested here.

**P3 gate:** interrupted byte/catalog publication, finalize retry, runtime-before-commit failure and lost confirmation cannot expose unverified or dangling accepted artifacts. Runtime can use only public receipts, not artifact-table access. Retention tests demonstrate the safety of the full commit/acknowledgement window.

### P4 ? Claims, fences and bounded control

**T7. Admit fixture runs and claim attempts.** Implement a restricted developer fixture-admission path binding a reviewed synthetic invocation, exact tool/plan digest and input snapshot. This is not a general activation/compiler API and must be labeled in health/status. Persist one-active-campaign constraint, explicit activation identity and attempt history. Two worker processes compete for claims; only one current fence can own a given activation. Lease renewal/expiry/reclaim use authoritative database time and finite retry limits. Keep prior attempts for diagnostics.

**T8. Enforce budget, authority and cancellation races.** Reserve finite invocation/attempt units atomically, with an explicit retry charging/settlement policy; demonstrate parallel spenders cannot exceed the run budget. Implement a minimal local authority adapter with server-configured identities/grants and durable run/worker revocation, not caller-asserted authorization. Separate test/developer credentials from deployment identity. Cancellation prevents later claims and serializes against completion; expired/revoked/stale workers cannot publish accepted state. Non-idempotent/uncertain effects are recorded as unresolved and never silently reissued.

**P4 gate:** independent workers/DB connections prove exclusive claims, increasing fences, expiry/reclaim, budget exhaustion, cancellation/revocation ordering and one-active-run behavior. A synthetic worker may compute output; real tool routing/replica eligibility remains BP-03.

### P5 ? Atomic completion and outbox delivery

**T9. Implement the completion committer.** Validate exact invocation/attempt/fence, scope, tool/plan binding, expected state revision, configured authority and artifact reservation receipts. Commit accepted result/checkpoint references, activation/attempt state, budget settlement, command receipt and audit/outbox in one runtime transaction. Validation before commit does not replace rechecking live runtime authority under lock. A concurrent completion for another valid activation must retry/reconcile rather than lose work solely because the run revision advanced. Return stable duplicate receipts; reject identity reuse with changed content and stale attempts. Diagnostics from rejected workers are not accepted results.

**T10. Deliver and replay outbox commitments.** Implement bounded claiming/delivery/acknowledgement for dispatch, artifact retention confirmation and notifications. Delivery is at least once with stable event/operation identity; consumers deduplicate. Restart after send-before-ack must safely redeliver. Provide bounded status/receipt reads sufficient for integration tests and later UI clients. A deterministic public test consumer stands in for future tool routing; no production scheduler in this slice.

**P5 gate:** simultaneous duplicate/conflicting completions, stale fences, cancellation-vs-completion, concurrent valid outputs, missing/released artifact reservations and acknowledgement loss all have deterministic observed outcomes. No accepted result without its required receipt/audit/outbox, no double settlement, no remote network call held inside the commit transaction.

### P6 ? Recovery, replacement proof and audit

**T11. Run public-boundary recovery scenarios.** Start separate runtime/artifact/worker processes with PostgreSQL and durable volumes. Use explicit barriers/fault injection rather than sleep-only timing. Kill/restart at the crash points below, retain exact command/artifact/event IDs and inspect committed state through public queries. Prove unfinished state is reconciled, not recreated from worker memory. Reuse the v1 fixture's proposal/scoring-shaped payloads where useful, but seed prepared activations explicitly; do not claim the graph has run. Collect module test/line/branch reports and isolated package install smokes.

**T12. Document and close.** Update module READMEs with actual public contracts, private ownership, state migrations, recovery, retention limitations and replacement acceptance commands. Produce the local run/recovery guide and generated inventory if tooling exists. Audit the changed components against owning architecture; fix blocking drift, name nonblocking successor work and preserve evidence. Synchronize canonical percentages, MBT and Restore; archive only after all gates pass. Handoff BP-03 exact claim/artifact contracts and BP-04 runtime transition primitives.

**P6 gate:** all required recovery scenarios pass against real PostgreSQL and separate processes; existing foundation tests remain green; independent package builds enforce isolation. Scope audit is complete. No unresolved failure is renamed future work to claim 100%.

## Test Ownership and Evidence Matrix

Proposed folders are created with their owning implementation, not as empty placeholders. Extend `dev/test_scopes.json` and granular selection to match new modules and behavior areas. Module runs must not implicitly require the entire composition; database suites declare their PostgreSQL prerequisite. Cross-service harness lives in a separate integration folder, owned by BP-02 runtime integration and calling only public interfaces.

| Suite / owning folder | Required evidence | Earliest gate |
|---|---|---|
| `contracts/<family>/tests/` | Wire versions, canonical digests, strict negatives and receipt binding | P1 |
| `campaign_runtime/tests/persistence/` | PostgreSQL rollback, receipt contention, revision/uniqueness and role isolation | P2 |
| `data_artifacts/tests/publication/`, `tests/retention/` | Corruption, wrong scope, publication crash windows and retention handshake | P3 |
| `campaign_runtime/tests/invocations/` | Two claimers, lease reclaim, fence monotonicity, budget and cancellation/revocation | P4 |
| `campaign_runtime/tests/completion/`, `tests/outbox/` | Atomicity, concurrency, duplicates, stale outputs and at-least-once replay | P5 |
| `v2/tests/integration/durable_foundation/` | Separate-process crashes and public-boundary reconciliation | P6 |

Service test folders above are relative to their owning service. Each source module has a mapped test suite and explicit coverage gaps. Report line and branch coverage per owner, including unexecuted owned files; do not use an aggregate percentage as a substitute for required failure scenarios. E2E/whole-composition runs are reserved for cross-boundary evidence.

Required crash points: upload before finalization; immutable bytes written before catalog commit; reservation issued before runtime commit; runtime transaction rolled back; runtime commit before response; runtime commit before artifact confirmation; outbox send before acknowledgement; worker lease expiry with late completion; restart with pending/uncertain work. Distinguish injected process-crash proof from power-loss and target-host durability, which need later deployment evidence.

## Proposed Defaults and Decisions to Resolve in P1

These are recommendations for review, not implemented guarantees or questions that require a separate user decision by default.

| Topic | Draft direction | Gate / unresolved detail |
|---|---|---|
| Artifact backend | Immutable files on an owned durable server volume, catalog in artifact-owned PostgreSQL schema | T1 specifies receipt protocol; T5 records filesystem/publication assumptions |
| Acceptance concurrency | Serialize short commits per run; independent worker computation remains parallel | T1 specifies lock order and stale-revision retry behavior; P5 proves concurrent valid results |
| Retention | Durable reservation until explicit reconciliation; conservative retention on unknown outcome | No elapsed-time-only deletion; T1 defines safe release/no-reference proof |
| Initial authority | Local developer credentials and server-owned policy adapter with durable cancellation/revocation | Not enterprise identity or remote deployment authorization; P4 tests the real local boundary |
| Budget | Finite integer execution/attempt units; separate reserved, settled and released dispositions | T1 fixes retry/uncertainty charging policy; monetary/model quotas later |
| Fixture admission | Prepared synthetic invocations with immutable pinned inputs; no general graph activation | BP-03 supplies indexed callable tools; BP-04 supplies compiler/interpreter |
| External side effects | Reject unsupported effectful dispatch; preserve uncertainty if encountered | Real provider reconciliation remains later tool/laboratory work |
| Compatibility | Existing validation remains available; new command families explicitly versioned | T2 names consumer/version changes; unsupported old durable state rejects explicitly |

## Review Findings and Scope Control

Initial bounded review found no architectural ownership conflict. T1 now specifies artifact reservation lifetime/release safety, command canonicalization and completion retry/cancellation ordering in the linked protocol leaves. T2 must encode these in contract fixtures before P2 begins. The fixture-admission restriction avoids depending on BP-03's future registry or BP-04's compiler to build BP-02. Research/Knowledge receipts remain separate from runtime result acceptance. The test/source baseline is useful input, not runnable evidence.

Review changes are recorded here with scope and completion-denominator impact. If recovery requires a new major service or real scientific workflow, propose a bounded successor rather than silently expanding BP-02. Leave BP-01/BP-01A closed. This checkpoint completes T1 protocol design only; no database creation, dependency installation or deployment occurred. BP-03 through BP-09 drafts are an authorized planning side task and remain at 0%.

## Recent Checkpoint

`2026-09-24 12:06:07`: T1 complete. Checked command identity/default canonicalization for idempotency; traced prepare/reserve/commit/confirm and irrevocable abort/release for response loss and cancellation; checked lease/budget/state ownership and race tables against the declared T1 operations. Corrected stale stack decisions in the interface design. Evidence is design review, not executable race verification. P1 is 50%; overall 1/12 = 8.33%. Next exact task T2. Later draft plans are available through MBT; their creation earns no implementation credit.

## Closeout Record

Pending implementation. Record exact revision, timestamps, test and artifact IDs, scoped audit link, known limitations and successor ownership here when P6 completes. Use a companion history file if checkpoints grow beyond a concise active tracker. User review of this draft is distinct from implementation completion or scientific acceptance.

## Accounting clarification 2026-09-25 08:47:38

The preliminary 34-child-delivery denominator included pure design gates S1 and A1. Corrected to 32 implementation deliveries, with both mandatory design gates preserved separately. Contract child contributes five completed tasks; persistence currently contributes four with S6 acceptance pending. Parent 9/32 = 28.13%; no elapsed-effort claim.

## Older MBT checkpoint archive

| 2026-09-22 20:53:09 | Pydantic/JSON Schema contract architecture added as sixth System child; no implementation or reopening of closed plans | [Contract architecture](../../Architecture/System/Contract_Architecture.md) |
| 2026-09-22 20:30:31 | Proposed runtime topology, graph machine, persistent-state protocol, interfaces and complete research loop delivered; single-server baseline confirmed | [Completed system plan](System%20Architecture%20Plan.md), [audit](../../Audits/System_Architecture_Closeout.md) |
| 2026-09-22 19:04:40 | Twenty deeper contracts, eight coordination summaries, three flow diagrams and architecture-depth template complete | [Completed detail plan](Architecture%20Detail%20Plan.md), [audit](../../Audits/Architecture_Detail_Closeout.md) |
| 2026-09-22 16:45:29 | Architecture documentation plan complete: 8 domains, 20 focused contracts, 102 requirement-section owners; no runtime code | [Completed plan](Architecture%20Decomposition%20Plan.md), [closeout audit](../../Audits/Architecture_Decomposition_Closeout.md) |
| 2026-09-22 13:47:22 | Local SDLC rules, tracker hierarchy, templates and drift surfaces established; no runtime implementation claimed | [Process](../../Development_Process.md), [process alignment record](../../Audits/Architecture%20Drift%20History.md) |

| 2026-09-22 20:57:10 | Careful readiness review: bounded implementation can start after scope/assumption closure; nine findings and six owner questions recorded | [Readiness review](../../Audits/Architecture_Readiness_Review.md) |

| 2026-09-22 21:03:27 | Initial internal/demo autonomous profile and replaceable-module boundaries recorded; owner questions answered, no runtime activated | [Delivery profile](../../Architecture/Requirements/Product_Requirements.md#initial-delivery-profile), [module template](../../Templates/Module%20README%20Template.md) |

| 2026-09-23 09:41:20 | Strict service isolation and proposed independently replicated tool workloads; source layout/state boundaries refined, no deployment | [Isolation](../../Architecture/System/Service_Isolation.md), [tool services](../../Architecture/Capabilities/Tool_Services.md) |

| 2026-09-23 09:48:47 | Graph Runner coordination/aggregation/supervision and durable LLM decision protocol documented; architecture only | [Graph Runner](../../Architecture/System/Graph_Runner.md) |

| 2026-09-23 09:51:08 | High-level specs/supporting references relocated into Architecture/Requirements; links and PDF preservation checked | [Requirements guide](../../Architecture/Requirements/README.md) |

| 2026-09-23 11:04:44 | Expanded MBT into initial program dashboard with nine queued planning areas, dependency gates, four milestones and exact next planning task; implementation unactivated | This tracker; [plan template](../../Templates/Build%20Plan%20Template.md) |

| 2026-09-23 19:55:48 | BP-01 complete: 39 tests, four independent wheel installs, strict schema/API boundary and replacement docs; archived after scoped audit | [Plan](BP-01%20Contract%20and%20Service%20Foundations.md), [audit](../../Audits/BP-01_Foundation_Closeout.md) |

| 2026-09-24 09:01:20 | BP-01A complete at 100%, all four phases 100%; module test ownership, granular coverage, extracted v1 graph and scaffold; 44 tests pass | [Plan](BP-01A%20Module%20Tests%20and%20V1%20Graph%20Baseline.md), [audit](../../Audits/BP-01A_Test_and_Graph_Baseline_Closeout.md) |

| 2026-09-24 09:10:34 | BP-02 draft authored for user review: six phases, twelve tasks, all implementation percentages 0%; no activation | [Canonical draft](BP-02%20Durable%20Runtime%20and%20Artifact%20Foundation.md) |

| 2026-09-24 12:06:07 | BP-03 through BP-09 first drafts published at 0%; BP-02 authorized and T1 complete, P1 50% / overall 8.33%; next T2 | Canonical plan links above; [protocol decisions](../../Architecture/System/Runtime_Command_Protocol.md) |

| 2026-09-24 12:10:07 | User UI references mapped to Studio modes and BP-05/06/08 prototype tasks; percentages unchanged, BP-02 remains P1/T2 | [Reference map](../../Architecture/Experience/Interaction_References.md) |

| 2026-09-25 08:49:41 | BP-02 decomposed; contracts and isolated persistence children closed; parent 31.25% (10/32), next .03/A1 | [Persistence audit](../../Audits/BP-02.02_Persistence_Closeout.md); 119 tests, eight independent builds |

| 2026-09-25 13:40:55 | Roadmap maturation: 34 canonical children added, four open BP-02 children deepened; implementation percentages unchanged | [Planning review](../../Audits/Planning_Maturity_Review.md), [readiness/handoffs](../Planning_Readiness.md) |

| 2026-09-25 13:54:17 | Amphora Lab insights incorporated into ten BP-05/06/07/08 children; authority, trace, material identity and view tests specified; percentages unchanged | [Reference/ownership map](../References/Amphora_Lab_Insights.md) |

| 2026-09-25 16:59:22 | BP-02.03 A2 complete; child 20%, V1 25%, parent 34.38%; next A3 | 141 tests, eight independent builds; artifact suite 30, two-process fencing |

| 2026-09-25 17:12:21 | BP-02.03 A3 complete; child 40%, V1 50%, parent 37.50%; next A4 | 158 tests, eight independent builds; finalizer crash/replay and atomic publication verified |

| 2026-09-26 16:31:31 | BP-02.03 A4 complete; child 60%, V1 75%, parent 40.63%; next A5 | 172 tests, eight independent builds; scripted authenticated runtime proof; Git identity pending |

| 2026-09-28 10:56:19 | BP-02.03 A5 complete; child 80%, V1 100%, parent 43.75%; next A6 | 182 tests/eight builds; crash-safe cleanup and bounded reconciliation |

| 2026-09-28 11:05:08 | BP-02.03 closed/audited at 100%; parent 46.88%; .04 I1 activated | 188 tests/eight independent builds; installed HTTP artifact acceptance |

| 2026-09-28 11:11:49 | BP-02.04 I1 passed; child 16.67%, V1 20%, parent 50%; next I2 | 21 pure policy tests; full gate 209/eight builds |

| 2026-09-28 11:18:55 | BP-02.04 I2 passed; child 33.33%, V1 40%, parent 53.13%; next I3 | Admission contention/replay/rollback; 218 tests/eight builds |

| 2026-09-28 11:28:20 | BP-02.04 I3 passed; child 50%, V1 60%, parent 56.25%; next I4 | Two-process claims/live-clock renewal; 224 tests/eight builds |

| 2026-09-28 11:37:28 | BP-02.04 I4 passed; child 66.67%, V1 80%, parent 59.38%; next I5 | Budget/rollback/prepared-intent guards; 229 full tests, 41 scoped |
