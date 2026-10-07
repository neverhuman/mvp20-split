# Criterion follow-up binding

Owner: Planning. SQ-01/C2a and C2b complete; Runtime acceptance remains C2c.
Research owns scientific records; Runtime owns execution. No peer-private imports,
SQL or scientific verdicts belong here. Source/test owner: agent-planning,
`tests/campaign_followup`. Current Planning0.104; no persistence migration.

FollowupSelectionPolicy requires the exact new output profile, selected scoped
question/need/assessment identities, unique criteria and an included focus Artifact
when supplied. ResearchSelection version1 bytes remain unchanged; version2 explicitly
selects the additive public contract. Factories reparse caller-modified DTOs.

CriterionBindings checks exact question/need relationship, criterion membership and
optional assessment request/status digest/criterion decision against revalidated
Research records. Missing selected identity records reject; weak/conflicting science
does not. Unassessed points use assessment=None. Selection is not authority to read
or evidence that an assessment exists. Direct dataclass construction is not proof.

FollowupResearch uses reviewed private planning-followup-seed.v1 configuration: exact
budget_template ArtifactRef, at most64 typed criterion refs and optional focus_artifact.
At most64 seeds are configured; their template identities must be unique. The worker
binds the request-specific public CampaignFollowupSelection, then reads exact public
Research records before immutable preparation. Incremental record checks use the base
selection; final binding checks complete criteria. No fresh scientific repinning on
retry or restart. Changes to seeds affect later preparation, never retained packets.
Missing selected records stop before issuance. Data processing permission remains
separately enforced by the existing Artifact reader before each physical attempt.

FollowupPreparation reconstructs immutable packet bytes, original selection, public
records and consumed observations. Existing Research slice formatv1 already carries
full selection, so no new packet codec is needed. Optional human focus must actually
be an included available Artifact body. It remains untrusted context, not permission.

FollowupOutput applies existing size/action/decision/scope rules to the future-only
profile. PreparedFollowupProposal additionally binds exact criterion/evidence/focus
references against retained input. Each selected point must remain targeted or
unresolved; duplicates and foreign points reject. A point may occur in both groups.
Abstention has no targets. Improvement/expected learning are nonblank qualitative
intent, not calibrated gain or scientific truth. Its fingerprint reconstructs the
whole record; retained replay grants no fresh owner access or execution authority.

Provider capture parses structure. The checkpoint wrapper applies retained-input
validation before successful observation; CaptureOrigin independently repeats it
before publication, even if a caller bypassed that wrapper. Invalid captures remain
diagnostics. The new profile cannot produce materialization adjustments. Runtime
acceptance and subsequent campaign admission are separate, currently pending gates.
Configured providers remain disabled by default; the deterministic abstention fixture
retains all unresolved points. Existing live adapter is still old-profile-only.

Verified 2026-10-07 14:02:37:242 affected-boundary tests pass850.77s, including actual
Planning SQL, process recovery, publication and old-profile compatibility. This module
187statements/26branches100%. Additional5 scoped checks pass12.89s, including assessed
seed reconstruction and publication rejection of a forged structurally valid capture.
No paid model call, independently installed new owner, or scientific qualification.
Frozen demo packages/assets remain separate. Replacements must preserve old canonical
bytes, original request/selection/read-set binding, immutable recovery and publication
validation; no routine in-campaign approval gate or active correction is introduced.
