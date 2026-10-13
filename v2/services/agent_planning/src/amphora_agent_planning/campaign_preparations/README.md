# Campaign preparations

UI-01.08/P2.2 reconstructs prompt-only Artifact bodies from the exact request-selected
reviewed instruction profile. Curation fit.v3 and its distinct prompt are additive;
old campaign/supervision prompt and manifest bytes remain unchanged.

Owner: Agent Planning. Architecture: [Planning](../../../../../docs/Architecture/Agents/Planning.md). The pure record, immutable journal and issuance/replacement integration are verified under the [journal design](../../../../../docs/Build%20Plans/BP-07/BP-07.03%20Campaign%20preparation%20journal.md).

`CampaignPreparation.bind(plan, packet)` reruns deterministic packet reconstruction and rejects changed fit/inclusion before creating a byte-owned record. `PacketEvidence` owns exact packet profile, original request, reviewed instructions and measured fixture budget. `PreparationInputs` owns ordered candidate identity, required/inclusion policy, omission and observation correspondence. Private Pydantic records serialize those objects; they do not authorize processing or own orchestration.

The canonical `planning-campaign-preparation.v1` manifest stores scoped engagement, original request SHA, original plan SHA, packet identity/fit and candidate summaries. Packet bytes remain a separate immutable value. Candidate summaries contain lane, identity, payload SHA, required/included flags and consumed observations. Omitted bodies and their unused observations are not copied into this history. Limits are2MiB manifest,8MiB packet,900 candidates and existing lane counts. Overflow rejects. The original full128MiB candidate plan is never silently persisted.

`from_bytes(original_request, manifest, packet)` is a strict canonical readback boundary: bounded bytes, no duplicate JSON keys, unknown fields, nonfinite numbers or alternate encodings. It binds the exact scoped request and packet digest/size/profile, reruns reviewed instruction and budget validation, checks required-first candidate order and unique identities, validates lane requirement/count/dependency rules, and matches included payload hashes, omitted hashes and consumed observations. It revalidates included Artifact roles/bodies/status and their original observation hashes. A prompt body represented by trusted-field location is restored solely from the reviewed profile for digest checks. Missing optional Artifact data remains an explicit observed gap.

Owner projection records are retained observations, not fresh owner reads or scientific truth. Readback establishes stored byte/selection consistency; it does not recompute omitted bodies or contact owners to renew grants. Full greedy packing can be reconstructed separately when the caller supplies the original validated plan. Register factories must use that original plan; byte readback alone is not a dispatch API. SQL must additionally verify every duplicate row identity/hash against this record.

Research slices now preserve the full original selection alongside context/findings, including expected assessment hashes for missing records. This provenance correction belongs to the preparation work; it does not reopen closed gates or change public contracts. The fixed Planning0.46 root/Runtime predecessor packet remains byte-identical. Prior transient Research slices without full selection are not claimed as durable preparation histories.

Tests under tests/campaign_preparations cover fixed predecessor preservation, immutable roundtrip, no copied omitted body, malformed/oversized/unknown fields, changed request/profile/fit, candidate/omission/read-set consistency, rehashed corrupt Artifact bodies, forged packet inclusion and optional denied reads. Initial SQL smoke covers registration/readback and privileges; provider behavior remains outside this module. Replacements must preserve canonical record/packet bytes or add versioned profiles while retaining readback of existing records. Never turn historical readback into fresh processing permission.

`journal.CampaignPreparationJournal` binds/reconstructs before SQL, then locks family before request and rejects extraction-family membership. It requires record_attempts and original actor/scope, exact stored request and campaign/supervision purpose. One scoped preparation wins; exact retry returns original bytes/timestamp, changed contents conflict. First registration after any dispatch/observation rejects; unissued reservations are unaffected. Read requires read_attempts and a known authorized request, returning None only for absent preparation. Every SQL identity/hash is compared with the validated record. planning_0012 grants SELECT/INSERT only and uses foreign keys/byte bounds; no update/delete, backfill or downgrade. Never run Planning<=0.48 migrators on0012. Module-owned SQL tests live under tests/campaign_preparation_storage, separate from pure tests and opt-in/serial. Twenty-three opt-in SQL cases verify authority, original-request/conflict, late-write refusal, unissued reservation, exact replay after issuance, copied-row corruption, immutable privileges, rollback and competing writers/dispatch. Two fresh isolated Planning0.49 installations pass23 SQL cases and7 worker stages: absence, commit then lost acknowledgement(exit91), recovery, replacement read/exact replay/conflict rejection and initial readback. Exact hashes and registration timestamp persist. This is process/install replacement of the same implementation, not a fresh rewrite. No peer calls occur inside SQL; old generic dispatch is unchanged.

UI-01.08/P2.3b.2 permits up to8 required graph slices for the exact curation output
profile. Single-graph/legacy canonical histories retain their1-graph limit and
unchanged bytes. Each graph remains separately identified and hash-checked during
replay; no graph is silently omitted to fit context.

Curation intent is a separately validated required lane for the exact new profile;
replay checks original command/request binding and empty scientific observations.
Existing retained curation fixtures without that later lane remain readable.

Curation Knowledge summaries require original intent and exact selected-head
coverage, bounded read accounting and one matching graph projection per available
head. Summary/head mismatches reject even if payload hashes were recomputed.

Curation Runtime replay revalidates exact original draft/content and predecessor
pins against required intent, including the authored-order public content digest.
Old profiles cannot acquire this additional required lane.

Curation registration supplies an optional SQL guard before a NEW preparation
insert, checking the current job fence while holding the request lock. Exact replay
returns immutable history without a new write. Generic registration is unchanged;
callbacks must not perform peer/provider I/O or open nested transactions.

UI-01.08j/M3.4 Planning0.141 bounds an exact-byte verification cache to one retained
preparation. from_bytes validates request/manifest/packet types and size ceilings
before lookup; its key includes the complete immutable request, manifest and packet
bytes. A miss runs the original canonical/profile/budget/candidate/observation checks;
failures do not populate the cache. The result contains only frozen byte-owned
CampaignPreparation/PacketEvidence/RequestSnapshot objects. document/context methods
still decode fresh projections, so mutating a returned DTO cannot change the proof.
Eviction and process replacement revalidate normally. Maximum retained input is
256KiB request +2MiB manifest +8MiB packet (plus bounded derived fit bytes); no growing
cross-campaign cache. This contains no principal grants, leases, fresh processing
permission, Registry capacity or mutable owner projection. SQL readers still check
stored row identities/digests and callers still perform fresh dispatch prerequisites.
Tests: test_verified_cache plus existing corruption, fit and storage/dispatch suites.
Actual original scientific compilation is a separate acceptance gate.
