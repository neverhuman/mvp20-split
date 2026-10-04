# Planning persistence boundary

- Reviewed implementation: Agent Planning0.11; BP-07.02/B1.03b.
- State: private planning schema, forward migrations planning_0001 through planning_0006.
- Responsibility: immutable request, attempt, observation, policy, reservation, settlement, issuance and late-evidence records. The orchestration module composes these objects; Runtime alone owns campaign decisions.

## Authority and immutable journal

The migrator role applies explicit forward DDL; imports never migrate. The service role has SELECT/INSERT only, no history update/delete or peer-table authority. A trusted Principal supplies actor, scope and operation grants; model text and caller DTOs cannot choose them. Readback requires the original request actor and exact scope. Raw provider captures are private scoped diagnostics, not a public Artifact or an unauthenticated endpoint.

PlanningJournal.register preserves exact canonical request bytes and fingerprint. Same-actor exact retry replays; changed identity/content conflicts. begin_attempt is a private legacy journal primitive, not authorization to call a provider. Unknown request, absent attempt, pending intent and terminal observation remain distinct. Ordinals are sequential and bounded by the immutable request. record validates attempt/capture size/hash/completeness and any successful proposal; first observation wins and differing writes conflict. The internal transaction helper lets DispatchJournal share that invariant without nested transactions.

All writes serialize under the same request-key advisory transaction lock. No SQL lock spans a provider, filesystem or peer call. Database timestamps describe persistence time, not fabricated provider duration. Reconstruction revalidates canonical identity and capture bindings. Existing unbudgeted histories stay readable and cannot be retroactively relabeled authorized.

## Reservation and conservative settlement

BudgetLedger.reserve validates the trusted private policy and atomically stores exact policy/demand with the attempt intent. Existing reservation replay preserves its original identity/time; replay is not a repeated dispatch grant. Changed policy/request conflicts; failed admission rolls back new policy/intent rows together. The next ordinal needs a prior observation and settlement. Limits remain per logical request; Runtime's campaign budget is separate.

SettlementJournal.settle/read stores and verifies immutable observation hash, reserved_floor_v1 charge and timestamp. The v1 policy has no refund authority: each component is max(reserved, observed lower bound). Unknown, missing, interrupted, zero or low reported usage never releases the floor. Reported overage remains exact, even when certainty is unknown, and stops further reservation/issuance. This does not gate scientific quality. Exact duplicate settlement replays; pending/unreserved attempts cannot settle. Future refund behavior requires a deliberate new profile, preserving v1 policy bytes and history.

## Issuance, expiry and late evidence

DispatchJournal.issue returns a newly committed random token/database deadline only to its first inserting worker. Existing issuance returns no grant, even to the same caller. The reserved attempt must be unobserved; any known request overage blocks new issuance. complete and recover serialize against each other: timely response may commit, while expired issuance produces an immutable unknown observation with reason attempt_deadline. Deadline recovery never assumes the external call was free.

A late response cannot overwrite recovered history. One bounded late_observations record preserves its exact bytes/usage and derived charge, with identical replay and changed-duplicate conflict. read_late verifies capture and charge against the original request/policy. Admission totals use per-component maxima across reservation, settlement and late evidence, preventing both undercounting and duplicate charge for one physical attempt. Late overage stops future reservation and unissued successors; already-issued effects cannot be undone.

The deadline fences accepted observations, not physical remote cancellation or network exactly-once effects. A real adapter must bound transport and avoid hidden physical retries. This package has no live adapter, public server, output publication, peer-state mutation or Runtime acceptance. Legacy observed/reserved records without issuance remain readable; they are not automatically resumable as authorized dispatches.

## Replacement and verification

Preserve canonical policy/request/observation bytes, exact attempt identities, first-writer outcomes, unknown/pending distinctions, actor/scope checks, conservative arithmetic and all issuance/late evidence. Migrations are forward-only and immutable after application; Planning<=0.10 migrators must not run against planning_0006. There is no fixture reset, downgrade or deletion authority.

Owned tests/persistence cover actual PostgreSQL migration/idempotency, competing writers, admission rollback and limits, legacy distinction, settlement/retry, expiry/late races, stored-record integrity and SQLSTATE42501 for forbidden mutations. tests/orchestration separately cover bounded composition and non-starvation. dev/verify_planning.py installs the public dependency closure twice and verifies isolated owner/process readback; dev/verify_planning_recovery.py exits installed workers abruptly at five committed boundaries. The latter uses exclusive synthetic call markers, not real remote effects. Neither harness claims independently authored replacement code, power-loss durability, scientific validity or live model quality. Detailed evidence lives under docs/Audits/Evidence/BP-07-Planning.

## Versioned observation storage

planning_0005 conditionally extends encoded observations and late observations to256KiB only for explicit string format2. Missing/numeric/legacy version records do not gain that allowance; v1 retains64KiB. Raw capture remains64KiB for both. The shared strict decoder and closed output catalog reconstruct either legacy ReferenceProposal or TypedProposal from retained capture before writing/replaying. Budget/issuance/settlement rows and all prior observation bytes remain unchanged. Actual SQL cases verify the conditional constraints and format2 late output/charges; an optional --legacy-manifest argument to dev/verify_planning.py verifies retained predecessor project hashes after migration using only service credentials.

## Extraction task and trace history

ExtractionJournal registers one immutable ExtractionSnapshot per engagement, bound to the already registered actor/request digest; task identities cannot move between requests. record accepts task/observed-attempt identity and optional prior trace reference, then derives all provenance from stored facts. Pending/unknown attempts cannot be traced. The task row is not dispatch authorization. Existing exact traces replay original bytes/digest/database timestamp; changed trace identity/content or parent conflicts. planning_0006 adds own extraction_tasks and extraction_traces with task/request/observed-attempt FKs, unique physical-attempt trace, exact parent digest FK, size bounds256KiB/1MiB and SELECT/INSERT-only role grants.

Readback verifies task/request bytes, trace digest, database identity columns and complete parent chain, then reconstructs the projection from immutable observations. Parent records must exist, share source/target/scope and original actor, and have bounded acyclic depth<=16. Repairs preserve failed traces; lineage grants no call or new budget. No peer calls occur under request-key SQL locks. Trace publication, current Data rights and Knowledge acceptance remain later workflow gates. Own actual PostgreSQL tests cover exact retry/time, replacement connections, failed/repaired lineage, unique task and competing trace writers, grants/actor/digest/binding, pending rejection and forbidden SQL mutations. Installed trace proof is the next substep.
