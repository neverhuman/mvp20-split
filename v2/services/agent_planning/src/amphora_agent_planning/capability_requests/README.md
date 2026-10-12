# Original capability requests

UI-01.08/P3.1. Owns deterministic, scoped read projections of immutable original
curation gaps. Does not create tools, run models, compile graphs, grant eligibility,
fulfill requests or rewrite proposal/receipt/progress bytes. capability_fulfillment
owns P3.2 commands and verification.

CapabilityAddress binds curation command identity plus original gap ordinal0..15;
IDs never depend on display text or a refreshed catalog. CurationCapabilities
validates the original scoped ordinal1 provider linkage and exact typed proposal,
rejects duplicate gaps and mismatched references, and hashes canonical proposal
bytes. OriginalCapability groups the origin, proposal hash and complete gap and
maps them to the approved CapabilityRequestView. The capture/progress journal is
the durable source; there is no second mutable copy of requested behavior.

Curation GET enriches only the response with stable capability references, including
pre-P3 retained outputs. Original queued receipts and append-only progress retain
their original bytes. Both graph proposals with gaps and capability-only outcomes
remain addressable; unknown/invalid/abstained outputs do not invent requests.

CapabilityRequestReader reads Planning original requests/progress and the scoped
fulfillment journal, preferring a verified winner over later pending/rejected intents.
It verifies the original gap against the frozen fulfillment snapshot. Reads are scoped to
the authenticated actor/project. GET /v1/capability-requests/{request_id} requires
read_capabilities independently of read_curations, rejects query/body additions,
returns no-store responses and hides foreign actor/scope/missing originals as404.
It performs no writes or peer I/O. Descriptions are model requests, not acceptance.
Stored inconsistency rejects; it does not manufacture a replacement description.

Tests: tests/capability_requests (projection, scoped SQL/HTTP, immutable history and
reader replacement). Public types remain campaign-curation0.1. Current fulfillment
readback requires the additive Planning0026/0027 migrations.
Architecture: [Planning](../../../../../docs/Architecture/Agents/Planning.md).
Delivery: [UI-01.08](../../../../../docs/Build%20Plans/UI-01.08%20Campaign%20curation%20boundary%20decision.md).
