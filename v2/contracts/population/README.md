# Population wire boundary

Owner: POP-01.01/E1; approved [POP-01.04](../../docs/Build%20Plans/POP-01.04%20Population%20contract%20decision.md).
Implementation checkpoint: specification and membership-page/manifest DTOs;
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

Package-owned tests live under `tests/specification`. Rebuilds must preserve strict
closed DTO behavior, generated schema identities and negative wire cases. New
versions must not silently relax old contracts. Birth, observations, fitness,
selection/successor records and process lineage remain subsequent E1 deliveries.
