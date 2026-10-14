# POP-01 E1 contract and consumer map

- Status: source-verified records/domain; graph-step transport and execution composition pending.
- Reviewed: 2026-10-13 21:24:08 America/Chicago.
- Owner: [POP-01.01/E1](../Build%20Plans/POP-01.01%20Population%20Execution.md).
- Source checkpoint: population0.4, Search0.9, independent process-mapping0.1.
- Evidence: 288 source checks and dependency guard pass;718 generated schemas preserve
  all704 predecessor schema bytes. Independent installation evidence recorded in plan history.
- Limits: no population worker registration, Runtime transition, scientific validity,
  scale measurement or deployed UI claim. Domain verification is not execution acceptance.

## Record and behavior ownership

| Public records | Behavior owner / producer | Consumers and remaining authority checks |
|---|---|---|
| PopulationSpecification; method/policy/budget pins | Search OriginalPopulation; eventual Planning preparation | Registry verifies exact eligible releases; Runtime binds admitted graph and work limits; Data verifies referenced content/access |
| CandidateBirth; BirthPage/Manifest | Search NumericBirth / successor replay | Research checks representation/eligibility; Runtime verifies accepted producer; Data retains every referenced page/birth |
| GenerationIdentity; MembershipPage/Manifest | Search GenerationMembership | Runtime accepts complete immutable cohort and predecessor before dispatch; Studio later consumes bounded authoritative projections |
| EvaluationKey; MethodObservation; key/observation pages/manifests | Search BoundEvaluation/FrozenEvaluations; actual scientific workers produce outputs | Runtime owns attempts, fences and completion; assembly verifies method/policy/material provenance; Research distinguishes predicted/measured/synthetic |
| FitnessRecord; FitnessPage/Manifest | Registered assembly tool supplies numeric objectives; Search verifies evidence links | Search performs whole-union selection; Runtime accepts exact tool output/protected closure; Studio does not rerank |
| SelectionPage/Receipt | Search PopulationSelection/PopulationDecision | Runtime verifies exact frozen pool/cut and accepted predecessor; proposed receipt is not a Runtime command receipt |
| PopulationCheckpoint; ProposedSuccessor | Search SelectedGeneration/SuccessorContinuity | Runtime authenticates checkpoint selection, counters, protected source closure and unique acceptance; successor publication alone cannot release new work |
| MaterialState; ProcessDerivation | Independent process-mapping validation; eventual registered synthetic transform supplies states | Runtime/SDK verify invocation/input/output and release pins; Data owns authorization/retention; Research owns scientific applicability |
| MaterialMappingPage/Manifest | Independent process-mapping MaterialMapping | Runtime ordinary scatter consumes verified bounded materialization; mapping is neither chemistry nor genetic crossover |

All public records remain in the focused population contract package. Numerical
behavior remains private to Search; process behavior remains private to the separate
process-mapping package. No service imports either implementation to gain authority.
Owners communicate through public contracts, Artifact APIs and accepted Runtime proofs.

## What byte verification establishes

Canonical population-json-v1 uses validated explicit fields, sorted compact finite
UTF-8 JSON and no trailing newline. Domain identities use separate hash namespaces.
Schemas publish through the existing generator; old search roots and limits do not
change. Immutable pages verify exact schema/scope/hash/size/count/order/partition.

Supplied membership/source references remain independently verified caller inputs.
They are not made trustworthy by placing them in a manifest. RetainedEvaluations and
RetainedFitness verify supplied page bytes and reconstructed evidence links. An
ExecutionPointer is an unverified locator until its owner checks accepted execution.
SelectedGeneration checks supplied selected birth bytes and replay; it cannot prove
that an arbitrary supplied checkpoint was accepted by Runtime.

Process mapping similarly binds independently verified ordered collection sources.
It checks context, exact material references and deterministic derived pages. No
mass balance, physical availability, real reaction, lab operation or safety claim
follows from a valid derivation record. Physical material batch IDs are distinct
from the process batch used to prevent candidate/generation cross-wiring.

## Transport/composition gate still open

Graph-step DTOs must be separate from these retained domain records. Do not reuse
legacy inline SearchStepContext/128-member EvaluationRequestBatch for the new
reference-backed profile, nor create an unbounded inline equivalent.

The concrete composition must resolve when an evaluation key can be frozen: exact
intermediate input Artifacts do not exist before their upstream transform completes.
The campaign must freeze candidate/method membership and admitted expansion policy
before dispatch, then bind a method occurrence to actual accepted inputs at local
readiness. Final terminal observation coverage must match that declared membership,
including skipped/failed paths. A post-hoc list of successful keys is insufficient.
Current FrozenEvaluations validates a supplied resolved key set; it does not yet
implement unresolved occurrence declarations or dynamic graph dispatch.

Runtime currently serializes claims under a run lock and enforces total attempt
budget, but GraphLimits has no campaign-wide active-invocation cap. Scatter
max_parallel counts active child scopes; a child can contain several concurrent
invokes. Limiting child count or deployed worker count is insufficient to enforce
the approved1..8 campaign invoke budget. Transport cannot claim that bound until the
concrete execution profile/transition design resolves it.

E1 must still produce the transport, compiled graph fixture, resource calculation
and write-set map. New public Runtime command/profile changes require the specific
review promised in POP-01.04. Existing generation, graph and command profiles remain
unchanged. E2 cannot begin at this source-record checkpoint.
