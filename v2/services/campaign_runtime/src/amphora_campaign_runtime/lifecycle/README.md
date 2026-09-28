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
