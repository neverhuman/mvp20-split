# POP-01.08 Artifact ancestry footprint decision

- Status: owner-approved; implemented and independently qualified in Data0.33/artifact_ancestry0.1, with Search0.24 consumer.
- Reviewed: 2026-10-15 22:24:23 America/Chicago.
- Owner: Data; POP-01.01/E2.3 external-source resource preflight prerequisite.
- Recommendation: one scoped read-only metadata GET, returning totals only.

## Verified gap

Search now bounds authored work, retries, numeric-worker publications and page
envelopes. Complete external-source ancestry remains invisible to an ordinary
read principal. GET ArtifactRef exposes the root only. GET derivation exposes
declared derivation inputs, but404 does not establish an ordinary leaf and that
route does not expose conversion-trace ancestry. Conversion trace reads require
the already-known trace ID; there is no artifact-to-all-traces discovery route.

Data already traverses BOTH conversion and derivation edges for protection. Its
retention-closure GET requires the retention grant, an existing reservation ID,
and returns the captured membership count/digest without content-byte totals.
Reserving just to inspect would mutate protection and give the authoring caller
retention authority it does not need. Caller-side guesses cannot verify that
new outputs will fit the4096-artifact retained-closure ceiling.

Evidence: Data api.py metadata/derivation routes; acquisition/api.py trace reads;
source_rights/ancestry.py bounded traversal; retention_closures/storage.py discovery
and reservations.py retention-only reads. This proposal reuses that owner-local
discovery rather than copying owner SQL into Search or granting worker retention.

## Approved exact boundary

GET `/v1/artifacts/{artifact_id}/ancestry-footprint`.
Existing tenant/project-scoped `read` grant. No new action, command or query inputs.
Separate public `artifact_ancestry`0.1 package avoids modifying existing DTO formats.

| ArtifactAncestryFootprint field | Shape |
| --- | --- |
| schema_version / profile | `1` / `artifact-ancestry-footprint-v1` |
| artifact | Exact scoped existing ArtifactRef for the root |
| artifact_count | Distinct root plus all conversion/derivation ancestors,1..4096 |
| content_bytes | Sum of distinct catalog content sizes,0..9007199254740991 |
| members_sha256 | Existing derived-closure membership digest recipe over sorted full ArtifactRefs |

Read scoped catalog/lineage in one read-only repeatable-read transaction. Reuse
the existing128-parent/4096-identity traversal and cycle/conflict/missing-catalog
rejection. Checked byte summation rejects overflow. Bound serialized response to
262144 bytes and set no-store. No payload/storage-object reads, network calls,
rights grant, reservation/renewal, commands, counters, writes or schema migration.
Metadata access has the same authority ceiling as existing ArtifactRef/derivation
inspection; an observation does not authorize content processing or execution.

Return401/403 for authentication/grants,404 for an absent or scoped-away root,
409 for invalid/incomplete/oversized lineage or byte overflow,503 for unavailable
owner storage. No silent truncation, partial count or404-as-leaf convention.

This is a point-in-time catalog observation, NOT a durable snapshot/lease or a
promise that later registrations cannot add conversion edges. A changed digest
requires reassessment; existing authoritative Data completion/protection checks
remain mandatory. Summing footprints for multiple source roots double-counts
shared ancestry conservatively. This first endpoint deliberately exposes no
member list, edges, content, source-rights bindings or pagination.

## Verification and approval gate

Preserve all existing schemas/routes/receipts. Verify leaf, derived, converted and
mixed DAGs; shared ancestors count once; exactly4096 identities; parent/cycle/
missing/conflicting lineage; exact root identity; scope/grants; byte overflow;
response size; catalog changes; Data restart; no writes or worker retention grant.
Qualify through independently installed Data and a read-only public client, then
bind the observed counts/digests into Search's prospective resource assessment.

POP-01.06 requires that "any further public route or changed legacy semantics
returns to review." Owner explicitly approved this exact boundary on 2026-10-15; implementation is authorized.
E1/E2.1/E2.2 stay complete; no E2.3 unit credit or change to execution authority.
Authored batch-loop compilation and validation-I/O accounting can continue
independently after this qualified prerequisite. This does not approve original-demo
promotion or service restarts, fleet activity or provider calls.

Qualification and scoped drift review: [ancestry footprint audit](../../Audits/POP-01_Artifact_Ancestry_Footprint.md).
