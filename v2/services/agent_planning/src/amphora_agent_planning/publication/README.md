# Planning trace publication boundary

Planning0.15, BP-07.02/B1.04c.iii. Pure identities/payloads/transitions, the owned PostgreSQL journal and public SDK workflow are implemented. Actual installed Data integration is the next gate; a prepared payload does not prove an Artifact exists.

PublicationIdentity binds a record_attempts principal, scoped exact trace
reference, publication ID and trusted publisher configuration identity. Its
immutable canonical bytes determine stable begin/finalize command IDs per upload
ordinal. The configured publisher identity contains no credential. The owner
journal loads the original actor's exact stored trace/task and reject
ID/content/configuration conflicts before any external effect.

TraceArtifact.reviewed validates the exact trace/task/request/actor/context pins
against a SourceReviewer observation, verifies source bundle and prompt bytes,
requires every declared source/conversion trace and includes all consumed inputs
without duplicates, foreign scope, missing or unreviewed entries. Derived input
order is stable by Artifact ID and bounded128. The exact canonical trace body is
bounded1MiB; it retains interpretation_only/profile_only metadata for failed and
successful attempts. Publishing does not upgrade citations or scientific truth.

extraction-trace-v1.schema.json is the trusted self-contained Data content schema,
pinned by exact UTF-8/LF file hash under planning.extraction-trace-content/v1.
It differs from the exported URN root identity; no caller may install validators.
The transformation descriptor binds the interpretation profile and exact task,
trace and observation hashes. Publication must freshly review sources; historical
payload reconstruction is not new-use permission. Data rechecks complete current
process ancestry at derived begin/finalize.

PublicationAttempt permits prepared -> begun -> streaming -> streamed ->
finalizing -> finalized. Receipt checks bind complete upload descriptor/scope,
stream upload identity, final content and exact derivation inputs/origin command
identity/hash. Stream intent must be persisted before PUT by the forthcoming
workflow. Uncertain streaming becomes abandoned; replacement has distinct stable
command IDs, at most8 upload attempts. It cannot repeat the old PUT or proceed
to finalization. An ambiguous finalization stays finalizing, using its original
command; abandonment/re-streaming is forbidden. Rejected begin/finalize outcomes
are terminal for that attempt. Old histories and charged uploads remain intact.

Tests/publication/test_values.py owns payload, actor/trace/task/source/ancestry,
schema, deterministic commands, transition, failed-interpretation and forged
receipt oracles.22 pure cases are included in351 owner/contract/dev checks;
158 statements2 branches100%. These are software boundary tests, not actual
Data publication or process recovery proof. Rebuilds must preserve exact content
and command identities, bounded attempts, honest uncertain states and complete
source ancestry; c.iii/d must add SDK recovery and actual-peer evidence.

## Owned durable boundary

PublicationStore owns exact registration plus DB-clock leases (1..300 seconds), holder/fence, renewal and release. PublicationJournal prepares from the original stored trace/task and reviewed source metadata, then appends bounded events through compare-and-set position writes. planning_0007 stores immutable intents/payloads/events and separately mutable control columns. Only SELECT/INSERT is granted on history; lease/control updates are column-scoped. No peer I/O occurs under SQL locks.

Readback requires read_attempts and the original actor; it does not invent a write grant. Every payload is rebuilt from the stored trace/task plus bounded historical Artifact/source/conversion metadata, then all contiguous events (max64) replay through the pure transition rules. Raw source bytes are not duplicated in publication storage. Metadata replay is not fresh rights authorization. A new lease cannot reuse a previous streaming intent to repeat PUT. Final-write lease expiry rolls back both event and position; readback takes a short owner lock for consistent multi-query reconstruction.

Verified2026-10-04 05:11:45:375 owner/contract/dev cases65.55s,46 publication cases including8 actual PostgreSQL cases;469 publication statements28 branches100%. Tests include competing holders, stale writers, expiry during write, injected rollback, immutable SQL grants, read-only replacement and strict corruption detection. Planning<=0.13 migrators must not touch planning_0007. Real Data calls and abruptly interrupted publication processes remain unproven until c.iii/d.

## SDK workflow and bounded transport

TracePublisher composes the journal, SourceReviewer and public ArtifactClient from amphora-tool-protocol0.2. It validates configured client actor/scope before registration, acquires a120-second DB-clock lease, re-reads state, and reviews source bytes outside SQL before first preparation. Completed/rejected histories replay without new peer effects. The original actor requires both record_attempts and read_attempts for execution. A publisher configuration ID binds the intended peer/configuration independently of its secret credential.

Begin/finalize use receipt-first SDK recovery with original stable IDs and exact command bytes. Only the invocation that commits the streaming transition may issue its single PUT. Any recovered streaming state is uncertain even if a crash occurred before the call; retain abandonment, then use a distinct next upload. An uncertain finalize or derivation lookup stays finalizing and reconciles the same command. A verified Data rejection becomes immutable rejected history; an unavailable/denied lookup never fabricates rejection or success. Every local transition rechecks lease/fence/position. Release ignores only expected lease loss; other persistence failures remain visible. Remote effects can outlive a lease and must be reconciled; no network exactly-once claim.

PublicationTransport implements the public SDK transport protocol for a closed GET receipt/derivation, POST derived-begin/finalize and PUT content catalog. Only explicitly configured127.0.0.1 HTTP with port is supported in this first local deployment. No redirects/proxies/implicit retries. Each exchange has a maximum5-second wall-clock deadline covering headers, body and writes,1MiB outbound bound and256KiB reply bound. Successful responses require JSON media and strict duplicate/non-finite rejection before SDK decoding. Errors expose safe reasons. SDK command recovery is bounded to three rounds; workflow transitions are capped at10 per invocation and8 lifetime uploads. A failing PUT exits this invocation; it does not immediately spend every successor attempt. Historical payload metadata is not continuing source authorization; Data must recheck current ancestry on each newly committed begin/finalize.

Owned tests/publication/test_workflow.py uses the actual Planning PostgreSQL journal and public SDK with scripted Data records; test_transport.py uses actual loopback HTTP with scripted responses. They prove lost replies, uncertain PUT, exact command resume, derivation mismatch, terminal rejection, lease loss, interrupted local transitions, finite attempts, strict routes/JSON and trickle bounds. B1.04d must still prove actual independently installed Data publication, inherited rights denial and replacement after process termination. Scientific meaning, Knowledge acceptance and live provider behavior are not this module's authority.

Verified2026-10-04 05:23:21:421 owner/contract/dev cases109.26s;92 publication cases;602/608 statements58/62 branches covered. Residuals: closed-socket shutdown catch and explicit timer-expiry fallback branches; unexpected release-error propagation and defensive workflow exhaustion. Actual SQL/SDK behavior is verified, actual installed Data acceptance remains d.
