# Source Rights

- Status: BP-06.01/B2 implemented within the bounded local/synthetic profile; failure/replacement acceptance remains B3/V1.
- Owner: Data/Artifacts; design [Acquisition](../../../../../docs/Architecture/Data/Acquisition.md).
- Public contract: evidence0.5.0 SourceRightsRevision; Data/Artifacts0.9.0; artifact_0006.

## Responsibility and Authority

RightsPolicy owns predecessor ordering, supported grant combinations, expiry and purpose checks. SourceRights owns immutable rights revisions/current heads and provenance-derived authorization fences. RightsSnapshot binds a scope, artifact IDs, explicit historical references, purpose and observed current head revisions. No Research, Runtime, license-provider or scientific acceptance authority is imported. Source rights are explicit owner assertions, not an interpretation of a license document.

A grant allows read, or read plus process. Process without read is invalid; revoked grants have no allowed uses. Expiry is timezone-aware and checked against the PostgreSQL clock: the boundary is exclusive (now >= expiry denies). Rights references must exist historically; their ID's current head controls new use. Unknown policy denies. RightsPolicy validates consecutive same-ID/scope predecessors; SourceRights.publish additionally enforces current-head order and exact immutable replay. Replaying an old revision never moves the current head backward.

The only supported retention profile is retain_audit_payload: retain immutable payloads and permitted metadata for audit, while restricting current consumption. This is the explicit synthetic/local fixture profile. Sources requiring payload erasure or incompatible license retention must not be admitted under it; this release does not implement mandatory deletion or infer a compatible policy. Existing finalized-artifact cleanup does not erase these payloads.

## State and Public Operations

artifact_0006 adds source_rights_revisions and source_rights_heads, plus raw-source/output lineage indexes. History is insert/select-only; only the head revision column is mutable. No rights are backfilled or invented for old source records: unresolved historical references deny future consumption until explicitly resolved. Existing source/trace/observation bytes and publication command encodings remain unchanged.

With acquisition enabled, POST /v1/acquisition/rights accepts SourceRightsRevision and requires manage_source_rights. GET /v1/acquisition/rights/{id}/{revision} requires source_history and returns immutable policy metadata or404. New source registrations must pin the current rights revision; exact old-source replay preserves its historical pin while checking current permission. Rights updates do not rewrite source, trace or observation history.

ArtifactReads.content always enforces rights, even when acquisition routes are disabled. Metadata-only ArtifactRef and history projections remain inspectable through their existing principal actions. Artifact reads follow retained conversion lineage back to all associated source revisions; every distinct rights binding must permit the use. Recursive UNION handles repeated ancestry without looping, and more than256 distinct rights-revision bindings fails closed. No binding means the existing unassociated-upload read policy still applies. Equal bytes with different artifact identities are not conflated: independently acquired contexts retain their own provenance. Unattached copies cannot acquire inferred lineage merely from a matching hash; callers must register real source/trace provenance before claiming evidence usability.

## Consistency and Failure Semantics

Current rights, new source bindings and new trace/result commits use one ordered advisory lock per tenant/project, appropriate to the single-campaign profile. Filesystem reads, conversion and peer HTTP run outside SQL locks. Byte reads capture policy before I/O and recheck current heads/expiry after I/O. Preparation similarly rechecks before returning. Trace and new identity-result commits recheck the captured rights inside their owner transaction. A changed policy head yields rights_epoch_changed even if both versions allow use; retry must re-evaluate the new policy. Revoked/expired/missing/denied grants yield safe403; immutable revision/head/epoch conflicts yield409.

Revocation committed before the final fence blocks that operation's result. This is an explicit authorization point, not a promise to retract bytes already delivered or undo a peer read. A rights change during Research HTTP can leave a pending observation after the external read occurred; it cannot publish the result. Exact completed observation receipt replay is historical metadata: it checks principal scope/actions, avoids raw reads and does not recontact Research. It confers no new-use or scientific authority.

The host requires migrated rights tables for content reads. Deploy Data/Artifacts0.9.0 or later wherever these policies must apply; older reader implementations do not implement this fence and are not supported rollback targets after activation. No migration or external rights refresh runs at service import/startup.

## Tests and Replacement Boundary

Run dev/run_tests.py --module data-artifacts --area source_rights for the focused policy/persistence/HTTP suite. Tests use actual PostgreSQL and finalized artifacts: immutable policy replay, stale heads, conflicting concurrent revisions, rollback, denied history mutation, exact expiry, unknown policy, read-only restrictions, revoked raw/derived reads, multi-level ancestry, mid-read head changes, mid-peer revocation, historical receipt replay and public management permissions. The acquisition suite preserves deterministic/inferred/missing-field and delivery/trace invariants; no new scientific acceptance is inferred.

Replacement must preserve the versioned DTO, immutable canonical history, scope authority, first-class use purposes, recursive provenance restrictions, transaction fence ordering and explicit retention limitations. Independent wheels run the policy suite with no Research implementation installed. Missing/corrupt database states and extreme lineage bounds fail closed; final crash/cutover and named B3 cases remain separately gated.

BP-06.03 DER-01 probe verifies the intentional identity boundary: a separately finalized equal-byte upload does not inherit another artifact's lineage or later revocation. New arbitrary derivation publication therefore requires explicit input edges before output visibility; the [proposed prerequisite](../../../../../docs/Build%20Plans/BP-06/BP-06.03%20Derived%20publication%20prerequisite.md) is awaiting owner direction. This adds no production behavior and does not weaken existing source/trace enforcement.
