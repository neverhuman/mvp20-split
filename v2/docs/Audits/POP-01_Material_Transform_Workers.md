# POP-01 synthetic transforms and accepted process derivation

Status: qualified, 2026-10-15 18:52:57 America/Chicago.
Owner: POP-01.01/E2.2. Process-mapping0.3, SDK0.4, Data0.32, Runtime0.70.

## Bounded delivery

Two new independently packaged operations use the existing public SDK. The default
mapping operation and its four qualified schema byte hashes remain unchanged.
transform-materials validates typed input roles, cardinalities, exact candidate/
generation/process-batch context and explicit optional absence. Its declared
copy-first-representation-v1 policy publishes fresh logical intermediate states,
with unknown composition/amount/phase/physical batch and explicit unknown reaction
feasibility/conservation. It makes no chemical or physical-production inference.
Activation-derived state IDs stay stable across retries but differ across graph
occurrences. All source/metadata bytes, ancestry and a conservative8192-byte future
derivation envelope are checked before any child publication. Size placeholders
never become published references or accepted producer pointers.

ProposedProcessTransform retains the actual request and known activation/invocation/
attempt/fence only. It does not invent a future completion ID. derive-process reads
a bounded snapshot header (limit1), the known activation's signed-cut detail, then
the actual canonical successful producer. It does not enumerate the graph or infer
identity from that first node. No lease renewal occurs between snapshot and detail;
later immutable proof/Artifact reads may renew the current assembler normally.

The assembler checks exact source scope/tool/request/output/settled attempt/fence,
Data actor and attempt-derived publication IDs, complete direct parents, and full
deterministic state replay. ProcessDerivation uses the ACTUAL source completion
pointer; its publishing actor remains distinct from its transform producer. It
also emits a MaterialCollection and DerivedMaterialBatch for authored downstream
work. Old accepted source leases need not remain live. Runtime alone accepts work;
Data alone retains it. The assembler uses existing read+inspect_receipts, with no
new route, grant, migration or shared DTO. No worker receives retention authority.

## Verification

- 58 source and58 independently installed checks pass. Source material semantics,
  role/representation/byte preflight, original19-stage pure lineage tests, canonical
  proof/actor/fence/scope/output corruption rejection, exact child replay and live
  lifecycle are covered. A dedicated check prevents our own renewal invalidating
  the signed snapshot/detail pair. Four qualified0.2 mapping schemas stay pinned.
- Final independent installation:
  `.test-results/pop01-process-transform-install-20261015c`; no Search/Data/Runtime/
  Planning implementations, SQLAlchemy or FastAPI. Earlier a/b builds are retained
  diagnostics, not final code acceptance. All three source/installed descriptors
  matched before the observation-client correction; final schema pins remain exact.
- Initial normal actual a completed transform and owner restarts, then tried to
  claim derivation before asynchronous request materialization completed. Fixed
  dev readiness loop. Normal b then exposed a real client omission: Runtime detail
  requires a signed snapshot token. Fixed the client to obtain a bounded header
  and keep the signed pair free of intervening renewal. No owner boundary changed.
  Each failed fixture removed its owned container/child services, retaining volumes.
- Earlier actual missing-required/cross-context cases terminally rejected transforms
  and blocked spent2. Final current-package cases are being verified again with
  safe specific rejection codes (legacy mapping error behavior remains unchanged).
- Final actual probes PASS with independent c:
  `.test-results/pop01-process-transform-restart-http-20261015c` (normal) and
  `.test-results/pop01-process-transform-missing-http-20261015c`.
  The TEST-ONLY admitted source generates three precursors with known synthetic
  physical properties. Normal must transform3 inputs into2 unknown-property states,
  restart BOTH owners after transform acceptance, verify the actual source pointer,
  publish retained derivation/collection/batch and complete spent3. Missing a required
  role must fail before child outputs and block spent2 without derivation work.
  The normal fixture also checks the assembler receives403 for retention reads.
- Normal confirms12 artifacts and completes spent3 after both owner restarts.
  Actual ProcessDerivation points to the transform's accepted completion, not the
  assembler. Required-role absence and final c cross-context cases both terminally
  block spent2 without child results or derivation work. Cross-context evidence:
  `.test-results/pop01-process-transform-cross-http-20261015c`.
- Current0.3 default mapping regression passes:
  `.test-results/pop01-process-mapping-regression-http-20261015c`, keyed1 pair+
  1 explicit exclusion/9 confirmed artifacts/completedspent2. All final drivers exit0;
  owned temporary containers/child services removed, original review/volumes preserved.
- Final production dependency guard,13 boundaries and750 shared schema publication
  pass. Generated package projection reflects0.3 and declared public dependencies.

## Gate and drift boundary

Final positive/negative actual acceptance passes. The complete worker exit is
recorded in [E2.2 worker exit](POP-01_E2_2_Worker_Exit.md). E2.3 owns authored multistage/population composition and
full-wave resource preflight; E2.4 owns batch1/8/32 x active1/4/8 equivalence and
saturation. Single transform/restart acceptance does not establish those gates.
Image/Registry/Linux host attestation and scientific validity remain separate.
No provider calls, original review promotion, v1 mutation or external fleet work.

The design preserves separate source proposal, accepted execution and publishing
identities. No incomplete ProcessDerivation or future acceptance pointer substitutes
for the closed shared record. New source validation factors MaterialDerivation's
existing semantic checks through from_record; original pure API behavior and bytes
remain covered. Tool-owned payloads add capability without widening owner authority.
