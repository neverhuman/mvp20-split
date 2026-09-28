# Intent and Decision Contracts

- Design status: detailed proposed contract; implementation and scientific acceptance pending
- Naming note: component/record/operation names below are proposed logical design, not implemented APIs or selected deployment technology
- Last reviewed: `2026-09-22 18:56:40` (America/Chicago)
- Parent: [Domain overview](Research_Architecture.md)
- Requirement source: [Product Requirements](../Requirements/Product_Requirements.md#envelope-intake)

## Owned Contract

A research objective becomes a versioned decision contract with scope, hypotheses, success criteria, hard constraints, soft objectives, allowed variables, budget, authority limits and unresolved questions. Preserve each field's source and customer-stated, inferred or defaulted origin. Human feedback produces attributable amendments; sign-off binds a revision before expensive generation.

Characterization owns sample identity, analytical fingerprints, competing composition hypotheses, mass balance and unidentified fractions. Baseline reconstruction is explicitly uncertain. A reconstruction becomes an optimization seed only after declared fingerprint, processing and performance gates pass, or an authorized alternative starting posture is recorded.

## Boundary and Flow

Inputs are source text, project context, methods and measurements. Outputs are reviewed objectives, ambiguity records and accepted baseline references. LLM extraction proposes fields; checks and review establish the contract. Campaigns owns execution. Qualification references do not confer external qualification authority.

## Invariants and Verification

Keep hypotheses, observations and accepted constraints distinct. Invalid units, missing method/context and blocking ambiguities remain visible. Verify source-to-field provenance, signed-revision immutability, feedback history and rejection of unsupported baselines. Research without a manufacturable formulation must not inherit epoxy fields by default.

## Component and Object Design

| Proposed component | Owned records and behavior |
|---|---|
| Intake compiler | Source-to-field proposals, source-span references, units and origin classification; never signs its own extraction |
| Decision-contract aggregate | Objective/envelope revisions, immutable signed snapshot, allowed variation and revision preconditions |
| Ambiguity resolver | Questions, responses, resolved field references and blocking/nonblocking classification |
| Baseline adjudicator | Reconstruction hypotheses, fingerprint/mass-balance comparisons and acceptance decisions |

A field assertion includes value, unit/context, source revision/span, origin, uncertainty and reviewer disposition. `ProductDesignSpace` owns variable types, bounds, fixed values, conditional combinations and permitted operators. Transport DTOs serialize these objects; validators and policies belong to the objects that own the failure modes.

## Lifecycle and Interaction

`Draft -> extracted proposal -> needs clarification / reviewable -> signed -> superseded` describes contract revision state, not campaign execution. An amendment forks a revision from a signed parent. Validation reports affected requirements; the previous signed revision remains usable by its already-bound campaigns unless an explicit withdrawal policy applies.

For an unknown incumbent material, an evidence request references sample and method identities. Returned observations update a reconstruction hypothesis, not the signed recipe. Acceptance compares declared fingerprint and process criteria; incomplete characterization yields an underdetermined result. Campaign submission consumes the signed objective and accepted baseline references, and returns a run identity rather than modifying the objective.

## Failure and Boundary Example

If a user corrects a concentration unit after sign-off, create a new field/envelope revision and an impact record. Do not reinterpret earlier candidate evaluations with the corrected value. If the change invalidates active work, submit a policy-bound pause/review command to Campaigns. Conflicting concurrent edits fail their base-revision precondition and return the current diff.

## Design Basis and Open Decisions

[Domain Model](../Requirements/Domain_Model.md) supplies envelope/design-space and reconstruction concepts. Remaining decisions: domain-specific minimum required fields, versioned unit ontology and which ambiguities block each operation. These must be chosen with acceptance fixtures; generic mandatory coatings fields are not the default for biology.
