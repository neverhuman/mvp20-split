# Criterion follow-up binding

SQ-01/C2a. Planning owns exact selected criterion membership and proposed future
intent. Research owns scientific records; Runtime owns execution acceptance.
This module has no SQL, provider, publication, filesystem or peer calls.

FollowupSelectionPolicy requires the new exact output profile and selected scoped
question/need/assessment identities, unique criteria and an included exact focus
Artifact when supplied. Existing ResearchSelection retains old version1 canonical
bytes; explicit version2 selects the new policy. Caller-modified DTOs are reparsed.

CriterionBindings verifies selected points against already revalidated Research
records: exact question/need relationship, criterion membership and optional exact
assessment request/status digest/criterion decision. Missing identity records reject;
unknown/conflicting/weak scientific outcomes do not. Unassessed points are supported
with assessment=None. A supplied assessment must be available and contain that
criterion; absence is not inferred to be an assessment. Factories validate membership,
not fresh processing rights or owner contact. Do not trust direct dataclass creation.

Output binding preserves exact point/assessment and human focus identity, rejects
duplicate or foreign targets, and requires every selected point to remain either a
future target or an unresolved item. The same point may appear in both. Abstention
cannot advertise targets. Learning is qualitative and nonblank. No target becomes
resolved or scientifically established. General action/payload/profile validation
and actual output publication integration remain C2b; Runtime acceptance remains C2c.

Tests belong to tests/campaign_followup. Existing context tests must preserve old
selection and packet fingerprints. Current Research packet remains version1; this
checkpoint validates membership but does not yet serialize target intent into model
preparation or enable the provider profile. That integration is C2b.
