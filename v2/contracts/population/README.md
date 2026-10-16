# Population wire boundary

Owner: POP-01.01/E1; approved [POP-01.04](../../docs/Build%20Plans/POP-01/POP-01.04%20Population%20contract%20decision.md).
Implementation checkpoint: package0.5, specification, membership, birth/evaluation,
fitness/selection records and bounded evidence pages/manifests;
not an executable population profile.

This isolated package owns closed version1 `population.*` transport records. The
first profile is `numeric-population-v1`; old search version1 bytes, cardinalities
and receipts are unchanged. Public core/tools/search value DTOs are reused without
private imports. No scheduler, persistence, Data reads, numerical ranking, model
request or scientific authority belongs here.

PopulationSpecification groups a pinned named method graph, fitness assembly,
selection policy, numerical operators and bounded resources. Its method graph is
an Artifact/compiled-plan reference, not a self-authorizing graph. Schema validation
does not establish unique methods, objective coverage, compatible units, original
pin consistency, artifact access or admissible expanded work. Search domain
validation and Runtime admission must establish their respective invariants.

Membership pages distinguish cohort from parent/offspring selection pool, carry an
exact generation identity and bind ordered references/counts. Pure Search validation
checks supplied canonical bytes and scopes. Data/Runtime must separately verify
access, publication, retention and accepted predecessor/producer history.

CandidateBirth keeps two-parent numerical ancestry distinct from material derivation.
Its disposition does not redefine its identity. EvaluationKey excludes attempt IDs;
MethodObservation separately names a producer attempt/completion or unavailable
outcome. An ExecutionPointer is a locator to verify with Runtime, not an accepted
execution proof. MethodBinding.output_schema identifies the one primary method
result; supplementary outputs require independent descriptor/provenance validation.

Package-owned tests live under `tests/specification` and `tests/identity`. Rebuilds must preserve strict
closed DTO behavior, generated schema identities and negative wire cases. New
versions must not silently relax old contracts. Graph execution remains a separate gate.

FitnessRecord retains ordered objective values/units and their supporting evaluation
identities, provenance labels and optional confidence. Unavailable fitness has an
explicit reason and no number. Selection pages distinguish ranked and excluded
members. PopulationSelectionReceipt binds the full pool, fitness source, observation
cut, every rank page, survivor membership and frozen policy; it is proposed evidence,
not a Runtime acceptance receipt. Old search receipts/limits remain unchanged.

Birth/evaluation/observation/fitness manifests keep full histories out of growing
inline checkpoints. Page counts alone do not prove byte bounds or integrity; Search
verifies canonical page bytes and complete source linkage. Fitness pages may retain
parent evidence from an earlier generation of the same immutable specification;
the selection owner must check parent membership/predecessor authority separately.
PopulationCheckpoint and ProposedSuccessor retain independently verified selection,
exact predecessor, RNG position, reference-backed birth/offspring/pool/evaluation
closure and budget counters. These are proposals, not accepted Runtime commands.
MaterialState/ProcessDerivation distinguish process context and physical batches,
unknowns, up-to32 inputs/outputs and typed port roles from genetic two-parent ancestry.
Synthetic process mapping pages/manifests preserve explicit pairing policy and source
pins. Process behavior belongs to independent process-mapping, not Search.
EvaluationSlot/DeclarationManifest freeze occurrence membership without exact future
inputs; ResolutionManifest binds its complete resolved key set. Admitted topology
still determines correct declarations, including skipped/conditional occurrences.
Graph-step DTOs are isolated in population_steps; execution composition remains E1/D4.
