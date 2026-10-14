# Population wire boundary

Owner: POP-01.01/E1; approved [POP-01.04](../../docs/Build%20Plans/POP-01.04%20Population%20contract%20decision.md).
Implementation checkpoint: package0.2, specification, membership-page/manifest,
candidate-birth, evaluation-key and method-observation DTOs;
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
versions must not silently relax old contracts. Fitness, selection/successor records,
evaluation paging/graph bindings and process lineage remain subsequent E1 deliveries.
