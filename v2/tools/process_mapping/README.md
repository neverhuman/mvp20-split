# Process mapping boundary

Owner: POP-01.01/E2.2 delivery, E2.3 integration. Version0.3.0 mapping, synthetic
transforms and accepted derivation assembly have independent actual public-owner
acceptance. No deployed service or chemistry model is claimed.
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
Synthetic material-transform workers are qualified below; complete authored
multistage composition remains unfinished.

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

## Synthetic transforms and accepted derivation

Version0.3 adds --operation transform-materials or derive-process to describe/worker;
the default remains map-materials. Four qualified mapping schema bytes stay exact.
TransformMaterialsRequest pins ProcessBinding roles/cardinalities, exact input states,
explicit optional absence, conditions and copy-first-representation-v1. The synthetic
tool publishes new logical intermediate states with the first input representation,
unknown composition/amount/phase/physical batch, and explicit unknown conservation/
reaction feasibility. State identity includes the graph activation, remaining stable
across retries but distinct across occurrences. The existing8192-byte derivation row
has a conservative size check before any child publication; field maxima do not
guarantee every combination fits.

ProposedProcessTransform contains only known activation/invocation/attempt/fence
locators, not an invented completion ID or acceptance claim. The separate assembler
reads a bounded snapshot header, its known node detail and successful producer,
verifies the
actual canonical settled attempt/output/request, and checks Data origin/actor,
attempt-derived publication IDs, exact ancestry and deterministic output replay.
It then publishes ProcessDerivation with the ACTUAL transform completion pointer,
a MaterialCollection for later mapping/scatter, and a DerivedMaterialBatch root.
The derivation publisher's Data identity stays distinct from its source transform
producer. Historical source acceptance does not require the old worker lease.
The snapshot/detail pair uses one signed cut without an intervening lease renewal;
the next immutable producer read may refresh the current attempt normally.

The assembler needs Runtime read+inspect_receipts in addition to ordinary worker
actions; no new route or retention grant is introduced. Only the current assembler
attempt is renewed. Data publications retain admitted carriers and complete source
ancestry through explicit parent trees. Same-release/image transforms are the initial
accepted-source profile; exact older releases keep their retained workers/history.
Shared population DTOs and existing mapping payload hashes remain unchanged.

58 source/58 independently installed checks pass. Actual3-input/2-output transform
and derivation survive BOTH owner restarts, use the actual accepted producer pointer,
confirm12 artifacts and complete spent3. Missing required role/cross-context input
terminally block spent2. Current-package keyed mapping regression confirms9 artifacts
and completes spent2. The assembler's retention GET returns403; no retention grant.
All owned temporary containers/child services removed. [Transform evidence](../../docs/Audits/POP-01_Material_Transform_Workers.md)
and [complete worker exit](../../docs/Audits/POP-01_E2_2_Worker_Exit.md) own the scoped
qualification. Authored composition/resource preflight and batch/cap matrix remain.

Tests: `tests/lineage` and `tests/mapping`, registered as `process-mapping` scope.
Replacement must preserve exact public schemas, canonical bytes, rejection reasons,
mapping order/cardinality and context isolation. The19-stage test verifies lineage
contracts only; local readiness, durability/restart and UI traversal are later POP
execution/experience/qualification gates. No shared mutable state or private imports.
