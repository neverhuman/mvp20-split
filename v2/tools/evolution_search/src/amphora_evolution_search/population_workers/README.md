# Population reference-backed workers

Owner: POP-01.01/E2.2; [Search architecture](../../../../../docs/Architecture/Campaigns/Search.md).
This independently packaged Search module owns bounded proposal/evidence adapters
through public contracts and the exported Tool Protocol SDK. Runtime alone accepts
execution, owns leases/fences/counters and schedules work. Data alone publishes
artifacts and protects declared ancestry. No peer-private imports, SQL, hidden
scheduler, execution ledger or retention authority belongs here.

## Current scope

Qualified through Search0.23: generation0 seed/slice, squares/negative-sum methods,
complete primary collection, explicit synthetic fitness, initial whole-pool selection,
initial successor preparation, generation1 slicing/methods/collection and complete
retained-parent/offspring fitness and global generation1 selection.
Source386/installed384 checks pass. E2.2 worker unit is complete; see the
cross-component POP-01_E2_2_Worker_Exit audit. Authored resource preflight and the
batch1/8/32 x cap1/4/8 matrix remain required gates. This is not a scientific or
production-scale qualification.

Search0.22 later-generation continuity is independently qualified. History
must match original/run/scope/spec, move exactly one generation backward per link
and remain within the existing100-generation bound. Request adapters and slices
accept later generations only through the same accepted preparation/evidence checks.
The probes cover full generation2 and a stopped generation1 checkpoint;
complete composition remains unfinished.

Search0.23 occurrence affinity is qualified. CollectionScope verifies
the caller's exact captured activation and admitted binding/address, then restricts
method nodes to its complete ancestor occurrence prefix before ordinary attribution.
Repeated loop node names therefore cannot mix iterations; candidate identity still
comes from retained input refs. Current probes use a real two-iteration Runtime
loop with identical body names, selected-state feedback and an explicit stopped
predicate.386 source/384 installed checks pass. Actual normal/failure loops end
with pools27/28, selected16/exclusions0/1, logical43/44/physical67/68, nodes124/126,
RNG208/front2 and generation_budget stop; confirmed282/283 artifacts. Both owned
temporary containers and services removed. No application-provider calls.

The explicit synthetic representation is CandidateBirth itself; no molecular
encoder is inferred. Primary methods have one candidate input, no internal scatter/
iterate and exact one-to-one frozen invoke bindings. The supplied public wire-v4
standalone method body must equal its admitted embedding. Outer method scope paths
are explicit; repeated loop occurrences bind through the collector's full ancestry.

## Interfaces and behavior

PopulationCapability/PopulationWorker expose population-describe, population-schema
and population-worker CLI modes, separately from the legacy numeric CLI. Configured
RuntimeClient/ArtifactClient/ToolAttemptContext own protocol transport/lifecycle.
Descriptors advertise synthetic CPU/Linux/x86_64, denied egress, no attempt checkpoint,
256MiB and3600s; these are fixture bounds, not maximum-profile throughput or OCI/
Registry/host attestation. The structural execution_profile is not accepted here.

- SeedPreparation/GenerationPublication publish every proposed, duplicate and rejected
  birth, canonical cohort/declaration pages and a prepared root. No future final
  EvaluationKeys are fabricated. SeedSlices/PrimaryCohort reconstruct complete
  membership and exact numeric replay before producing truthful1..32 context slices.
- PrimaryMethod verifies exact context/member/birth, full method release/node/schema
  pins and one dimensionless objective. Squares and negative sum use math.fsum.
  ObjectiveValue uses tool-owned population-method.objective-value; exactly one
  direct candidate-context parent identifies each result.
- PrimaryCollection freezes complete declared primary coverage. Runtime retained
  inputs and canonical completion must agree with Data transformation/origin and
  exact direct context lineage. Failed/expired/skipped/blocked work remains explicit;
  only successful methods use the existing successful-only producer endpoint.
  There is no arrival-order, page-index or missing-zero association.
- PrimaryFitness requires separately pinned primary-dimensionless-sum-v1 and
  unconstrained-synthetic-v1 artifacts. Only frozen numerical values may be summed.
  Required/objective unavailability never produces a numeric score. PrimaryAssembly
  authenticates the accepted collector and builds the complete union. Parents keep
  ORIGINAL fitness generation, values, quality, evaluation-set digest and evidence;
  manifests name historical/current observation roots explicitly.
- InitialSelection authenticates accepted whole-pool assembly. SelectionEvidence
  groups reconstruction, explicit evidence union, RNG and cumulative progress.
  SelectionReadCut counts actual attempts (including its own claim) and materialized
  nodes at one closed owner cut, permits only serial loop ancestors and rejects
  unrelated parallel work. Every finish/future operation must depend on selection.
  The proposed cut is correlation, never an execution/budget grant.
- SuccessorPreparation/PreparedSuccessorSource authenticate canonical preparer,
  selector and assembler outputs against the admitted plan and Data origin/carriers.
  Immutable evidence replay inside a method does not assert a fresh serial counter
  cut. Work cuts predate accepted completions. Observed original/Runtime remaining
  attempt capacity can only REDUCE the default allocator; exact parents/RNG/births/
  declarations/pool must replay. Explicit stopped outcomes create no offspring.

Typed prepare-selection, prepare-successor-request, prepare-successor-slice and
prepare-successor-collection adapters move existing references between graph steps;
they confer no authority. CollectSuccessorSliceRequest carries slice plus plan/scope
refs into existing CollectPrimaryRequest. PreparedPrimarySuccessor and
PrimarySuccessorDecision are tool-owned preparation envelopes. The public legacy
ProposedSuccessor retains finalized evaluation-continuity semantics. Population
checkpoints are durable domain Artifacts, distinct from attempt checkpoints.

## I/O, bounds and failure semantics

PopulationArtifacts checks the live attempt around owner I/O and binds every
publication to the admitted input carrier plus scoped deduplicated parents.
UUID5 command IDs bind an attempt and semantic label; changed label reuse rejects.
An ambiguous stream is not retried or assumed finalized. Completion ambiguity stays
under SDK/Runtime recovery; upload success is not accepted execution.

Each publication is at most262144 UTF8 bytes/128 direct parents; local publication
count4096. publish_root groups larger parent sets through explicit120-parent reference
artifacts, retaining every ancestor. Combined generation pages are bounded512/64MiB.
Runtime0.69+ derived-closure-retention-v1 must be selected for these runs; its4096
ancestor limit is separate from local publication count. Legacy runs stay direct-root.

Workers receive Data read/upload/finalize, never reserve/confirm. Runtime claim/
renew/complete/read is required. Collection, assembly, selection, preparation and
successor slices/methods additionally require read+inspect_receipts on Runtime0.70+
graph history/retained-input inspection. Generation0 seed/slice/methods need no new
inspection grant. All public reads are scoped and bounded; snapshot pages cannot be
spliced across cuts. Changed/expired observation cuts and owner unavailability are
retryable; denied/malformed/mismatched immutable evidence rejects. Lost attempt
fences propagate rather than becoming ordinary invalid-input failures.

Observed successor capacity is a logical method floor, NOT a full-wave reservation.
E2.3 must preflight all orchestration, queue, envelope and ancestry costs before
scientific dispatch. Independently valid field maxima need not fit every combination;
never silently raise caps or truncate evidence. RunSnapshot exposes at most256 queued/
leased activations. The legacy no_feasible_survivors stop can mean no eligible scored
parents, and is not a scientific infeasibility conclusion.

## Replacement evidence

Owned tests: evolution_search/tests/population_workers; source doubles prove
identity/fencing/policy, while independently installed public-owner probes establish
acceptance separately. dev/verify_retention_closure_installation.py composes bounded
fixtures and removes every owned temporary container in finally, preserving labeled
volumes and the active demo. No application-provider calls are used.

Qualified0.21:374 source/372 installed,13 boundaries,750 shared schemas/24 predecessor
tool pins. Actual success/required-offspring failure select16 globally from32 with
exclusions0/1,32 logical evaluations,47 physical attempts,87 nodes, RNG112, unchanged
front1 and generation_budget stop. Confirmed198/197 artifacts, completedspent47.
Both owned containers/processes removed, no provider calls.
Qualified0.22:375 source/373 installed, same service/schema/pin guards. Actual gen2
has11 new members/27 pool/16 selected, logical43/physical67/nodes121/RNG208/front2,
confirmed282 artifacts and completed generation_budget stop. A stopped gen1 checkpoint
creates no births, confirmed201 artifacts/finalspent49. Both owned containers removed.
Independent packages exclude Data/Runtime/Planning implementations,
SQLAlchemy and FastAPI. Original v1 is read-only; seven reuse hashes were separately
checked against it. Replacement must preserve old wire bytes, exact pins, numerical
replay, truthful coverage, owner acceptance/origin, ancestry and no-retention grants.

Detailed component evidence lives in docs/Audits: POP-01_Population_Seed_Worker,
POP-01_Population_Method_Workers, POP-01_Population_Collection,
POP-01_Population_Fitness, POP-01_Population_Selection,
POP-01_Population_Successor_Preparation, POP-01_Population_Successor_Consumption and
POP-01_Population_Successor_Fitness and POP-01_Population_Successor_Selection.
POP-01_Population_Later_Continuity owns the generation2/stop proof.
POP-01_Population_Loop_Affinity owns actual repeated-loop normal/failure proof.
POP-01_Population_Paired_Methods qualifies two named methods on unequal paths:
32 declared outcomes,16 exact summed fitness records (normal), or16 evaluated plus
16 inapplicable outcomes/all16 unavailable fitness without scores (required skip).
Confirmed final125/109 artifacts; completedspent36/20; both owned fixtures removed.
Process0.3 separately qualifies typed mapping/transform/accepted derivation workers
with owner restart and actual source pointers. Authored multistage composition
remains the E2.3 gate; numerical joins do not substitute for those typed transforms.
POP-01_Node_Input_Inspection and
POP-01_Closure_Retention own the qualified service prerequisites. A full plan
closeout, generic loop/recovery proof and production Linux image attestation remain
separate gates; these component probes do not imply them.
