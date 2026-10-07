# Planning persistence boundary

- Reviewed implementation: Agent Planning0.69; compiler selection/lease and operation/event SQL verified; v1 original-history regression preserved.
- State: private planning schema, forward migrations planning_0001 through planning_0015. Never run Planning<=0.69 migrators on0015.
- Responsibility: immutable request, attempt, observation, policy, reservation, settlement, issuance and late-evidence records. The orchestration module composes these objects; Runtime alone owns campaign decisions.

## Repair preparation journal

planning_0009 adds SELECT/INSERT-only repair_preparations, keyed by scoped child engagement and linked to exact family, member, task, request and parent trace. PreparationJournal re-renders/revalidates outside SQL, then locks family before request and binds the manifest to owned membership/task facts. First registration after dispatch issuance or observation is rejected; an unissued reservation is allowed. Exact replay preserves canonical bytes and database timestamp; changed packet/input availability conflicts. Readback verifies all duplicate identities and fingerprints. Store only bounded input references/hashes/gaps and packet digest/size, never another raw-source repository. Planning<=0.22 migrators/writers must not touch the new preparation workflow. Earlier migrations/history remain immutable.

## Authority and immutable journal

The migrator role applies explicit forward DDL; imports never migrate. The service role has SELECT/INSERT only, no history update/delete or peer-table authority. A trusted Principal supplies actor, scope and operation grants; model text and caller DTOs cannot choose them. Readback requires the original request actor and exact scope. Raw provider captures are private scoped diagnostics, not a public Artifact or an unauthenticated endpoint.

PlanningJournal.register preserves exact canonical request bytes and fingerprint. Same-actor exact retry replays; changed identity/content conflicts. begin_attempt is a private legacy journal primitive, not authorization to call a provider. Unknown request, absent attempt, pending intent and terminal observation remain distinct. Ordinals are sequential and bounded by the immutable request. record validates attempt/capture size/hash/completeness and any successful proposal; first observation wins and differing writes conflict. The internal transaction helper lets DispatchJournal share that invariant without nested transactions.

Request writes serialize under a request-key advisory transaction lock; enrolled budget, dispatch, settlement and trace operations first acquire the immutable family lock. No SQL lock spans a provider, filesystem or peer call. Database timestamps describe persistence time, not fabricated provider duration. Reconstruction revalidates canonical identity and capture bindings. Existing unbudgeted histories stay readable and cannot be retroactively relabeled authorized.

## Reservation and conservative settlement

BudgetLedger.reserve validates the trusted private policy and atomically stores exact policy/demand with the attempt intent. Existing reservation replay preserves its original identity/time; replay is not a repeated dispatch grant. Changed policy/request conflicts; failed admission rolls back new policy/intent rows together. The next ordinal needs a prior observation and settlement. Per-request limits remain in force. Enrolled requests also share their root ceilings across every family member; Runtime's campaign budget remains separate.

SettlementJournal.settle/read stores and verifies immutable observation hash, reserved_floor_v1 charge and timestamp. The v1 policy has no refund authority: each component is max(reserved, observed lower bound). Unknown, missing, interrupted, zero or low reported usage never releases the floor. Reported overage remains exact, even when certainty is unknown, and stops further reservation/issuance. This does not gate scientific quality. Exact duplicate settlement replays; pending/unreserved attempts cannot settle. Future refund behavior requires a deliberate new profile, preserving v1 policy bytes and history.

## Issuance, expiry and late evidence

DispatchJournal.issue returns a newly committed random token/database deadline only to its first inserting worker. Existing issuance returns no grant, even to the same caller. The reserved attempt must be unobserved; any known request overage blocks new issuance. complete and recover serialize against each other: timely response may commit, while expired issuance produces an immutable unknown observation with reason attempt_deadline. Deadline recovery never assumes the external call was free.

A late response cannot overwrite recovered history. One bounded late_observations record preserves its exact bytes/usage and derived charge, with identical replay and changed-duplicate conflict. read_late verifies capture and charge against the original request/policy. Admission totals use per-component maxima across reservation, settlement and late evidence, preventing both undercounting and duplicate charge for one physical attempt. Late overage stops future reservation and unissued successors; already-issued effects cannot be undone.

The deadline fences accepted observations, not physical remote cancellation or network exactly-once effects. A real adapter must bound transport and avoid hidden physical retries. This package has no live adapter, public server, private peer-state mutation or Runtime acceptance. Legacy observed/reserved records without issuance remain readable; they are not automatically resumable as authorized dispatches.

## Replacement and verification

Preserve canonical policy/request/observation bytes, exact attempt identities, first-writer outcomes, unknown/pending distinctions, actor/scope checks, conservative arithmetic and all issuance/late evidence. Migrations are forward-only and immutable after application; Planning<=0.13 migrators must not run against planning_0007. There is no fixture reset, downgrade or deletion authority.

Owned tests/persistence cover actual PostgreSQL migration/idempotency, competing writers, admission rollback and limits, legacy distinction, settlement/retry, expiry/late races, stored-record integrity and SQLSTATE42501 for forbidden mutations. tests/orchestration separately cover bounded composition and non-starvation. dev/verify_planning.py installs the public dependency closure twice and verifies isolated owner/process readback; dev/verify_planning_recovery.py exits installed workers abruptly at five committed boundaries. The latter uses exclusive synthetic call markers, not real remote effects. Neither harness claims independently authored replacement code, power-loss durability, scientific validity or live model quality. Detailed evidence lives under docs/Audits/Evidence/BP-07-Planning.

## Versioned observation storage

planning_0005 conditionally extends encoded observations and late observations to256KiB only for explicit string format2. Missing/numeric/legacy version records do not gain that allowance; v1 retains64KiB. Raw capture remains64KiB for both. The shared strict decoder and closed output catalog reconstruct either legacy ReferenceProposal or TypedProposal from retained capture before writing/replaying. Budget/issuance/settlement rows and all prior observation bytes remain unchanged. Actual SQL cases verify the conditional constraints and format2 late output/charges; an optional --legacy-manifest argument to dev/verify_planning.py verifies retained predecessor project hashes after migration using only service credentials.

## Extraction task and trace history

ExtractionJournal registers one immutable ExtractionSnapshot per engagement, bound to the already registered actor/request digest; task identities cannot move between requests. record accepts task/observed-attempt identity and optional prior trace reference, then derives all provenance from stored facts. Pending/unknown attempts cannot be traced. The task row is not dispatch authorization. Existing exact traces replay original bytes/digest/database timestamp; changed trace identity/content or parent conflicts. planning_0006 adds own extraction_tasks and extraction_traces with task/request/observed-attempt FKs, unique physical-attempt trace, exact parent digest FK, size bounds256KiB/1MiB and SELECT/INSERT-only role grants.

Readback verifies task/request bytes, trace digest, database identity columns and complete parent chain, then reconstructs the projection from immutable observations. Parent records must exist, share source/target/scope and original actor, and have bounded acyclic depth<=16. Repairs preserve failed traces; lineage grants no call or new budget. No peer calls occur under request-key SQL locks. Trace publication, current Data rights and Knowledge acceptance remain later workflow gates. Own actual PostgreSQL tests cover exact retry/time, replacement connections, failed/repaired lineage, unique task and competing trace writers, grants/actor/digest/binding, pending rejection and forbidden SQL mutations. Installed trace proof is verified; adjacent publication owns actual Data integration.

Verified2026-10-04 04:24:20:274 source/contract/dev cases;256 cases in two independent installations plus17 readback processes including failed/repaired extraction trace continuity and retained v1 history. Eighteen synthetic corpus cases are software oracles only; B3 owns semantic scoring. Trace authority remains interpretation-only.

## Publication persistence

planning_0007 belongs to the adjacent [publication module](../publication/README.md): exact trace-bound intents, immutable prepared payloads/events, mutable DB-clock leases and positions. This migration is applied and immutable. Publication reads reconstruct historical facts without granting new source use.375 owner/contract/dev cases65.55s verify the combined owner; publication469 statements28 branches100%. SDK I/O and actual Data integration remain subsequent gates.

## Repair-family admission

planning_0008 adds immutable repair_families and repair_members with owner-scoped task/request/policy/parent foreign keys, exact canonical bytes and SELECT/INSERT-only service grants. RepairJournal.enroll_root binds the stored task and reviewed policy. Legacy roots may be adopted only with complete budgeted attempt history and an unchanged policy; existing charges are counted without rewriting history. Enrollment is allowed even when already exhausted, but grants no further spend. A child must have no physical attempt before enrollment and must identify a persisted parent in the family. Exact replay preserves original membership/timestamp; changed roots, policies or parents conflict.

RepairRoot owns narrowing and source/target/context authority. BudgetLedger acquires family then request locks, rechecks membership after lock selection and atomically counts all family reservations using componentwise greatest reservation/settlement/late charges. Request-level admission still applies. Failed admission creates neither an attempt nor policy row. Existing reservations replay unchanged. Family ceilings use the original request, not a child's allowance or caller-supplied totals. Legacy begin_attempt cannot create new unbudgeted attempts inside a family.

Dispatch issue rechecks family-wide known overage, including late reports from siblings. Settlement/late writes use the same family lock, ordering their committed facts against new admission. Membership-change races abort with repair_membership_changed; callers may retry the unchanged operation, never reverse the lock order or create a fresh root. Enrollment and trace linking additionally acquire a scope lineage lock before family/request locks, preventing a concurrent legacy-root adoption from authorizing a post-hoc outsider trace. Only these short owned-state operations use that scope lock; no external I/O occurs inside them.

ExtractionJournal requires a child's enrolled parent on its first trace; later local retries may chain within that member. Cross-request links involving a family require both memberships and the exact enrolled parent. Unrelated legacy history remains readable. This is admission/lineage enforcement, not published findings, owner submission or integrated repair orchestration.

Cutover must replace all Planning admission writers before enabling families. Planning<=0.20 lacks this enforcement and its migrator must not run against0008. Preserve0001..0008 and all predecessor bytes; no reset/downgrade. Tests/persistence/test_repair_families.py covers actual PostgreSQL sibling contention, rollback, adoption, enrollment/trace races, late overage, immutable replay and ordinary runner enforcement. The installed repair_family_probe verifies replacement between reservation and dispatch.

Unsettled recorded replies also count as known exposure. A crash between observation commit and settlement must not let a sibling spend through reported overage. Family totals reconcile those bounded stored observations with the existing BudgetCharge domain policy, without inserting settlement or rewriting history. Direct observation writes share the family lock so the committed ordering against admission is explicit.

Verified 2026-10-04 08:01:56:588 source tests,570 independently installed tests25 process stages/two builds. Changed persistence/repair/orchestration coverage799 statements118 branches99.78%; only migration CLI outside instrumentation. Family modules217 statements32 branches100%. Installed proof preserves pending reservations and known unsettled overage across fresh processes.

Preparation verified 2026-10-04 09:21:08:owned PostgreSQL cases cover concurrent exact writes, replacement, changed availability conflicts, missing membership, retrospective registration denial, reserved-but-unissued preparation, actor/scope/grants and SQL mutation denial. All66 preparation journal statements/4 branches covered; isolated three-stage workflow preserves exact preparation time/bytes, request, packet, reservation, settlement and trace.


Planning0.25 adds forward planning_0010 for the [result publication](../result_publication/README.md) selection/preparation/event journals and separate lease/fence controls. Existing trace-publication tables and0001..0009 are unchanged. Result history grants are SELECT/INSERT; control grants are column-scoped. Never run Planning<=0.24 migrators after0010. BP-07.02/B2.03b.ii.a storage is verified:54 scoped and684 installed cases,32 process/replay stages. Production upload/producer work remains b.ii.b/c.


Owner handoff storage is implemented in the owner_handoff module under planning0011. It separates immutable selections/preparations/events from mutable DB-clock controls. Result publication uses its existing separate planning0010 tables. See each module README for payload limits, authority, recovery and replacement verification; earlier migration bytes are immutable.

## Campaign preparation journal

planning_0012 adds only SELECT/INSERT campaign_preparations, scoped by engagement and exact immutable request SHA. The focused [campaign_preparations boundary](../campaign_preparations/README.md) owns pure readback and journal behavior. Historical repair/extraction tables remain unchanged. Pure record rendering happens before SQL; family-before-request locking rejects extraction membership, preserves exact retry bytes/time and rejects first registration after any dispatch/observation. Readback verifies original actor and all duplicate identities/digests. No existing dispatch path gains an implicit preparation or processing grant. New campaign dispatch integration belongs to B2.

Compiler selection storage (planning0013) is owned by campaign_dispatch/history.py and store.py. It reconstructs immutable original campaign preparation, observation and accounting, then retains one scoped original-attempt selection. Only separate holder/fence/expiry control columns are mutable. Compiler effect/event writes remain B2.03b.ii; no outgoing command is dispatched by this storage.

planning0014 stores complete bounded compiler rounds, exact effect payloads and immutable events. UPDATE is limited to per-effect position control, in addition to the existing selection lease fields. There is no peer SQL, request dispatch or activation authority. Current migrations must be used for tests against the retained0014 database.


planning0015 adds original supervisor wrappers and immutable recording commands/receipts. The [supervision intake](../supervision_intake/README.md) module registers a legacy-compatible planning.requests row atomically with its wrapper/receipt, using command-key then decision-slot then existing request-key locks. No provider attempt, family enrollment, budget or dispatch is granted. Prior migrations remain unchanged.

Planning0018 adds immutable checkpoint_execution_reports. execution_state.require_execution_open is called under the existing request lock before new budget reservations, attempt intents, dispatch and primary observations; exact original replay precedes closure checks. Late observations remain diagnostic and prior migrations are unchanged. Never use Planning<=0.85 migrators against this head.

## Initial selected-model checkpoint scope

Planning0.101 adds the [checkpoint allowance](../checkpoint_budget/README.md) using existing
immutable journals, schema0020 unchanged. Only the new checkpoint profile acquires a scoped
budget lock before family/request locks. Six reserved calls/USD0.50 per dedicated project,
no refunds, known primary/late overage blocks new issuance. Legacy profiles retain their
existing behavior. Public checkpoint completion maps group exhaustion to accounting_budget_exhausted.
