# Process mapping boundary

Owner: POP-01.01/E2.2. Version0.2.0 mapping worker is independently qualified with
actual public-owner acceptance. No deployed service or chemistry model is claimed.
Design: [Multistage process graphs](../../docs/Architecture/Campaigns/Multistage_Process_Graphs.md).

This independently built package owns MaterialState/ProcessDerivation validation
and pairwise, keyed or explicitly opted-in Cartesian material mapping. It imports
public contracts and the public Tool Protocol SDK; Search, Runtime, Data and Research
implementations are absent.
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

The original process.py domain has no filesystem/network/state or execution side
effects. Failures raise ValueError with
stable reason codes. Producer pointers are unverified locators. No reaction feasibility,
stoichiometry, safety, mass conservation, real material availability or lab-control
authority is inferred. Existing graph joins remain synchronization, not transforms.

## Mapping worker

CLI describe/schema/worker exposes one opt-in process.synthetic-map-materials release
through public Tool Protocol SDK0.4 only. Tool-owned MapMaterialsRequest references
two canonical MaterialCollection carriers, each at most32 items with exact context.
Existing shared population schemas remain unchanged. MappingPublication verifies
scope/run/candidate/generation/process-batch, all states and referenced representation,
composition/conditions/checkpoint bytes before any upload. Pairwise/keyed/Cartesian
behavior still comes from the original domain; opted-in Cartesian may produce at
most1024 pairs in this profile, subject to the lower caller policy limit.

Every page retains its admitted input carrier, both source collections, all material
states and their metadata. The128-direct-parent bound is checked before publication;
independently valid collection maxima need not fit every metadata combination. Root
retains both source collections and complete pages. Reads cap64MiB per attempt and
262144bytes per Artifact; existing page/row/manifest bounds remain. No truncation.
Tool-owned ProcessArtifacts adapts the reviewed Search publication pattern locally;
it does not import Search or service implementations. It renews/checks leases around
I/O, rejects conflicting label replay and does not blindly retry an ambiguous stream.
Runtime alone claims/accepts work and protects derived closures. Worker credentials
need read/upload/finalize and claim/renew/complete/read, with no retention grants.

The worker is stateless between invocations. New attempts have new publication IDs;
accepted history remains with Runtime/Data. Completion ambiguity is propagated without
contradictory failure reporting; only a reconfirmed live attempt may report retryable
transport failure. Structural execution profiles and attempt checkpoints are rejected.
CPU/Linux/x86_64 descriptor resources are fixture bounds, not image/host attestation.
Synthetic material-transform workers and multistage composition remain unfinished.

Verification:32 source and32 independently installed domain/publication/lifecycle
checks pass, including complete
ancestry, pre-upload context/digest/parent rejection, lease loss and ambiguous completion.
Production dependency guard/13 boundaries and750 shared schemas pass. Actual owner
HTTP acceptance passes: pairwise2 pairs/Cartesian4 pairs confirm10 artifacts;
keyed1 match+1 exclusion confirms9 artifacts. Runs complete spent2. A cross-candidate
material rejects terminally and blocks its graph without a result root. All owned
test containers and child services removed; no provider calls. Existing pure19-stage
lineage coverage remains distinct from those actual worker proofs.
[Worker audit](../../docs/Audits/POP-01_Material_Mapping_Worker.md) owns exact evidence.

Tests: `tests/lineage` and `tests/mapping`, registered as `process-mapping` scope.
Replacement must preserve exact public schemas, canonical bytes, rejection reasons,
mapping order/cardinality and context isolation. The19-stage test verifies lineage
contracts only; local readiness, durability/restart and UI traversal are later POP
execution/experience/qualification gates. No shared mutable state or private imports.
