# Runtime Inspection Boundary

- Status: BP-02.05/D5 scoped history and bounded pages implemented.
- Owner: Campaign Runtime. This module reads only private runtime records and never changes authority, leases, results or commands.

RuntimeHistory requires configured read action on every call. Command lookup binds tenant/project, family, command ID and authenticated actor. Inspecting a different actor additionally requires inspect_receipts. Pending commands return their original digest/operation identity; terminal commands return the stored CommandReceipt or ClaimResponse. Historical claims can still say claimed after revocation: that is original evidence, never a revived grant. Worker mutations continue to check live authority separately.

CompletionRecord reads the immutable accepted attempt report and its atomic original command receipt. It exposes scoped result/artifact references, accepted run revision, artifact-owner retention reservation IDs and whether the report occupies the canonical terminal activation-result slot. Retryable/uncertain reports remain distinguishable from a terminal result. No raw artifact payload, credential, canonical request body or delivery token is returned.

Audit pages pin the current run revision in a read-only repeatable-read transaction. Immutable event membership is ordered by revision/ordinal, optionally filtered by event kind, with at most 100 entries. Later events cannot appear in subsequent pages of that snapshot. A fresh request with since_revision starts a new snapshot for reconnect; since_revision and cursor cannot be combined. Raw audit payloads remain private; entries identify event/revision/kind, and clients fetch authoritative run/report state separately.

CursorCodec signs versioned scope/resource/mode/filter/revision/position/expiry with HMAC-SHA256. A configured environment-backed key of at least 32 bytes and lifetime 60-3600 seconds is required (default 900). Restart with the same key preserves cursors until expiry; key rotation, altered binding, invalid signature or a restored database behind the pinned revision requires resnapshot. The cursor only selects authorized observations; it cannot grant read access. Errors are sanitized and carry resnapshot=true (expired 410, invalid/mismatch/snapshot gap 409).

Delivery inspection supports exact operation lookup across both journals and pages of one scoped immutable audit event's delivery membership, ordered by operation ID. Event-to-delivery membership is committed with the owning transition; late reservation evidence gets a new audit event. Transport status/attempts/generation/timing/reason are current observations on each page, not historical delivery-state snapshots. Leased tokens and raw outbound payloads are excluded. Policy deliveries can be inspected even before a run exists.

The configured HTTP surface is:

| Method/path | Result |
|---|---|
| GET /v1/commands/{family}/{command_id}?actor_id=... | Original or pending receipt, with explicit cross-actor authorization |
| GET /v1/runs/{run}/completions/{completion} | Accepted attempt report and canonical-result flag |
| GET /v1/runs/{run}/audit | Pinned AuditPage; limit, cursor, kind, since_revision |
| GET /v1/events/{run-or-policy}/{event}/deliveries | Bounded delivery page; limit and cursor |
| GET /v1/deliveries/{operation} | Exact scoped delivery entry in a DeliveryPage |

Host inspection config names cursor_key_env and optional ttl_seconds. Default application construction has no history routes; explicit fixture hosting with inspection enables them. Current RunSnapshot and exact retention outcome proof remain owned by lifecycle/completion. All DTO roots are additive public wire-v1 schemas; no new migration is needed for inspection.

Tests live in tests/inspection and run with dev/run_tests.py --module runtime --area inspection. Oracles cover pending/accepted/claim receipts, denied scope/actor access, immutable completion reports, signed page replay/reconnect, concurrent newer revisions, filter/tamper/expiry rejection, exhausted delivery visibility, policy lookup, no token exposure and explicit host key configuration. Rebuilds preserve authenticated scope, original receipt identity and bounded consistent membership; cursor wire encoding may change only with explicit resnapshot/version behavior.

Runtime0.64 additionally mounts [accepted producer evidence](../execution_proofs/README.md) under the same explicit inspection configuration. The separate read-only route binds original tool/input specification to canonical successful completion and requires read+inspect_receipts. Existing inspection contracts and command lookup behavior remain unchanged; no migration or live grant is introduced.
