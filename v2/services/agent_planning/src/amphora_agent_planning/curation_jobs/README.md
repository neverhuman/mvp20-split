# Recoverable campaign curation jobs

UI-01.08/P2.3b.1; Planning-owned internal state, migration0023. Public request
and receipt contracts remain0.1.0. Architecture: ../../../../../docs/Architecture/Agents/Planning.md.

CurationJobs claims an exact original curation for its authenticated actor/scope
with the distinct execute_curations grant. Record/read grants cannot claim, fail
or heartbeat work. Initial claim appends assembling revision1; replacement resumes
the latest retained projection without resetting it. Each claim has a fresh random
fence and database-clock lease (1..60seconds). Expired/replaced leases and stale
progress revisions reject writes, even if the replacement reuses a worker name.
Heartbeats update only the private lease, never immutable evidence.

State: curation_progress is SELECT/INSERT-only canonical CurationView bytes/hash
and revisions; curation_leases is the mutable coordination record. Original queued
receipts stay byte-for-byte intact. CurationJournal GET projects current progress;
receipt reconciliation always returns the original acknowledgment. Advisory locks
serialize short job transactions; all peer/provider I/O occurs outside them. SQL
failure rolls back both initial progress and lease acquisition. Claiming a job does
not issue a provider request, reserve money, save a graph or admit a campaign.

Current implementation supports claim/reclaim, heartbeat, prepared-input progress and terminal failure.
Failure before preparation is failed; later unfinished side effects require
indeterminate. Prepared transition is coordinated atomically by curation_preparation with its
immutable exact-input link. Proposed/compiled transitions belong to P2.3c and
must bind original durable records before exposing those states. No running worker,
public context builder or live-demo readiness is claimed by this module alone.

Replacement acceptance: module tests prove duplicate claim contention, lease
expiry/fencing, rollback, actor/scope/grants, immutable history, unchanged original
receipts and zero provider attempts. Restore/latest progress is validated against
the original command pins and canonical digest. No private peer-service dependencies.
