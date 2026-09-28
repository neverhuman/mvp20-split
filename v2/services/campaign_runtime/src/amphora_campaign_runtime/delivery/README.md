# Runtime Delivery Boundary

- Status: BP-02.05/D4 bounded delivery implemented; integrated peer/crash acceptance remains D6/.06.
- Owner: Campaign Runtime. Delivery changes transport metadata only; it cannot accept execution or rewrite committed history.

DeliveryStore serves outbox and policy_outbox through a fixed owner-local journal map. Scope derives from each immutable audit event; a configured deliver action is mandatory. Short transactions select due pending or expired leased entries with FOR UPDATE SKIP LOCKED, lock at most twice the requested batch across both journals, order candidates by creation/operation identity and issue at most the requested bound. Database time is read after locks. No network call occurs inside these transactions.

Each delivery increments its generation/attempt count, obtains a fresh opaque token and bounded lease, and preserves the original operation/event/target/payload. Conditional acknowledgement/failure rechecks scope, journal, current token/generation, leased state and database expiry. An old worker cannot acknowledge or fail its successor. Expired leases remain recoverable.

DeliveryPolicy defaults to eight attempts and a 30-second lease, configurable within 1-100 attempts and 1-300 seconds. Failures use exponential backoff capped at 60 seconds. Final failure or final-lease expiry becomes exhausted with an explicit reason; it never silently acknowledges or undoes accepted results. Automatic redrive/reset is absent; a future explicit recovery action must preserve lifetime evidence.

DeliveryWorker performs one count/time-bounded pass, claiming one entry just before each remote call so a sequential batch does not spend its leases waiting locally. Count is capped at 100, pass time at 30 seconds; one already-started bounded request may finish after the pass budget. Unknown targets fail and retry within policy. No daemon starts implicitly.

Configured runtime_notifications/runtime_policy_notifications send public RuntimeNotification containing scope, stable operation/event IDs, event kind and a run/policy reference for authoritative refresh. The closed DeliveryAcknowledgement must match scope, operation and event; HTTP 200 is insufficient. Receivers must durably deduplicate operation IDs before acknowledging. Notifications never grant execution authority; transport is at least once.

Artifact targets send the exact queued confirm/reconcile command to the configured reservation endpoint plus /confirm or /reconcile, using its scoped runtime-owner credential. Returned receipts must match full artifact/intent/reservation identity. Confirmation must match the committed runtime receipt; reconciliation must return released. A mismatch cannot acknowledge delivery. Endpoints are configured HTTPS or literal loopback HTTP, with bounded timeout/body and redirects/environment proxies disabled. Worker payloads cannot supply destinations.

runtime_0006 adds token/generation, available/created timestamps, reason and exhausted status to both journals, plus delivery/recovery indexes. Pre-fencing leased entries reset to pending during migration; quiesce any older delivery implementation first. Immutable payload/audit service-role protections remain. Notification/ack schemas are additive wire-v1 roots; old command bytes remain unchanged.

Host delivery configuration accepts max_attempts, lease_seconds and a closed notifications map with endpoint/token_env per target. CLI deliver selects config/actor/tenant/project, --limit and --time-budget; run is unnecessary because policy events may precede runs. No notification endpoint is enabled by default. Service-role migration and secret configuration belong to the service README.

Tests live in tests/delivery, selectable with dev/run_tests.py --module runtime --area delivery. They cover both journals, scoped denial, real transaction contention, stale token/expiry rejection, backoff/exhaustion, send-before-ack replay with one synthetic consumer effect, and exact notification/artifact receipt checks. Lease-expiry injection is distinct from process-kill evidence; cross-process interruption acceptance remains .06. Replacements preserve these boundaries and never equate delivery with state authority.
