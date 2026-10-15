# Population reference-backed workers

Owner: POP-01.01/E2.2; [Search architecture](../../../../../docs/Architecture/Campaigns/Search.md).
This module is separate from legacy numeric worker operations and the pure
population domain. It owns bounded Artifact I/O and eventual population graph-step
adapters using public contracts and the exported Tool Protocol SDK only. Runtime
alone claims/fences/accepts work; Data alone publishes and protects declared ancestry.

Current implementation: PopulationArtifacts binds reads/publication to one SDK
ToolAttemptContext and original implementation pin. Every child has explicit scoped
deduplicated derivation parents, at most128 direct parents,262144 bytes and4096 local
publications. Deterministic command IDs bind the attempt and stable semantic label;
changed label reuse rejects. Lease renewal/checks surround each owner operation.
An ambiguous stream is not retried or assumed finalized. Finalized metadata is
validated by ArtifactClient; no direct storage/owner-private access exists.

SeedPreparation publishes all proposed/rejected/duplicate births, bounded canonical
birth/cohort/declaration pages and a complete prepared root. Every published child
is reachable through declared ancestry, including original context pins and the
admitted request carrier. SeedSlices reconstructs the full source cohort, exact
numerical birth replay and primary occurrence declarations before emitting one
truthful1..32 candidate-context slice. Dispatch size does not change context bytes.

The first explicit synthetic profile uses CandidateBirth itself as the candidate
representation; other representations reject before publication. It is generation0
and primary-occurrence only. No molecular encoder or arbitrary method topology is
inferred. Scientific representations need their own registered producer.

PopulationCapability and PopulationWorker provide explicit population-describe,
population-schema and population-worker CLI modes for seed/slice/evaluate-squares/evaluate-negative-sum. They compose
public RuntimeClient/ArtifactClient/ToolAttemptContext; the lifecycle is adapted
from the v2 SDK pure worker with tool-owned reference publication. Claims, renewals,
completion ambiguity and final acceptance retain SDK/Runtime authority. A successful
upload is never reported as accepted execution. Descriptors are Linux/x86_64,
CPU-only, synthetic-only, denied egress, no checkpoints and one logical invocation.
Their3600-second ceiling is a bounded engineering fixture limit, not measured
throughput. Lease renewal surrounds each owner operation.

Deployment/composition MUST select Runtime0.69 derived-closure-retention-v1 for
these reference-backed outputs. Workers receive ordinary read/upload/finalize grants,
never retention authority. Runtime also requires scoped claim/renew/complete/read
so the SDK can verify each renewed lease. Enforcing complete configured population composition,
expanded-ancestry feasibility and installed actual-owner worker acceptance remain
E2 gates. The installed seed primitive is qualified for16 members/26 retained
artifacts; its fixture does not execute the declared method graph. Slicing has
source batch1/8/32 checks and an actual installed same-run wire-v4 handoff: eight
contexts, correct cursor, confirmed36-artifact closure and exactly two spent invokes.
Selection/successor and scientific method/fitness execution remain later
owned deliveries. Input references alone do not prove accepted predecessors.

Owned verification lives in evolution_search/tests/population_workers. Test doubles
prove fencing/identity/ancestry behavior; actual Data/Runtime acceptance is separate.

Search0.14 adds PrimaryCohort reconstruction shared by slices and PrimaryMethod.
The two explicit dimensionless numerical primitives consume CandidateContext,
validate complete frozen membership, birth replay and exact method tool/node/schema
pins, then publish the public ObjectiveValue DTO under tool-owned schema
population-method.objective-value/1. Each result has exactly one direct context
parent; invocation input carriers and frozen context remain in the ancestry.
No chemistry evaluator, conditional policy or fitness aggregation is inferred.
Both independently installed methods passed real eight-member scatter, exact values,
Data derivation attribution, confirmed retention and Runtime completion/spent10.
The sixteen-member source cohort was intentionally only half dispatched. Full
collection, selection, successor composition and Registry/image attestation remain
unqualified. See docs/Audits/POP-01_Population_Method_Workers.md.

Search0.15 collection is independently qualified for the bounded primary fixture. collect-primary consumes tool-owned
CollectPrimaryRequest, verifies complete generation0 preparation and supplied public
wire-v4 plan digests against Runtime's observed admitted digest, and requires the
frozen standalone method body to match its authored embedding. Initial primary
methods have one candidate input and no nested scatter/iterate inside that body.
Candidate identity comes from exact retained/prepared context refs, not indices.
Accepted successful execution and exact Data transformation/direct-context lineage
must agree. Failed, skipped and dependency-blocked leaves retain explicit outcomes;
missing coverage rejects. No score is created here.

Cut-bound graph reads finish before Artifact I/O/lease renewals; lease checks fence
every call. Incomplete/mixed pages reject. Collector needs scoped inspect_receipts
in addition to standard worker actions; other numerical workers do not. Serialized
owner evidence retains credential-free public records. Keys, observations and exact
resolution use existing population contracts. Manifest parent grouping preserves
all ancestry under128 direct parents; combined source/key/observation pages retain
512-page/64MiB limits. Approval of4096-artifact retention remains unchanged; largest
composition feasibility is an E2.3 gate, not an established scale claim.

Qualification: Search328 source/326 installed checks; final installed actual-owner
16-candidate success, one required failure, and16 conditional-not-taken outcomes
retain exact coverage and confirmed closure. See POP-01_Population_Collection audit.
Fitness assembly and full authored composition remain separate unfinished gates.

Search0.16 assemble-primary is independently qualified for the initial synthetic pool. A separately pinned
primary-dimensionless-sum-v1 policy and unconstrained-synthetic-v1 declaration permit
only registered numerical fixture values. Authenticate the accepted collected root
through Runtime producer proof and Data origin, verify complete frozen evidence, then
produce explicit available/unavailable fitness and a generation0 selection pool.
Missing required/objective methods never create zero scores. Other constraints,
scientific units, parent/offspring unions and arbitrary scientific quality need their
own registered policy/phase; no universal sum or feasibility assumption is introduced.

PrimaryFitness owns the explicit sum/unavailable policy; PrimaryAssembly verifies
retained evidence and publishes initial-pool fitness; AcceptedCollectionSource
checks Runtime canonical acceptance and Data origin rather than trusting an upload.
Collector/assembly require Runtime0.70+ with graph history and scoped inspect_receipts;
seed/slice only require the previously documented0.69 closure profile. Ten existing
tool schemas retain exact bytes. Source345/installed343 checks plus actual16-success,
one-required-failure and all16-not-taken runs pass; see POP-01_Population_Fitness audit.
The256MiB/3600s descriptor remains a small-fixture engineering bound, not a measured
claim for all independently valid population/method maxima.

Search0.17 initial selection is independently qualified for the bounded fixture. select-primary consumes the existing
public SelectPopulationRequest and verifies accepted whole-pool fitness, exact
initial membership/evaluation/resolution, RNG replay and all ranks/exclusions.
SelectionReadCut counts actual materialized graph nodes and physical attempts
(including the current claim) at one owner cut. It rejects unrelated parallel work,
allows only serial generation-loop ancestors and requires scope finishes/future
work to depend on selection. The cut is correlation, never a budget/execution grant.
prepare-selection is an explicit typed transport adapter for generation0's null
predecessor; graph scalar formats remain unchanged. SelectedPrimaryGeneration keeps
an explicit stopped boolean plus reason, checkpoint and source proof. Later
generation/parent-union selection and successor preparation remain separate work.

Selection qualification: source355/installed353, actual16 success/one required
failure/all16-not-taken runs. Checkpoint attempts match22/22/6 and materialized
nodes43/43/75 exactly. Source loops are checked; actual nested-loop selection remains
a later composition gate. See POP-01_Population_Selection audit.

Search0.18 adds prepare-successor-request and prepare-successor for the accepted
initial checkpoint. SuccessorPreparation verifies canonical Runtime selection and
Data origin, replays the full selection and RNG, and reads a fresh closed work cut.
Observed remaining Runtime and original attempt budgets can only reduce the legacy
allocator's capacity. GenerationPublication publishes every birth disposition,
offspring membership, primary declarations and a pool of retained parents plus new
offspring. Explicit stopped results publish no next generation.

PreparedPrimarySuccessor and PrimarySuccessorDecision are tool-owned preparation
envelopes. Existing public ProposedSuccessor still means finalized evaluation
continuity; no future EvaluationKeys or inputs are invented here. Capacity is a
logical method floor, not a reservation or full-wave dispatch grant. E2.3 must
preflight all orchestration, envelopes, queue and ancestry costs before dispatch.
Preparation is initial checkpoint to generation1 only. Existing slice/method/
collection/fitness/selection consumers still enforce generation0; successor-aware
consumption and parent-union fitness remain required E2.2 work. This release does
not establish an executing multigeneration population loop.

Search0.19 successor consumption is independently qualified. PreparedSuccessorSource
checks the admitted public plan and canonical accepted preparer/selector/assembler
outputs through Runtime, independently checks Data origin and retained carriers,
then replays immutable initial fitness/selection and the bounded birth allocator.
It does not claim a fresh serial selection work cut from inside parallel methods.
SeedSlices and PrimaryMethod can consume generation1 only through that evidence;
the old generation0 path retains its checks and requires no added grants.
Successor slicing/method principals need scoped Runtime read+inspect_receipts in
addition to claim/renew/complete. The prepare-successor-slice typed adapter creates
the initial slice request; it grants no execution/acceptance authority. Complete
birth/cohort/declaration pages, parent-union membership and page closure must agree.
Generation1 collection/fitness/selection and subsequent generation preparation
remain unfinished; no generic multigeneration execution claim is made.

Qualification:367 source/365 independently installed checks,13 boundaries,750 shared
schemas and twenty predecessor endpoint schema pins preserved. Final installed run
executes all16 initial and16 generation1 numerical methods, exact values, confirmed
146-artifact successor slice closure and completed spent42. No paid calls. Both
owned test containers removed. See POP-01_Population_Successor_Consumption audit.

Search0.20 is independently qualified: collection reconstructs accepted generation1
preparation, and assembly retains original selected-parent fitness/evidence beside
offspring results. The complete union uses PopulationSelection coverage checks and
names historical/current observation manifests explicitly. The new tool-owned
prepare-successor-collection typed adapter consumes CollectSuccessorSliceRequest
and produces existing CollectPrimaryRequest; Runtime projection semantics remain
unchanged. Generation1 global selection and later-generation preparation remain
unfinished. No whole-worker or generic loop qualification is claimed.

Qualification:371 source/369 installed checks,13 boundaries,750 shared schemas and
22 predecessor endpoint schema pins preserved. Actual normal and required-offspring
failure runs publish32-record pools with16 unchanged parent records and two explicit
observation sources;32 available versus31 available/one unavailable. Confirmed roots
retain192/191 artifacts, completedspent45. Temporary containers/processes removed,
no provider calls. See POP-01_Population_Successor_Fitness audit.
