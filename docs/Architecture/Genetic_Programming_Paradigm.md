# Genetic Programming Paradigm

## Why This Is The Preferred Implementation Style

The artifacts describe two different technical styles:

- a neuro-symbolic interface/core: knowledge graph, neural property models, symbolic physics judges, and policy gates
- an evolutionary/generative optimizer: deterministic candidate generation, retained rejects/duplicates, mutation operators, typed module outcomes, policy-controlled selection, and lab-feedback-driven improvement

For this project, the genetic programming paradigm should be treated as the primary implementation direction. The neuro-symbolic layer is useful as an interface and evaluator stack, but the product workflow should center on evolving candidate populations inside signed manufacturing envelopes.

## Source Reading

The strongest genetic-programming signal appears in:

- `amphora-founder-readiness-brief-2026-07-19.pdf`
- `epoxy-amine-phase0-implementation-review.pdf`
- `TECHNICAL_APPENDIX 3.pdf`
- `Amphora_Engine_Strategy_Memo 8July2026.docx`
- `Amphora_Engine_Upgrade_Tech_Memo 8July 2026.docx`
- `Amphora Platform Architecture.pdf`

The documents use several names for the same family of behavior: evolutionary engine, molecule generator, compound funnel, manufacturing compiler, deterministic enumeration, Bayesian CRO optimizer, candidate generation, and selection.

## Current Evidence Posture

The existing artifacts are explicit that the evolutionary shell exists, but scientific selection is not fully authorized.

Current posture extracted from the artifacts:

- deterministic generation can be governed
- ordered requests, retained rejects, retained duplicates, typed outcomes, signed lineage, replay, and export are required
- chemistry-changing mutation is disabled or quarantined until a separate generator campaign validates it
- optimizer-usable scores and final aggregate ranks are unauthorized until modules earn authority
- feasibility bands are not performance ranks
- lab data is required before active-learning optimization should drive the next batch

This is not a reason to avoid the genetic-programming paradigm. It is the implementation contract for doing it safely.

## Target Loop

The target loop is:

```text
signed envelope
  -> seed population
  -> generate variants
  -> compute deterministic properties
  -> run specialist gates
  -> preserve rejects and duplicates
  -> assign evidence-bound fitness components
  -> policy-authorized selection
  -> lab/CRO batch
  -> candidate-bound measurement intake
  -> model and fitness promotion
  -> next generation
```

The system should initially run with deterministic enumeration and disabled scientific ranking. As evidence arrives, modules become eligible to contribute fitness components.

## Core Objects

### EvolutionCampaign

Owns a bounded optimization effort under a specific product envelope.

Required fields:

- campaign id
- product envelope version
- domain pack id
- objective policy version
- seed policy
- population size
- generation limit
- mutation/crossover operator allowlist
- hard constraints
- soft objectives
- evidence authority snapshot
- status

### Genome

Represents a candidate in a form the engine can mutate or recombine.

For coatings, a genome may include:

- ingredient identities
- role assignments
- mass fractions
- part A / part B assignments
- resin/hardener ratio
- solvent package
- pigment/filler package
- additive package
- process parameters

For molecule or polymer design, a genome may include:

- parent structure ids
- reaction template id
- grammar id
- role
- seed
- structural representation
- lineage and scaffold facts

### GenerationRequest

A locked request that creates candidate attempts.

Required fields:

- family
- parents
- role
- seed
- request id
- operator id
- grammar/template version
- envelope id

### CandidateAttempt

Every attempt must be retained, including rejects and duplicates.

Required statuses:

- accepted
- rejected
- duplicate
- invalid
- quarantined

### FitnessComponent

A bounded score or gate emitted by a module.

Fitness components must carry:

- module id
- authority tier
- applicability
- result status
- scalar value only where authorized
- uncertainty where available
- limitation text

### SelectionDecision

Selection is a policy decision, not a raw average.

Required fields:

- selected candidate ids
- rejected candidate ids
- abstention summary
- authority snapshot
- fitness component set
- policy solver version
- reason
- whether ranking was authorized

## Operators

The architecture should support operators as versioned, authority-controlled plugins.

Initial formulation operators:

- mass-fraction perturbation
- ingredient substitution within role
- solvent package swap
- pigment/filler package swap
- part A / part B rebalance
- stoichiometric repair
- cost-constrained substitution
- supplier-loss recompilation

Future chemistry operators:

- reaction-template expansion
- scaffold-preserving substitution
- functional-group substitution
- polymer repeat-unit mutation
- role-constrained molecule generation
- crossover between compatible parent formulations or structures

Chemistry-changing operators require their own validation campaign before activation.

## Fitness Policy

Fitness must be multi-component and authority-aware.

Candidate fitness may include:

- hard-gate feasibility
- envelope arithmetic
- VOC compliance
- stoichiometric fit
- solids and density targets
- PVC/CPVC posture
- cost
- sourcing robustness
- solvency compatibility
- viscosity/process fit
- cure/pot-life evidence
- corrosion/barrier evidence
- novelty and rights posture
- lab-measured outcomes

No component may influence selection unless its module authority permits that use. Missing evidence remains missing evidence. Abstention is not zero.

## Bootstrap Strategy

The safe bootstrap path is:

1. Start with deterministic enumeration inside the signed envelope.
2. Preserve all candidate attempts, rejects, and duplicates.
3. Use deterministic formulation arithmetic and hard gates first.
4. Emit feasibility bands, not performance ranks.
5. Send selected bands to lab/CRO for falsification.
6. Ingest candidate-bound measurements.
7. Activate Bayesian/active-learning batch selection only after enough measured points exist.
8. Promote mutation and selection operators only after external evidence and review.

This aligns with the artifacts' warning that optimizing before wet-lab returns would optimize surrogate assumptions.

## Relationship To Neuro-Symbolic Interface

The neuro-symbolic layer should be treated as evaluator infrastructure:

- symbolic judges provide hard constraints and deterministic calculations
- neural models may provide property estimates when benchmarked and authorized
- knowledge graph/source ledger provides provenance and rights context
- policy solver controls what evidence may influence selection

The genetic programming engine owns the candidate population, variation, retention, lineage, and selection workflow.

## MVP Implementation Implications

The current `suggestions` MVP should evolve from a stateless next-formulation endpoint into an `EvolutionCampaign` service.

Near-term implementation additions:

- `evolution_campaigns`
- `genomes`
- `generation_requests`
- `candidate_attempts`
- `fitness_components`
- `selection_decisions`
- `operator_registry`
- `generation_events`

The existing Gaussian Process / Expected Improvement suggestion engine remains useful after lab measurements exist, but it should be one selection strategy inside the broader genetic/evolutionary campaign architecture, not the whole optimization model.
