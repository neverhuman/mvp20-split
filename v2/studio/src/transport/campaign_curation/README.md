# Recorded campaign curation reads

UI-01.08/P3.3a. Research SMEs inspect an exact original curation and lazily select
its requested capabilities. Planning owns both projections. This transport has only
GET methods; no model invocation, fulfillment submission, current-catalog fetch,
latest-head lookup or browser credential storage. P4 owns command interaction.

Generated validators consume the unchanged Python-owned serialization schemas.
Reads bound success1MiB/errors4KiB, timeout/cancellation and same-origin credentials.
Named404 means missing; generic404/unavailable endpoint, denial, invalid response
and timeout stay distinct. No fallback to fixture content or another record.

Curation reads bind authenticated actor/scope, exact reference and predecessor,
original provider linkage and deterministic capability references. Detail binds
the same original curation/gap and exact fulfillment receipt scope/actor/request.
Verified historical fulfillment is not current tool/scientific/processing authority.
The proposal digest is owner-reported canonical proposal identity. It differs from
the raw provider capture hash; browser number serialization is not used to claim
independent verification of Python canonical proposal bytes.

The page model owns visible/loading/empty/stale/denied states and generation fences;
transport cancellation also rejects a late response from an uncancellable fetcher.
Tests belong to tests/transport/campaign_curation; source import ownership remains
the Studio contract suite. Replacement preserves strict shape/binding checks,
bounded reads and absence versus outage semantics.

Qualified P3.3a:8 transport/import tests plus generated-schema check and tsc pass.
The owning Gateway0.6 boundary passes84 source/boundary and78 independently
installed checks. Visual/page-model acceptance remains P3.3b/c.

## Original command submission

`CurationSubmission` normalizes the public request and identity default, validates
same-scope unique context pins, and freezes integer/reference-only command bytes.
It uses the published Python command profile's ASCII escaping and exact SHA-256;
Unicode vectors from the public parser verify parity. This encoder must not be
reused for graph constants or arbitrary floating-point payloads. Curation ID is
the canonical original identity digest. Intake/query receipts must be the exact
original revision-zero queued receipt, not the later curation progress view.

`CurationCommands` exposes only explicit POST intake and read-only receipt query.
Named missing differs from endpoint outage. It never retries, changes identity,
raises a budget, reads a provider key or interprets receipt acceptance as a model
result. Response bounds, cancellation and exact receipt binding apply to both.
