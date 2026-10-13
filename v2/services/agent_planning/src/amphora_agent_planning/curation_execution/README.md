# Once-only curation provider execution

UI-01.08/P2.3c.2. No public API/schema or extra attempt profile.
CurationExecutor recovers retained observations/issuance before new configuration
or Data reads. Pending issuance waits; expired issuance records original unknown
outcome. Exactly one physical call is granted by existing DispatchJournal ordinal1.
No retry, fallback, refund, prompt rewrite or second qualification scope.

New execution requires original finalized declaration and exact prepared request,
reviewed original budget and current processing access to every included available
Artifact. Rights are checked before reservation and again before transport; omitted
inputs remain omitted. New reservation/issuance transactions fence the active job
before writes and commit. Current access observations are not durable rights grants.
No peer I/O occurs inside SQL transactions. Packet/envelope is retained unchanged.

Provider receives exact packet and durable dispatch deadline (configured1..60s).
Its transport must enforce that deadline. Lease expiry during a paid call cannot
erase the original observation/accounting; only job-progress writes need a current
lease. Unknown outcomes retain conservative accounting and never reissue.
Tests: tests/curation_execution. Process heartbeat/managed scheduling and compiler
handoff remain separate gates. Zero live calls in module qualification.

Planning0.140 adds explicit scientific-v1 response window up to180s only for the
reviewed demo scope and v10 model profile. Defaults remain60s; transport requires
its own explicit profile and executor requires an explicit180s ceiling. Dispatch
records the chosen deadline, provider narrows to remaining time, existing job
heartbeat renews its60s fence independently. No retry, budget increase, reinterpretation
of retained attempts or promise of remote cancellation. Provider-disabled checks
validate model/window compatibility without loading keys. The earlier managed v10
call remains indeterminate with unknown usage and its full0.25USD hold.
