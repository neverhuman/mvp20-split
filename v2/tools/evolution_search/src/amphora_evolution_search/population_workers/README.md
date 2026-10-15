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
