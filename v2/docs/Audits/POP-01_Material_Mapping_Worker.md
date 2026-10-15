# POP-01 synthetic material mapping worker

Status: qualified, 2026-10-15 18:06:18 America/Chicago.
Owner: POP-01.01/E2.2. Process-mapping0.2.0, SDK0.4, Data0.32, Runtime0.70.

## Bounded delivery and ownership

The existing process-mapping domain now has a tool-owned public-SDK adapter for
process.synthetic-map-materials. MapMaterialsRequest references two canonical
MaterialCollection carriers (at most32 items each) with exact ProcessContext.
Existing pairwise, keyed/unmatched and explicit Cartesian semantics remain in
MaterialMapping. Maximum Cartesian cardinality is1024 within this input profile,
subject to the lower caller policy cap and complete ancestry/byte preflight.

MappingPublication verifies all source bytes, context, source-reference consistency,
material states and referenced representation/composition/conditions/checkpoint
metadata before the first upload. Every page declares its admitted input carrier,
both source collections and complete source/metadata ancestry. Incompatible direct
parent maxima reject before publication; pages and rows are never truncated. The
manifest retains both source collections and every page. Source schemas, canonical
bytes, unknown amounts/phases/compositions and physical batch IDs remain unchanged.

ProcessArtifacts adapts the reviewed Search publication pattern locally; the package
has no Search or service-implementation dependency. Reads cap262144bytes per Artifact
and64MiB total. Direct parents and publications each cap128. Leases are refreshed
around I/O, publication labels are attempt-derived, changed-label replay rejects,
ambiguous streams are not blindly retried and completion ambiguity stays outside
failure reporting. Runtime alone claims/accepts work; Data alone finalizes/retains.
Workers receive no retention grant or admission/execution authority.

## Verification

- 32 source checks pass: original pure domain, all mapping modes, exact manifest
  replay/ancestry, preserved unmatched source, pre-upload context/digest/parent/lease
  rejection, wrong input metadata before reads, label conflicts, live transport
  failure classification and no contradictory completion after ambiguity.
- Production guard,13 boundary checks and750 shared schema publication pass.
  The package projection reflects0.2 and declared public dependencies; this is
  scoped inventory refresh, not a new full-foundation acceptance claim.
- Independent a install excludes Search/Data/Runtime/Planning implementations,
  SQLAlchemy and FastAPI;29 tests passed before the final three metadata checks.
  Final b install is complete; all32 independently installed tests pass.
  Tool lock Pydantic2.14.1/dev2.13.5 produce identical input/output schema hashes.
- Initial actual a cases failed host startup because the dev fixture omitted the
  existing Artifact bindings peer. Fixed configuration. b passed the admitted
  source worker, then its proof read hit404 because inspection was not configured.
  Fixed existing inspection configuration for the test controller only. Both a/b
  sets removed owned containers/child services and preserved volumes/demo.
- Final actual c cases PASS with final independent b package:
  `.test-results/pop01-process-cartesian-http-20261015c` and
  `.test-results/pop01-process-cross-context-http-20261015c`.
  The admitted TEST-ONLY source worker obtains the actual Runtime run ID before
  publishing typed materials/collections, through public SDK calls only. The mapper
  must accept4 Cartesian pairs or reject a cross-candidate material terminally.
  No prediction of Runtime IDs or direct access to owner state is used.
- Pairwise and keyed actual cases also PASS using final installed b:
  `.test-results/pop01-process-pairwise-http-20261015a` and
  `.test-results/pop01-process-keyed-http-20261015a`. Pairwise preserves2 pairs,
  Cartesian produces4, each confirms10 artifacts; keyed retains1 matched pair and
  1 explicit unmatched exclusion, confirms9 artifacts. All complete spent2.
  Cross-context rejects terminally with invalid_process_mapping, no result root,
  and blocks the graph after spent2. Every driver exits0 and removes its owned
  temporary container and child services. Original review demo/volumes preserved.

## Remaining gate

Scoped drift assessment: mapping semantics stay in Process Mapping, acceptance in
Runtime and retention in Data. No control join became a chemical transform and no
new shared schema/owner API was introduced. The32-item collection/128-parent
profile is explicit; it does not promise every independently valid domain maximum
can execute. E2.3 must reject unsupported compositions before dispatch. No blocking
drift is identified in this bounded mapping worker; synthetic transforms remain
an explicit prerequisite, with no whole-unit completion credit.

Actual mapping acceptance passes. This does not implement a synthetic material
transform, qualify the full E2.2 unit, prove multistage restart/local readiness,
preflight full authored campaign resources or qualify the batch/cap matrix. Those
remain ordered worker/composition/matrix gates. Descriptor Linux resources are
fixture bounds, not OCI/host attestation. No chemistry/conservation/feasibility or
lab-control authority is inferred. No provider calls.

E2=25%, Execution31.25%, parent10.42%, Build15.63%, Verification0; whole E2.2 stays0.
