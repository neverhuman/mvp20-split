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

Tests in tests/lifecycle cover exact expiry, stale fences, missing/revoked/wrong authority, budget conservation, duplicate settlement, bounded retry, terminal runs, abstention, cancellation revision and uncertainty retention. Run `dev/run_tests.py --module runtime --area lifecycle`. I2-I6 own actual admission, claims, settlement, cancellation/revocation and public process proof; .05 owns completion intent atomicity. General campaign validation remains executable=false. A replacement must preserve these transition oracles and independently prove its transaction/authority integration.

## Synthetic Fixture Admission (I2)

FixtureCatalog holds an explicit immutable allowlist of PreparedFixture objects. It rejects duplicate activation/invocation identities and input ports at configuration time. Admission compares the entire normalized request against the configured definition: fixture/plan identity, exact tool pins, input/checkpoint references, timeout and finite attempt budget. Caller-authored fixtures cannot extend the allowlist. Configured references are trusted fixture pins; this admission step does not fetch artifacts or establish scientific/source validity. Integrated input availability remains .06.

FixtureAdmission authenticates configured action/actor/scope before registering a canonical command. It locks the installation admission guard, rechecks original receipts, requires no running run, and atomically inserts the immutable run snapshot, queued activations, guard binding, initial audit/outbox and accepted receipt. Known mismatch/active-run failures store stable rejections. Infrastructure failure rolls back every transition and leaves the registered command pending. Public RuntimeReply maps owner dispositions to existing CommandReceipt; no contract shape changes.

Lock order starts with admission guard, then new run/activation writes and terminal command. The running-run unique index independently enforces the installation bound. Receipt replay does not create another run or notification. No external/network call occurs within this transaction. Existing outbox records are pending delivery; admission is not worker dispatch.

`api.create_app(admission, credentials)` explicitly enables POST /v1/fixture-runs through lifecycle/http.py. Default construction remains validation-only; execution_available stays false and general CampaignDefinition validation stays non-executable. RuntimeCredentials maps opaque configured tokens to RuntimePrincipal; it neither issues worker grants nor implements durable revocation (I5). I3/I4 own issued attempts and atomic budget application; I6 owns executable/public worker acceptance.

The module-owned prepared-run.json is a synthetic example copied from the public runtime contract fixture with per-test isolated scope. PostgreSQL tests cover two contenders/one run, exact pin mutations, original receipt replay, HTTP credential/actor rejection and a fault after domain writes that rolls back run/activations/audit/outbox. Fixture teardown cancels only its own test scope. This is transaction evidence, not a general graph interpreter or scientific campaign.

## Claims and Renewal (I3)

RuntimeLeases serializes transitions under the scoped run row, then worker policy and activation/attempt locks. It reads clock_timestamp after those locks; waiting on a lock cannot preserve expired eligibility. Only the authenticated actor's matching worker ID and the configured claim/renew action may proceed. Current durable revocation is checked; full revocation/cancellation commands arrive in I5.

The first claim fixes an absolute activation deadline from the configured timeout. Renewal and all retries stay inside that activation window; retries also require remaining run budget and attempt count. Matching exact tool pins select prepared queued work. A new attempt increments the activation fence and reserves a unit; expired pure work settles once before an eligible successor can issue. Duplicate claim/renew returns the original receipt without extending or charging twice. No eligible work is a stable receipt; a future poll needs a new command ID. Input availability/scientific validation remains separate from pin identity.

Migration runtime_0002 adds activation/attempt deadlines and a lease<=deadline constraint. Legacy attempts backfill deadline from their existing expiry; they gain no extra authority. Persistence fixture inserts were updated to supply the new required deadline. The per-attempt grant_id is the issued attempt ID, an opaque reference whose authority always requires live scope/worker/fence/time checks; it is not a bearer credential.

HTTP adds /v1/invocations/claim and /v1/attempts/renew only to the explicitly configured fixture app. Claim returns a public ClaimResponse or a typed rejected CommandReceipt; renew returns a CommandReceipt bound to the same attempt. Run budget/revision, attempt/activation, receipt and audit/outbox commit atomically. End-to-end completion is still unavailable. I4 owns exhaustive budget/terminalization handling; I5 owns cancellation/revocation; I6 owns lifecycle acceptance and read projections.

Real PostgreSQL cases prove original receipt replay, exact tool filtering, expired reissue with increasing fence, stale renewal rejection and budget movement. Two separate worker processes are observed waiting on the same held run lock before release; only one receives the activation. A renewal waiting on a held run lock rejects when the lease is expired before that lock is released. Pure tests retain the exact-equality time oracle. No cross-service table access or network calls occur in these transactions.
