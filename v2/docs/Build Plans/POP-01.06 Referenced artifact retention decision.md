# POP-01.06 Referenced artifact retention decision

- Status: proposed; new public boundary awaits owner approval.
- Reviewed: 2026-10-14 21:32:00 America/Chicago.
- Owner: POP-01.01/E2.2 prerequisite. E1 and E2.1 remain complete.
- Recommendation: Data-owned retention of a complete declared derivation closure,
  using Runtime's existing completion proof. Preserve worker completion wire formats.

## Reproduced gap

The existing numerical fixture generates1000 distinct proposed births. Each
CandidateMember requires a CandidateBirth-schema Artifact reference; a birth-page
reference cannot replace it. Ordinary completion permits64 named output artifacts
and one checkpoint. Runtime CompletionProposal.artifacts reserves only those direct
references. Data's current reserve transaction reserves exactly the named catalog
artifact; derivation/conversion ancestry does not create additional reservations.

Thus returning a manifest does not establish protection for its referenced records.
Finalized content currently has no deletion operation, but that is not the protected
closure promised by POP-01.04. Publishing more unreserved children or giving workers
Runtime's retention authority is not an acceptable implementation of that promise.

Pure proof: .test-results/prove_population_retention_gap.py and
pop01-retention-gap-proof.json. Source: tools/models.py Succeeded;
campaign_runtime/completion/model.py CompletionProposal.artifacts;
data_artifacts/retention/reservations.py ArtifactReservations.reserve;
population/membership.py GenerationMembership. No live run or new container used.

## Proposed additive boundary

1. A separate public `artifact_retention` contract package defines profile
   `derived-closure-retention-v1`, with a root ArtifactRef and existing
   CompletionIntentBinding. Command `artifacts.reserve_derived_closure` uses
   `POST /v1/retention-closures/reserve`; scoped readback uses
   `GET /v1/retention-closures/{reservation_id}`. Same Runtime-owner retention grant.
2. Data follows its immutable derivation/conversion edges, validates exact scoped
   catalog identities and rejects cycles/conflicts or more than4096 distinct
   artifacts. Existing128-direct-input bounds remain. It does not interpret opaque
   scientific payloads. Population producers must declare every referenced child
   through these edges; source/processing rights remain separate checks.
3. One reservation binds the root, exact membership digest/count and immutable
   member set atomically. The receipt wraps the existing root reservation receipt
   with the explicit profile/digest/count. Existing Runtime committed/aborted proof
   confirms/releases the whole group atomically; pending/uncertain keeps it protected.
   New private Data membership storage is expected; no execution counter is added.
4. Runtime explicitly selects and durably pins this retention profile for new
   configured runs. Its Artifact client uses the new Data boundary and verifies
   its receipt/readback. Unprofiled history keeps ordinary reservation behavior;
   there is no silent fallback or repinning. Worker claim/completion DTOs, command
   bytes and Runtime's sole execution authority remain unchanged. Admission/startup
   must reject unavailable/incompatible configured owner support before execution.

Every currently published schema and legacy receipt/command byte remains pinned.
Private migration/profile/recovery details are implemented and qualified within E2;
any further public route or changed legacy semantics returns to review.

## Qualification and rollback

Prove nested/shared ancestry, exact scope/hash/count, all-or-nothing reservation,
same-command replay, partial failure, prepared/uncertain proof, cancellation and
independent Data/Runtime restart through actual owner APIs. Preserve old direct-root
behavior and old history. Keep all newly created test containers under finally cleanup.

Expanded ancestry is another admission bound: reject combinations that exceed4096;
do not advertise the population/generation maxima as an unrestricted product.
Drain profiled runs before downgrading and retain all confirmed protection/history.
No new graph primitive, numerical policy, scientific authority or second runner.

## Owner decision requested

Approve this additive Data retention boundary and explicit Runtime profile binding
so the population workers can publish fully protected reference-backed generations.
