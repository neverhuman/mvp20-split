# Evolutionary Search and Experience

- Design status: bounded numeric graph steps, accepted generations and worker/Runtime recovery implemented; independent replacement accepted; synthetic representation/fitness and authenticated reuse accepted; topology and scientific acceptance remain successors
- Naming note: component/record/operation names below are proposed logical design, not implemented APIs or selected deployment technology
- Last reviewed: `2026-10-06 15:45:26` (America/Chicago)
- Parent: [Domain overview](Campaign_Architecture.md)
- Requirement source: [Product Requirements](../Requirements/Product_Requirements.md#campaign-evolution-and-cross-project-discovery)

## Owned Contract

Search binds an authorized design space, genome, permitted operators, evaluators, hard constraints and termination budget. Parameter search, molecular/sequence variation and graph-topology evolution are different spaces. Numerical kernels need appropriate adapters and scientific validation.

Retain all attempts, parentage, seeds, operators, changed fields, duplicates, rejects, objective inputs and selection decisions. Fitness has units, direction, uncertainty and eligibility. Unknown evaluations cannot become attractive defaults. Diversity and novelty cannot override authority.

## Boundary and Flow

Research owns candidate meaning; Capabilities supplies operators/evaluators; Knowledge supplies reviewed constraints. Topology mutation creates graph descendants that pass activation checks. Rights-eligible motifs/seeds/operator statistics are experience artifacts governed with Data; prior success is not evidence for a new candidate.

## Invariants and Verification

Operators cannot mutate signed objectives, hard constraints, authority or lineage. Verify permitted-domain preservation, failed-attempt retention, replay and explained empty-feasible-set outcomes. Compare evolution, enumeration, active-learning and expert strategies using equivalent evidence. Existing numeric/feature search does not prove graph evolution.

## Component and Object Design

| Proposed component | Owned behavior |
|---|---|
| Design-space adapter | Decode genomes, validate/repair permitted values and expose operator applicability |
| Population controller | Generation checkpoints, seeds, parentage, attempt scheduling and stop decisions |
| Fitness assembler | Eligible objective/constraint vectors with units, direction and missing-evidence dispositions |
| Selection policy | Feasibility, ranking/diversity and reproducible selection receipts |
| Topology proposer | Bounded graph mutations/crossover as proposals, not activated graph edits |

A search checkpoint binds objective policy, operator/model/data versions, seed/RNG state, population members and outstanding evaluations. `CandidateAttempt` retains every proposed individual; deduplication does not erase it. `SelectionDecision` owns the exact counted/excluded evaluations and policy rationale.

## Iteration Contract

Generate within the authorized design space, validate offspring, schedule typed evaluations, assemble eligible fitness and select only under a declared completion policy. Asynchronous experiments may leave evaluations pending; selecting from partial returns requires an explicit rule rather than whichever results arrive first. Pin evaluator snapshots for comparable fitness; adopting a new model may require reevaluating retained candidates.

Feedback can change permitted parameters or propose a new graph revision at an iteration boundary. Candidate-generation loops and topology-search loops use distinct state and ancestry. A topology proposal is evaluated against graph validity, resource constraints and declared research objectives before activation.

## Failure and Boundary Example

If all candidates violate hard constraints, retain the failure distribution and stop or propose an authorized design-space review. Do not normalize infeasibility into success. Mismatched objective-vector dimensions, non-finite values and uncertain eligibility block selection. A historical seed can initialize search but its old score cannot substitute for current-project evaluation.

## Design Basis and Open Decisions

[Reuse Baseline](../Evolutionary_Code_Reuse_Baseline.md) identifies actual NSGA-II/simplex/feature-GA mechanics and missing step/checkpoint integration. Remaining choices: mixed-variable operators, batch-completion policy, fairness across expensive evaluations and topology fitness benchmarks. Search strategy is pluggable; no scientific winner is assumed.

## Implemented Boundary and Successor

BP-08.01 implements public search/checkpoint DTOs and the isolated numeric module: finite continuous boxes, constrained Pareto/crowding selection, original-spec pin binding, portable counter RNG, retained initial attempts and intrinsic checkpoint consistency. Two clean wheel installations preserve checkpoint bytes, pending identities and the next draw. This independent implementation does not claim v1 Rust bit parity or scientific validity.

BP-08.02 implements explicit seed, request expansion, evaluation, collection and variation steps. Runtime owns graph iteration, scatter membership, accepted transitions and attempts; Data owns immutable bytes and retention. Original specification and the actual evaluator policy Artifact are explicit graph inputs and loop captures. Checkpoints bind canonical bytes and predecessor Artifact identity; a valid snapshot alone neither authorizes execution nor proves evidence exists.

Actual independently installed workers and owner APIs demonstrate generations 0/1/2, retained evaluation provenance, interruption after Artifact finalization, Runtime restart, byte-identical retry under a new fence and rejection of a stale completion. Pure compiler tests, scripted Artifact transaction tests, actual HTTP, Linux image arithmetic and independent installation proofs retain separate scopes. Current-release Registry/replacement acceptance passed in BP-08.02; target-host/container orchestration is not established by image builds.

Numerical search freezes pending membership before collection. Failed or unavailable required numeric fitness stops diagnostically without fabricated zero; weak but present evidence does not veto exploration solely for its quality label. Stopped transitions are bounded no-ops. Collection and byte budgets remain explicit, and an exhausted graph limit without a search stop blocks instead of reporting success.

BP-08.03 owns distinct representation operators and evidence/fitness applicability; BP-08.04 owns successor topology proposals. Neither follows automatically from numeric generation execution. Scientific validation and target-host deployment require their own evidence.

[Representation and fitness boundary](Representation_Fitness.md) decomposes the activated BP-08.03 design into distinct synthetic operator profiles and Research-owned comparison policy.

[Bounded topology successors](Topology_Search.md) owns permitted edits, original-plan/release binding and fair-comparison boundaries. Pure Planning proposal policy is implemented; authenticated persistence and actual compiler/adoption remain BP-08.04.
