# Population graph-step transport boundary

Owner: POP-01.01/E1; public package0.1. Retained domain records live in population;
this package owns bounded reference-backed graph tool inputs and output envelopes.
No scheduler, scientific policy, Artifact I/O or private service imports.

SeedPopulationRequest names the original specification; the actual worker context
supplies the admitted run identity. PreparedPopulationGeneration groups exact birth,
cohort and declared-occurrence manifests. It is a proposal, not a grant to dispatch.
PopulationSliceRequest names that immutable preparation and a start/limit1..32;
PopulationMemberSlice references candidate-context Artifacts, not an inline full
population. Candidate context retains exact member/specification/declaration pins.
SelectPopulationRequest names the whole pool, fitness and complete declaration-to-key
resolution; predecessor is absent only for generation0. Successor request names an
exact selected checkpoint. Neither request itself proves accepted history.

The graph scatters candidate contexts into the admitted reusable method subgraph;
it does not flatten methods into independently scheduled tool requests or select per
page. Input dependencies resolve locally inside that subgraph. Intermediate-producing
tools retain their own named steps; declarations do not fabricate future Artifact refs.
Final selection requires every declared occurrence to resolve to terminal evidence,
including explicit unavailable/conditional-not-taken cases.

Consumers must verify source access/hash/schema/scope, cursor/member coverage, manifest
closure and original budget; <=262144 serialized bytes still applies. A schema-valid
slice can lie about its complete flag/count, so the Search domain must reconstruct
it from the immutable membership before publication/consumption. Tool/Registry binding,
Runtime acceptance and SDK delivery are E2 gates, not supplied by these transport DTOs.
Outputs of selection/successor use existing population retained roots.

Tests in `tests/transport` own strict shape/cardinality; generated publication pins own
schema compatibility. Later worker tests must verify semantic cursor and full-coverage
rules. Rebuilds preserve closed schemas and old SearchStepContext/128-member contracts;
never silently raise legacy limits or copy their inline checkpoint format.
