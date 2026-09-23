# Dependency-aware mission roadmap

Priority score = `3*decision_value + 3*evidence_gap + 2*authority_risk_reduction + 2*downstream_leverage - effort - external_delay`; all factors are integers from 0 through 5. Declared ladder rank is the deterministic tie-breaker. An active authority escalation, schema-integrity defect, or silent runtime divergence overrides both ladders as P0.

Factor columns are D (decision value), G (evidence gap), A (authority-risk reduction), L (downstream leverage), E (effort penalty), and X (external-delay penalty). Factors are explicit module assessments, not values derived from rank. Machine-readable per-factor rationales are checked in `config/module-priorities.json`.

## Scientific opportunity ladder

| Rank | Module | D | G | A | L | E | X | Score |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | `amphora-public-corrosion-benchmark` | 5 | 5 | 3 | 5 | 3 | 3 | 40 |
| 2 | `amphora-cure-potlife-gate` | 5 | 5 | 3 | 5 | 4 | 4 | 38 |
| 3 | `amphora-viscosity-score` | 5 | 5 | 2 | 5 | 4 | 4 | 36 |
| 4 | `amphora-barrier-corrosion-score` | 5 | 5 | 2 | 5 | 5 | 5 | 34 |
| 5 | `amphora-molecule-generator` | 4 | 5 | 3 | 5 | 5 | 4 | 34 |
| 6 | `amphora-molecule-role-ranker` | 4 | 4 | 3 | 5 | 3 | 3 | 34 |
| 7 | `amphora-molecule-novelty` | 3 | 4 | 3 | 5 | 2 | 2 | 33 |
| 8 | `amphora-solvency-score` | 4 | 5 | 2 | 3 | 5 | 5 | 27 |
| 9 | `amphora-process-qc-twin` | 4 | 4 | 3 | 3 | 5 | 5 | 26 |
| 10 | `amphora-tolerance-robustness` | 3 | 3 | 3 | 3 | 3 | 2 | 25 |
| 11 | `amphora-design-rule-score` | 3 | 4 | 2 | 3 | 4 | 3 | 24 |
| 12 | `amphora-molecule-property` | 3 | 3 | 2 | 2 | 2 | 2 | 22 |
| 13 | `amphora-formulation-universe` | 2 | 3 | 2 | 3 | 3 | 2 | 20 |
| 14 | `amphora-ingredient-library` | 2 | 2 | 2 | 3 | 2 | 1 | 19 |
| 15 | `amphora-envelope-gates` | 2 | 1 | 3 | 2 | 2 | 1 | 16 |
| 16 | `amphora-formulation-arithmetic` | 1 | 1 | 3 | 2 | 2 | 1 | 13 |
| 17 | `amphora-molecule-design-gate` | 1 | 1 | 3 | 1 | 2 | 1 | 11 |

## Infrastructure and assurance ladder

| Rank | Module | D | G | A | L | E | X | Score |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | `amphora-candidate-contract` | 5 | 4 | 5 | 5 | 2 | 0 | 45 |
| 2 | `amphora-model-card-authority` | 5 | 4 | 5 | 5 | 3 | 0 | 44 |
| 3 | `amphora-optimizer-orchestrator` | 5 | 4 | 5 | 5 | 4 | 0 | 43 |
| 4 | `amphora-evidence-intake-validator` | 5 | 4 | 5 | 4 | 2 | 0 | 43 |
| 5 | `amphora-run-provenance` | 4 | 4 | 5 | 5 | 2 | 0 | 42 |
| 6 | `amphora-redteam-audit` | 4 | 4 | 5 | 5 | 3 | 0 | 41 |
| 7 | `amphora-source-ledger` | 4 | 4 | 4 | 5 | 3 | 0 | 39 |
| 8 | `amphora-known-answer-benchmarks` | 4 | 3 | 4 | 5 | 2 | 0 | 37 |
| 9 | `amphora-sourceability-ehs` | 4 | 4 | 4 | 3 | 3 | 2 | 33 |
| 10 | `amphora-cro-protocol-packager` | 4 | 4 | 4 | 3 | 4 | 2 | 32 |
| 11 | `amphora-ip-fto-guard` | 3 | 3 | 5 | 2 | 2 | 2 | 28 |
| 12 | `amphora-report-packager` | 3 | 2 | 4 | 3 | 2 | 0 | 27 |

## Assessment basis

Every module below is assessed on the same basis: **current locked independent
promotion evidence is absent or incomplete.** What differs is the decision each
module exists to inform.

- `amphora-public-corrosion-benchmark` — whether public corrosion data can support a reproducible external benchmark
- `amphora-cure-potlife-gate` — whether a formulation should proceed to multi-temperature CRO cure testing
- `amphora-viscosity-score` — whether rheology and sag should be measured for a formulation
- `amphora-barrier-corrosion-score` — which barrier hypotheses merit blinded panel testing
- `amphora-molecule-generator` — which valid, diverse molecular proposals enter expert review
- `amphora-molecule-role-ranker` — whether a defined molecule fits an explicitly declared resin or hardener role
- `amphora-molecule-novelty` — whether a molecule expands the frozen corpus design space
- `amphora-solvency-score` — which solvent blends merit compatibility measurement
- `amphora-process-qc-twin` — which batches require review without granting release authority
- `amphora-tolerance-robustness` — whether declared input tolerances preserve all hard formulation gates
- `amphora-design-rule-score` — which within-study directional hypotheses deserve experiments
- `amphora-molecule-property` — whether exact molecular properties are computable within a defined single-component domain
- `amphora-formulation-universe` — whether a declared formulation search space has been completely accounted
- `amphora-ingredient-library` — whether all positive-mass ingredients have cited constants for the requested calculation
- `amphora-envelope-gates` — whether deterministic formulation margins satisfy the declared screening envelope
- `amphora-formulation-arithmetic` — whether a declared two-part recipe has finite internally consistent formulation arithmetic
- `amphora-molecule-design-gate` — whether a defined molecule passes structural applicability rules
- `amphora-candidate-contract` — whether candidate and score messages are canonical and safe to dispatch
- `amphora-model-card-authority` — whether a model receipt may be used at a requested R&D authority level
- `amphora-optimizer-orchestrator` — which centrally authorized objectives and constraints may reach Pareto selection
- `amphora-evidence-intake-validator` — whether observed evidence bytes may enter the accepted evidence store
- `amphora-run-provenance` — whether a complete validated run can be replayed from hash-bound inputs
- `amphora-redteam-audit` — whether artifacts preserve contracts, claim locks, and prohibited-claim boundaries
- `amphora-source-ledger` — whether a scientific constant has a current traceable source and permitted use
- `amphora-known-answer-benchmarks` — whether deterministic services still match locked positive and negative controls
- `amphora-sourceability-ehs` — whether candidate-bound public evidence justifies further supplier diligence
- `amphora-cro-protocol-packager` — whether a candidate-bound numeric recipe is complete enough to issue a CRO protocol
- `amphora-ip-fto-guard` — which technical patent categories require qualified counsel review
- `amphora-report-packager` — whether validated envelopes can be packaged without stripping locks or escalating claims

## Delivery waves

### Wave 0 — Trust boundary

Prerequisite waves: none. Phase claim: `NO_AUTOMATIC_PROMOTION`.

- `amphora-candidate-contract` — Schema/runtime parity, finite canonical hashing, and typed candidate payload enforcement. Prerequisites: none.
- `amphora-run-provenance` — Validated nonempty artifact sets and replay-bound canonical input/output hashes. Prerequisites: `amphora-candidate-contract`.
- `amphora-source-ledger` — Hash-bound cited-constant records with unresolved rights and mutation surfaced. Prerequisites: `amphora-candidate-contract`.
- `amphora-model-card-authority` — Minimum-privilege receipt evaluation across manifest, adapter, model card, portfolio, and envelope. Prerequisites: `amphora-candidate-contract`, `amphora-run-provenance`.
- `amphora-evidence-intake-validator` — Observed-byte hash verification with candidate/issuer binding and fail-closed signatures. Prerequisites: `amphora-candidate-contract`, `amphora-source-ledger`.
- `amphora-redteam-audit` — Malformed-envelope, unknown-lock, and authority-escalation regression corpus. Prerequisites: `amphora-candidate-contract`, `amphora-model-card-authority`.
- `amphora-optimizer-orchestrator` — Python policy resolution plus Rust final rejection of spoofed or unauthorized ranking rows. Prerequisites: `amphora-candidate-contract`, `amphora-model-card-authority`, `amphora-redteam-audit`.
- `amphora-ingredient-library` — Positive-mass-only cited-constant coverage with zero-mass ingredients ignored. Prerequisites: `amphora-candidate-contract`, `amphora-source-ledger`.
- `amphora-formulation-arithmetic` — Finite deterministic arithmetic separated from formulation fitness and objective eligibility. Prerequisites: `amphora-ingredient-library`.
- `amphora-formulation-universe` — Required formulation input and exact Cartesian solved/infeasible accounting. Prerequisites: `amphora-ingredient-library`, `amphora-formulation-arithmetic`.
- `amphora-envelope-gates` — Consistent in-domain status, hard gates, and signed margins. Prerequisites: `amphora-formulation-arithmetic`.
- `amphora-molecule-property` — Single-component applicability rules and locked EEW/AHEW known answers. Prerequisites: `amphora-candidate-contract`, `amphora-source-ledger`.
- `amphora-molecule-design-gate` — Malformed, polymeric, mixture, and nonreactive structure rejection controls. Prerequisites: `amphora-candidate-contract`, `amphora-molecule-property`.
- `amphora-tolerance-robustness` — Finite perturbation gates whose robust flag, objective, and receipt agree. Prerequisites: `amphora-formulation-arithmetic`, `amphora-envelope-gates`.
- `amphora-sourceability-ehs` — Candidate-bound current public prescreen without supplier or procurement closure. Prerequisites: `amphora-evidence-intake-validator`.
- `amphora-cro-protocol-packager` — Finite nonnegative unit-normalized recipe packets bound to candidate and formula hashes. Prerequisites: `amphora-candidate-contract`, `amphora-formulation-arithmetic`.
- `amphora-ip-fto-guard` — Technical landscape output that always states FTO was not performed. Prerequisites: `amphora-evidence-intake-validator`.
- `amphora-report-packager` — Validated-envelope packaging that preserves authority and every claim lock. Prerequisites: `amphora-run-provenance`, `amphora-redteam-audit`.

### Wave 1 — Data foundation

Prerequisite waves: Wave 0. Phase claim: `NO_AUTOMATIC_PROMOTION`.

- `amphora-known-answer-benchmarks` — Versioned positive/negative controls for deterministic services. Prerequisites: `amphora-candidate-contract`, `amphora-source-ledger`.
- `amphora-public-corrosion-benchmark` — Reproducible labels, group identities, rights, hashes, hostile nulls, and locked external split. Prerequisites: `amphora-evidence-intake-validator`, `amphora-source-ledger`.
- `amphora-cure-potlife-gate` — Complete family/source-held-out rows plus multi-temperature capture schema. Prerequisites: `amphora-cro-protocol-packager`, `amphora-evidence-intake-validator`.
- `amphora-viscosity-score` — Measured KU/sag schema across formulation families and temperatures. Prerequisites: `amphora-cro-protocol-packager`, `amphora-evidence-intake-validator`.
- `amphora-barrier-corrosion-score` — Blinded four-track panel protocol with solids-only and PVC-only hostile nulls. Prerequisites: `amphora-public-corrosion-benchmark`, `amphora-cro-protocol-packager`.
- `amphora-molecule-generator` — Deterministic lineage, validity, uniqueness, scaffold split, and synthesis-review manifests. Prerequisites: `amphora-candidate-contract`, `amphora-molecule-design-gate`.
- `amphora-molecule-role-ranker` — Frozen role-fit dataset with explicit resin/hardener labels and ambiguous-role controls. Prerequisites: `amphora-molecule-property`, `amphora-molecule-design-gate`.
- `amphora-molecule-novelty` — Frozen canonical corpus and scaffold-aware distance controls. Prerequisites: `amphora-candidate-contract`.
- `amphora-solvency-score` — Measured blend schema with group-held-out identities and calibration fields. Prerequisites: `amphora-evidence-intake-validator`, `amphora-source-ledger`.
- `amphora-process-qc-twin` — Candidate/batch-bound prospective pilot schema and seeded-control plan without release authority. Prerequisites: `amphora-evidence-intake-validator`, `amphora-run-provenance`.
- `amphora-design-rule-score` — Eligible literature-series manifest with study-held-out split and named baseline. Prerequisites: `amphora-evidence-intake-validator`, `amphora-source-ledger`.

### Wave 2 — Human parity

Prerequisite waves: Wave 0, Wave 1. Phase claim: `PHASE_1_ONLY_IF_LOCKED_GATES_PASS`.

Wave-wide obligation, identical for every module listed: Run the named group/time/source-safe locked benchmark, attach uncertainty, and issue an independent receipt without presumed promotion.

Additional prerequisite beyond the module itself: `amphora-known-answer-benchmarks`.

Modules:

- `amphora-public-corrosion-benchmark`
- `amphora-cure-potlife-gate`
- `amphora-viscosity-score`
- `amphora-barrier-corrosion-score`
- `amphora-molecule-generator`
- `amphora-molecule-role-ranker`
- `amphora-molecule-novelty`
- `amphora-solvency-score`
- `amphora-process-qc-twin`
- `amphora-tolerance-robustness`
- `amphora-design-rule-score`
- `amphora-molecule-property`
- `amphora-formulation-universe`
- `amphora-ingredient-library`
- `amphora-envelope-gates`
- `amphora-formulation-arithmetic`
- `amphora-molecule-design-gate`

### Wave 3 — Closed-loop validation

Prerequisite waves: Wave 0, Wave 1, Wave 2. Phase claim: `NO_AUTOMATIC_PROMOTION`.

Wave-wide obligation, identical for every module listed: Compare solver- and expert-selected candidates under equal budgets; measure hit rate, regret, diversity, failures, time, and cost.

Additional prerequisite beyond the module itself: `amphora-optimizer-orchestrator`, `amphora-cro-protocol-packager`, `amphora-run-provenance`.

Modules:

- `amphora-molecule-generator`
- `amphora-molecule-role-ranker`
- `amphora-molecule-novelty`
- `amphora-solvency-score`
- `amphora-cure-potlife-gate`
- `amphora-viscosity-score`
- `amphora-barrier-corrosion-score`
- `amphora-tolerance-robustness`
- `amphora-process-qc-twin`

### Wave 4 — Defensible IP

Prerequisite waves: Wave 0, Wave 1, Wave 2, Wave 3. Phase claim: `PHASE_2_ONLY_IF_ALL_REPLICATION_AND_IP_GATES_PASS`.

Wave-wide obligation, identical for every module listed: Independently repeat prospective superiority, freeze owned provenance and ablations, and document patent-versus-trade-secret review; product, procurement, release, and legal authority remain excluded.

Additional prerequisite beyond the module itself: `amphora-evidence-intake-validator`, `amphora-run-provenance`, `amphora-ip-fto-guard`.

Modules:

- `amphora-public-corrosion-benchmark`
- `amphora-cure-potlife-gate`
- `amphora-viscosity-score`
- `amphora-barrier-corrosion-score`
- `amphora-molecule-generator`
- `amphora-solvency-score`
- `amphora-process-qc-twin`
