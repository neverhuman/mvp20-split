# Planning trace publication boundary

Planning0.13, BP-07.02/B1.04c.i. Pure publication identities, payloads and upload
transitions are implemented. Durable journal, lease/fence, external SDK workflow
and actual Data integration are subsequent gates; these values alone do not
authorize I/O or prove that an Artifact exists.

PublicationIdentity binds a record_attempts principal, scoped exact trace
reference, publication ID and trusted publisher configuration identity. Its
immutable canonical bytes determine stable begin/finalize command IDs per upload
ordinal. The configured publisher identity contains no credential. The owner
journal must still load the original actor's exact stored trace/task and reject
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
source ancestry; c.ii/c.iii/d must add durable and actual-peer evidence.
