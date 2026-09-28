# Runtime Lifecycle Domain Boundary

BP-02.04/I1 implements pure immutable transition decisions. RunState owns run eligibility/revision cancellation; WorkerAuthority owns configured worker identity and durable revocation projection; RunBudget owns available/reserved/spent conservation; AttemptLease owns identity/fence/time checks, renewal and once-only settlement; ActivationState owns issuance and bounded pure retry/uncertainty decisions. These are private behavior objects, not public DTO replacements or live database authority.

| Transition | Preconditions | Result |
|---|---|---|
| Claim | Running run, present matching nonrevoked worker, queued pure activation, attempt/budget/deadline remaining | New attempt identity supplied by owner, fence +1, issued +1, reserved +1 |
| Renew | Same worker/attempt/fence, running run and strictly before expiry/deadline | Same identity/fence, expiry extended up to deadline, never shortened |
| Expire pure work | At/after expiry | Spend issued unit once; queue only with retry count, budget and deadline remaining |
| Cancel | Optional run revision matches; running run | Cancelled run/revision +1; caller composes activation/attempt/intent transaction |
| Cancel unclaimed | Queued activation | Cancelled; no budget unit issued/spent |
| Success/abstention | Current fence, live authority/run and unexpired lease | Terminal activation/attempt; spend once; abstention never auto-retries |
| Retryable failure | Pure work with eligible remaining budget/attempt/deadline | Queue successor attempt; old issued unit remains spent |
| Uncertain effect | Reported uncertainty or non-pure expired work | No automatic retry; keep reserved unit pending explicit authoritative resolution |

Initial dispatch rejects external effects. Defensive uncertainty handling does not enable effectful tools. Explicit uncertainty resolution is an internal owner decision, never permission inferred from elapsed time. Known terminal attempts cannot change disposition or spend again. Numeric and state invariants reject malformed persisted projections, including unbounded counters and naive clocks.

The transaction owner must supply current database time after acquiring locks, current worker policy and the exact activation/attempt projection; worker clocks and stale DTOs never establish authority. Handlers must validate scope/tool/input/command bindings and persist the returned objects, audit/receipts and budget mutations atomically. Lease expiry/clock comparisons here are deterministic policy, not real concurrency evidence. Domain methods perform no SQL, HTTP, filesystem or provider side effects.

Tests in tests/lifecycle cover exact expiry, stale fences, missing/revoked/wrong authority, budget conservation, duplicate settlement, bounded retry, terminal runs, abstention, cancellation revision and uncertainty retention. Run `dev/run_tests.py --module runtime --area lifecycle`. The following sections own durable admission, claims, settlement, cancellation/revocation and public process proof; .05 owns completion intent acceptance atomicity. General campaign validation remains executable=false. A replacement must preserve these transition oracles and independently prove its transaction/authority integration.

## Synthetic Fixture Admission (I2)

FixtureCatalog holds an explicit immutable allowlist of PreparedFixture objects. It rejects duplicate activation/invocation identities and input ports at configuration time. Admission compares the entire normalized request against the configured definition: fixture/plan identity, exact tool pins, input/checkpoint references, timeout and finite attempt budget. Caller-authored fixtures cannot extend the allowlist. Configured references are trusted fixture pins; this admission step does not fetch artifacts or establish scientific/source validity. Integrated fixtures now upload/finalize and read actual input bytes before admission; general source eligibility remains outside this fixture boundary.

FixtureAdmission authenticates configured action/actor/scope before registering a canonical command. It locks the installation admission guard, rechecks original receipts, requires no running run, and atomically inserts the immutable run snapshot, queued activations, guard binding, initial audit/outbox and accepted receipt. Known mismatch/active-run failures store stable rejections. Infrastructure failure rolls back every transition and leaves the registered command pending. Public RuntimeReply maps owner dispositions to existing CommandReceipt; no contract shape changes.

Lock order starts with admission guard, then new run/activation writes and terminal command. The running-run unique index independently enforces the installation bound. Receipt replay does not create another run or notification. No external/network call occurs within this transaction. Existing outbox records are pending delivery; admission is not worker dispatch.

`api.create_app(admission, credentials)` explicitly enables POST /v1/fixture-runs through lifecycle/http.py. Default construction remains validation-only; execution_available stays false and general CampaignDefinition validation stays non-executable. RuntimeCredentials maps opaque configured tokens to RuntimePrincipal; live worker revocation is checked by owner handlers. Issued attempts and atomic budget application belong to the handlers below.

The module-owned prepared-run.json is a synthetic example copied from the public runtime contract fixture with per-test isolated scope. PostgreSQL tests cover two contenders/one run, exact pin mutations, original receipt replay, HTTP credential/actor rejection and a fault after domain writes that rolls back run/activations/audit/outbox. Fixture teardown cancels only its own test scope. This is transaction evidence, not a general graph interpreter or scientific campaign.

## Claims and Renewal (I3)

RuntimeLeases serializes transitions under the scoped run row, then worker policy and activation/attempt locks. It reads clock_timestamp after those locks; waiting on a lock cannot preserve expired eligibility. Only the authenticated actor's matching worker ID and the configured claim/renew action may proceed. Current durable revocation is checked; revocation/cancellation commands below use the same owner locks.

The first claim fixes an absolute activation deadline from the configured timeout. Renewal and all retries stay inside that activation window; retries also require remaining run budget and attempt count. Matching exact tool pins select prepared queued work. A new attempt increments the activation fence and reserves a unit; expired pure work settles once before an eligible successor can issue. Duplicate claim/renew returns the original receipt without extending or charging twice. No eligible work is a stable receipt; a future poll needs a new command ID. Input availability/scientific validation remains separate from pin identity.

Migration runtime_0002 adds activation/attempt deadlines and a lease<=deadline constraint. Legacy attempts backfill deadline from their existing expiry; they gain no extra authority. Persistence fixture inserts were updated to supply the new required deadline. The per-attempt grant_id is the issued attempt ID, an opaque reference whose authority always requires live scope/worker/fence/time checks; it is not a bearer credential.

HTTP adds /v1/invocations/claim and /v1/attempts/renew only to the explicitly configured fixture app. Claim returns a public ClaimResponse or a typed rejected CommandReceipt; renew returns a CommandReceipt bound to the same attempt. Run budget/revision, attempt/activation, receipt and audit/outbox commit atomically. Atomic fixture completion is implemented by the sibling completion module. Budget, cancellation/revocation and observations are described below.

Real PostgreSQL cases prove original receipt replay, exact tool filtering, expired reissue with increasing fence, stale renewal rejection and budget movement. Two separate worker processes are observed waiting on the same held run lock before release; only one receives the activation. A renewal waiting on a held run lock rejects when the lease is expired before that lock is released. Pure tests retain the exact-equality time oracle. No cross-service table access or network calls occur in these transactions.

## Budget Settlement (I4)

BudgetSettlement sweeps one scoped run under its owner lock and requires a configured maintain action. Its transaction-local apply method supports composition with the later cancellation command. It settles expired issued work once, cancels unclaimed work without cost when the run is already cancelled, and charges issued pure work even when cancelled. Exhaustion/deadline failure closes queued work with a failed run; it never invents successful completion. Uncertain effects retain reserved units and block automatic retry. Current fixture dispatch remains pure-only.

Every changed sweep commits attempt/activation state, conserved run budget, revision and audit/outbox together; an unchanged repeat adds nothing. Prepared completion intents block blind settlement and roll back the entire sweep: the completion/authority owner must reconcile or abort those intents under the same locks before allowing settlement. I5/.05 must compose that boundary; a timeout is never proof of abort. Maintenance operations have owner-generated durable outbox identities and do not masquerade as caller commands.

Real-DB cases cover two independent activations competing for one unit, repeated expiry settlement, zero-cost unclaimed cancellation, once-only issued cancellation, rollback after budget write and the prepared-intent guard. The cancellation-state setup is explicitly fixture-only; the authority section independently verifies the actual authorized atomic command. Initial reservation/expiry in I3 was necessary for safe claims; I4 supplies these broader settlement/exhaustion oracles. ClaimedWork now isolates worker DTO projection from the claim transaction.

## Authority and Cancellation (I5)

AuthorityCommands authenticates cancel/revoke actions and exact actor/scope before command registration. Cancellation checks the optional run revision under the same run lock as claims/renewals, then locks activations/attempts/intents in order. Prepared intents receive immutable aborted outcome records before settlement. Run status, charged issued work, zero-cost queued cancellation, original receipt and audit/outbox commit together. A blocked uncertain run retains reservations; cancellation never fabricates certainty or a refund. Stable replay does not re-abort or alter existing proof.

Revocation takes the admission guard, stable ordered affected run locks, the scoped worker-policy row, then work/intent locks. It persists a monotonic revoked policy revision, aborts that worker's prepared intents and terminalizes issued attempts. Eligible pure work can return to queued for another configured worker with a higher fence; unknown effects remain blocked and charged. Revoked workers cannot make new claims or renewals; an old replayed receipt is historical evidence, never restored live authority. Revocation is scoped to the command's tenant/project.

runtime_0003 introduces policy_audit_events/policy_outbox because revocation can occur before any run exists; inventing a dummy run or nullable run event would blur ownership. These are private runtime state, with service-role insert/read and bounded outbox update grants. A policy command owns one immutable audit/notification; per-run notifications derive stable delivery IDs from the parent operation and run. Later outbox delivery must cover both journals. No direct artifact database access occurs.

AbortDecision stores status/receipt/reason on the immutable intent binding; .05 must expose authenticated public projections and compose prepared completion commits using the same locks. This child does not claim that public runtime outcome integration yet. I5 tests use explicit synthetic prepared/uncertain state to verify cancellation behavior, not a fictitious completed .05 service.

Configured fixture apps add /v1/runs/cancel and /v1/workers/revoke. PostgreSQL tests cover revision/grant/scope rejection, cancellation-versus-claim and revocation-versus-renewal ordering, pre-run policy audit, higher-fence recovery by another worker, prepared abort/settlement rollback and uncertainty retention. Independent worker/lifecycle acceptance is described below.

## Standalone Lifecycle and Observations (I6)

Host.load validates explicit principal actions/identities, exact fixture definitions, runtime_service and required migrations. The executable binds loopback, with separate check/settle operations; startup never migrates. GET /ready probes persistence. The default app remains validation-only. Hosting config and invocation pins contain no implicit scientific authority.

RuntimeReads requires a read grant and uses a scoped read-only REPEATABLE READ transaction so budget, revision and current activation/attempt rows describe one snapshot. ObservedRun owns mapping and derives available units through RunBudget. RunSnapshot is a new additive wire-v1 schema; it includes no credentials, raw inputs or mutable worker authority. At most 256 configured activations are returned. Wrong/missing scope is indistinguishable (404); historical observation does not resurrect a lease. Paginated audit/command/outcome queries remain .05/D5.

The independent installed-wheel probe starts the service outside the checkout, admits synthetic work, kills an HTTP-only worker after claim, lets its real lease expire and claims from a second process. It verifies higher fence/new attempt, stale renewal rejection, original claim replay, current renewal, scoped observation, revocation/cancellation and exact reserved/spent units. Worker environment is restricted to OS essentials; tokens/commands arrive through stdin, never database credentials. This complements direct database-contention probes, whose owner credentials are explicitly not public-worker evidence. External effects, scientific validity and actual completion/artifact integration remain excluded until their successor gates.

R5 clarification: the installation slot limits RUNNING campaigns. A terminal BLOCKED run cannot claim/renew/accept new work and has no resume operation; unresolved reservation/evidence remains preserved. A distinct successor campaign can be admitted without altering the blocked predecessor. This implements the initial product terminal-blocked semantics, not multi-campaign scheduling or automatic effect reconciliation.

## Graph-mode integration (BP-04.02)

Runtime 0.3.0 adds a separate coordinator and explicit durable graph execution mode. Existing fixture semantics remain unchanged. Graph invocation rows use the same claims/fences/budget protocol, ordered by immutable dispatch ordinal then activation ID; fixture ordinals default to zero. Graph tool snapshots are immutable exact binding maps, so new graph activations do not require rewriting an admitted snapshot. Completion/settlement cannot infer graph terminality from issued invocations; the graph coordinator owns Finish/frontier closure. Uncertain effects and emergency cancellation retain their existing fail-closed authority. The graph module README owns remaining advancement, bounded active-worker observation and hosting gates.
