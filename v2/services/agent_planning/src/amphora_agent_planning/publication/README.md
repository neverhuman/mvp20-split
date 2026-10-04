# Planning trace publication boundary

Planning0.14, BP-07.02/B1.04c.ii. Pure identities/payloads/transitions and the owned PostgreSQL journal are implemented. Public SDK workflow and actual Data publication are subsequent gates; a prepared payload does not prove an Artifact exists.

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
