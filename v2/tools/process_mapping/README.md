# Process mapping boundary

Owner: POP-01.01/E1. Implementation: 0.1 pure synthetic process lineage/mapping;
no registered worker, deployed service, chemistry model or Runtime acceptance yet.
Design: [Multistage process graphs](../../docs/Architecture/Campaigns/Multistage_Process_Graphs.md).

This independently built package owns MaterialState/ProcessDerivation validation
and pairwise, keyed or explicitly opted-in Cartesian material mapping. It imports
only public contracts; Search, Runtime, Data and Research implementations are absent.
Search owns genetic parentage and survivor selection, not material transformation.

BoundMaterial verifies supplied canonical bytes/reference pins, candidate/generation/
process-batch identity and scoped representation/conditions. Physical material batch
identity stays separate from the process batch that prevents cross-wiring. Unknown
amounts/compositions/phases remain unknown. MaterialDerivation checks exact tool,
producer run, required/optional ports, typed representations, explicit optional-input
absence, new output revisions and output conditions. Inputs/outputs each cap at32;
the8192-byte row bound also applies, so maximum cardinalities are not always reachable.

MaterialMapping preserves pairwise declared order, sorts keyed intersections and
retains explicit unmatched exclusions when configured. Cartesian expansion requires
opt-in and preflight output count <=10000. Both input collections cap at10000; each
row <=8192bytes, page <=64rows/131072bytes, closure <=512pages/64MiB. Mapping manifests
bind separately verified ordered source references, policy and every page. Complete
byte replay verifies derived pages; callers still verify source collection bytes,
authorization, retention and accepted provenance before trusting this pure proposal.

No filesystem/network/state or execution side effects. Failures raise ValueError with
stable reason codes. Producer pointers are unverified locators. No reaction feasibility,
stoichiometry, safety, mass conservation, real material availability or lab-control
authority is inferred. Existing graph joins remain synchronization, not transforms.

Tests: `tests/lineage` and `tests/mapping`, registered as `process-mapping` scope.
Replacement must preserve exact public schemas, canonical bytes, rejection reasons,
mapping order/cardinality and context isolation. The19-stage test verifies lineage
contracts only; local readiness, durability/restart and UI traversal are later POP
execution/experience/qualification gates. No shared mutable state or private imports.
