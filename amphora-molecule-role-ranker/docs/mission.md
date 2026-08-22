---
{"audit_date": "2026-07-17", "authority_ceiling": "LIMITED_SANITY", "candidate_types": ["molecule"], "capability_profile": "capability-profile.json", "consumers": [], "dependencies": ["amphora-candidate-contract", "amphora-source-ledger"], "evidence_inventory": "../../config/module-evidence-inventory.json", "lane": "molecule", "module_id": "amphora-molecule-role-ranker", "operational_readiness": "SHADOW", "phase": "PRE_PHASE_0", "schema": "amphora.module-mission.v1", "scientific_readiness": "UNVALIDATED", "solver_use_ceiling": "R&D_OBJECTIVE"}
---

# amphora-molecule-role-ranker mission

## Decision and falsifiable hypothesis

This module supports the decision of whether a defined molecule fits an explicitly declared resin or hardener role. Its falsifiable hypothesis is that exact reactive-function controls can noninferiorly reproduce a frozen role-fit baseline.

It does not establish product qualification, batch release, procurement approval, legal freedom to operate, regulatory compliance, supplier closure, or wet-lab performance. Phase 2, if later earned, means defensible R&D technical IP only.

## Honest current state

The live checked implementation is native Rust at `amphora-molecule-capabilities/src/lib.rs` with SHA-256 `5968f518f199cf697d153018afdfee887e9b3ec0bee8a9c00dcc3c5a854ec861`. Runtime registration is owned by `amphora-engine/src/lib.rs` and is checked against `module-manifest.json`. Retired Python implementation records have diagnostic provenance only and are not live authority.

Focused checked test evidence:

- `amphora-molecule-capabilities/src/lib.rs` — SHA-256 `5968f518f199cf697d153018afdfee887e9b3ec0bee8a9c00dcc3c5a854ec861`

Operational state is `SHADOW`; scientific state is `UNVALIDATED`, so the current phase is **Pre-Phase 0**. Execution and passing unit tests do not establish human parity. No readiness percentage is asserted.

### Checked datasets and artifacts

- `dataset` `amphora-molecule-role-ranker/reference/mvp20/data/corrosion_series.json` — SHA-256 `ef5cf7b4af77dbb74aa2c9ae112fed56e9132b9bcb0265065c8490b15aebdfde`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-molecule-role-ranker/reference/mvp20/data/cure_verification_set.json` — SHA-256 `884356a094bd6f4def926e7ef218070b83d917742009c8922f953c097f9305d2`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-molecule-role-ranker/reference/mvp20/data/facts.json` — SHA-256 `0af2456a443692093fc4a89174e5cc87da86323108b14c3aa20cc3af159f06fb`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-molecule-role-ranker/reference/mvp20/data/feedback_v1/dataset_context.json` — SHA-256 `49a3f6ffd663ce136542c6efa650f881d037b3a24fede9d6b1866e7f918ab01a`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-molecule-role-ranker/reference/mvp20/data/molecule_library.json` — SHA-256 `1f83a689db0997a5c226b3838ad0c1cb46e1b363004d526319c1761fc7ae8fe6`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-molecule-role-ranker/reference/mvp20/data/role_fit_benchmark.v1.json` — SHA-256 `74c01721752ce42a55b3c76e586446954cdb3c3e701eaa9914ec2bd93c8312ee`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)

Rights are reported per file; local presence is not evidence of ownership or permission. Artifact presence and a matching hash do not establish dataset rights, scientific validity, or ownership. All listed artifact rights remain `UNRESOLVED` because no SHA-bound rights receipt was found.

### Current benchmark result

Phase-0 known-answer harness at
`amphora-molecule-capabilities/tests/role_ranker_phase0_kpi.rs` drives the
deterministic capability across a self-authored fixture at
`amphora-molecule-role-ranker/reference/phase0-role-known-answer.v1.json`
(SHA-256 `8ce4d54192a20e8de1bb89f6181b11630fc184b4dda2918ce934610630855c8f`;
CC0-1.0, `eligible_for_derivatives: true`; 39 records: 12 epoxy resins,
12 amine hardeners, 6 dual-functional ambiguous hostile nulls, 6
no-reactive-group out-of-domain controls, 3 commercial polydisperse DGEBA
records) and emits a byte-stable canonical receipt at
`evidence/phase0/benchmark/result.v1.json`
(SHA-256 `f2a21f74e03b6b20f53fb10d4cdb6f2b477ce2b9a6e5200947c1ed91ad3a136a`).
The Phase-0 KPI receipt lives at
`evidence/phase0/kpis/role-classification-kpi.v1.json`.

Observed Phase-0 KPI outcomes (all deterministic, `cargo test --workspace --locked`):

- `structural_inference_agreement_rate` observed 1.0 (24/24 resin+hardener) — **PASSED** (threshold 1.0)
- `ambiguous_rejection_rate` observed 1.0 (6/6 dual-functional glycidylamines correctly return `role_fit_status: ABSTAINED_AMBIGUOUS_OR_OUT_OF_DOMAIN`) — **PASSED**
- `out_of_domain_rejection_rate` observed 1.0 (6/6 alkanes/alcohols/amides/ketones/aromatics correctly abstain) — **PASSED**
- `measured_only_lock_preservation_rate` observed 1.0 (3/3 commercial DGEBA records keep `commercial_product_claim_locked=true`) — **PASSED**
- `unauthorized_objective_boundary_rate` observed 1.0 (39/39 records return empty `objective_values` in the absence of an authorized model) — **PASSED**
- `fitted_model_baseline_agreement_rate` observed 1.0 (24/24 fitted-model resin_probability agrees with structural label at threshold 0.5) — **PASSED**
- `expected_calibration_error` observed **0.00199** (Brier score on the 24 in-domain records; reported observationally; Phase-1 lock will gate at ≤ 0.10 with an independently double-labeled expert reference)

The fitted logistic regression is trained offline via scikit-learn 1.7.2
(L2, C=1, LBFGS) over z-scored structural features
(`molecular_weight_g_mol`, `oxirane_ring_count`,
`reactive_amine_hydrogen_count`, `has_oxirane`,
`has_reactive_amine_hydrogen`) and reaches 100% training accuracy on the
24 in-domain records. Frozen coefficients, means, and scales live in both
the fixture and the KPI receipt so auditors can independently replay the
sigmoid math. The authorized-objective path at runtime remains gated by
`AuthorizedMoleculeModelInputV1::validate_binding` — even a
candidate-supplied Phase-1 receipt is rejected (unit test
`caller_supplied_role_receipt_cannot_authorize_an_objective`).

### Phase-0 readiness

All Phase-0 deterministic gates in
`evidence/phase0/promotion/policy.v1.json` (`RIGHTS` for the CC0
self-authored fixture, `LOCKED_SPLIT`, `LOCKED_BENCHMARK`, `TWO_REPLAYS`,
`RED_TEAM` across ~23 attack axes, `CLAIM_LOCKS`, `FOLDER_CONFINEMENT`,
`BENCHMARK_EXECUTION_COMPLETE`, `MODULE_INVARIANTS`) are passing.
Awaiting `PHASE0_EVALUATOR` and `PHASE0_INTERNAL_REVIEWER` signatures per
the `evaluation.v1.dsse.json` and `phase0-review-receipt.v1.json`
protocol before the `phase` header flips to `PHASE_0`. No signed receipt
has been produced yet; the module remains `PRE_PHASE_0` for authority
purposes, and `operational_readiness` stays `SHADOW`.

### Known contradictions

- Role-fit rules and declared evidence do not establish polyamide identity, marine qualification, synthesis feasibility, or performance.

Across the portfolio, the emitted envelope, adapter, manifest, model receipt/card, portfolio policy, and Rust ranking boundary must all agree. The most restrictive policy controls.

## Inputs, outputs, and normalization

Current accepted format: canonical CandidateEnvelope JSON. The current runtime supports JSON plus molecule SMILES only through the central candidate contract. Target interface: canonical CandidateEnvelope JSON. That target interface is already the runtime interface for this module. Unsupported formats fail closed.

External chemistry normalizes once in `amphora-candidate-contract`; this module consumes canonical `CandidateEnvelope` data. Original bytes, normalized structure/formula, toolkit/version, stereochemistry, isotope, charge, fragment, mixture, polymer, and commercial-grade policies are retained in the capability profile.

Canonical input is a finite `molecule` `CandidateEnvelope` whose payload matches `candidate_type`. Canonical output is `ScoreEnvelope`; the primary value path is `objective_values.role_fit`. Units, direction, nullability, authority, uncertainty, and claim locks are explicit in the profile and envelope. A null or blocked value cannot be converted to an objective.

## Canonical current examples and typed paths

```json
{"candidate_id": "amphora-molecule-role-ranker-example", "candidate_type": "molecule", "molecule": {"role": "resin", "smiles": "CC"}}
```

The schema-valid fail-closed output example is checked in at `docs/capability-profile.json#/examples/current_output`. Exact paths are: objective `objective_values.role_fit`, metric `objective_values.role_fit`, gate `gates`, uncertainty `uncertainty`, evidence gaps `missing_inputs`, and claim locks `claim_locks`. Nullability is explicit; empirical units and direction come only from the locked benchmark receipt. The authority ceiling is `LIMITED_SANITY` and solver-use ceiling is `R&D_OBJECTIVE`.

## Data, theory, model, and uncertainty strategy

Applicability domain is solvent-borne two-component epoxy-polyamide marine-coating R&D and the explicitly declared candidate types. Missing values are not imputed across an authority boundary. Empirical work uses group, family, source, and time-safe splits; computed values remain labeled computed; candidate evidence remains separate from public context. Subgroup reporting and calibrated intervals are required wherever the locked KPI is empirical. Named standard, expert/CRO, primary-literature, simple physical, and hostile-null baselines precede promotion.

## KPI register and promotion gates

Primary KPI: **role-fit benchmark pass** at `objective_values.role_fit`. Direction and unit are declared by the locked benchmark; population is the declared applicability domain; split is group/time/source-safe; confidence intervals are mandatory for empirical claims. Locked target: Zero silent acceptance of malformed, unsupported, or unauthorized inputs before Phase 0; locked module-specific benchmark required for Phase 1.

- Phase 0 — Useful: deterministic or evidence-bound capability, contract parity, fail-closed malformed/OOD behavior, no unresolved authority contradiction, and the module acceptance tests pass.
- Phase 1 — Human parity: the locked independent evaluation beats or matches the best reproducible named baseline at the stated target with uncertainty.
- Phase 2 — Defensible IP: prospective superiority repeats independently, owned provenance and ablations freeze, and patent-versus-trade-secret review is documented. Counsel separately determines FTO.

Focused acceptance command: `rtk cargo test --workspace --locked`. The native demo and replay commands in `AMPHORA_RUST.md` are the portfolio acceptance path.

External dependency or delay:

- Independent expert role labels and candidate-bound grade evidence

Estimated effort is represented by the checked-in 0–5 priority factors, not a fabricated schedule. Schema drift, source mutation, incomplete folds, non-finite output, authority escalation, or lost claim locks automatically demote the module.

## Red-team dossier

Regression coverage must exercise malformed chemistry; mixtures, fragments, and polymers; unsupported formats; unit ambiguity; zero-mass ingredients; NaN and Infinity; out-of-domain inputs; group/source/time leakage; mutated sources; computed-as-measured records; spoofed identity; authority escalation; stripped or unknown claim locks; fixed-seed replay drift; and legal, regulatory, supplier, procurement, qualification, or release overclaim. Every such case must fail closed or remain an explicit evidence gap.

Module-focused checked fixture: `amphora-molecule-capabilities/src/lib.rs` via `rtk cargo test --workspace --locked`. Scenario: Keep measured-only and missing-class evidence from becoming qualification authority.
