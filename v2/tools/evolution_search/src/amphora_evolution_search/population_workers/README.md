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
population-schema and population-worker CLI modes for seed/slice. They compose
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
source batch1/8/32 checks; its actual same-run graph binding remains pending.
Selection/successor and scientific method/fitness execution remain later
owned deliveries. Input references alone do not prove accepted predecessors.

Owned verification lives in evolution_search/tests/population_workers. Test doubles
prove fencing/identity/ancestry behavior; actual Data/Runtime acceptance is separate.
