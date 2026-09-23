# Evolutionary Code Reuse Baseline

## Status

- Status: initial source review complete; runtime verification and extraction pending
- Last reviewed: `2026-09-16 14:39:23`
- Scope: local MVP20 evolutionary/search code against the five products in `docs/Artifacts/AMPHORA_Top5_Product_Brief_1.docx`
- Baseline: local source at `7d29752`; no external Kiral implementation or remote runtime inspected
- Next gate: demonstrate the numerical search kernel with two distinct, typed product representations and retained evaluation history
- Validation limits: Rust toolchain unavailable locally; Python pytest/NumPy/pandas/CatBoost unavailable. Existing tests were inspected, not executed. No regulatory, clinical, or commercial claims in the brief were independently verified.

## Finding

There is reusable evolutionary computation here, but it is distributed across three different implementations: a numerical optimizer, a feature-selection research system, and a governed candidate-execution shell. These must not be counted as one integrated, scientifically validated genetic-programming engine.

The most reusable code is search mathematics, deterministic execution conventions, provenance, and evidence/authority handling. Existing scientific representations, fixtures, and evaluators are predominantly epoxy/coatings or crystalline-materials specific. Polymer science itself is not a reason to discard a component: numerical mixture constraints and molecular identity operations can transfer, while a coating cure model does not become a drug-release model merely because both involve polymers.

## Implemented Reuse Map

| Component and source | What exists | Reuse disposition |
|---|---|---|
| [NSGA-II](../../../v1/amphora-solver-lab/src/nsga2.rs) | Seeded populations, binary tournament selection, simulated binary crossover, polynomial mutation, constrained dominance, crowding, and deterministic final-front sorting | Reuse numerical kernel for continuous parameter search; supply product-specific decoding, constraints, and fitness |
| [Simplex optimization](../../../v1/amphora-solver-lab/src/simplex.rs) | Projection onto nonnegative fractions summing to one and fixed-step projected-gradient minimization | Reuse for permitted mixture fractions; fixed ingredients, per-component bounds, categorical choices, and process variables need separate handling |
| [Factorial enumeration](../../../v1/amphora-solver-lab/src/doe.rs) | Deterministic enumeration of named discrete axes | Reuse for bounded experimental/design grids; add size/resource guards before broad production use |
| [Solver demos and oracles](../../../v1/amphora-solver-lab/README.md) | Real optimization of solvent VOC/solvency, hardener selection, and coating screening using pinned evidence | Keep as regression fixtures; replace scientific objectives, constants, constraints, and oracle bindings for the drug products. Outputs are explicitly `AUDIT_ONLY` |
| [NOMAD genetic reduction](../../../v1/nomad_feature_hunt/v2/genetic_reduction.py) | Feature-mask genomes, set crossover, add/drop/swap mutation, deterministic IDs, parentage, bounded uniqueness attempts, and discovery/confirmation separation | Extract selected mechanics for model-feature search after parameterizing targets, controls, feature counts, and evaluation protocol; this does not generate formulations |
| [Paired CatBoost feature GA](../../../v1/nomad_feature_hunt/v2/catboost_feature_ga.py) | Paired masks, population evaluation, Pareto selection, caching/checkpoints, and distributed evaluation | Reusable model-development patterns, but tightly coupled to NOMAD targets, file layouts, CatBoost, fixed search settings, and historical hosts |
| [Capability boundary](../../../v1/amphora-core/src/capability.rs) and [artifact contracts](../../../v1/amphora-core/src/artifacts.rs) | Module results, typed execution context, uncertainty/missing inputs, source references, rights, datasets, splits, model artifacts, and authority rules | Reuse infrastructure concepts and suitable implementations; extend schemas and applicability for new representations/endpoints rather than copy entire campaign contracts |
| [Run archive and optimizer authorization](../../../v1/amphora-core/src/lib.rs) | Run/event persistence, verification, constraints, authority checks, score history, and candidate display | Reuse with integration review. `rank_candidates` currently sets `ranked = false` and has no eligible objective vector; its name does not establish production scientific selection |
| [Main engine](../../../v1/amphora-engine/src/lib.rs) and [CLI loop](../../../v1/amphora-cli/src/main.rs) | Native module execution, worker pool, candidate scoring, iteration/display, and lineage mutation | Reuse execution plumbing after extracting fixed lane/module assumptions. `EnginePool::mutate` changes ID/lineage only and emits `QUARANTINED_NO_STRUCTURE_CHANGE` |
| [Authorized molecule generation](../../../v1/amphora-molecule-capabilities/src/lib.rs) | Verified grammar execution through RDKit, canonical molecular facts, scaffold/fingerprint handling, sorted/deduplicated proposals | Genuine chemistry generation exists separately from lineage-only mutation, but its admissible roles are resin/epoxide and hardener/reactive amine. Reuse chemistry primitives, not its role rules as a drug-formulation generator |
| [Compound campaigns v1](../../../v1/amphora-core/src/compound.rs), [v2](../../../v1/amphora-core/src/compound_v2.rs), and [CLI execution](../../../v1/amphora-cli/src/compound.rs) | Locked sources/toolchains, bounded requests, retained campaign evidence, pairing, and review | Extract binding/provenance patterns; current contracts contain epoxy cohorts, resin/hardener pairing, fixed reaction families, and audit restrictions |
| [Formulation capabilities](../../../v1/amphora-formulation-capabilities/src/lib.rs) | Epoxy equivalent arithmetic plus reusable arithmetic/QC pieces, including time-ordered Shewhart/EWMA/CUSUM audit calculations | Separate general arithmetic/QC from chemistry. Model parameters and scientific authority do not transfer automatically |

The module directory named `amphora-optimizer-orchestrator` is not where a complete generic GA is implemented. Its README describes the scoring/authorization boundary; the actual numerical evolutionary kernel is in `amphora-solver-lab`. The engine's orchestrator capability explicitly quarantines objectives that have not passed their evidence gate.

## Domain Coupling That Must Be Removed or Isolated

1. **Candidate representation:** current candidate types are molecule, formulation, and evidence package. Drug-delivery design needs explicit formulation/process/geometry representations and measured response curves; arbitrary JSON additions do not establish a validated domain model.
2. **Operators:** the numerical GA handles continuous vectors, the NOMAD GA handles feature subsets, and the chemistry generator handles locked reaction grammars with epoxy roles. None is already a complete mixed-variable drug-product genome/operator library.
3. **Fitness:** solvent VOC/Hansen-RED, coating cure/pot life, corrosion/barrier, and epoxy equivalent balance are different scientific questions from release, stability, exposure, or product performance. Shared numerical techniques require new data, applicability limits, calibration, and validation.
4. **Training targets:** NOMAD feature search is hard-coded around `formation_energy_ev_natom` and `bandgap_energy_ev`, with crystalline-material feature bundles. Feature-search procedures may transfer; those learned relationships are not drug-delivery predictors.
5. **Workflow:** `active_modules` selects fixed molecule/formulation/evidence lanes. The campaign contracts also pin specific datasets and reaction families. This is not yet the configurable campaign graph interpreter described by the architecture.
6. **Authority:** audit capability is not production ranking authority. Reuse must preserve abstentions, missing evidence, and scientific review; removing quarantine is not an integration shortcut.

## Search-Kernel Integration Gaps

The NSGA-II callback is already a useful separation: `eval(genes) -> (objectives_to_minimize, constraint_violation)`. It can be connected to different evaluators without changing the search algorithm. However:

- `Nsga2Config` supplies one scalar lower/upper bound for all genes. Normalize continuous variables or add explicit per-gene bounds and typed decoding.
- Categorical, integer, conditional, and fixed values need appropriate operators/repair and validation. Do not apply a composition-simplex projection to process or geometry variables.
- `run` returns only the deduplicated feasible final front. It does not expose a durable record of every generation, rejected evaluation, duplicate, or parent/child relationship; campaign instrumentation must capture those before selection discards them.
- Evaluation is a synchronous callback, without a built-in asynchronous laboratory wait, checkpoint/resume contract, cost accounting, or evidence-promotion gate.
- Assertions check some conditions, but production admission should validate complete configuration, finite genes, bounds/probabilities, and consistent objective-vector dimensions. Dominance currently zips objective vectors, so mismatched lengths require explicit rejection at the boundary.
- An empty feasible front needs an explanation based on retained constraint failures, not an unqualified recommendation.

These are bounded hardening/integration tasks around a real numerical kernel. They do not require replacing it with a newly written optimizer.

## Mapping to the Five Products

The following are proposed software representation and evaluation needs derived from the brief, not validated scientific models or regulatory requirements. Product choices and allowable variation must be reviewed before activation.

| Product | Reusable computation | Product-specific work still needed |
|---|---|---|
| Dexamethasone intravitreal implant | Bounded enumeration, continuous multi-objective search, constraints, evidence/versioning | Fixed-composition policy where required by the reviewed product brief; allowed polymer-grade/process/geometry variables; reference release curves and assay conditions; release-match, stability, and manufacturing evaluators |
| Goserelin implant | Same numerical search and potentially shared rod-process representation | Peptide-specific identity/stability and loading rules, product-specific release data, scale-change experiment design, and exposure/PK evidence interfaces; no automatic transfer of dexamethasone calibration |
| Buspirone once-daily formulation | Mixture/search primitives, discrete screening, model-feature selection, experiment lineage | Oral-matrix/excipient/process representation; dissolution and absorption/exposure evaluators; variability and interaction evidence; modulator eligibility as a reviewed constraint |
| Veterinary post-surgical depot | Multi-objective search, release-data schema, bounded experimental loops | Explicit choice among local/systemic delivery, molecule, depot architecture, and route; duration/performance endpoints and species-specific evidence. These are alternative campaign branches, not interchangeable numeric genes |
| Canine OA injectable | Shared depot representation and acquisition/analysis modules where contracts and applicability match | Distinct local steroid versus systemic NSAID branches, route-specific exposure and product-performance models, joint/tissue safety evidence, duration constraints, and a separately reviewed equine extension |

Products 1 and 2 may share rod-manufacturing modules. Products 1, 2, 4, and 5 may share some polymer characterization, release-observation formats, and model families. That is potential implementation reuse, not proof of a common validated release model. API, matrix, geometry, processing, route, assay, species, and endpoint remain applicability dimensions. Safety evidence is not automatically transferable between the veterinary products or species.

Buspirone is a useful second software fixture because it forces the shared engine to work with a different delivery representation instead of concealing depot assumptions in supposedly general code.

## What Was Not Found

Searches of repository Rust/Python source outside evidence/reference/benchmark trees for PLGA, the named active ingredients, drug release, and pharmacokinetics did not locate corresponding product evaluators. This supports treating those capabilities as unverified/new work for this checkout. It does not establish their absence from an external Kiral codebase, omitted models/datasets, remote archives, or other repositories.

No generic campaign-topology mutation/crossover implementation was identified in the inspected search paths. Numerical parameter evolution and feature-mask evolution are implemented; graph/program evolution remains a separate capability to build. The product brief's assumption that an engine can find these formulations is therefore not established by this code review.

## Proposed Reuse Boundary and First Proof

```text
Versioned campaign graph
  -> scoped source acquisition and reviewed evidence
  -> product genome/domain adapter
  -> reusable search kernel
  -> typed scientific evaluators and hard constraints
  -> retained attempts, ancestry, uncertainty, and decisions
  -> experiment/review gate
  -> next campaign iteration
```

1. Preserve the existing coating solver fixtures as numerical regressions. Extract or expose the kernel without making their pinned scientific oracles universal defaults.
2. Define domain objects for variable specifications, candidate decoding, operator applicability, evaluated objectives/constraints, and retained search history. Keep outward DTOs as serialization boundaries.
3. Demonstrate the same kernel on a rod-depot fixture and an oral-matrix fixture using explicitly synthetic/known-answer objectives. Prove generality and provenance first; do not call this drug-performance validation.
4. Preserve every evaluated attempt and selection decision, pin source/model versions and seeds, and validate all objective inputs before numerical selection. Add adapter tests for invalid categorical choices, forbidden composition changes, missing evidence, and incompatible assay inputs.
5. Add an acquired, reviewed release dataset and a narrowly scoped release evaluator with held-out validation. Treat generalization across API, process scale, route, or species as explicit later evidence gates.
6. Integrate that activity as a campaign graph node/subgraph; keep numerical generations separate from campaign topology evolution. Add topology search only after graph contracts and interpreter semantics exist.

No credible reuse percentage follows from counting files or modules. The reusable mathematical core is substantial, but product readiness will depend on domain representation, evaluator/data availability, and validated integration.

## Verification Evidence and Limits

- Inspected [NSGA-II tests](../../../v1/amphora-solver-lab/tests/nsga2_determinism.rs), [simplex tests](../../../v1/amphora-solver-lab/tests/simplex_projection.rs), and [demo replay tests](../../../v1/amphora-solver-lab/tests/demo_replay.rs).
- Inspected [feature-GA tests](../../../v1/tests/crystal360/test_genetic_reduction_v2.py) and [paired-mask tests](../../../v1/tests/crystal360/test_catboost_feature_ga_v2.py) for determinism, bounds, uniqueness, fold completeness, and leakage boundaries.
- The test named `front_is_feasible_and_mutually_nondominated` rejects mutual dominance using an OR condition; that is weaker than asserting neither member dominates the other. Strengthen this before treating it as a complete Pareto-front correctness check.
- [BUILD.md](../../../v1/BUILD.md) records historical workspace checks and omitted-data requirements. Those historical results were not rerun or promoted to current validation here.
- No code, external runtime, model authority, or operational freeze was changed by this review.
